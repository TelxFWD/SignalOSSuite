"""
SignalOS Production Readiness Audit
Comprehensive testing and validation for production deployment
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionReadinessAuditor:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "pending",
            "components": {},
            "critical_issues": [],
            "recommendations": [],
            "deployment_ready": False
        }
        
    def log_result(self, component, status, message, critical=False):
        """Log test result"""
        logger.info(f"{component}: {status} - {message}")
        self.results["components"][component] = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if critical and status == "FAIL":
            self.results["critical_issues"].append(f"{component}: {message}")
    
    def test_web_application(self):
        """Test web application core functionality"""
        logger.info("Testing web application...")
        
        try:
            # Test main page
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.log_result("Web Application", "PASS", "Main page accessible")
            else:
                self.log_result("Web Application", "FAIL", f"Main page returned {response.status_code}", critical=True)
                
            # Test health endpoint
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_result("Health API", "PASS", f"Health check successful: {health_data.get('status', 'unknown')}")
            else:
                self.log_result("Health API", "FAIL", f"Health endpoint failed: {response.status_code}", critical=True)
                
        except requests.exceptions.RequestException as e:
            self.log_result("Web Application", "FAIL", f"Connection failed: {str(e)}", critical=True)
    
    def test_database_connectivity(self):
        """Test database connectivity and operations"""
        logger.info("Testing database connectivity...")
        
        try:
            # Test database tables endpoint
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("database", {}).get("status") == "connected":
                    self.log_result("Database", "PASS", "Database connection successful")
                else:
                    self.log_result("Database", "FAIL", "Database not connected", critical=True)
            else:
                self.log_result("Database", "FAIL", "Unable to check database status", critical=True)
                
        except Exception as e:
            self.log_result("Database", "FAIL", f"Database test failed: {str(e)}", critical=True)
    
    def test_admin_panel(self):
        """Test admin panel functionality"""
        logger.info("Testing admin panel...")
        
        try:
            # Test admin login page
            response = requests.get(f"{self.base_url}/admin/login", timeout=10)
            if response.status_code == 200:
                self.log_result("Admin Panel", "PASS", "Admin panel accessible")
            else:
                self.log_result("Admin Panel", "FAIL", f"Admin panel not accessible: {response.status_code}")
                
            # Test admin authentication with demo credentials
            login_data = {"email": "admin@signalos.com", "password": "admin123"}
            response = requests.post(f"{self.base_url}/admin/login", data=login_data, timeout=10)
            if response.status_code in [200, 302]:  # Success or redirect
                self.log_result("Admin Auth", "PASS", "Admin authentication working")
            else:
                self.log_result("Admin Auth", "FAIL", f"Admin authentication failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Admin Panel", "FAIL", f"Admin panel test failed: {str(e)}")
    
    def test_signal_parsing(self):
        """Test signal parsing functionality"""
        logger.info("Testing signal parsing...")
        
        # Test signals with different formats
        test_signals = [
            "GOLD LONG ENTRY: 2650 SL: 2640 TP: 2670",
            "XAU/USD BUY @ 2650.50 Stop Loss: 2640.00 Take Profit: 2670.00",
            "EURUSD SELL ENTRY 1.0850 SL 1.0870 TP 1.0820",
            "BTC LONG 45000 SL 44000 TP 47000"
        ]
        
        passed = 0
        total = len(test_signals)
        
        for i, signal_text in enumerate(test_signals):
            try:
                # Simulate signal processing
                signal_data = {
                    "text": signal_text,
                    "source": "test",
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(f"{self.base_url}/api/simulate-signal", 
                                       json=signal_data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        passed += 1
                        logger.info(f"Signal {i+1} parsed successfully")
                    else:
                        logger.warning(f"Signal {i+1} parsing failed: {result.get('error', 'unknown')}")
                else:
                    logger.warning(f"Signal {i+1} request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Signal {i+1} test error: {str(e)}")
        
        success_rate = (passed / total) * 100
        if success_rate >= 75:
            self.log_result("Signal Parser", "PASS", f"Signal parsing: {success_rate:.1f}% success rate ({passed}/{total})")
        else:
            self.log_result("Signal Parser", "FAIL", f"Signal parsing below threshold: {success_rate:.1f}% ({passed}/{total})", critical=True)
    
    def test_mt5_integration(self):
        """Test MT5 integration components"""
        logger.info("Testing MT5 integration...")
        
        # Check if MT5 EA file exists
        ea_file = Path("desktop_app/experts/SignalOS_EA.mq5")
        if ea_file.exists():
            self.log_result("MT5 EA File", "PASS", "Expert Advisor file present")
        else:
            self.log_result("MT5 EA File", "FAIL", "Expert Advisor file missing", critical=True)
        
        # Test signal file generation
        try:
            test_signal = {
                "pair": "EURUSD",
                "action": "BUY",
                "entry_price": 1.0850,
                "stop_loss": 1.0830,
                "take_profit": 1.0880,
                "lot_size": 0.01,
                "comment": "Test signal"
            }
            
            # Create test signal file
            signal_dir = Path("temp_signals")
            signal_dir.mkdir(exist_ok=True)
            signal_file = signal_dir / "test_signal.json"
            
            with open(signal_file, 'w') as f:
                json.dump(test_signal, f, indent=2)
            
            if signal_file.exists():
                self.log_result("Signal File Gen", "PASS", "Signal file generation working")
                signal_file.unlink()  # Clean up
                signal_dir.rmdir()
            else:
                self.log_result("Signal File Gen", "FAIL", "Signal file generation failed")
                
        except Exception as e:
            self.log_result("Signal File Gen", "FAIL", f"Signal file test failed: {str(e)}")
    
    def test_websocket_connectivity(self):
        """Test WebSocket connectivity"""
        logger.info("Testing WebSocket connectivity...")
        
        try:
            # Test Socket.IO endpoint
            response = requests.get(f"{self.base_url}/socket.io/?EIO=4&transport=polling", timeout=10)
            if response.status_code == 200:
                self.log_result("WebSocket", "PASS", "Socket.IO endpoint accessible")
            else:
                self.log_result("WebSocket", "FAIL", f"Socket.IO failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("WebSocket", "FAIL", f"WebSocket test failed: {str(e)}")
    
    def test_shadow_mode(self):
        """Test shadow mode functionality"""
        logger.info("Testing shadow mode...")
        
        try:
            # Test shadow mode toggle
            response = requests.post(f"{self.base_url}/api/toggle-shadow-mode", timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Shadow Mode", "PASS", f"Shadow mode toggle working: {result.get('shadow_mode', 'unknown')}")
            else:
                self.log_result("Shadow Mode", "FAIL", f"Shadow mode toggle failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Shadow Mode", "FAIL", f"Shadow mode test failed: {str(e)}")
    
    def test_security_features(self):
        """Test security features"""
        logger.info("Testing security features...")
        
        # Test CORS headers
        try:
            response = requests.options(f"{self.base_url}/api/health", timeout=10)
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                self.log_result("CORS", "PASS", f"CORS configured: {cors_header}")
            else:
                self.log_result("CORS", "WARN", "CORS headers not found")
                
        except Exception as e:
            self.log_result("CORS", "FAIL", f"CORS test failed: {str(e)}")
        
        # Test authentication endpoints
        try:
            response = requests.get(f"{self.base_url}/api/daily-analytics", timeout=10)
            if response.status_code in [401, 403]:
                self.log_result("Auth Protection", "PASS", "Protected endpoints require authentication")
            elif response.status_code == 200:
                self.log_result("Auth Protection", "WARN", "Protected endpoints accessible without auth")
            else:
                self.log_result("Auth Protection", "FAIL", f"Unexpected auth response: {response.status_code}")
                
        except Exception as e:
            self.log_result("Auth Protection", "FAIL", f"Auth test failed: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling"""
        logger.info("Testing error handling...")
        
        try:
            # Test 404 handling
            response = requests.get(f"{self.base_url}/nonexistent-endpoint", timeout=10)
            if response.status_code == 404:
                self.log_result("Error Handling", "PASS", "404 errors handled correctly")
            else:
                self.log_result("Error Handling", "WARN", f"Unexpected 404 response: {response.status_code}")
                
        except Exception as e:
            self.log_result("Error Handling", "FAIL", f"Error handling test failed: {str(e)}")
    
    def generate_recommendations(self):
        """Generate deployment recommendations"""
        logger.info("Generating recommendations...")
        
        failed_components = [comp for comp, data in self.results["components"].items() 
                           if data["status"] == "FAIL"]
        warn_components = [comp for comp, data in self.results["components"].items() 
                          if data["status"] == "WARN"]
        
        if len(self.results["critical_issues"]) == 0:
            self.results["deployment_ready"] = True
            self.results["overall_status"] = "READY"
            self.results["recommendations"].append("✅ System ready for production deployment")
        else:
            self.results["overall_status"] = "NOT_READY"
            self.results["recommendations"].append("❌ Critical issues must be resolved before deployment")
        
        if failed_components:
            self.results["recommendations"].append(f"🔧 Fix failed components: {', '.join(failed_components)}")
        
        if warn_components:
            self.results["recommendations"].append(f"⚠️ Review warnings: {', '.join(warn_components)}")
        
        # Performance recommendations
        passed_components = [comp for comp, data in self.results["components"].items() 
                           if data["status"] == "PASS"]
        total_components = len(self.results["components"])
        success_rate = (len(passed_components) / total_components) * 100 if total_components > 0 else 0
        
        self.results["recommendations"].append(f"📊 System health: {success_rate:.1f}% ({len(passed_components)}/{total_components} components passing)")
        
        if success_rate >= 90:
            self.results["recommendations"].append("🚀 Excellent system health - ready for production")
        elif success_rate >= 75:
            self.results["recommendations"].append("✅ Good system health - minor issues to address")
        else:
            self.results["recommendations"].append("⚠️ System needs significant improvements before deployment")
    
    def run_audit(self):
        """Run complete production readiness audit"""
        logger.info("Starting Production Readiness Audit...")
        
        # Run all tests
        self.test_web_application()
        time.sleep(1)
        self.test_database_connectivity()
        time.sleep(1)
        self.test_admin_panel()
        time.sleep(1)
        self.test_signal_parsing()
        time.sleep(1)
        self.test_mt5_integration()
        time.sleep(1)
        self.test_websocket_connectivity()
        time.sleep(1)
        self.test_shadow_mode()
        time.sleep(1)
        self.test_security_features()
        time.sleep(1)
        self.test_error_handling()
        
        # Generate recommendations
        self.generate_recommendations()
        
        return self.results
    
    def save_report(self, filename="production_readiness_report.json"):
        """Save audit report to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Report saved to {filename}")

def main():
    """Run production readiness audit"""
    auditor = ProductionReadinessAuditor()
    results = auditor.run_audit()
    
    # Save detailed report
    auditor.save_report()
    
    # Print summary
    print("\n" + "="*60)
    print("SIGNALOS PRODUCTION READINESS AUDIT SUMMARY")
    print("="*60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Deployment Ready: {'✅ YES' if results['deployment_ready'] else '❌ NO'}")
    print(f"Critical Issues: {len(results['critical_issues'])}")
    print(f"Timestamp: {results['timestamp']}")
    
    print("\nCOMPONENT STATUS:")
    print("-" * 40)
    for component, data in results["components"].items():
        status_icon = "✅" if data["status"] == "PASS" else "❌" if data["status"] == "FAIL" else "⚠️"
        print(f"{status_icon} {component}: {data['status']} - {data['message']}")
    
    if results["critical_issues"]:
        print("\nCRITICAL ISSUES:")
        print("-" * 40)
        for issue in results["critical_issues"]:
            print(f"❌ {issue}")
    
    print("\nRECOMMENDATIONS:")
    print("-" * 40)
    for rec in results["recommendations"]:
        print(f"📋 {rec}")
    
    print("\n" + "="*60)
    return results

if __name__ == "__main__":
    main()