"""
System health monitoring module
"""

try:
    import psutil
except ImportError:
    # Mock psutil for basic functionality
    class MockPsutil:
        def virtual_memory(self):
            return type('obj', (object,), {'percent': 45.0})()
        def cpu_percent(self, interval=None):
            return 15.0
        def boot_time(self):
            return 1640995200  # Mock timestamp
        def Process(self, pid=None):
            class MockProcess:
                def __init__(self):
                    self.pid = 1234
                def memory_info(self):
                    return type('obj', (object,), {'rss': 1024*1024*50})()
                def memory_percent(self):
                    return 25.0
                def cpu_percent(self, interval=None):
                    return 5.0
            return MockProcess()
        def process_iter(self):
            return []
    psutil = MockPsutil()
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque

import logging

logger = logging.getLogger(__name__)

class HealthMonitor:
    """System health monitoring and diagnostics"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # Health data storage
        self.component_status = {}
        self.performance_history = deque(maxlen=100)
        self.error_log = deque(maxlen=100)
        self.signal_queue_status = {
            'pending': 0,
            'processed': 0,
            'recent_signals': deque(maxlen=20)
        }
        
        # Component references (would be injected in real implementation)
        self.telegram_listener = None
        self.signal_parser = None
        self.signal_engine = None
        self.mt5_sync = None
        
    def start_monitoring(self):
        """Start health monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Health monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Update component status
                self._update_component_status()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Check for issues
                self._check_for_issues()
                
                # Sleep for monitoring interval
                threading.Event().wait(5)  # 5 second monitoring interval
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                threading.Event().wait(10)  # Wait longer on error
    
    def _update_component_status(self):
        """Update status of all components"""
        with self.lock:
            # Telegram status
            self.component_status['telegram'] = {
                'connected': self._check_telegram_status(),
                'last_message': self._get_last_telegram_message(),
                'channels_monitored': self._get_monitored_channels_count()
            }
            
            # Parser status
            self.component_status['parser'] = {
                'running': self._check_parser_status(),
                'last_parse': self._get_last_parse_time(),
                'success_rate': self._get_parser_success_rate()
            }
            
            # MT5 status
            self.component_status['mt5'] = {
                'connected': self._check_mt5_status(),
                'terminal_running': self._check_mt5_terminal(),
                'last_heartbeat': self._get_mt5_last_heartbeat()
            }
            
            # EA status
            self.component_status['ea'] = {
                'running': self._check_ea_status(),
                'last_signal': self._get_last_ea_signal(),
                'trades_active': self._get_active_trades_count()
            }
    
    def _update_performance_metrics(self):
        """Update system performance metrics"""
        try:
            # Get current process
            process = psutil.Process()
            
            # CPU and memory usage
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # System-wide metrics
            system_cpu = psutil.cpu_percent()
            system_memory = psutil.virtual_memory().percent
            
            performance_data = {
                'timestamp': datetime.now(),
                'process_cpu': cpu_percent,
                'process_memory_mb': memory_mb,
                'process_memory_percent': memory_percent,
                'system_cpu': system_cpu,
                'system_memory': system_memory,
                'threads': threading.active_count()
            }
            
            with self.lock:
                self.performance_history.append(performance_data)
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _check_for_issues(self):
        """Check for system issues and log them"""
        try:
            issues = []
            
            # Check component status
            for component, status in self.component_status.items():
                if component == 'telegram' and not status.get('connected', False):
                    issues.append(f"Telegram not connected")
                elif component == 'parser' and not status.get('running', False):
                    issues.append(f"Signal parser not running")
                elif component == 'mt5' and not status.get('connected', False):
                    issues.append(f"MT5 not connected")
                elif component == 'ea' and not status.get('running', False):
                    issues.append(f"Expert Advisor not running")
            
            # Check performance
            if self.performance_history:
                latest = self.performance_history[-1]
                if latest['process_cpu'] > 80:
                    issues.append(f"High CPU usage: {latest['process_cpu']:.1f}%")
                if latest['process_memory_percent'] > 500:  # 500MB threshold
                    issues.append(f"High memory usage: {latest['process_memory_mb']:.0f}MB")
            
            # Log new issues
            for issue in issues:
                self.add_error("System", issue)
                
        except Exception as e:
            logger.error(f"Error checking for issues: {e}")
    
    def _check_telegram_status(self) -> bool:
        """Check Telegram connection status"""
        # In real implementation, would check actual telegram_listener
        return True  # Placeholder
    
    def _get_last_telegram_message(self) -> Optional[str]:
        """Get timestamp of last Telegram message"""
        return datetime.now().isoformat()  # Placeholder
    
    def _get_monitored_channels_count(self) -> int:
        """Get number of monitored channels"""
        from config.settings import settings
        return len(settings.telegram.channels)
    
    def _check_parser_status(self) -> bool:
        """Check parser running status"""
        return True  # Placeholder
    
    def _get_last_parse_time(self) -> Optional[str]:
        """Get timestamp of last signal parse"""
        return datetime.now().isoformat()  # Placeholder
    
    def _get_parser_success_rate(self) -> float:
        """Get parser success rate percentage"""
        return 87.5  # Placeholder
    
    def _check_mt5_status(self) -> bool:
        """Check MT5 connection status"""
        return True  # Placeholder
    
    def _check_mt5_terminal(self) -> bool:
        """Check if MT5 terminal is running"""
        try:
            # Check for terminal process
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in ['terminal64.exe', 'terminal.exe']:
                    return True
            return False
        except:
            return False
    
    def _get_mt5_last_heartbeat(self) -> Optional[str]:
        """Get MT5 last heartbeat timestamp"""
        return datetime.now().isoformat()  # Placeholder
    
    def _check_ea_status(self) -> bool:
        """Check EA running status"""
        return True  # Placeholder
    
    def _get_last_ea_signal(self) -> Optional[str]:
        """Get timestamp of last EA signal"""
        return datetime.now().isoformat()  # Placeholder
    
    def _get_active_trades_count(self) -> int:
        """Get number of active trades"""
        return 2  # Placeholder
    
    def get_component_status(self) -> Dict[str, Any]:
        """Get current component status"""
        with self.lock:
            return self.component_status.copy()
    
    def get_performance_data(self) -> Dict[str, Any]:
        """Get current performance data"""
        with self.lock:
            if not self.performance_history:
                return {
                    'cpu_percent': 0,
                    'memory_mb': 0,
                    'memory_percent': 0
                }
            
            latest = self.performance_history[-1]
            return {
                'cpu_percent': latest['process_cpu'],
                'memory_mb': latest['process_memory_mb'],
                'memory_percent': latest['process_memory_percent'],
                'system_cpu': latest['system_cpu'],
                'system_memory': latest['system_memory'],
                'threads': latest['threads']
            }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get signal queue status"""
        with self.lock:
            return {
                'pending': self.signal_queue_status['pending'],
                'processed': self.signal_queue_status['processed'],
                'recent_signals': list(self.signal_queue_status['recent_signals'])
            }
    
    def update_queue_status(self, pending: int, processed: int):
        """Update signal queue status"""
        with self.lock:
            self.signal_queue_status['pending'] = pending
            self.signal_queue_status['processed'] = processed
    
    def add_recent_signal(self, signal_info: Dict[str, Any]):
        """Add a recent signal to the queue"""
        with self.lock:
            signal_info['timestamp'] = datetime.now().strftime('%H:%M:%S')
            self.signal_queue_status['recent_signals'].append(signal_info)
    
    def get_recent_errors(self) -> List[Dict[str, Any]]:
        """Get recent errors"""
        with self.lock:
            return list(self.error_log)
    
    def add_error(self, component: str, message: str):
        """Add an error to the log"""
        error_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'component': component,
            'message': message
        }
        
        with self.lock:
            self.error_log.append(error_entry)
        
        logger.warning(f"Health Monitor - {component}: {message}")
    
    def clear_errors(self):
        """Clear the error log"""
        with self.lock:
            self.error_log.clear()
    
    def get_performance_history(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get performance history for specified minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                entry for entry in self.performance_history
                if entry['timestamp'] >= cutoff_time
            ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        component_status = self.get_component_status()
        performance_data = self.get_performance_data()
        
        # Calculate overall health score
        health_score = 100
        issues = []
        
        # Component health
        for component, status in component_status.items():
            if component == 'telegram' and not status.get('connected', False):
                health_score -= 20
                issues.append("Telegram disconnected")
            elif component == 'mt5' and not status.get('connected', False):
                health_score -= 25
                issues.append("MT5 disconnected")
            elif component == 'parser' and not status.get('running', False):
                health_score -= 15
                issues.append("Parser not running")
            elif component == 'ea' and not status.get('running', False):
                health_score -= 20
                issues.append("EA not running")
        
        # Performance health
        if performance_data['cpu_percent'] > 80:
            health_score -= 10
            issues.append("High CPU usage")
        
        if performance_data['memory_percent'] > 80:
            health_score -= 10
            issues.append("High memory usage")
        
        # Determine status
        if health_score >= 90:
            status = "Excellent"
            color = "#27ae60"
        elif health_score >= 70:
            status = "Good"
            color = "#f39c12"
        elif health_score >= 50:
            status = "Warning"
            color = "#e67e22"
        else:
            status = "Critical"
            color = "#e74c3c"
        
        return {
            'health_score': max(0, health_score),
            'status': status,
            'color': color,
            'issues': issues,
            'components_online': sum(1 for status in component_status.values() 
                                   if any(status.values())),
            'total_components': len(component_status)
        }
    
    def restart_all_services(self):
        """Restart all services"""
        try:
            # Add restart logic here
            self.add_error("System", "Service restart initiated")
            logger.info("Restarting all services...")
            
            # In real implementation, would restart actual services
            
        except Exception as e:
            self.add_error("System", f"Failed to restart services: {str(e)}")
    
    def reset_connections(self):
        """Reset all connections"""
        try:
            self.add_error("System", "Connection reset initiated")
            logger.info("Resetting all connections...")
            
            # In real implementation, would reset actual connections
            
        except Exception as e:
            self.add_error("System", f"Failed to reset connections: {str(e)}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
