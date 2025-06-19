#!/usr/bin/env python3
"""
SignalOS Desktop Application Entry Point
Main launcher for the Windows desktop application
"""

import sys
from pathlib import Path

# Add desktop_app to Python path
desktop_app_path = Path(__file__).parent / 'desktop_app'
sys.path.insert(0, str(desktop_app_path))

def main():
    """Launch the SignalOS desktop application"""
    try:
        from desktop_app.main import main as desktop_main
        return desktop_main()
    except ImportError as e:
        print(f"Failed to import desktop application: {e}")
        print("Make sure all dependencies are installed and desktop_app folder exists.")
        return 1

if __name__ == "__main__":
    sys.exit(main())