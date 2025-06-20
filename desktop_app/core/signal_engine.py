"""
Signal execution engine for processing and executing trading signals
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import asdict

try:
    from config.settings import AppSettings
    settings = AppSettings()
except ImportError:
    # Mock settings when not available
    class MockSettings:
        def __init__(self):
            self.app_dir = "/tmp/signalos"
            self.execution = type('obj', (object,), {'enabled': True})()
    settings = MockSettings()
try:
    from signal_model import ParsedSignal, ExecutionSignal, SignalStatus
except ImportError:
    # Mock signal models when not available
    class SignalStatus:
        PENDING = "pending"
        PROCESSING = "processing"
        EXECUTED = "executed"
        FAILED = "failed"
    
    class ParsedSignal:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class ExecutionSignal:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
import logging

logger = logging.getLogger(__name__)

class SignalEngine:
    """Engine for processing and executing trading signals"""
    
    def __init__(self):
        self.signal_queue = []
        self.processed_signals = []
        self.execution_queue = []
        self.signal_file = settings.app_dir / "signals" / "signal.json"
        self.backup_dir = settings.app_dir / "signals" / "backup"
        
        # Ensure directories exist
        self.signal_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing signals
        self.load_signals()
    
    def add_signal(self, parsed_signal: ParsedSignal) -> bool:
        """Add a parsed signal to the processing queue"""
        try:
            # Validate signal
            if not self.validate_signal(parsed_signal):
                logger.warning(f"Signal validation failed: {parsed_signal.pair}")
                return False
            
            # Add to queue
            self.signal_queue.append(parsed_signal)
            logger.info(f"Added signal to queue: {parsed_signal.pair} {parsed_signal.action}")
            
            # Process immediately if engine is enabled
            if settings.execution.enabled:
                return self.process_signal(parsed_signal)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding signal: {e}")
            return False
    
    def process_signal(self, parsed_signal: ParsedSignal) -> bool:
        """Process a parsed signal and create execution signal"""
        try:
            # Create execution signal
            execution_signal = self.create_execution_signal(parsed_signal)
            
            if not execution_signal:
                logger.error(f"Failed to create execution signal for {parsed_signal.pair}")
                return False
            
            # Apply stealth mode modifications if enabled
            if settings.execution.stealth_mode:
                execution_signal = self.apply_stealth_mode(execution_signal)
            
            # Add execution delay if configured
            if settings.execution.delay_seconds > 0:
                execution_signal.execution_time = datetime.now() + timedelta(
                    seconds=settings.execution.delay_seconds
                )
            
            # Add to execution queue
            self.execution_queue.append(execution_signal)
            
            # Write to signal.json for MT5 EA
            if not settings.shadow_mode:
                self.write_signal_file(execution_signal)
            
            # Move to processed
            self.processed_signals.append(parsed_signal)
            if parsed_signal in self.signal_queue:
                self.signal_queue.remove(parsed_signal)
            
            logger.info(f"Processed signal: {execution_signal.pair} {execution_signal.action}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return False
    
    def create_execution_signal(self, parsed_signal: ParsedSignal) -> Optional[ExecutionSignal]:
        """Create an execution signal from a parsed signal"""
        try:
            # Calculate risk management
            risk_data = self.calculate_risk_management(parsed_signal)
            
            # Create execution signal
            execution_signal = ExecutionSignal(
                signal_id=f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{parsed_signal.pair}",
                pair=parsed_signal.pair,
                action=parsed_signal.action,
                entry_price=parsed_signal.entry_price,
                stop_loss=self.adjust_stop_loss(parsed_signal),
                take_profit=self.adjust_take_profit(parsed_signal),
                lot_size=risk_data.get('lot_size', parsed_signal.lot_size or 0.01),
                magic_number=settings.mt5.magic_number,
                comment=self.generate_comment(parsed_signal),
                status=SignalStatus.PENDING,
                created_at=datetime.now(),
                metadata={
                    'original_confidence': parsed_signal.confidence,
                    'risk_percent': risk_data.get('risk_percent', 1.0),
                    'pip_value': risk_data.get('pip_value', 0.0)
                }
            )
            
            return execution_signal
            
        except Exception as e:
            logger.error(f"Error creating execution signal: {e}")
            return None
    
    def calculate_risk_management(self, signal: ParsedSignal) -> Dict[str, float]:
        """Calculate risk management parameters"""
        try:
            # Default values
            risk_data = {
                'lot_size': signal.lot_size or 0.01,
                'risk_percent': min(settings.execution.max_risk_percent, 2.0),
                'pip_value': 0.1
            }
            
            # Calculate position size based on risk percentage
            if signal.entry_price and signal.stop_loss:
                pip_distance = abs(signal.entry_price - signal.stop_loss)
                if pip_distance > 0:
                    # Simplified calculation - would need account balance for accurate sizing
                    risk_data['pip_distance'] = pip_distance
                    # Adjust lot size based on risk (simplified)
                    risk_data['lot_size'] = min(0.1, risk_data['risk_percent'] / 100.0)
            
            return risk_data
            
        except Exception as e:
            logger.error(f"Error calculating risk management: {e}")
            return {'lot_size': 0.01, 'risk_percent': 1.0, 'pip_value': 0.1}
    
    def adjust_stop_loss(self, signal: ParsedSignal) -> Optional[float]:
        """Adjust stop loss with buffer if configured"""
        if not signal.stop_loss:
            return None
        
        # Apply buffer pips
        buffer = settings.parser.buffer_pips / 10000.0  # Convert pips to price
        
        if signal.action == 'BUY':
            # For buy orders, SL should be below entry, so subtract buffer
            return signal.stop_loss - buffer
        else:
            # For sell orders, SL should be above entry, so add buffer
            return signal.stop_loss + buffer
    
    def adjust_take_profit(self, signal: ParsedSignal) -> Optional[float]:
        """Adjust take profit if needed"""
        if not signal.take_profit:
            return None
        
        # Apply buffer pips if needed
        buffer = settings.parser.buffer_pips / 10000.0
        
        if signal.action == 'BUY':
            # For buy orders, TP should be above entry
            return signal.take_profit + buffer
        else:
            # For sell orders, TP should be below entry
            return signal.take_profit - buffer
    
    def generate_comment(self, signal: ParsedSignal) -> str:
        """Generate comment for the trade"""
        if settings.execution.remove_comments:
            return ""
        
        return f"SignalOS_{signal.pair}_{datetime.now().strftime('%H%M%S')}"
    
    def apply_stealth_mode(self, execution_signal: ExecutionSignal) -> ExecutionSignal:
        """Apply stealth mode modifications with enhanced logging"""
        logger.info(f"Checking stealth mode for signal {getattr(execution_signal, 'signal_id', 'unknown')}")
        
        # Check if shadow mode is enabled (using correct attribute)
        shadow_mode_enabled = getattr(settings, 'shadow_mode', False)
        stealth_mode_enabled = getattr(settings.execution, 'stealth_mode', False) if hasattr(settings, 'execution') else False
        
        logger.info(f"Shadow mode: {shadow_mode_enabled}, Stealth mode: {stealth_mode_enabled}")
        
        if not (shadow_mode_enabled or stealth_mode_enabled):
            logger.info("Neither shadow nor stealth mode enabled, returning original signal")
            return execution_signal
            
        # Create a copy to avoid modifying the original
        from copy import deepcopy
        stealth_signal = deepcopy(execution_signal)
        
        # Apply shadow mode modifications
        if shadow_mode_enabled:
            logger.info("Applying shadow mode modifications")
            # In shadow mode, we simulate but don't actually execute
            if hasattr(stealth_signal, 'metadata'):
                stealth_signal.metadata['shadow_mode'] = True
                stealth_signal.metadata['original_execution'] = False
            
        # Apply stealth modifications
        if stealth_mode_enabled:
            logger.info("Applying stealth mode modifications")
            
            # Remove SL and TP if configured
            remove_sl_tp = getattr(settings.execution, 'remove_sl_tp', True)
            if remove_sl_tp:
                logger.info("Removing SL/TP for stealth mode")
                if hasattr(stealth_signal, 'stop_loss'):
                    stealth_signal.stop_loss = None
                if hasattr(stealth_signal, 'take_profit'):
                    stealth_signal.take_profit = None
            
            # Remove comment if configured
            remove_comments = getattr(settings.execution, 'remove_comments', True)
            if remove_comments:
                logger.info("Removing comments for stealth mode")
                if hasattr(stealth_signal, 'comment'):
                    stealth_signal.comment = ""
            else:
                if hasattr(stealth_signal, 'comment'):
                    stealth_signal.comment = getattr(stealth_signal, 'comment', '') + " [STEALTH]"
            
            # Modify magic number for stealth
            if hasattr(stealth_signal, 'magic_number'):
                stealth_signal.magic_number = 0
            
            # Mark as stealth in metadata
            if hasattr(stealth_signal, 'metadata'):
                stealth_signal.metadata['stealth_mode'] = True
                stealth_signal.metadata['original_sl'] = getattr(execution_signal, 'stop_loss', None)
                stealth_signal.metadata['original_tp'] = getattr(execution_signal, 'take_profit', None)
        
        logger.info(f"Applied stealth/shadow mode to signal {getattr(execution_signal, 'signal_id', 'unknown')}")
        return stealth_signal
    
    def write_signal_file(self, execution_signal: ExecutionSignal) -> bool:
        """Write execution signal to signal.json file for MT5 EA"""
        try:
            # Create signal data for MT5 EA
            signal_data = {
                'signal_id': execution_signal.signal_id,
                'pair': execution_signal.pair,
                'action': execution_signal.action,
                'entry_price': execution_signal.entry_price,
                'stop_loss': execution_signal.stop_loss,
                'take_profit': execution_signal.take_profit,
                'lot_size': execution_signal.lot_size,
                'magic_number': execution_signal.magic_number,
                'comment': execution_signal.comment,
                'timestamp': execution_signal.created_at.isoformat(),
                'execution_time': execution_signal.execution_time.isoformat() if execution_signal.execution_time else None
            }
            
            # Write to signal file
            with open(self.signal_file, 'w', encoding='utf-8') as f:
                json.dump(signal_data, f, indent=2, ensure_ascii=False)
            
            # Create backup
            backup_file = self.backup_dir / f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(signal_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Signal written to {self.signal_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing signal file: {e}")
            return False
    
    def validate_signal(self, signal: ParsedSignal) -> bool:
        """Validate signal before processing"""
        # Check required fields
        if not signal.pair or not signal.action:
            return False
        
        # Check confidence threshold
        if signal.confidence < settings.parser.confidence_threshold:
            return False
        
        # Check if signal is too old (older than 1 hour)
        if signal.parsed_at and (datetime.now() - signal.parsed_at).seconds > 3600:
            return False
        
        # Check for duplicate signals
        for processed in self.processed_signals[-10:]:  # Check last 10 signals
            if (processed.pair == signal.pair and 
                processed.action == signal.action and
                processed.entry_price == signal.entry_price):
                time_diff = datetime.now() - processed.parsed_at
                if time_diff.seconds < 300:  # 5 minutes
                    logger.warning(f"Duplicate signal detected: {signal.pair}")
                    return False
        
        return True
    
    def get_pending_signals(self) -> List[ParsedSignal]:
        """Get pending signals in queue"""
        return self.signal_queue.copy()
    
    def get_processed_signals(self) -> List[ParsedSignal]:
        """Get processed signals"""
        return self.processed_signals.copy()
    
    def get_execution_queue(self) -> List[ExecutionSignal]:
        """Get execution queue"""
        return self.execution_queue.copy()
    
    def update_signal_status(self, signal_id: str, status: SignalStatus, message: str = "") -> bool:
        """Update signal execution status"""
        try:
            for signal in self.execution_queue:
                if signal.signal_id == signal_id:
                    signal.status = status
                    signal.updated_at = datetime.now()
                    if message:
                        signal.metadata['status_message'] = message
                    
                    logger.info(f"Updated signal {signal_id} status to {status}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            return False
    
    def clear_processed_signals(self) -> bool:
        """Clear processed signals (keep last 100)"""
        try:
            if len(self.processed_signals) > 100:
                self.processed_signals = self.processed_signals[-100:]
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing processed signals: {e}")
            return False
    
    def load_signals(self):
        """Load existing signals from storage"""
        try:
            # This would load signals from a database or file
            # For now, just initialize empty lists
            pass
        except Exception as e:
            logger.error(f"Error loading signals: {e}")
    
    def save_signals(self):
        """Save signals to storage"""
        try:
            # This would save signals to a database or file
            # For now, just log the action
            logger.info("Signals saved to storage")
        except Exception as e:
            logger.error(f"Error saving signals: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get signal processing statistics"""
        return {
            'pending_count': len(self.signal_queue),
            'processed_count': len(self.processed_signals),
            'execution_queue_count': len(self.execution_queue),
            'success_rate': self.calculate_success_rate(),
            'avg_confidence': self.calculate_average_confidence()
        }
    
    def calculate_success_rate(self) -> float:
        """Calculate signal success rate"""
        if not self.execution_queue:
            return 0.0
        
        successful = sum(1 for signal in self.execution_queue 
                        if signal.status == SignalStatus.EXECUTED)
        return (successful / len(self.execution_queue)) * 100
    
    def calculate_average_confidence(self) -> float:
        """Calculate average confidence of processed signals"""
        if not self.processed_signals:
            return 0.0
        
        total_confidence = sum(signal.confidence for signal in self.processed_signals)
        return total_confidence / len(self.processed_signals)
