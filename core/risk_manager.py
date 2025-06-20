"""
SignalOS Risk Manager
Equity protection, drawdown management, and risk controls
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class RiskSettings:
    max_daily_loss_percent: float = 5.0
    max_daily_loss_amount: float = 1000.0
    max_equity_drawdown_percent: float = 10.0
    max_concurrent_trades: int = 10
    max_risk_per_trade_percent: float = 2.0
    max_trades_per_day: int = 50
    max_trades_per_hour: int = 10
    stop_trading_on_loss: bool = True
    emergency_close_all: bool = False

@dataclass
class LotSizeConfig:
    mode: str = "fixed"  # fixed, percent_balance, risk_to_sl, from_signal
    fixed_lots: float = 0.01
    balance_percent: float = 1.0
    risk_percent: float = 1.0
    max_lots: float = 1.0
    min_lots: float = 0.01

@dataclass
class NewsFilter:
    enabled: bool = False
    minutes_before: int = 30
    minutes_after: int = 30
    high_impact_only: bool = True
    currencies: List[str] = None

@dataclass
class TimeWindow:
    enabled: bool = False
    start_hour: int = 8
    end_hour: int = 18
    timezone: str = "UTC"
    trading_days: List[str] = None  # ['Monday', 'Tuesday', etc.]

class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, settings: RiskSettings = None):
        self.settings = settings or RiskSettings()
        self.lot_config = LotSizeConfig()
        self.news_filter = NewsFilter()
        self.time_window = TimeWindow()
        
        self.daily_stats = {
            "trades_count": 0,
            "profit_loss": 0.0,
            "last_reset": datetime.utcnow().date()
        }
        self.hourly_trades = []
        self.account_balance = 10000.0  # Default, should be updated from MT5
        self.account_equity = 10000.0
        self.peak_equity = 10000.0
        
    async def check_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Comprehensive signal validation"""
        try:
            # Reset daily stats if new day
            self._reset_daily_stats_if_needed()
            
            # Check if trading is stopped
            if self.settings.emergency_close_all:
                logger.warning("Emergency mode active - all trading stopped")
                return False
            
            # Check daily loss limits
            if not self._check_daily_limits():
                return False
            
            # Check equity drawdown
            if not self._check_equity_drawdown():
                return False
            
            # Check concurrent trades
            if not await self._check_concurrent_trades():
                return False
            
            # Check hourly trade limits
            if not self._check_hourly_limits():
                return False
            
            # Check time windows
            if not self._check_time_window():
                return False
            
            # Check news filter
            if not await self._check_news_filter(signal_data):
                return False
            
            logger.info(f"Signal {signal_data.get('id')} passed all risk checks")
            return True
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            return False
    
    def calculate_lot_size(self, signal_data: Dict[str, Any]) -> float:
        """Calculate appropriate lot size based on configuration"""
        try:
            if self.lot_config.mode == "fixed":
                return self._validate_lot_size(self.lot_config.fixed_lots)
            
            elif self.lot_config.mode == "percent_balance":
                balance_risk = self.account_balance * (self.lot_config.balance_percent / 100)
                # Approximate lot size (simplified calculation)
                lot_size = balance_risk / 1000  # Rough approximation
                return self._validate_lot_size(lot_size)
            
            elif self.lot_config.mode == "risk_to_sl":
                return self._calculate_risk_based_lot_size(signal_data)
            
            elif self.lot_config.mode == "from_signal":
                signal_risk = signal_data.get("risk_percent", 1.0)
                return self._calculate_signal_risk_lot_size(signal_data, signal_risk)
            
            return self._validate_lot_size(self.lot_config.fixed_lots)
            
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}")
            return self.lot_config.min_lots
    
    def _calculate_risk_based_lot_size(self, signal_data: Dict[str, Any]) -> float:
        """Calculate lot size based on risk-to-SL ratio"""
        try:
            entry = signal_data.get("entry", 0)
            sl = signal_data.get("sl", 0)
            pair = signal_data.get("pair", "EURUSD")
            
            if not entry or not sl:
                return self.lot_config.min_lots
            
            # Calculate pip difference
            pip_diff = abs(entry - sl)
            if pair.endswith("JPY"):
                pip_diff *= 100  # JPY pairs have different pip calculation
            else:
                pip_diff *= 10000  # Standard pairs
            
            if pip_diff == 0:
                return self.lot_config.min_lots
            
            # Risk amount
            risk_amount = self.account_balance * (self.lot_config.risk_percent / 100)
            
            # Pip value calculation (simplified)
            pip_value = 10 if not pair.endswith("JPY") else 1000  # Per standard lot
            
            # Calculate lot size
            lot_size = risk_amount / (pip_diff * pip_value)
            
            return self._validate_lot_size(lot_size)
            
        except Exception as e:
            logger.error(f"Error in risk-based lot calculation: {e}")
            return self.lot_config.min_lots
    
    def _calculate_signal_risk_lot_size(self, signal_data: Dict[str, Any], risk_percent: float) -> float:
        """Calculate lot size from signal's risk specification"""
        try:
            risk_amount = self.account_balance * (risk_percent / 100)
            
            # Simple approximation - should be enhanced with proper pip value calculation
            lot_size = risk_amount / 1000
            
            return self._validate_lot_size(lot_size)
            
        except Exception as e:
            logger.error(f"Error in signal risk lot calculation: {e}")
            return self.lot_config.min_lots
    
    def _validate_lot_size(self, lot_size: float) -> float:
        """Validate and clamp lot size to configured limits"""
        lot_size = max(self.lot_config.min_lots, lot_size)
        lot_size = min(self.lot_config.max_lots, lot_size)
        
        # Round to valid lot size increment (0.01)
        lot_size = round(lot_size, 2)
        
        return lot_size
    
    def _reset_daily_stats_if_needed(self):
        """Reset daily statistics if new day"""
        today = datetime.utcnow().date()
        if self.daily_stats["last_reset"] != today:
            self.daily_stats = {
                "trades_count": 0,
                "profit_loss": 0.0,
                "last_reset": today
            }
            logger.info("Daily statistics reset")
    
    def _check_daily_limits(self) -> bool:
        """Check daily loss and trade limits"""
        # Check daily loss percentage
        if self.settings.max_daily_loss_percent > 0:
            loss_percent = (abs(self.daily_stats["profit_loss"]) / self.account_balance) * 100
            if self.daily_stats["profit_loss"] < 0 and loss_percent >= self.settings.max_daily_loss_percent:
                logger.warning(f"Daily loss limit reached: {loss_percent:.2f}%")
                return False
        
        # Check daily loss amount
        if self.settings.max_daily_loss_amount > 0:
            if self.daily_stats["profit_loss"] <= -self.settings.max_daily_loss_amount:
                logger.warning(f"Daily loss amount limit reached: ${abs(self.daily_stats['profit_loss'])}")
                return False
        
        # Check daily trade count
        if self.settings.max_trades_per_day > 0:
            if self.daily_stats["trades_count"] >= self.settings.max_trades_per_day:
                logger.warning(f"Daily trade limit reached: {self.daily_stats['trades_count']}")
                return False
        
        return True
    
    def _check_equity_drawdown(self) -> bool:
        """Check equity drawdown limits"""
        if self.settings.max_equity_drawdown_percent <= 0:
            return True
        
        current_drawdown = ((self.peak_equity - self.account_equity) / self.peak_equity) * 100
        
        if current_drawdown >= self.settings.max_equity_drawdown_percent:
            logger.warning(f"Equity drawdown limit reached: {current_drawdown:.2f}%")
            return False
        
        return True
    
    async def _check_concurrent_trades(self) -> bool:
        """Check concurrent trade limits"""
        # This would need to check with execution engine
        # For now, assume we're within limits
        return True
    
    def _check_hourly_limits(self) -> bool:
        """Check hourly trade limits"""
        if self.settings.max_trades_per_hour <= 0:
            return True
        
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self.hourly_trades = [t for t in self.hourly_trades if t > one_hour_ago]
        
        if len(self.hourly_trades) >= self.settings.max_trades_per_hour:
            logger.warning(f"Hourly trade limit reached: {len(self.hourly_trades)}")
            return False
        
        return True
    
    def _check_time_window(self) -> bool:
        """Check if current time is within trading window"""
        if not self.time_window.enabled:
            return True
        
        now = datetime.utcnow()
        current_hour = now.hour
        current_day = now.strftime('%A')
        
        # Check trading hours
        if not (self.time_window.start_hour <= current_hour < self.time_window.end_hour):
            logger.info(f"Outside trading hours: {current_hour}")
            return False
        
        # Check trading days
        if self.time_window.trading_days and current_day not in self.time_window.trading_days:
            logger.info(f"Not a trading day: {current_day}")
            return False
        
        return True
    
    async def _check_news_filter(self, signal_data: Dict[str, Any]) -> bool:
        """Check news filter (placeholder - would integrate with news API)"""
        if not self.news_filter.enabled:
            return True
        
        # Placeholder for news filtering logic
        # Would check against economic calendar API
        pair = signal_data.get("pair", "")
        
        # Extract currencies from pair
        currencies = [pair[:3], pair[3:6]] if len(pair) >= 6 else []
        
        # Check if any of the currencies have news events
        # This is a simplified check - real implementation would use news API
        
        return True  # Allow for now
    
    def update_account_info(self, balance: float, equity: float):
        """Update account balance and equity"""
        self.account_balance = balance
        self.account_equity = equity
        
        # Update peak equity
        if equity > self.peak_equity:
            self.peak_equity = equity
    
    def record_trade(self, profit_loss: float):
        """Record trade result"""
        self.daily_stats["trades_count"] += 1
        self.daily_stats["profit_loss"] += profit_loss
        self.hourly_trades.append(datetime.utcnow())
        
        logger.info(f"Trade recorded: P/L ${profit_loss:.2f}, Daily total: ${self.daily_stats['profit_loss']:.2f}")
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        self._reset_daily_stats_if_needed()
        
        # Calculate current drawdown
        current_drawdown = ((self.peak_equity - self.account_equity) / self.peak_equity) * 100 if self.peak_equity > 0 else 0
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        if current_drawdown >= self.settings.max_equity_drawdown_percent * 0.8:
            risk_level = RiskLevel.CRITICAL
        elif current_drawdown >= self.settings.max_equity_drawdown_percent * 0.6:
            risk_level = RiskLevel.HIGH
        elif current_drawdown >= self.settings.max_equity_drawdown_percent * 0.4:
            risk_level = RiskLevel.MEDIUM
        
        return {
            "risk_level": risk_level.value,
            "account_balance": self.account_balance,
            "account_equity": self.account_equity,
            "peak_equity": self.peak_equity,
            "current_drawdown_percent": current_drawdown,
            "daily_trades": self.daily_stats["trades_count"],
            "daily_pnl": self.daily_stats["profit_loss"],
            "hourly_trades": len(self.hourly_trades),
            "emergency_mode": self.settings.emergency_close_all,
            "trading_allowed": not self.settings.emergency_close_all and self._check_daily_limits() and self._check_equity_drawdown()
        }
    
    def set_emergency_mode(self, enabled: bool):
        """Enable/disable emergency mode"""
        self.settings.emergency_close_all = enabled
        logger.warning(f"Emergency mode {'enabled' if enabled else 'disabled'}")
    
    def update_risk_settings(self, new_settings: Dict[str, Any]):
        """Update risk management settings"""
        for key, value in new_settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                logger.info(f"Updated risk setting {key} = {value}")
    
    def update_lot_config(self, new_config: Dict[str, Any]):
        """Update lot size configuration"""
        for key, value in new_config.items():
            if hasattr(self.lot_config, key):
                setattr(self.lot_config, key, value)
                logger.info(f"Updated lot config {key} = {value}")
    
    def update_time_window(self, new_window: Dict[str, Any]):
        """Update trading time window"""
        for key, value in new_window.items():
            if hasattr(self.time_window, key):
                setattr(self.time_window, key, value)
                logger.info(f"Updated time window {key} = {value}")
    
    def update_news_filter(self, new_filter: Dict[str, Any]):
        """Update news filter settings"""
        for key, value in new_filter.items():
            if hasattr(self.news_filter, key):
                setattr(self.news_filter, key, value)
                logger.info(f"Updated news filter {key} = {value}")