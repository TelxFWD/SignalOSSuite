#!/usr/bin/env python3
"""
Comprehensive Dashboard Testing and Bug Detection Script
Tests all dashboard functionality end-to-end and identifies issues
"""

import requests
import json
import time
import sys
from datetime import datetime

class DashboardTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_authentication(self):
        """Test user authentication flow"""
        print("\n🔐 Testing Authentication...")
        
        # Test login with demo credentials
        try:
            response = self.session.post(f"{self.base_url}/api/auth/login", 
                json={'email': 'demo@signalos.com', 'password': 'demo'})
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.auth_token = data['token']
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log_test("Demo Login", True, f"User: {data['user']['name']}")
                else:
                    self.log_test("Demo Login", False, "Missing token or user data")
            else:
                self.log_test("Demo Login", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Demo Login", False, f"Exception: {str(e)}")
            
        # Test invalid login
        try:
            response = self.session.post(f"{self.base_url}/api/auth/login", 
                json={'email': 'invalid@test.com', 'password': 'wrong'})
            
            if response.status_code == 401:
                self.log_test("Invalid Login Rejection", True, "Correctly rejected")
            else:
                self.log_test("Invalid Login Rejection", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Login Rejection", False, f"Exception: {str(e)}")
    
    def test_system_health(self):
        """Test system health monitoring"""
        print("\n🏥 Testing Health Monitoring...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['status', 'timestamp', 'services']
                
                if all(field in data for field in required_fields):
                    services = data['services']
                    if 'database' in services and 'telegram' in services and 'mt5' in services:
                        self.log_test("Health Endpoint Structure", True, "All required fields present")
                    else:
                        self.log_test("Health Endpoint Structure", False, "Missing service status fields")
                else:
                    self.log_test("Health Endpoint Structure", False, "Missing required fields")
            else:
                self.log_test("Health Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Exception: {str(e)}")
    
    def test_telegram_management(self):
        """Test Telegram session and channel management"""
        print("\n📱 Testing Telegram Management...")
        
        # Test getting sessions
        try:
            response = self.session.get(f"{self.base_url}/api/telegram/sessions")
            
            if response.status_code == 200:
                data = response.json()
                if 'sessions' in data:
                    self.log_test("Get Telegram Sessions", True, f"Found {len(data['sessions'])} sessions")
                else:
                    self.log_test("Get Telegram Sessions", False, "Missing 'sessions' field")
            else:
                self.log_test("Get Telegram Sessions", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Telegram Sessions", False, f"Exception: {str(e)}")
        
        # Test adding session
        try:
            session_data = {
                'phone': '+1987654321',
                'api_id': '54321',
                'api_hash': 'test_hash'
            }
            response = self.session.post(f"{self.base_url}/api/telegram/sessions", json=session_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'id' in data:
                    session_id = data['id']
                    self.log_test("Add Telegram Session", True, f"Session ID: {session_id}")
                    
                    # Test deleting the session
                    delete_response = self.session.delete(f"{self.base_url}/api/telegram/sessions/{session_id}")
                    if delete_response.status_code == 200:
                        self.log_test("Delete Telegram Session", True, "Session deleted successfully")
                    else:
                        self.log_test("Delete Telegram Session", False, f"Status: {delete_response.status_code}")
                else:
                    self.log_test("Add Telegram Session", False, "Missing response fields")
            else:
                self.log_test("Add Telegram Session", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Add Telegram Session", False, f"Exception: {str(e)}")
        
        # Test getting channels
        try:
            response = self.session.get(f"{self.base_url}/api/telegram/channels")
            
            if response.status_code == 200:
                data = response.json()
                if 'channels' in data:
                    self.log_test("Get Telegram Channels", True, f"Found {len(data['channels'])} channels")
                else:
                    self.log_test("Get Telegram Channels", False, "Missing 'channels' field")
            else:
                self.log_test("Get Telegram Channels", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Telegram Channels", False, f"Exception: {str(e)}")
    
    def test_mt5_management(self):
        """Test MT5 terminal management"""
        print("\n💹 Testing MT5 Management...")
        
        # Test getting terminals
        try:
            response = self.session.get(f"{self.base_url}/api/mt5/terminals")
            
            if response.status_code == 200:
                data = response.json()
                if 'terminals' in data:
                    self.log_test("Get MT5 Terminals", True, f"Found {len(data['terminals'])} terminals")
                else:
                    self.log_test("Get MT5 Terminals", False, "Missing 'terminals' field")
            else:
                self.log_test("Get MT5 Terminals", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get MT5 Terminals", False, f"Exception: {str(e)}")
        
        # Test adding terminal
        try:
            terminal_data = {
                'name': 'Test Terminal',
                'server': 'TestServer-Demo',
                'login': '999999',
                'password': 'test_password'
            }
            response = self.session.post(f"{self.base_url}/api/mt5/terminals", json=terminal_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'id' in data:
                    terminal_id = data['id']
                    self.log_test("Add MT5 Terminal", True, f"Terminal ID: {terminal_id}")
                    
                    # Test deleting the terminal
                    delete_response = self.session.delete(f"{self.base_url}/api/mt5/terminals/{terminal_id}")
                    if delete_response.status_code == 200:
                        self.log_test("Delete MT5 Terminal", True, "Terminal deleted successfully")
                    else:
                        self.log_test("Delete MT5 Terminal", False, f"Status: {delete_response.status_code}")
                else:
                    self.log_test("Add MT5 Terminal", False, "Missing response fields")
            else:
                self.log_test("Add MT5 Terminal", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Add MT5 Terminal", False, f"Exception: {str(e)}")
    
    def test_strategy_management(self):
        """Test trading strategy management"""
        print("\n🎯 Testing Strategy Management...")
        
        # Test getting strategies
        try:
            response = self.session.get(f"{self.base_url}/api/strategies")
            
            if response.status_code == 200:
                data = response.json()
                if 'strategies' in data:
                    self.log_test("Get Strategies", True, f"Found {len(data['strategies'])} strategies")
                else:
                    self.log_test("Get Strategies", False, "Missing 'strategies' field")
            else:
                self.log_test("Get Strategies", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Get Strategies", False, f"Exception: {str(e)}")
        
        # Test creating strategy
        try:
            strategy_data = {
                'name': 'Test Strategy',
                'type': 'beginner',
                'max_risk': '1.5',
                'description': 'Test strategy for automated testing'
            }
            response = self.session.post(f"{self.base_url}/api/strategies", json=strategy_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'id' in data:
                    strategy_id = data['id']
                    self.log_test("Create Strategy", True, f"Strategy ID: {strategy_id}")
                    
                    # Test deleting the strategy
                    delete_response = self.session.delete(f"{self.base_url}/api/strategies/{strategy_id}")
                    if delete_response.status_code == 200:
                        self.log_test("Delete Strategy", True, "Strategy deleted successfully")
                    else:
                        self.log_test("Delete Strategy", False, f"Status: {delete_response.status_code}")
                else:
                    self.log_test("Create Strategy", False, "Missing response fields")
            else:
                self.log_test("Create Strategy", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Create Strategy", False, f"Exception: {str(e)}")
    
    def test_analytics(self):
        """Test analytics and performance data"""
        print("\n📈 Testing Analytics...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/daily")
            
            if response.status_code == 200:
                data = response.json()
                if 'daily_stats' in data:
                    stats = data['daily_stats']
                    if len(stats) > 0:
                        # Validate structure of first stat entry
                        first_stat = stats[0]
                        required_fields = ['date', 'trades', 'pips', 'profit']
                        
                        if all(field in first_stat for field in required_fields):
                            self.log_test("Analytics Data Structure", True, f"Found {len(stats)} days of data")
                        else:
                            self.log_test("Analytics Data Structure", False, "Missing required fields in stats")
                    else:
                        self.log_test("Analytics Data", False, "No analytics data returned")
                else:
                    self.log_test("Analytics Data", False, "Missing 'daily_stats' field")
            else:
                self.log_test("Analytics Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Analytics Endpoint", False, f"Exception: {str(e)}")
    
    def test_signal_simulation(self):
        """Test signal simulation functionality"""
        print("\n🔄 Testing Signal Simulation...")
        
        # Test basic signal simulation
        try:
            signal_data = {
                'pair': 'GBPUSD',
                'action': 'SELL'
            }
            response = self.session.post(f"{self.base_url}/api/signals/simulate", json=signal_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'signal' in data:
                    signal = data['signal']
                    required_fields = ['id', 'pair', 'action', 'entry', 'sl', 'tp', 'timestamp', 'status']
                    
                    if all(field in signal for field in required_fields):
                        self.log_test("Signal Simulation", True, f"Generated signal for {signal['pair']}")
                    else:
                        self.log_test("Signal Simulation", False, "Missing signal fields")
                else:
                    self.log_test("Signal Simulation", False, "Missing response fields")
            else:
                self.log_test("Signal Simulation", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Signal Simulation", False, f"Exception: {str(e)}")
    
    def test_shadow_mode(self):
        """Test shadow mode functionality"""
        print("\n🌙 Testing Shadow Mode...")
        
        try:
            # Test enabling shadow mode
            response = self.session.post(f"{self.base_url}/api/settings/shadow-mode", 
                json={'enabled': True})
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'enabled' in data:
                    if data['enabled'] == True:
                        self.log_test("Enable Shadow Mode", True, "Shadow mode enabled")
                        
                        # Test disabling shadow mode
                        disable_response = self.session.post(f"{self.base_url}/api/settings/shadow-mode", 
                            json={'enabled': False})
                        
                        if disable_response.status_code == 200:
                            disable_data = disable_response.json()
                            if disable_data.get('enabled') == False:
                                self.log_test("Disable Shadow Mode", True, "Shadow mode disabled")
                            else:
                                self.log_test("Disable Shadow Mode", False, "Failed to disable")
                        else:
                            self.log_test("Disable Shadow Mode", False, f"Status: {disable_response.status_code}")
                    else:
                        self.log_test("Enable Shadow Mode", False, "Not properly enabled")
                else:
                    self.log_test("Enable Shadow Mode", False, "Missing response fields")
            else:
                self.log_test("Enable Shadow Mode", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Shadow Mode", False, f"Exception: {str(e)}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🚨 Testing Edge Cases...")
        
        # Test invalid strategy creation
        try:
            response = self.session.post(f"{self.base_url}/api/strategies", json={})
            # Should handle empty data gracefully
            self.log_test("Empty Strategy Data", response.status_code in [400, 500], 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Empty Strategy Data", False, f"Exception: {str(e)}")
        
        # Test invalid terminal creation
        try:
            response = self.session.post(f"{self.base_url}/api/mt5/terminals", 
                json={'name': 'Test', 'server': '', 'login': '', 'password': ''})
            # Should handle invalid data gracefully
            self.log_test("Invalid Terminal Data", response.status_code in [400, 500], 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Terminal Data", False, f"Exception: {str(e)}")
        
        # Test deleting non-existent resources
        try:
            response = self.session.delete(f"{self.base_url}/api/strategies/99999")
            # Should return 404 or handle gracefully
            self.log_test("Delete Non-existent Strategy", response.status_code in [404, 500], 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Delete Non-existent Strategy", False, f"Exception: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE DASHBOARD TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"\nOverall Results:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        print(f"Failed: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n✅ Successful Tests:")
        for result in self.test_results:
            if result['passed']:
                print(f"  - {result['test']}")
        
        # Save detailed report
        with open('dashboard_test_report.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.test_results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: dashboard_test_report.json")
        
        return failed_tests == 0
    
    def run_comprehensive_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Dashboard Testing...")
        print(f"Target URL: {self.base_url}")
        
        # Test connection
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code != 200:
                print(f"❌ Cannot connect to dashboard at {self.base_url}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
        
        # Run all tests
        self.test_authentication()
        self.test_system_health()
        self.test_telegram_management()
        self.test_mt5_management()
        self.test_strategy_management()
        self.test_analytics()
        self.test_signal_simulation()
        self.test_shadow_mode()
        self.test_edge_cases()
        
        # Generate final report
        return self.generate_report()

if __name__ == "__main__":
    tester = DashboardTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 All tests passed! Dashboard is fully functional.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the report for details.")
        sys.exit(1)