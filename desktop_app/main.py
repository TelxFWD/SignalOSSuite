#!/usr/bin/env python3
"""
SignalOS Desktop Application - Windows App Entry Point
Main entry point for the desktop Windows application with GUI interface
"""

import sys
import os
from pathlib import Path

# Add desktop_app to Python path
desktop_app_root = Path(__file__).parent
sys.path.insert(0, str(desktop_app_root))

# Import GUI components
try:
    from gui.main_window import SignalOSMainWindow
    from core.logger import setup_logging, get_signalos_logger
    from config.settings import AppSettings
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"GUI components not available: {e}")
    GUI_AVAILABLE = False

def main():
    """Main entry point for SignalOS Desktop Application"""
    if not GUI_AVAILABLE:
        print("Desktop application requires GUI components")
        return 1
    
    # Setup logging
    setup_logging()
    logger = get_signalos_logger(__name__)
    
    try:
        # Initialize settings
        settings = AppSettings()
        
        # Create and run the GUI application
        app = SignalOSMainWindow(settings)
        return app.run()
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())