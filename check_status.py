#!/usr/bin/env python3
"""
Quick status check for SignalOS components
"""

import os
import sys

def check_environment():
    """Check environment variables and dependencies"""
    print("=== SignalOS Environment Check ===")
    
    # Check environment variables
    db_url = os.environ.get('DATABASE_URL')
    print(f"DATABASE_URL: {'✓ Set' if db_url else '✗ Missing'}")
    
    port = os.environ.get('PORT', '5000')
    print(f"PORT: {port}")
    
    # Check Python packages
    packages = ['flask', 'flask-socketio', 'psutil', 'pyjwt', 'requests']
    missing = []
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"{package}: ✓ Available")
        except ImportError:
            print(f"{package}: ✗ Missing")
            missing.append(package)
    
    # Check optional packages
    optional = ['sqlalchemy', 'psycopg2']
    for package in optional:
        try:
            __import__(package.replace('-', '_'))
            print(f"{package}: ✓ Available (optional)")
        except ImportError:
            print(f"{package}: ⚠ Missing (optional, fallback mode active)")
    
    print(f"\nStatus: {'✓ Ready' if not missing else '⚠ Missing required packages'}")
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)