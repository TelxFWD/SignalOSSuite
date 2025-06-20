#!/usr/bin/env python3
"""
SignalOS Desktop Console Monitor
Standalone monitoring application that doesn't import Flask modules
"""

import sys
import time
import requests
from datetime import datetime

def main():
    """Main entry point for SignalOS Desktop Console Monitor"""
    print("SignalOS Desktop Console Monitor - Starting...")
    print("Features:")
    print("- Real-time system monitoring")
    print("- Web application health checks") 
    print("- Trading analytics display")
    print("- Connection status monitoring")
    print("-" * 50)
    
    try:
        # Test initial connection
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=5)
            web_status = "Connected" if response.status_code == 200 else "Disconnected"
        except:
            web_status = "Disconnected"
        
        print(f"Initial Web Application Status: {web_status}")
        print("Monitoring active - updates every 30 seconds")
        print("Press Ctrl+C to exit")
        
        while True:
            try:
                # Check web app health
                health_response = requests.get('http://localhost:5000/api/health', timeout=5)
                health_data = health_response.json() if health_response.status_code == 200 else {}
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] SignalOS Monitor")
                print(f"Web App: {'✓ Online' if health_response.status_code == 200 else '✗ Offline'}")
                print(f"Database: {'✓ Connected' if health_data.get('services', {}).get('database') else '✗ Disconnected'}")
                print(f"Dashboard: http://localhost:5000")
                
                # Check analytics data
                try:
                    analytics_response = requests.get('http://localhost:5000/api/analytics/daily', timeout=5)
                    if analytics_response.status_code == 200:
                        analytics = analytics_response.json()
                        print(f"Signals: {analytics.get('active_signals', 'N/A')} | Pips: {analytics.get('total_pips', 'N/A')} | Win Rate: {analytics.get('win_rate', 'N/A')}%")
                except:
                    print("Analytics: Not available")
                
            except Exception as e:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Connection error: {e}")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nShutting down SignalOS Desktop Monitor...")
        return 0
    except Exception as e:
        print(f"Console error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())