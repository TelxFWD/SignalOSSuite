"""
Logging configuration and utilities
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys

def setup_logging(log_level=logging.INFO):
    """Setup application logging"""
    # Create logs directory
    log_dir = Path.home() / ".signalos" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file path
    log_file = log_dir / f"signalos_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Error file handler
    error_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    logging.info("Logging system initialized")

def get_logger(name: str) -> logging.Logger:
    """Get a logger for the specified module"""
    return logging.getLogger(name)

class SignalOSLogger:
    """Custom logger class for SignalOS with additional features"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.signal_log_file = Path.home() / ".signalos" / "logs" / "signals.log"
        self.trade_log_file = Path.home() / ".signalos" / "logs" / "trades.log"
        
        # Create specialized handlers
        self._setup_signal_logger()
        self._setup_trade_logger()
    
    def _setup_signal_logger(self):
        """Setup specialized signal logging"""
        signal_handler = logging.FileHandler(self.signal_log_file, encoding='utf-8')
        signal_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        signal_handler.setFormatter(signal_formatter)
        
        # Create signal logger
        self.signal_logger = logging.getLogger(f"{self.logger.name}.signals")
        self.signal_logger.addHandler(signal_handler)
        self.signal_logger.setLevel(logging.INFO)
        self.signal_logger.propagate = False
    
    def _setup_trade_logger(self):
        """Setup specialized trade logging"""
        trade_handler = logging.FileHandler(self.trade_log_file, encoding='utf-8')
        trade_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        trade_handler.setFormatter(trade_formatter)
        
        # Create trade logger
        self.trade_logger = logging.getLogger(f"{self.logger.name}.trades")
        self.trade_logger.addHandler(trade_handler)
        self.trade_logger.setLevel(logging.INFO)
        self.trade_logger.propagate = False
    
    def log_signal(self, pair: str, action: str, entry: float, source: str, confidence: float):
        """Log signal processing"""
        message = f"SIGNAL | {pair} | {action} | Entry: {entry} | Source: {source} | Confidence: {confidence:.2f}"
        self.signal_logger.info(message)
    
    def log_trade(self, pair: str, action: str, lot_size: float, entry: float, sl: float = None, tp: float = None):
        """Log trade execution"""
        sl_str = f"SL: {sl}" if sl else "No SL"
        tp_str = f"TP: {tp}" if tp else "No TP"
        message = f"TRADE | {pair} | {action} | Size: {lot_size} | Entry: {entry} | {sl_str} | {tp_str}"
        self.trade_logger.info(message)
    
    def log_error(self, component: str, error: str, details: str = ""):
        """Log error with component information"""
        message = f"ERROR | {component} | {error}"
        if details:
            message += f" | Details: {details}"
        self.logger.error(message)
    
    def log_performance(self, operation: str, duration: float, success: bool = True):
        """Log performance metrics"""
        status = "SUCCESS" if success else "FAILED"
        message = f"PERF | {operation} | {duration:.3f}s | {status}"
        self.logger.info(message)
    
    def debug(self, message: str):
        """Debug logging"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Info logging"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warning logging"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Error logging"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Critical logging"""
        self.logger.critical(message)

def get_signalos_logger(name: str) -> SignalOSLogger:
    """Get a SignalOS logger instance"""
    return SignalOSLogger(name)

class LogAnalyzer:
    """Analyze log files for insights"""
    
    def __init__(self):
        self.log_dir = Path.home() / ".signalos" / "logs"
    
    def get_error_summary(self, days: int = 7) -> dict:
        """Get error summary for the last N days"""
        summary = {
            'total_errors': 0,
            'by_component': {},
            'by_day': {},
            'recent_errors': []
        }
        
        try:
            # Analyze error log files
            for log_file in self.log_dir.glob("errors_*.log"):
                # Read and analyze log file
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'ERROR' in line:
                            summary['total_errors'] += 1
                            # Parse line for component and error details
                            # This is a simplified implementation
        except Exception as e:
            logging.error(f"Error analyzing logs: {e}")
        
        return summary
    
    def get_signal_statistics(self, days: int = 7) -> dict:
        """Get signal processing statistics"""
        stats = {
            'total_signals': 0,
            'by_pair': {},
            'by_source': {},
            'success_rate': 0.0
        }
        
        try:
            signal_log = self.log_dir / "signals.log"
            if signal_log.exists():
                with open(signal_log, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'SIGNAL' in line:
                            stats['total_signals'] += 1
                            # Parse signal details
        except Exception as e:
            logging.error(f"Error analyzing signal logs: {e}")
        
        return stats
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up log files older than specified days"""
        try:
            cutoff_date = datetime.now().date()
            for log_file in self.log_dir.glob("*.log"):
                # Check file age and delete if too old
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime).date()
                if (cutoff_date - file_date).days > days:
                    log_file.unlink()
                    logging.info(f"Deleted old log file: {log_file}")
        except Exception as e:
            logging.error(f"Error cleaning up logs: {e}")
