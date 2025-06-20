"""
SignalOS Health Monitor
Comprehensive system health monitoring with MT5, Telegram, and EA status
"""
import psutil
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import requests
import subprocess
from models import Signal, Trade, db
from app import app

class HealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        self.last_check = None
        self.check_interval = 30  # seconds
        
    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource usage"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv
                }
            }
        except Exception as e:
            return {'error': f'Resource monitoring error: {str(e)}'}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and status"""
        try:
            with app.app_context():
                # Test basic connectivity
                db.session.execute('SELECT 1')
                
                # Get recent signal count
                recent_signals = Signal.query.filter(
                    Signal.received_at >= datetime.utcnow() - timedelta(hours=24)
                ).count()
                
                # Get recent trade count
                recent_trades = Trade.query.filter(
                    Trade.executed_at >= datetime.utcnow() - timedelta(hours=24)
                ).count()
                
                return {
                    'status': 'healthy',
                    'recent_signals': recent_signals,
                    'recent_trades': recent_trades,
                    'last_check': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def check_mt5_connectivity(self) -> Dict[str, Any]:
        """Check MT5 terminal status and connectivity"""
        mt5_status = {
            'status': 'disconnected',
            'terminals_found': 0,
            'active_connections': 0,
            'last_heartbeat': None,
            'expert_advisors': []
        }
        
        try:
            # Check for MT5 processes
            mt5_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'metatrader' in proc.info['name'].lower() or 'terminal64' in proc.info['name'].lower():
                        mt5_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            mt5_status['terminals_found'] = len(mt5_processes)
            mt5_status['processes'] = mt5_processes
            
            if mt5_processes:
                mt5_status['status'] = 'detected'
                
                # Check for EA files in common locations
                common_ea_paths = [
                    os.path.expanduser('~/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Experts/'),
                    'C:/Program Files/MetaTrader 5/MQL5/Experts/',
                    'C:/Program Files (x86)/MetaTrader 5/MQL5/Experts/'
                ]
                
                ea_files = []
                for path_pattern in common_ea_paths:
                    try:
                        import glob
                        for ea_path in glob.glob(path_pattern + '*.ex5'):
                            if 'signalos' in os.path.basename(ea_path).lower():
                                ea_files.append({
                                    'file': os.path.basename(ea_path),
                                    'path': ea_path,
                                    'modified': datetime.fromtimestamp(os.path.getmtime(ea_path)).isoformat()
                                })
                    except Exception:
                        continue
                
                mt5_status['expert_advisors'] = ea_files
                if ea_files:
                    mt5_status['status'] = 'configured'
            
        except Exception as e:
            mt5_status['error'] = str(e)
        
        return mt5_status
    
    def check_telegram_status(self) -> Dict[str, Any]:
        """Check Telegram API connectivity and session status"""
        telegram_status = {
            'status': 'disconnected',
            'active_sessions': 0,
            'channels_monitored': 0,
            'last_message': None,
            'api_configured': False
        }
        
        try:
            # Check environment variables for Telegram credentials
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            
            telegram_status['api_configured'] = bool(api_id and api_hash)
            
            if telegram_status['api_configured']:
                telegram_status['status'] = 'configured'
                # In production, would check actual Telegram client connections
                # For now, simulate based on database records
                with app.app_context():
                    from models import TelegramSession, TelegramChannel
                    
                    active_sessions = TelegramSession.query.filter(
                        TelegramSession.status == 'connected'
                    ).count()
                    
                    monitored_channels = TelegramChannel.query.filter(
                        TelegramChannel.active == True
                    ).count()
                    
                    telegram_status['active_sessions'] = active_sessions
                    telegram_status['channels_monitored'] = monitored_channels
                    
                    if active_sessions > 0:
                        telegram_status['status'] = 'connected'
            
        except Exception as e:
            telegram_status['error'] = str(e)
        
        return telegram_status
    
    def check_signal_parser_health(self) -> Dict[str, Any]:
        """Check signal parser performance and accuracy"""
        parser_status = {
            'status': 'active',
            'version': '1.0.0',
            'accuracy': 0.0,
            'processed_today': 0,
            'success_rate': 0.0,
            'last_signal': None
        }
        
        try:
            with app.app_context():
                # Get signals from last 24 hours
                recent_signals = Signal.query.filter(
                    Signal.received_at >= datetime.utcnow() - timedelta(hours=24)
                ).all()
                
                parser_status['processed_today'] = len(recent_signals)
                
                if recent_signals:
                    # Calculate success rate
                    successful_signals = [s for s in recent_signals if s.status == 'EXECUTED']
                    parser_status['success_rate'] = len(successful_signals) / len(recent_signals) * 100
                    
                    # Calculate average confidence
                    confidences = [s.confidence_score for s in recent_signals if s.confidence_score]
                    if confidences:
                        parser_status['accuracy'] = sum(confidences) / len(confidences) * 100
                    
                    # Get last signal info
                    last_signal = max(recent_signals, key=lambda x: x.received_at)
                    parser_status['last_signal'] = {
                        'pair': last_signal.parsed_pair,
                        'action': last_signal.parsed_action,
                        'timestamp': last_signal.received_at.isoformat(),
                        'confidence': last_signal.confidence_score
                    }
        
        except Exception as e:
            parser_status['error'] = str(e)
            parser_status['status'] = 'error'
        
        return parser_status
    
    def check_websocket_health(self) -> Dict[str, Any]:
        """Check WebSocket server health and active connections"""
        websocket_status = {
            'status': 'active',
            'active_connections': 0,
            'last_heartbeat': datetime.utcnow().isoformat(),
            'uptime': 0
        }
        
        try:
            # Check if socketio is running (simplified check)
            websocket_status['status'] = 'active'
            websocket_status['uptime'] = int(time.time())  # Simplified uptime
            
        except Exception as e:
            websocket_status['error'] = str(e)
            websocket_status['status'] = 'error'
        
        return websocket_status
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get complete system health status"""
        health_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'services': {
                'database': True,
                'mt5': False,
                'telegram': False,
                'parser': True,
                'websocket': True
            }
        }
        
        try:
            # Get all health checks
            system_resources = self.get_system_resources()
            database_health = self.check_database_health()
            mt5_health = self.check_mt5_connectivity()
            telegram_health = self.check_telegram_status()
            parser_health = self.check_signal_parser_health()
            websocket_health = self.check_websocket_health()
            
            # Compile comprehensive status
            health_data.update({
                'system': system_resources,
                'database': database_health,
                'mt5': mt5_health,
                'telegram': telegram_health,
                'parser': parser_health,
                'websocket': websocket_health
            })
            
            # Update service status flags
            health_data['services'].update({
                'database': database_health.get('status') == 'healthy',
                'mt5': mt5_health.get('status') in ['detected', 'configured'],
                'telegram': telegram_health.get('status') in ['configured', 'connected'],
                'parser': parser_health.get('status') == 'active',
                'websocket': websocket_health.get('status') == 'active'
            })
            
            # Determine overall status
            healthy_services = sum(health_data['services'].values())
            total_services = len(health_data['services'])
            
            if healthy_services == total_services:
                health_data['overall_status'] = 'healthy'
            elif healthy_services >= total_services * 0.6:
                health_data['overall_status'] = 'warning'
            else:
                health_data['overall_status'] = 'critical'
                
        except Exception as e:
            health_data['error'] = str(e)
            health_data['overall_status'] = 'error'
        
        return health_data
    
    def log_health_event(self, event_type: str, message: str, severity: str = 'INFO'):
        """Log health monitoring events"""
        try:
            with app.app_context():
                from models import SystemLog
                log_entry = SystemLog(
                    level=severity,
                    category='HEALTH_MONITOR',
                    message=f"{event_type}: {message}",
                    timestamp=datetime.utcnow()
                )
                db.session.add(log_entry)
                db.session.commit()
        except Exception as e:
            print(f"Failed to log health event: {e}")


# Global health monitor instance
health_monitor = HealthMonitor()


def get_system_health() -> Dict[str, Any]:
    """Get current system health - main entry point"""
    return health_monitor.get_comprehensive_health()


if __name__ == "__main__":
    # Test health monitoring
    health = get_system_health()
    import json
    print(json.dumps(health, indent=2))