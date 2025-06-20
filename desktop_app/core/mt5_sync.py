"""
MetaTrader 5 synchronization and communication module
"""

import os
import json
import shutil
import logging
import subprocess
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

from config.settings import settings
from signal_model import ExecutionSignal, SignalStatus
from core.logger import get_logger

logger = get_logger(__name__)

class MT5Sync:
    """Handles MetaTrader 5 synchronization and communication"""
    
    def __init__(self):
        self.terminal_path = Path(settings.mt5.terminal_path) if settings.mt5.terminal_path else None
        self.experts_folder = None
        self.common_folder = None
        self.is_connected = False
        self.last_heartbeat = None
        
        # Find MT5 paths
        self.detect_mt5_paths()
    
    def detect_mt5_paths(self):
        """Detect MT5 installation paths with enhanced auto-detection"""
        try:
            logger.info("Starting MT5 path detection...")
            
            # Common MT5 installation paths
            potential_paths = [
                Path("C:/Program Files/MetaTrader 5/terminal64.exe"),
                Path("C:/Program Files (x86)/MetaTrader 5/terminal64.exe"),
                Path("C:/Program Files/MetaTrader 5/terminal.exe"),
                Path("C:/Program Files (x86)/MetaTrader 5/terminal.exe"),
            ]
            
            # Check if user provided path exists
            if self.terminal_path and self.terminal_path.exists():
                logger.info(f"Using configured terminal path: {self.terminal_path}")
                install_dir = self.terminal_path.parent
            else:
                # Auto-detect MT5 installation
                install_dir = None
                for path in potential_paths:
                    if path.exists():
                        logger.info(f"Found MT5 installation at: {path}")
                        self.terminal_path = path
                        install_dir = path.parent
                        break
                
                if not install_dir:
                    logger.warning("No MT5 installation found in standard locations")
                    return False
            
            # Find MQL5 folder structure
            mql5_folder = install_dir / "MQL5"
            if mql5_folder.exists():
                self.experts_folder = mql5_folder / "Experts"
                self.common_folder = mql5_folder / "Files"
                logger.info(f"Found MQL5 structure: {mql5_folder}")
            else:
                # Try AppData folder for terminal data
                appdata_folder = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal"
                if appdata_folder.exists():
                    logger.info(f"Checking AppData terminals: {appdata_folder}")
                    # Find terminal data folder (usually a hash)
                    for folder in appdata_folder.iterdir():
                            if folder.is_dir():
                                mql5_path = folder / "MQL5"
                                if mql5_path.exists():
                                    self.experts_folder = mql5_path / "Experts"
                                    self.common_folder = mql5_path / "Files"
                                    break
                
                logger.info(f"Detected MT5 paths - Experts: {self.experts_folder}, Common: {self.common_folder}")
                
        except Exception as e:
            logger.error(f"Error detecting MT5 paths: {e}")
    
    def scan_terminals(self) -> List[str]:
        """Scan for MT5 terminal installations"""
        try:
            terminals = []
            
            # Common installation paths
            search_paths = [
                Path("C:/Program Files/MetaTrader 5"),
                Path("C:/Program Files (x86)/MetaTrader 5"),
                Path.home() / "AppData" / "Local" / "Programs" / "MetaTrader 5"
            ]
            
            # Search for terminal executables
            for search_path in search_paths:
                if search_path.exists():
                    for exe_file in search_path.rglob("terminal64.exe"):
                        terminals.append(str(exe_file))
                    for exe_file in search_path.rglob("terminal.exe"):
                        terminals.append(str(exe_file))
            
            # Remove duplicates
            terminals = list(set(terminals))
            
            logger.info(f"Found {len(terminals)} MT5 terminals")
            return terminals
            
        except Exception as e:
            logger.error(f"Error scanning terminals: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test connection to MT5 terminal"""
        try:
            if not self.terminal_path or not self.terminal_path.exists():
                logger.error("MT5 terminal path not configured or invalid")
                return False
            
            # Check if terminal is running
            if self.is_terminal_running():
                # Test file communication
                return self.test_file_communication()
            else:
                logger.warning("MT5 terminal is not running")
                return False
                
        except Exception as e:
            logger.error(f"Error testing MT5 connection: {e}")
            return False
    
    def is_terminal_running(self) -> bool:
        """Check if MT5 terminal is running"""
        try:
            # Check for terminal process
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'],
                capture_output=True,
                text=True
            )
            
            return 'terminal64.exe' in result.stdout
            
        except Exception as e:
            logger.error(f"Error checking terminal status: {e}")
            return False
    
    def test_file_communication(self) -> bool:
        """Test file-based communication with EA"""
        try:
            if not self.common_folder:
                return False
            
            # Create test file
            test_file = self.common_folder / "signalos_test.txt"
            test_content = {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'message': 'SignalOS connection test'
            }
            
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_content, f)
            
            # Check if file was created
            if test_file.exists():
                # Clean up
                test_file.unlink()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing file communication: {e}")
            return False
    
    def install_ea(self) -> bool:
        """Install SignalOS Expert Advisor"""
        try:
            if not settings.mt5.expert_path or not self.experts_folder:
                logger.error("EA path or experts folder not configured")
                return False
            
            ea_source = Path(settings.mt5.expert_path)
            if not ea_source.exists():
                logger.error(f"EA file not found: {ea_source}")
                return False
            
            # Copy EA to experts folder
            ea_destination = self.experts_folder / ea_source.name
            shutil.copy2(ea_source, ea_destination)
            
            logger.info(f"EA installed to: {ea_destination}")
            
            # Create configuration file for EA
            self.create_ea_config()
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing EA: {e}")
            return False
    
    def create_ea_config(self) -> bool:
        """Create configuration file for EA"""
        try:
            if not self.common_folder:
                return False
            
            config_file = self.common_folder / "signalos_config.json"
            config_data = {
                'magic_number': settings.mt5.magic_number,
                'heartbeat_interval': settings.mt5.heartbeat_interval,
                'signal_file': str(settings.app_dir / "signals" / "signal.json"),
                'status_file': str(self.common_folder / "signalos_status.json"),
                'auto_restart': settings.mt5.auto_restart,
                'created_at': datetime.now().isoformat()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"EA config created: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating EA config: {e}")
            return False
    
    def sync_ea(self) -> bool:
        """Synchronize with Expert Advisor"""
        try:
            # Check EA status
            status = self.get_ea_status()
            if not status:
                return False
            
            # Send heartbeat
            self.send_heartbeat()
            
            # Check for responses
            responses = self.check_ea_responses()
            
            self.is_connected = True
            self.last_heartbeat = datetime.now()
            
            logger.info("EA sync successful")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing EA: {e}")
            return False
    
    def get_ea_status(self) -> Optional[Dict[str, Any]]:
        """Get Expert Advisor status"""
        try:
            if not self.common_folder:
                return None
            
            status_file = self.common_folder / "signalos_status.json"
            if not status_file.exists():
                return None
            
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting EA status: {e}")
            return None
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to EA"""
        try:
            if not self.common_folder:
                return False
            
            heartbeat_file = self.common_folder / "signalos_heartbeat.json"
            heartbeat_data = {
                'timestamp': datetime.now().isoformat(),
                'app_status': 'running',
                'magic_number': settings.mt5.magic_number
            }
            
            with open(heartbeat_file, 'w', encoding='utf-8') as f:
                json.dump(heartbeat_data, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    def check_ea_responses(self) -> List[Dict[str, Any]]:
        """Check for EA responses"""
        try:
            if not self.common_folder:
                return []
            
            responses_file = self.common_folder / "signalos_responses.json"
            if not responses_file.exists():
                return []
            
            with open(responses_file, 'r', encoding='utf-8') as f:
                responses = json.load(f)
            
            # Clear the responses file after reading
            responses_file.unlink()
            
            return responses if isinstance(responses, list) else [responses]
            
        except Exception as e:
            logger.error(f"Error checking EA responses: {e}")
            return []
    
    def send_signal_to_ea(self, execution_signal: ExecutionSignal) -> bool:
        """Send execution signal to EA"""
        try:
            signal_file = settings.app_dir / "signals" / "signal.json"
            
            # Prepare signal data for EA
            signal_data = {
                'signal_id': execution_signal.signal_id,
                'pair': execution_signal.pair,
                'action': execution_signal.action.upper(),
                'entry_price': execution_signal.entry_price,
                'stop_loss': execution_signal.stop_loss,
                'take_profit': execution_signal.take_profit,
                'lot_size': execution_signal.lot_size,
                'magic_number': execution_signal.magic_number,
                'comment': execution_signal.comment,
                'timestamp': execution_signal.created_at.isoformat(),
                'status': 'pending'
            }
            
            # Write to signal file
            with open(signal_file, 'w', encoding='utf-8') as f:
                json.dump(signal_data, f, indent=2)
            
            logger.info(f"Signal sent to EA: {execution_signal.signal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending signal to EA: {e}")
            return False
    
    def restart_terminal(self) -> bool:
        """Restart MT5 terminal"""
        try:
            if not self.terminal_path:
                return False
            
            # Kill existing terminal processes
            subprocess.run(['taskkill', '/F', '/IM', 'terminal64.exe'], 
                         capture_output=True)
            subprocess.run(['taskkill', '/F', '/IM', 'terminal.exe'], 
                         capture_output=True)
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Start terminal
            subprocess.Popen([str(self.terminal_path)])
            
            logger.info("MT5 terminal restarted")
            return True
            
        except Exception as e:
            logger.error(f"Error restarting terminal: {e}")
            return False
    
    def check_ea_heartbeat(self) -> bool:
        """Check if EA is responding to heartbeats"""
        try:
            status = self.get_ea_status()
            if not status:
                return False
            
            last_seen = status.get('last_heartbeat')
            if not last_seen:
                return False
            
            # Parse timestamp
            last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            
            # Check if within heartbeat interval
            time_diff = datetime.now() - last_seen_dt.replace(tzinfo=None)
            max_interval = timedelta(seconds=settings.mt5.heartbeat_interval * 2)
            
            return time_diff < max_interval
            
        except Exception as e:
            logger.error(f"Error checking EA heartbeat: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            'terminal_running': self.is_terminal_running(),
            'ea_installed': self.is_ea_installed(),
            'ea_responding': self.check_ea_heartbeat(),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'experts_folder': str(self.experts_folder) if self.experts_folder else None,
            'common_folder': str(self.common_folder) if self.common_folder else None
        }
    
    def is_ea_installed(self) -> bool:
        """Check if EA is installed"""
        try:
            if not self.experts_folder or not settings.mt5.expert_path:
                return False
            
            ea_name = Path(settings.mt5.expert_path).name
            ea_path = self.experts_folder / ea_name
            
            return ea_path.exists()
            
        except Exception as e:
            logger.error(f"Error checking EA installation: {e}")
            return False
    
    def cleanup_files(self) -> bool:
        """Cleanup temporary communication files"""
        try:
            if not self.common_folder:
                return False
            
            # List of files to clean up
            cleanup_files = [
                "signalos_heartbeat.json",
                "signalos_responses.json",
                "signalos_test.txt"
            ]
            
            for filename in cleanup_files:
                file_path = self.common_folder / filename
                if file_path.exists():
                    file_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            return False
