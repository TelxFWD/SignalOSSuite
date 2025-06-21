"""
SignalOS Advanced Risk Manager
Comprehensive risk management with provider-specific controls
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .risk_manager import RiskManager, RiskSettings, LotSizeConfig

logger = logging.getLogger(__name__)

class DrawdownAction(Enum):
    STOP_NEW_SIGNALS = "STOP_NEW_SIGNALS"
    CLOSE_ALL_POSITIONS = "CLOSE_ALL_POSITIONS"
    CLOSE_LOSING_POSITIONS = "CLOSE_LOSING_POSITIONS"
    REDUCE_LOT_SIZES = "REDUCE_LOT_SIZES"
    ALERT_ONLY = "ALERT_ONLY"

@dataclass
class ProviderRiskSettings:
    provider_id: str
    max_daily_loss: float = 500.0
    max_concurrent_trades: int = 5
    max_lot_size: float = 1.0
    risk_per_trade_percent: float = 2.0
    enabled: bool = True
    
@dataclass
class PairRiskSettings:
    pair: str
    max_exposure_lots: float = 1.0
    max_trades_per_day: int = 10
    max_spread_pips: float = 5.0
    enabled: bool = True

@dataclass
class AdvancedDrawdownSettings:
    max_daily_drawdown_percent: float = 5.0
    max_daily_drawdown_amount: float = 1000.0
    max_weekly_drawdown_percent: float = 10.0
    max_monthly_drawdown_percent: float = 20.0
    drawdown_action: DrawdownAction = DrawdownAction.STOP_NEW_SIGNALS
    recovery_threshold_percent: float = 2.0  # Allow trading again when equity recovers by this %

@dataclass
class MarginSettings:
    min_margin_level_percent: float = 100.0  # Minimum margin level to allow new trades
    margin_call_action: DrawdownAction = DrawdownAction.CLOSE_LOSING_POSITIONS
    stop_out_buffer_percent: float = 20.0  # Stop trading when margin level is this % above stop out

class AdvancedRiskManager(RiskManager):
    """Advanced risk management with provider and pair-specific controls"""
    
    def __init__(self, settings: RiskSettings = None):
        super().__init__(settings)
        self.provider_settings: Dict[str, ProviderRiskSettings] = {}
        self.pair_settings: Dict[str, PairRiskSettings] = {}
        self.drawdown_settings = AdvancedDrawdownSettings()
        self.margin_settings = MarginSettings()
        
        # Advanced tracking
        self.provider_stats: Dict[str, Dict[str, Any]] = {}
        self.pair_exposure: Dict[str, float] = {}
        self.drawdown_history: List[Dict[str, Any]] = []
        self.peak_balance = self.account_balance
        self.current_drawdown_percent = 0.0
        
        # Signal frequency tracking
        self.signal_frequency: Dict[str, List[datetime]] = {}
        self.max_signals_per_minute = 10
        self.max_signals_per_hour = 100
        
    async def check_signal_advanced(self, signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Advanced signal validation with provider and pair specific checks"""
        try:
            # Basic checks first
            basic_allowed = await self.check_signal(signal_data)
            if not basic_allowed:
                return False, "Failed basic risk checks"
            
            provider_id = signal_data.get('provider_id')
            pair = signal_data.get('pair')
            
            # Provider-specific checks
            if provider_id:
                provider_allowed, provider_reason = self._check_provider_limits(provider_id, signal_data)
                if not provider_allowed:
                    return False, provider_reason
            
            # Pair-specific checks
            if pair:
                pair_allowed, pair_reason = self._check_pair_limits(pair, signal_data)
                if not pair_allowed:
                    return False, pair_reason
            
            # Advanced drawdown checks
            drawdown_allowed, drawdown_reason = self._check_advanced_drawdown()
            if not drawdown_allowed:
                return False, drawdown_reason
            
            # Margin level checks
            margin_allowed, margin_reason = await self._check_margin_levels()
            if not margin_allowed:
                return False, margin_reason
            
            # Signal frequency checks
            freq_allowed, freq_reason = self._check_signal_frequency(provider_id, pair)
            if not freq_allowed:
                return False, freq_reason
            
            return True, "Signal approved"
            
        except Exception as e:
            logger.error(f"Error in advanced signal check: {e}")
            return False, f"Risk check error: {str(e)}"
    
    def _check_provider_limits(self, provider_id: str, signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check provider-specific risk limits"""
        try:
            provider_settings = self.provider_settings.get(provider_id)
            if not provider_settings or not provider_settings.enabled:
                return True, ""
            
            # Initialize provider stats if not exists
            if provider_id not in self.provider_stats:
                self.provider_stats[provider_id] = {
                    'daily_pnl': 0.0,
                    'trades_today': 0,
                    'active_trades': 0,
                    'last_reset': datetime.utcnow().date()
                }
            
            stats = self.provider_stats[provider_id]
            
            # Reset daily stats if new day
            if stats['last_reset'] != datetime.utcnow().date():
                stats['daily_pnl'] = 0.0
                stats['trades_today'] = 0
                stats['last_reset'] = datetime.utcnow().date()
            
            # Check daily loss limit
            if stats['daily_pnl'] <= -provider_settings.max_daily_loss:
                return False, f"Provider {provider_id} daily loss limit exceeded"
            
            # Check concurrent trades
            if stats['active_trades'] >= provider_settings.max_concurrent_trades:
                return False, f"Provider {provider_id} max concurrent trades exceeded"
            
            # Check lot size limit
            requested_lots = signal_data.get('lot_size', 0.01)
            if requested_lots > provider_settings.max_lot_size:
                # Reduce lot size instead of blocking
                signal_data['lot_size'] = provider_settings.max_lot_size
                logger.info(f"Reduced lot size for provider {provider_id}: {requested_lots} -> {provider_settings.max_lot_size}")
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking provider limits: {e}")
            return True, ""  # Allow on error
    
    def _check_pair_limits(self, pair: str, signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check pair-specific risk limits"""
        try:
            pair_settings = self.pair_settings.get(pair)
            if not pair_settings or not pair_settings.enabled:
                return True, ""
            
            # Check current exposure
            current_exposure = self.pair_exposure.get(pair, 0.0)
            requested_lots = signal_data.get('lot_size', 0.01)
            
            if current_exposure + requested_lots > pair_settings.max_exposure_lots:
                return False, f"Pair {pair} exposure limit exceeded ({current_exposure + requested_lots} > {pair_settings.max_exposure_lots})"
            
            # Check daily trades for this pair
            today = datetime.utcnow().date()
            pair_trades_today = len([
                trade for trade in self.hourly_trades
                if trade.date() == today and getattr(trade, 'pair', None) == pair
            ])
            
            if pair_trades_today >= pair_settings.max_trades_per_day:
                return False, f"Pair {pair} daily trade limit exceeded"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking pair limits: {e}")
            return True, ""  # Allow on error
    
    def _check_advanced_drawdown(self) -> Tuple[bool, str]:
        """Check advanced drawdown rules"""
        try:
            # Update current drawdown
            self._update_drawdown_stats()
            
            # Check daily drawdown
            if self.current_drawdown_percent >= self.drawdown_settings.max_daily_drawdown_percent:
                return False, f"Daily drawdown limit exceeded: {self.current_drawdown_percent:.2f}%"
            
            # Check absolute amount
            daily_loss = abs(self.daily_stats["profit_loss"]) if self.daily_stats["profit_loss"] < 0 else 0
            if daily_loss >= self.drawdown_settings.max_daily_drawdown_amount:
                return False, f"Daily loss amount limit exceeded: ${daily_loss:.2f}"
            
            # Check if we're in recovery mode
            if self._is_in_recovery_mode():
                recovery_needed = self.drawdown_settings.recovery_threshold_percent
                return False, f"In recovery mode - need {recovery_needed}% equity recovery to resume trading"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking advanced drawdown: {e}")
            return True, ""  # Allow on error
    
    async def _check_margin_levels(self) -> Tuple[bool, str]:
        """Check margin level requirements"""
        try:
            # Get margin info from MT5 if available
            if not hasattr(self, 'mt5_bridge') or not self.mt5_bridge:
                return True, ""  # Skip check if no MT5 connection
            
            # This would get real margin data from MT5
            # For now, simulate based on account equity
            margin_level = (self.account_equity / max(self.account_equity * 0.1, 1)) * 100  # Simplified
            
            if margin_level < self.margin_settings.min_margin_level_percent:
                return False, f"Margin level too low: {margin_level:.1f}% (min: {self.margin_settings.min_margin_level_percent}%)"
            
            # Check stop out buffer
            stop_out_level = 50.0  # Typical stop out level
            safe_margin_level = stop_out_level + self.margin_settings.stop_out_buffer_percent
            
            if margin_level < safe_margin_level:
                return False, f"Margin level approaching stop out: {margin_level:.1f}% (safe: {safe_margin_level:.1f}%)"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking margin levels: {e}")
            return True, ""  # Allow on error
    
    def _check_signal_frequency(self, provider_id: str, pair: str) -> Tuple[bool, str]:
        """Check signal frequency limits"""
        try:
            now = datetime.utcnow()
            
            # Check overall signal frequency
            recent_signals = len([
                ts for ts in self.hourly_trades
                if (now - ts).total_seconds() < 60  # Last minute
            ])
            
            if recent_signals >= self.max_signals_per_minute:
                return False, f"Signal frequency too high: {recent_signals} signals in last minute"
            
            # Check hourly frequency
            hourly_signals = len([
                ts for ts in self.hourly_trades
                if (now - ts).total_seconds() < 3600  # Last hour
            ])
            
            if hourly_signals >= self.max_signals_per_hour:
                return False, f"Hourly signal limit exceeded: {hourly_signals} signals"
            
            # Check provider-specific frequency
            if provider_id:
                provider_key = f"provider_{provider_id}"
                if provider_key not in self.signal_frequency:
                    self.signal_frequency[provider_key] = []
                
                provider_signals = self.signal_frequency[provider_key]
                # Clean old signals (older than 1 hour)
                provider_signals[:] = [
                    ts for ts in provider_signals
                    if (now - ts).total_seconds() < 3600
                ]
                
                if len(provider_signals) >= 50:  # Max 50 signals per hour per provider
                    return False, f"Provider {provider_id} signal frequency too high"
            
            # Check pair-specific frequency
            if pair:
                pair_key = f"pair_{pair}"
                if pair_key not in self.signal_frequency:
                    self.signal_frequency[pair_key] = []
                
                pair_signals = self.signal_frequency[pair_key]
                # Clean old signals
                pair_signals[:] = [
                    ts for ts in pair_signals
                    if (now - ts).total_seconds() < 3600
                ]
                
                if len(pair_signals) >= 20:  # Max 20 signals per hour per pair
                    return False, f"Pair {pair} signal frequency too high"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking signal frequency: {e}")
            return True, ""  # Allow on error
    
    def _update_drawdown_stats(self):
        """Update drawdown statistics"""
        try:
            # Update peak balance
            if self.account_equity > self.peak_balance:
                self.peak_balance = self.account_equity
            
            # Calculate current drawdown
            if self.peak_balance > 0:
                self.current_drawdown_percent = ((self.peak_balance - self.account_equity) / self.peak_balance) * 100
            else:
                self.current_drawdown_percent = 0.0
            
            # Record drawdown event if significant
            if self.current_drawdown_percent > 1.0:  # More than 1% drawdown
                self.drawdown_history.append({
                    'timestamp': datetime.utcnow(),
                    'peak_balance': self.peak_balance,
                    'current_equity': self.account_equity,
                    'drawdown_percent': self.current_drawdown_percent,
                    'drawdown_amount': self.peak_balance - self.account_equity
                })
                
                # Keep only recent history
                if len(self.drawdown_history) > 100:
                    self.drawdown_history = self.drawdown_history[-100:]
            
        except Exception as e:
            logger.error(f"Error updating drawdown stats: {e}")
    
    def _is_in_recovery_mode(self) -> bool:
        """Check if system is in recovery mode"""
        try:
            # Check if we recently hit a major drawdown and haven't recovered enough
            if not self.drawdown_history:
                return False
            
            recent_drawdown = max(self.drawdown_history, key=lambda x: x['drawdown_percent'])
            
            # If max recent drawdown was significant and we haven't recovered enough
            if recent_drawdown['drawdown_percent'] >= self.drawdown_settings.max_daily_drawdown_percent * 0.8:
                recovery_needed = self.drawdown_settings.recovery_threshold_percent
                current_recovery = ((self.account_equity - recent_drawdown['current_equity']) / recent_drawdown['current_equity']) * 100
                
                return current_recovery < recovery_needed
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking recovery mode: {e}")
            return False
    
    def add_provider_settings(self, provider_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Add or update provider-specific risk settings"""
        try:
            provider_settings = ProviderRiskSettings(
                provider_id=provider_id,
                max_daily_loss=settings.get('max_daily_loss', 500.0),
                max_concurrent_trades=settings.get('max_concurrent_trades', 5),
                max_lot_size=settings.get('max_lot_size', 1.0),
                risk_per_trade_percent=settings.get('risk_per_trade_percent', 2.0),
                enabled=settings.get('enabled', True)
            )
            
            self.provider_settings[provider_id] = provider_settings
            
            return {
                'status': 'success',
                'message': f'Provider settings updated for {provider_id}'
            }
            
        except Exception as e:
            logger.error(f"Error adding provider settings: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def add_pair_settings(self, pair: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Add or update pair-specific risk settings"""
        try:
            pair_settings = PairRiskSettings(
                pair=pair,
                max_exposure_lots=settings.get('max_exposure_lots', 1.0),
                max_trades_per_day=settings.get('max_trades_per_day', 10),
                max_spread_pips=settings.get('max_spread_pips', 5.0),
                enabled=settings.get('enabled', True)
            )
            
            self.pair_settings[pair] = pair_settings
            
            return {
                'status': 'success',
                'message': f'Pair settings updated for {pair}'
            }
            
        except Exception as e:
            logger.error(f"Error adding pair settings: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def record_trade_advanced(self, trade_data: Dict[str, Any]):
        """Record trade with advanced tracking"""
        try:
            # Call parent method
            super().record_trade(trade_data.get('profit_loss', 0))
            
            # Advanced tracking
            provider_id = trade_data.get('provider_id')
            pair = trade_data.get('pair')
            lot_size = trade_data.get('lot_size', 0)
            
            # Update provider stats
            if provider_id and provider_id in self.provider_stats:
                stats = self.provider_stats[provider_id]
                stats['daily_pnl'] += trade_data.get('profit_loss', 0)
                if trade_data.get('status') == 'opened':
                    stats['active_trades'] += 1
                    stats['trades_today'] += 1
                elif trade_data.get('status') == 'closed':
                    stats['active_trades'] = max(0, stats['active_trades'] - 1)
            
            # Update pair exposure
            if pair:
                if trade_data.get('status') == 'opened':
                    self.pair_exposure[pair] = self.pair_exposure.get(pair, 0) + lot_size
                elif trade_data.get('status') == 'closed':
                    self.pair_exposure[pair] = max(0, self.pair_exposure.get(pair, 0) - lot_size)
            
            # Update signal frequency tracking
            now = datetime.utcnow()
            if provider_id:
                provider_key = f"provider_{provider_id}"
                if provider_key not in self.signal_frequency:
                    self.signal_frequency[provider_key] = []
                self.signal_frequency[provider_key].append(now)
            
            if pair:
                pair_key = f"pair_{pair}"
                if pair_key not in self.signal_frequency:
                    self.signal_frequency[pair_key] = []
                self.signal_frequency[pair_key].append(now)
            
        except Exception as e:
            logger.error(f"Error recording advanced trade: {e}")
    
    def get_advanced_risk_status(self) -> Dict[str, Any]:
        """Get comprehensive risk status"""
        try:
            basic_status = self.get_risk_status()
            
            # Add advanced metrics
            advanced_status = {
                **basic_status,
                'drawdown_stats': {
                    'current_drawdown_percent': self.current_drawdown_percent,
                    'peak_balance': self.peak_balance,
                    'max_daily_drawdown_limit': self.drawdown_settings.max_daily_drawdown_percent,
                    'in_recovery_mode': self._is_in_recovery_mode(),
                    'recent_max_drawdown': max([dd['drawdown_percent'] for dd in self.drawdown_history], default=0)
                },
                'provider_stats': {
                    pid: {
                        'daily_pnl': stats['daily_pnl'],
                        'trades_today': stats['trades_today'],
                        'active_trades': stats['active_trades'],
                        'settings': {
                            'max_daily_loss': self.provider_settings.get(pid, ProviderRiskSettings(pid)).max_daily_loss,
                            'max_concurrent': self.provider_settings.get(pid, ProviderRiskSettings(pid)).max_concurrent_trades,
                            'enabled': self.provider_settings.get(pid, ProviderRiskSettings(pid)).enabled
                        }
                    }
                    for pid, stats in self.provider_stats.items()
                },
                'pair_exposure': self.pair_exposure,
                'pair_settings_count': len(self.pair_settings),
                'provider_settings_count': len(self.provider_settings),
                'signal_frequency': {
                    key: len(signals) for key, signals in self.signal_frequency.items()
                }
            }
            
            return advanced_status
            
        except Exception as e:
            logger.error(f"Error getting advanced risk status: {e}")
            return self.get_risk_status()  # Fallback to basic status
    
    def trigger_emergency_action(self, action: DrawdownAction, reason: str) -> Dict[str, Any]:
        """Trigger emergency risk management action"""
        try:
            if action == DrawdownAction.STOP_NEW_SIGNALS:
                self.set_emergency_mode(True)
                message = "New signals blocked due to risk limits"
            
            elif action == DrawdownAction.CLOSE_ALL_POSITIONS:
                # This would close all positions via MT5
                message = "Emergency: All positions closed"
            
            elif action == DrawdownAction.CLOSE_LOSING_POSITIONS:
                # This would close only losing positions
                message = "Emergency: Losing positions closed"
            
            elif action == DrawdownAction.REDUCE_LOT_SIZES:
                # Reduce lot sizes for all providers
                for provider_settings in self.provider_settings.values():
                    provider_settings.max_lot_size *= 0.5
                message = "Emergency: Lot sizes reduced by 50%"
            
            else:
                message = f"Alert: {reason}"
            
            # Log emergency action
            logger.warning(f"Emergency action triggered: {action.value} - {reason}")
            
            return {
                'status': 'success',
                'action': action.value,
                'reason': reason,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error triggering emergency action: {e}")
            return {'status': 'error', 'message': str(e)}