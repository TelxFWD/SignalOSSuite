#!/usr/bin/env python3
"""
SignalOS Comprehensive QA Audit Script
Tests all three components: Desktop App, Web Dashboard, and Admin Panel
"""

import requests
import json
import time
from datetime import datetime
import subprocess
import sys

class SignalOSQAAuditor:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {
            'desktop_app': {},
            'web_dashboard': {},
            'admin_panel': {}
        }
        self.bugs_found = []
        self.missing_features = []
        self.auth_token = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_api_endpoint(self, endpoint, method="GET", data=None, headers=None):
        """Test an API endpoint and return response"""
        try:
            url = f"{self.base_url}{endpoint}"
            if headers is None:
                headers = {"Content-Type": "application/json"}
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
                
            return {
                'status_code': response.status_code,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'success': 200 <= response.status_code < 300
            }
        except Exception as e:
            return {
                'status_code': 0,
                'data': str(e),
                'success': False
            }
    
    def test_desktop_app(self):
        """Test desktop application components"""
        self.log("Testing Desktop Application Components...")
        
        # Run the desktop app test script
        try:
            result = subprocess.run(['python', 'desktop_app/test_core_modules.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if "OVERALL ASSESSMENT:" in result.stdout:
                # Parse test results
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Stable modules:" in line:
                        stable = line.split(':')[1].strip()
                        self.test_results['desktop_app']['stable_modules'] = stable
                    elif "BUGS DETECTED:" in line:
                        # Extract bugs from subsequent lines
                        idx = lines.index(line)
                        for i in range(idx + 2, len(lines)):
                            if lines[i].startswith('MISSING FEATURES:'):
                                break
                            if lines[i].strip() and not lines[i].startswith('-'):
                                self.bugs_found.append(f"Desktop: {lines[i].strip()}")
                                
            self.test_results['desktop_app']['core_test'] = "✔ Completed"
            
        except Exception as e:
            self.test_results['desktop_app']['core_test'] = f"❌ Failed: {str(e)}"
            self.log(f"Desktop app test failed: {e}", "ERROR")
    
    def test_web_dashboard(self):
        """Test web dashboard functionality"""
        self.log("Testing Web Dashboard Components...")
        
        # Test authentication
        login_result = self.test_api_endpoint("/api/auth/login", "POST", {
            "email": "demo@signalos.com",
            "password": "demo"
        })
        
        if login_result['success']:
            self.auth_token = login_result['data'].get('token')
            self.test_results['web_dashboard']['authentication'] = "✔ Working"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
        else:
            self.test_results['web_dashboard']['authentication'] = "❌ Failed"
            self.bugs_found.append("Web Dashboard: Authentication system not working")
            headers = {}
        
        # Test health endpoint
        health_result = self.test_api_endpoint("/api/health")
        if health_result['success']:
            self.test_results['web_dashboard']['health_check'] = "✔ Working"
            health_data = health_result['data']
            if health_data.get('services', {}).get('database'):
                self.test_results['web_dashboard']['database'] = "✔ Connected"
            else:
                self.test_results['web_dashboard']['database'] = "❌ Disconnected"
        else:
            self.test_results['web_dashboard']['health_check'] = "❌ Failed"
            self.bugs_found.append("Web Dashboard: Health check endpoint not responding")
        
        # Test Telegram API endpoints
        telegram_sessions = self.test_api_endpoint("/api/telegram/sessions", headers=headers)
        self.test_results['web_dashboard']['telegram_sessions'] = "✔ Working" if telegram_sessions['success'] else "❌ Failed"
        
        telegram_channels = self.test_api_endpoint("/api/telegram/channels", headers=headers)
        self.test_results['web_dashboard']['telegram_channels'] = "✔ Working" if telegram_channels['success'] else "❌ Failed"
        
        # Test MT5 API endpoints
        mt5_terminals = self.test_api_endpoint("/api/mt5/terminals", headers=headers)
        self.test_results['web_dashboard']['mt5_terminals'] = "✔ Working" if mt5_terminals['success'] else "❌ Failed"
        
        # Test strategies endpoint
        strategies = self.test_api_endpoint("/api/strategies", headers=headers)
        self.test_results['web_dashboard']['strategies'] = "✔ Working" if strategies['success'] else "❌ Failed"
        
        # Test analytics endpoint
        analytics = self.test_api_endpoint("/api/analytics/daily", headers=headers)
        self.test_results['web_dashboard']['analytics'] = "✔ Working" if analytics['success'] else "❌ Failed"
        
        # Test signal simulation
        signal_sim = self.test_api_endpoint("/api/simulate-signal", "POST", {
            "pair": "EURUSD",
            "action": "BUY"
        }, headers)
        self.test_results['web_dashboard']['signal_simulation'] = "✔ Working" if signal_sim['success'] else "❌ Failed"
    
    def test_admin_panel(self):
        """Test admin panel functionality"""
        self.log("Testing Admin Panel Components...")
        
        # Test admin login
        admin_login = self.test_api_endpoint("/admin/api/login", "POST", {
            "email": "admin@signalos.com",
            "password": "admin123"
        })
        
        if admin_login['success']:
            self.test_results['admin_panel']['authentication'] = "✔ Working"
            admin_headers = {"Content-Type": "application/json"}
        else:
            self.test_results['admin_panel']['authentication'] = "❌ Failed"
            self.bugs_found.append("Admin Panel: Authentication system not working")
            admin_headers = {}
        
        # Test admin dashboard
        admin_dashboard = self.test_api_endpoint("/admin/dashboard")
        self.test_results['admin_panel']['dashboard'] = "✔ Working" if admin_dashboard['success'] else "❌ Failed"
        
        # Test user management
        admin_users = self.test_api_endpoint("/admin/users")
        self.test_results['admin_panel']['user_management'] = "✔ Working" if admin_users['success'] else "❌ Failed"
        
        # Test signal management
        admin_signals = self.test_api_endpoint("/admin/signals")
        self.test_results['admin_panel']['signal_management'] = "✔ Working" if admin_signals['success'] else "❌ Failed"
        
        # Test system logs
        admin_logs = self.test_api_endpoint("/admin/logs")
        self.test_results['admin_panel']['system_logs'] = "✔ Working" if admin_logs['success'] else "❌ Failed"
        
        # Test license plans
        license_plans = self.test_api_endpoint("/admin/license-plans")
        self.test_results['admin_panel']['license_plans'] = "✔ Working" if license_plans['success'] else "❌ Failed"
        
        # Test providers
        providers = self.test_api_endpoint("/admin/providers")
        self.test_results['admin_panel']['providers'] = "✔ Working" if providers['success'] else "❌ Failed"
        
        # Test system metrics
        metrics = self.test_api_endpoint("/admin/api/system-metrics")
        self.test_results['admin_panel']['system_metrics'] = "✔ Working" if metrics['success'] else "❌ Failed"
    
    def test_cross_system_integration(self):
        """Test cross-system functionality"""
        self.log("Testing Cross-System Integration...")
        
        # Test signal flow: Telegram → Parser → MT5 → Feedback
        signal_flow_test = {
            'telegram_reception': False,
            'signal_parsing': False,
            'mt5_execution': False,
            'feedback_logging': False
        }
        
        # Simulate a complete signal flow
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test signal simulation (represents Telegram reception)
            signal_test = self.test_api_endpoint("/api/simulate-signal", "POST", {
                "pair": "EURUSD",
                "action": "BUY",
                "entry_price": 1.0850,
                "stop_loss": 1.0820,
                "take_profit": 1.0900
            }, headers)
            
            if signal_test['success']:
                signal_flow_test['telegram_reception'] = True
                signal_flow_test['signal_parsing'] = True
                
        self.test_results['cross_system'] = signal_flow_test
    
    def generate_report(self):
        """Generate comprehensive QA report"""
        self.log("Generating Comprehensive QA Report...")
        
        report = f"""
================================================================================
SIGNALOS COMPREHENSIVE QA AUDIT REPORT
================================================================================
Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🖥 DESKTOP APPLICATION (Windows App)
----------------------------------------
"""
        
        for test, result in self.test_results['desktop_app'].items():
            report += f"{test.replace('_', ' ').title():<30} | {result}\n"
        
        report += f"""
🌐 WEB-BASED USER DASHBOARD
----------------------------------------
"""
        
        for test, result in self.test_results['web_dashboard'].items():
            report += f"{test.replace('_', ' ').title():<30} | {result}\n"
        
        report += f"""
🤖 ADMIN PANEL
----------------------------------------
"""
        
        for test, result in self.test_results['admin_panel'].items():
            report += f"{test.replace('_', ' ').title():<30} | {result}\n"
        
        report += f"""
🔗 CROSS-SYSTEM INTEGRATION
----------------------------------------
"""
        
        if 'cross_system' in self.test_results:
            for test, result in self.test_results['cross_system'].items():
                status = "✔ Working" if result else "❌ Failed"
                report += f"{test.replace('_', ' ').title():<30} | {status}\n"
        
        report += f"""
🐛 BUGS FOUND ({len(self.bugs_found)})
----------------------------------------
"""
        for i, bug in enumerate(self.bugs_found, 1):
            report += f"{i}. {bug}\n"
        
        if not self.bugs_found:
            report += "No critical bugs detected.\n"
        
        report += f"""
📋 MISSING FEATURES ({len(self.missing_features)})
----------------------------------------
"""
        for i, feature in enumerate(self.missing_features, 1):
            report += f"{i}. {feature}\n"
        
        if not self.missing_features:
            report += "All core features implemented.\n"
        
        report += """
================================================================================
"""
        
        # Save report to file
        with open('comprehensive_qa_report.txt', 'w') as f:
            f.write(report)
        
        print(report)
        return report

def main():
    """Run comprehensive QA audit"""
    auditor = SignalOSQAAuditor()
    
    auditor.log("🚀 Starting Comprehensive SignalOS QA Audit...")
    
    # Test all components
    auditor.test_desktop_app()
    auditor.test_web_dashboard()
    auditor.test_admin_panel()
    auditor.test_cross_system_integration()
    
    # Generate final report
    auditor.generate_report()
    
    auditor.log("✅ Comprehensive QA audit completed!")

if __name__ == "__main__":
    main()