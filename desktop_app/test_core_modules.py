#!/usr/bin/env python3
"""
SignalOS Core Module Testing and Validation Script
Comprehensive testing of all core modules to identify bugs and missing functionality
"""

import sys
import os
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import setup_logging, get_signalos_logger
from config.settings import AppSettings
from core.health_monitor import HealthMonitor
from core.signal_engine import SignalEngine
from core.telegram_listener import TelegramListener
from core.signal_parser import SignalParser
from core.mt5_sync import MT5Sync
from signal_model import RawSignal, ParsedSignal, ExecutionSignal, SignalStatus

logger = get_signalos_logger(__name__)

class CoreModuleTester:
    """Comprehensive testing framework for SignalOS core modules"""
    
    def __init__(self):
        self.test_results = {
            'login_config_sync': '❌ Not Tested',
            'telegram_session': '❌ Not Tested',
            'ai_signal_parser': '❌ Not Tested',
            'sl_buffer_logic': '❌ Not Tested',
            'signal_execution': '❌ Not Tested',
            'mt5_sync_system': '❌ Not Tested',
            'health_monitor': '❌ Not Tested',
            'config_import_export': '❌ Not Tested',
            'shadow_mode': '❌ Not Tested'
        }
        
        self.detected_bugs = []
        self.missing_features = []
        self.execution_log = []
        
        # Initialize components
        self.settings = AppSettings()
        self.health_monitor = HealthMonitor()
        self.signal_engine = SignalEngine()
        self.telegram_listener = TelegramListener()
        self.signal_parser = SignalParser()
        self.mt5_sync = MT5Sync()
        
    def log_execution(self, message: str, level: str = "INFO"):
        """Log execution with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {level}: {message}"
        self.execution_log.append(entry)
        print(entry)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    async def test_telegram_session_manager(self):
        """Test Telegram session management with Telethon"""
        self.log_execution("Testing Telegram Session Manager...")
        
        try:
            # Check if API credentials are configured
            api_id, api_hash = self.settings.get_api_credentials()
            
            if not api_id or not api_hash:
                self.detected_bugs.append("Telegram API credentials not configured")
                self.test_results['telegram_session'] = '⚠ Partial - No API credentials'
                return
            
            # Test client initialization
            init_result = await self.telegram_listener.initialize()
            
            if init_result:
                self.test_results['telegram_session'] = '✔ Stable'
                self.log_execution("Telegram session manager working correctly")
            else:
                self.test_results['telegram_session'] = '⚠ Partial - Init failed'
                self.detected_bugs.append("Telegram client initialization failed")
                
        except Exception as e:
            self.detected_bugs.append(f"Telegram session error: {str(e)}")
            self.test_results['telegram_session'] = '❌ Broken'
            self.log_execution(f"Telegram session test failed: {e}", "ERROR")
    
    def test_ai_signal_parser(self):
        """Test AI signal parser with text and OCR"""
        self.log_execution("Testing AI Signal Parser...")
        
        try:
            # Test with sample signal texts
            test_signals = [
                "EURUSD BUY at 1.0850 SL 1.0820 TP 1.0920",
                "GBPUSD SELL @ 1.2550 Stop Loss: 1.2580 Take Profit: 1.2480",
                "Gold Long Entry: 1980 SL: 1975 TP: 1990",
                "XAU/USD short position 1985 stop 1990 target 1970"
            ]
            
            parsed_count = 0
            confidence_sum = 0
            
            for signal_text in test_signals:
                raw_signal = RawSignal(
                    text=signal_text,
                    source_id="test_channel",
                    source_name="Test Channel",
                    message_id=f"test_{parsed_count}"
                )
                
                parsed_signal = self.signal_parser.parse_signal(raw_signal)
                
                if parsed_signal and parsed_signal.is_valid():
                    parsed_count += 1
                    confidence_sum += parsed_signal.confidence
                    self.log_execution(f"Parsed: {parsed_signal.pair} {parsed_signal.action} @ {parsed_signal.entry_price}")
                else:
                    self.detected_bugs.append(f"Failed to parse signal: {signal_text}")
            
            if parsed_count > 0:
                avg_confidence = confidence_sum / parsed_count
                if avg_confidence >= 0.8:
                    self.test_results['ai_signal_parser'] = '✔ Stable'
                elif avg_confidence >= 0.6:
                    self.test_results['ai_signal_parser'] = '⚠ Partial - Low confidence'
                else:
                    self.test_results['ai_signal_parser'] = '❌ Broken - Very low confidence'
                    
                self.log_execution(f"Parser success rate: {parsed_count}/{len(test_signals)}, Avg confidence: {avg_confidence:.2f}")
            else:
                self.test_results['ai_signal_parser'] = '❌ Broken'
                self.detected_bugs.append("Signal parser failed to parse any test signals")
                
        except Exception as e:
            self.detected_bugs.append(f"Signal parser error: {str(e)}")
            self.test_results['ai_signal_parser'] = '❌ Broken'
            self.log_execution(f"Signal parser test failed: {e}", "ERROR")
    
    def test_sl_buffer_logic(self):
        """Test SL buffer (1-10 pip smart offset logic)"""
        self.log_execution("Testing SL Buffer Logic...")
        
        try:
            # Test SL buffer application
            test_cases = [
                {"pair": "EURUSD", "entry": 1.0850, "sl": 1.0820, "expected_buffer": 5},
                {"pair": "GBPUSD", "entry": 1.2550, "sl": 1.2580, "expected_buffer": 5},
                {"pair": "USDJPY", "entry": 150.50, "sl": 150.20, "expected_buffer": 5}
            ]
            
            buffer_tests_passed = 0
            
            for test_case in test_cases:
                # Create a test signal
                parsed_signal = ParsedSignal(
                    raw_signal_id="test",
                    pair=test_case["pair"],
                    action="BUY" if test_case["entry"] > test_case["sl"] else "SELL",
                    entry_price=test_case["entry"],
                    stop_loss=test_case["sl"],
                    confidence=0.9
                )
                
                # Test buffer application through signal engine
                execution_signal = self.signal_engine.create_execution_signal(parsed_signal)
                
                if execution_signal:
                    # Check if SL was adjusted
                    original_sl = test_case["sl"]
                    new_sl = execution_signal.stop_loss
                    
                    if new_sl != original_sl:
                        buffer_tests_passed += 1
                        self.log_execution(f"SL buffer applied: {original_sl} -> {new_sl}")
                    else:
                        self.detected_bugs.append(f"SL buffer not applied for {test_case['pair']}")
                else:
                    self.detected_bugs.append(f"Failed to create execution signal for SL buffer test")
            
            if buffer_tests_passed == len(test_cases):
                self.test_results['sl_buffer_logic'] = '✔ Stable'
            elif buffer_tests_passed > 0:
                self.test_results['sl_buffer_logic'] = '⚠ Partial'
            else:
                self.test_results['sl_buffer_logic'] = '❌ Broken'
                
        except Exception as e:
            self.detected_bugs.append(f"SL buffer logic error: {str(e)}")
            self.test_results['sl_buffer_logic'] = '❌ Broken'
            self.log_execution(f"SL buffer test failed: {e}", "ERROR")
    
    def test_signal_execution_engine(self):
        """Test signal execution engine for all order types"""
        self.log_execution("Testing Signal Execution Engine...")
        
        try:
            # Test signal processing pipeline
            test_signal = ParsedSignal(
                raw_signal_id="test_execution",
                pair="EURUSD",
                action="BUY",
                entry_price=1.0850,
                stop_loss=1.0820,
                take_profit=1.0920,
                lot_size=0.1,
                confidence=0.85
            )
            
            # Add signal to engine
            result = self.signal_engine.add_signal(test_signal)
            
            if result:
                # Check if signal was processed
                pending_signals = self.signal_engine.get_pending_signals()
                execution_queue = self.signal_engine.get_execution_queue()
                
                if len(execution_queue) > 0:
                    self.test_results['signal_execution'] = '✔ Stable'
                    self.log_execution("Signal execution engine processing correctly")
                else:
                    self.test_results['signal_execution'] = '⚠ Partial - No execution signals generated'
                    self.detected_bugs.append("Signal execution engine not generating execution signals")
            else:
                self.test_results['signal_execution'] = '❌ Broken'
                self.detected_bugs.append("Signal execution engine failed to add signal")
                
        except Exception as e:
            self.detected_bugs.append(f"Signal execution engine error: {str(e)}")
            self.test_results['signal_execution'] = '❌ Broken'
            self.log_execution(f"Signal execution test failed: {e}", "ERROR")
    
    def test_mt5_sync_system(self):
        """Test MT5 sync system with auto path detection and EA communication"""
        self.log_execution("Testing MT5 Sync System...")
        
        try:
            # Test terminal detection
            terminals = self.mt5_sync.scan_terminals()
            
            if not terminals:
                self.missing_features.append("MT5 terminal auto-detection not finding any terminals")
                
            # Test connection
            connection_result = self.mt5_sync.test_connection()
            
            if connection_result:
                self.test_results['mt5_sync_system'] = '✔ Stable'
                self.log_execution("MT5 sync system connected successfully")
            else:
                self.test_results['mt5_sync_system'] = '⚠ Partial - Connection failed'
                self.log_execution("MT5 terminal not running or not configured", "WARNING")
            
            # Test EA installation
            ea_installed = self.mt5_sync.is_ea_installed()
            if not ea_installed:
                self.missing_features.append("SignalOS EA not installed in MT5")
            
            # Test signal file communication
            file_test = self.mt5_sync.test_file_communication()
            if not file_test:
                self.detected_bugs.append("MT5 file communication not working")
                
        except Exception as e:
            self.detected_bugs.append(f"MT5 sync system error: {str(e)}")
            self.test_results['mt5_sync_system'] = '❌ Broken'
            self.log_execution(f"MT5 sync test failed: {e}", "ERROR")
    
    def test_health_monitor(self):
        """Test health and recovery monitor UI"""
        self.log_execution("Testing Health Monitor...")
        
        try:
            # Start health monitoring
            self.health_monitor.start_monitoring()
            
            # Get health summary
            health_summary = self.health_monitor.get_health_summary()
            
            if health_summary and isinstance(health_summary, dict):
                required_keys = ['components', 'performance', 'overall_status']
                
                if all(key in health_summary for key in required_keys):
                    self.test_results['health_monitor'] = '✔ Stable'
                    self.log_execution("Health monitor providing comprehensive status")
                else:
                    self.test_results['health_monitor'] = '⚠ Partial - Missing health data'
                    self.detected_bugs.append("Health monitor missing required status fields")
            else:
                self.test_results['health_monitor'] = '❌ Broken'
                self.detected_bugs.append("Health monitor not returning valid status")
                
        except Exception as e:
            self.detected_bugs.append(f"Health monitor error: {str(e)}")
            self.test_results['health_monitor'] = '❌ Broken'
            self.log_execution(f"Health monitor test failed: {e}", "ERROR")
    
    def test_config_import_export(self):
        """Test configuration import/export functionality"""
        self.log_execution("Testing Config Import/Export...")
        
        try:
            # Test configuration export
            config_data = self.settings.export_config_data()
            
            if config_data:
                # Test saving to file
                test_file = Path("test_config_export.json")
                export_result = self.settings.export_config(str(test_file))
                
                if export_result and test_file.exists():
                    # Test import
                    import_result = self.settings.import_config(str(test_file))
                    
                    if import_result:
                        self.test_results['config_import_export'] = '✔ Stable'
                        self.log_execution("Config import/export working correctly")
                    else:
                        self.test_results['config_import_export'] = '⚠ Partial - Import failed'
                        self.detected_bugs.append("Config import functionality broken")
                    
                    # Cleanup
                    test_file.unlink(missing_ok=True)
                else:
                    self.test_results['config_import_export'] = '⚠ Partial - Export failed'
                    self.detected_bugs.append("Config export functionality broken")
            else:
                self.test_results['config_import_export'] = '❌ Broken'
                self.detected_bugs.append("Config export data generation failed")
                
        except Exception as e:
            self.detected_bugs.append(f"Config import/export error: {str(e)}")
            self.test_results['config_import_export'] = '❌ Broken'
            self.log_execution(f"Config import/export test failed: {e}", "ERROR")
    
    def test_shadow_mode(self):
        """Test shadow/offline mode for non-execution testing"""
        self.log_execution("Testing Shadow Mode...")
        
        try:
            # Enable stealth mode (shadow mode)
            original_stealth = self.settings.execution.stealth_mode
            self.settings.execution.stealth_mode = True
            
            # Create test execution signal
            execution_signal = ExecutionSignal(
                signal_id="shadow_test",
                pair="EURUSD",
                action="BUY",
                entry_price=1.0850,
                stop_loss=1.0820,
                take_profit=1.0920,
                lot_size=0.1
            )
            
            # Apply stealth mode modifications
            stealth_signal = self.signal_engine.apply_stealth_mode(execution_signal)
            
            if stealth_signal:
                # Check if modifications were applied (SL/TP removal, etc.)
                stealth_applied = (
                    stealth_signal.stop_loss is None or 
                    stealth_signal.take_profit is None or
                    stealth_signal.comment.find("STEALTH") >= 0
                )
                
                if stealth_applied:
                    self.test_results['shadow_mode'] = '✔ Stable'
                    self.log_execution("Shadow mode modifications applied correctly")
                else:
                    self.test_results['shadow_mode'] = '⚠ Partial - Modifications not applied'
                    self.detected_bugs.append("Shadow mode not applying stealth modifications")
            else:
                self.test_results['shadow_mode'] = '❌ Broken'
                self.detected_bugs.append("Shadow mode signal processing failed")
            
            # Restore original setting
            self.settings.execution.stealth_mode = original_stealth
            
        except Exception as e:
            self.detected_bugs.append(f"Shadow mode error: {str(e)}")
            self.test_results['shadow_mode'] = '❌ Broken'
            self.log_execution(f"Shadow mode test failed: {e}", "ERROR")
    
    def test_login_config_sync(self):
        """Test login and config synchronization with backend"""
        self.log_execution("Testing Login & Config Sync...")
        
        try:
            # This would need actual API endpoints to test properly
            # For now, check if auth system is implemented
            
            from config.auth import AuthManager
            auth_manager = AuthManager()
            
            # Test token loading/saving
            auth_manager.save_token()
            auth_manager.load_token()
            
            # Test config sync (will fail without API but shows structure exists)
            sync_result, config_data = auth_manager.sync_user_config()
            
            if hasattr(auth_manager, 'login') and hasattr(auth_manager, 'sync_user_config'):
                self.test_results['login_config_sync'] = '⚠ Partial - Structure exists but no API'
                self.missing_features.append("Backend API integration for login/config sync")
            else:
                self.test_results['login_config_sync'] = '❌ Broken'
                self.detected_bugs.append("Login/config sync system not implemented")
                
        except Exception as e:
            self.detected_bugs.append(f"Login/config sync error: {str(e)}")
            self.test_results['login_config_sync'] = '❌ Broken'
            self.log_execution(f"Login/config sync test failed: {e}", "ERROR")
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("SIGNALOS CORE MODULE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Module status summary
        report.append("MODULE STATUS SUMMARY:")
        report.append("-" * 40)
        for module, status in self.test_results.items():
            report.append(f"{module:25} | {status}")
        report.append("")
        
        # Overall assessment
        stable_count = sum(1 for status in self.test_results.values() if status.startswith('✔'))
        partial_count = sum(1 for status in self.test_results.values() if status.startswith('⚠'))
        broken_count = sum(1 for status in self.test_results.values() if status.startswith('❌'))
        
        report.append("OVERALL ASSESSMENT:")
        report.append(f"Stable modules:  {stable_count}/{len(self.test_results)}")
        report.append(f"Partial modules: {partial_count}/{len(self.test_results)}")
        report.append(f"Broken modules:  {broken_count}/{len(self.test_results)}")
        report.append("")
        
        # Bugs detected
        if self.detected_bugs:
            report.append("BUGS DETECTED:")
            report.append("-" * 40)
            for i, bug in enumerate(self.detected_bugs, 1):
                report.append(f"{i}. {bug}")
            report.append("")
        
        # Missing features
        if self.missing_features:
            report.append("MISSING FEATURES:")
            report.append("-" * 40)
            for i, feature in enumerate(self.missing_features, 1):
                report.append(f"{i}. {feature}")
            report.append("")
        
        # Execution log
        report.append("EXECUTION LOG:")
        report.append("-" * 40)
        for log_entry in self.execution_log[-20:]:  # Last 20 entries
            report.append(log_entry)
        
        return "\n".join(report)
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        self.log_execution("Starting comprehensive SignalOS core module testing...")
        
        # Test all modules
        await self.test_telegram_session_manager()
        self.test_ai_signal_parser()
        self.test_sl_buffer_logic()
        self.test_signal_execution_engine()
        self.test_mt5_sync_system()
        self.test_health_monitor()
        self.test_config_import_export()
        self.test_shadow_mode()
        self.test_login_config_sync()
        
        # Generate and display report
        report = self.generate_report()
        print("\n" + report)
        
        # Save report to file
        report_file = Path("signalos_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log_execution(f"Test report saved to: {report_file}")
        
        return self.test_results, self.detected_bugs, self.missing_features

async def main():
    """Main test execution"""
    # Setup logging
    setup_logging()
    
    # Run tests
    tester = CoreModuleTester()
    results, bugs, missing = await tester.run_all_tests()
    
    return results, bugs, missing

if __name__ == "__main__":
    asyncio.run(main())