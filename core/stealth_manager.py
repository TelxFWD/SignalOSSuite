"""
SignalOS Stealth Manager
Prop firm stealth capabilities and trade masking
"""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class StealthSettings:
    enabled: bool = False
    random_delay_min: float = 1.0  # seconds
    random_delay_max: float = 10.0  # seconds
    remove_comments: bool = True
    mask_sl_tp: bool = True
    cap_lots_per_pair: bool = True
    max_lots_per_pair: float = 0.1
    randomize_lot_sizes: bool = True
    lot_randomization_percent: float = 5.0  # ±5%
    delay_signal_execution: bool = True
    max_execution_delay: float = 60.0  # seconds
    spread_entry_orders: bool = True
    entry_spread_seconds: float = 30.0
    clone_detection_prevention: bool = True
    synthetic_trades: bool = False
    synthetic_trade_frequency: int = 10  # Every N real trades

class StealthManager:
    """Manages stealth features for prop firm compliance"""
    
    def __init__(self, settings: StealthSettings = None):
        self.settings = settings or StealthSettings()
        self.trade_history: List[Dict[str, Any]] = []
        self.delayed_orders: List[Dict[str, Any]] = []
        self.pair_lot_tracking: Dict[str, float] = {}
        self.last_synthetic_trade = datetime.utcnow()
        
    def process_signal_stealth(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stealth processing to signal"""
        if not self.settings.enabled:
            return signal_data
        
        try:
            modified_signal = signal_data.copy()
            stealth_actions = []
            
            # Apply random delay
            if self.settings.delay_signal_execution:
                delay = self._calculate_random_delay()
                modified_signal['execution_delay'] = delay
                stealth_actions.append(f"Delayed execution by {delay:.1f}s")
            
            # Randomize lot size
            if self.settings.randomize_lot_sizes:
                original_lot = modified_signal.get('lot_size', 0.01)
                randomized_lot = self._randomize_lot_size(original_lot)
                modified_signal['lot_size'] = randomized_lot
                stealth_actions.append(f"Lot size randomized: {original_lot} → {randomized_lot}")
            
            # Check lot cap per pair
            if self.settings.cap_lots_per_pair:
                pair = modified_signal.get('pair')
                if pair:
                    capped_lot = self._apply_lot_cap(pair, modified_signal.get('lot_size', 0.01))
                    if capped_lot != modified_signal.get('lot_size'):
                        modified_signal['lot_size'] = capped_lot
                        stealth_actions.append(f"Lot size capped for {pair}: {capped_lot}")
            
            # Remove/mask comments
            if self.settings.remove_comments:
                modified_signal['comment'] = ""
                modified_signal['magic_number'] = self._generate_random_magic()
                stealth_actions.append("Comments removed, magic number randomized")
            
            # Mask SL/TP (set via modification after execution)
            if self.settings.mask_sl_tp:
                masked_sl = modified_signal.pop('sl', None)
                masked_tp = modified_signal.pop('tp', None)
                if masked_sl or masked_tp:
                    modified_signal['deferred_sl_tp'] = {
                        'sl': masked_sl,
                        'tp': masked_tp,
                        'delay': random.uniform(5, 30)  # Apply after N seconds
                    }
                    stealth_actions.append("SL/TP masked for deferred application")
            
            # Check if synthetic trade should be added
            if self.settings.synthetic_trades:
                if self._should_add_synthetic_trade():
                    synthetic_trade = self._generate_synthetic_trade(modified_signal)
                    modified_signal['synthetic_companion'] = synthetic_trade
                    stealth_actions.append("Synthetic companion trade generated")
            
            modified_signal['stealth_actions'] = stealth_actions
            
            logger.info(f"Stealth processing applied: {len(stealth_actions)} actions")
            return modified_signal
            
        except Exception as e:
            logger.error(f"Error in stealth processing: {e}")
            return signal_data
    
    def _calculate_random_delay(self) -> float:
        """Calculate random delay for execution"""
        min_delay = self.settings.random_delay_min
        max_delay = min(self.settings.random_delay_max, self.settings.max_execution_delay)
        return random.uniform(min_delay, max_delay)
    
    def _randomize_lot_size(self, original_lot: float) -> float:
        """Apply randomization to lot size"""
        try:
            randomization = self.settings.lot_randomization_percent / 100
            variance = original_lot * randomization
            
            # Add random variance (can be positive or negative)
            adjustment = random.uniform(-variance, variance)
            randomized_lot = original_lot + adjustment
            
            # Ensure minimum lot size
            randomized_lot = max(0.01, randomized_lot)
            
            # Round to valid lot size increments
            randomized_lot = round(randomized_lot, 2)
            
            return randomized_lot
            
        except Exception as e:
            logger.error(f"Error randomizing lot size: {e}")
            return original_lot
    
    def _apply_lot_cap(self, pair: str, requested_lot: float) -> float:
        """Apply lot size cap per pair"""
        try:
            current_exposure = self.pair_lot_tracking.get(pair, 0.0)
            max_allowed = self.settings.max_lots_per_pair
            
            available_capacity = max_allowed - current_exposure
            capped_lot = min(requested_lot, available_capacity)
            
            # Ensure minimum viable lot
            if capped_lot < 0.01:
                capped_lot = 0.01  # Allow minimum but log warning
                logger.warning(f"Pair {pair} exceeds lot cap, using minimum lot size")
            
            return round(capped_lot, 2)
            
        except Exception as e:
            logger.error(f"Error applying lot cap: {e}")
            return requested_lot
    
    def _generate_random_magic(self) -> int:
        """Generate random magic number"""
        return random.randint(100000, 999999)
    
    def _should_add_synthetic_trade(self) -> bool:
        """Determine if synthetic trade should be added"""
        trades_since_synthetic = len([t for t in self.trade_history 
                                    if t.get('timestamp', datetime.min) > self.last_synthetic_trade])
        
        return trades_since_synthetic >= self.settings.synthetic_trade_frequency
    
    def _generate_synthetic_trade(self, reference_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic/decoy trade"""
        try:
            # Create opposite or unrelated trade
            synthetic_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
            reference_pair = reference_signal.get('pair', 'EURUSD')
            
            # Choose different pair
            available_pairs = [p for p in synthetic_pairs if p != reference_pair]
            synthetic_pair = random.choice(available_pairs) if available_pairs else 'EURUSD'
            
            # Opposite action or random
            reference_action = reference_signal.get('action', 'BUY')
            synthetic_action = 'SELL' if reference_action == 'BUY' else 'BUY'
            
            # Small lot size
            synthetic_lot = round(random.uniform(0.01, 0.05), 2)
            
            synthetic_trade = {
                'pair': synthetic_pair,
                'action': synthetic_action,
                'lot_size': synthetic_lot,
                'entry': 'MARKET',
                'sl': None,  # Will be set later
                'tp': None,  # Will be set later
                'synthetic': True,
                'reference_signal_id': reference_signal.get('id'),
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.last_synthetic_trade = datetime.utcnow()
            
            logger.info(f"Synthetic trade generated: {synthetic_pair} {synthetic_action} {synthetic_lot}")
            return synthetic_trade
            
        except Exception as e:
            logger.error(f"Error generating synthetic trade: {e}")
            return {}
    
    def update_pair_exposure(self, pair: str, lot_change: float):
        """Update pair exposure tracking"""
        try:
            current = self.pair_lot_tracking.get(pair, 0.0)
            new_exposure = current + lot_change
            
            if new_exposure <= 0:
                self.pair_lot_tracking.pop(pair, None)
            else:
                self.pair_lot_tracking[pair] = round(new_exposure, 2)
                
        except Exception as e:
            logger.error(f"Error updating pair exposure: {e}")
    
    def record_trade_execution(self, trade_data: Dict[str, Any]):
        """Record trade for stealth tracking"""
        try:
            trade_record = {
                'timestamp': datetime.utcnow(),
                'pair': trade_data.get('pair'),
                'action': trade_data.get('action'),
                'lot_size': trade_data.get('lot_size'),
                'synthetic': trade_data.get('synthetic', False),
                'stealth_applied': bool(trade_data.get('stealth_actions'))
            }
            
            self.trade_history.append(trade_record)
            
            # Update pair exposure
            if trade_data.get('action') in ['BUY', 'SELL']:
                lot_size = trade_data.get('lot_size', 0)
                self.update_pair_exposure(trade_data.get('pair', ''), lot_size)
            
            # Keep only recent history
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            self.trade_history = [t for t in self.trade_history if t['timestamp'] > cutoff_time]
            
        except Exception as e:
            logger.error(f"Error recording trade execution: {e}")
    
    def get_stealth_statistics(self) -> Dict[str, Any]:
        """Get stealth operation statistics"""
        try:
            recent_trades = len([t for t in self.trade_history 
                               if t['timestamp'] > datetime.utcnow() - timedelta(hours=24)])
            
            stealth_trades = len([t for t in self.trade_history 
                                if t.get('stealth_applied', False)])
            
            synthetic_trades = len([t for t in self.trade_history 
                                  if t.get('synthetic', False)])
            
            return {
                'stealth_enabled': self.settings.enabled,
                'trades_last_24h': recent_trades,
                'stealth_trades_percentage': (stealth_trades / max(len(self.trade_history), 1)) * 100,
                'synthetic_trades': synthetic_trades,
                'pair_exposures': self.pair_lot_tracking.copy(),
                'average_delay': self._calculate_average_delay(),
                'settings': {
                    'random_delay_range': f"{self.settings.random_delay_min}-{self.settings.random_delay_max}s",
                    'lot_randomization': f"±{self.settings.lot_randomization_percent}%",
                    'max_lots_per_pair': self.settings.max_lots_per_pair,
                    'synthetic_frequency': f"1 per {self.settings.synthetic_trade_frequency} trades"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting stealth statistics: {e}")
            return {"error": str(e)}
    
    def _calculate_average_delay(self) -> float:
        """Calculate average execution delay"""
        if not self.settings.delay_signal_execution:
            return 0.0
        
        return (self.settings.random_delay_min + self.settings.random_delay_max) / 2
    
    def update_stealth_settings(self, new_settings: Dict[str, Any]):
        """Update stealth settings"""
        try:
            for key, value in new_settings.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
                    logger.info(f"Stealth setting updated: {key} = {value}")
            
        except Exception as e:
            logger.error(f"Error updating stealth settings: {e}")
    
    def apply_deferred_sl_tp(self, order_id: str, deferred_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply deferred SL/TP after initial execution"""
        try:
            # Wait for specified delay
            delay = deferred_data.get('delay', 5.0)
            time.sleep(delay)
            
            # Return modification commands
            modifications = {}
            
            if deferred_data.get('sl'):
                modifications['stop_loss'] = deferred_data['sl']
            
            if deferred_data.get('tp'):
                modifications['take_profit'] = deferred_data['tp']
            
            logger.info(f"Applying deferred SL/TP to order {order_id}")
            
            return {
                'order_id': order_id,
                'modifications': modifications,
                'delay_applied': delay
            }
            
        except Exception as e:
            logger.error(f"Error applying deferred SL/TP: {e}")
            return {}
    
    def generate_clone_detection_report(self) -> Dict[str, Any]:
        """Generate report to help detect clone detection"""
        try:
            # Analyze trading patterns for clone detection risks
            analysis = {
                'risk_level': 'LOW',
                'risk_factors': [],
                'recommendations': []
            }
            
            # Check for suspicious patterns
            if len(set(t.get('pair') for t in self.trade_history)) < 3:
                analysis['risk_factors'].append("Limited pair diversity")
                analysis['risk_level'] = 'MEDIUM'
            
            lot_sizes = [t.get('lot_size', 0) for t in self.trade_history]
            if len(set(lot_sizes)) < 3:
                analysis['risk_factors'].append("Repetitive lot sizes")
                analysis['risk_level'] = 'HIGH' if analysis['risk_level'] != 'HIGH' else 'HIGH'
            
            # Timing analysis
            execution_times = [t.get('timestamp') for t in self.trade_history if t.get('timestamp')]
            if len(execution_times) > 1:
                time_intervals = []
                for i in range(1, len(execution_times)):
                    if execution_times[i] and execution_times[i-1]:
                        interval = (execution_times[i] - execution_times[i-1]).total_seconds()
                        time_intervals.append(interval)
                
                if time_intervals and len(set([round(t/60) for t in time_intervals])) < 3:
                    analysis['risk_factors'].append("Regular timing patterns")
                    analysis['risk_level'] = 'HIGH'
            
            # Generate recommendations
            if analysis['risk_level'] == 'HIGH':
                analysis['recommendations'].extend([
                    "Increase lot size randomization",
                    "Add more synthetic trades",
                    "Extend random delay ranges",
                    "Diversify trading pairs"
                ])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating clone detection report: {e}")
            return {"error": str(e)}