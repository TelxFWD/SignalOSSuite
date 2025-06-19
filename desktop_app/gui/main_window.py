"""
Main application window
"""

import sys
from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTabWidget, QStatusBar, QMenuBar, QAction, 
                               QMessageBox, QProgressBar, QLabel, QSplitter)
from PySide2.QtCore import Qt, QTimer, Signal, QThread
from PySide2.QtGui import QKeySequence, QIcon

from gui.login_dialog import LoginDialog
from gui.dashboard import DashboardWidget
from gui.telegram_manager import TelegramManagerWidget
from gui.parser_config import ParserConfigWidget
from gui.mt5_config import MT5ConfigWidget
from gui.health_monitor import HealthMonitorWidget
from config.auth import auth_manager
from config.settings import settings
from core.logger import get_logger

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    status_updated = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SignalOS - Forex Signal Automation Platform")
        self.setMinimumSize(1200, 800)
        
        # Initialize components
        self.central_widget = None
        self.tab_widget = None
        self.status_bar = None
        self.progress_bar = None
        self.status_label = None
        
        # Initialize UI
        self.init_ui()
        self.init_menu_bar()
        self.init_status_bar()
        
        # Connect signals
        self.status_updated.connect(self.update_status)
        
        # Check authentication
        self.check_authentication()
        
        # Setup periodic updates
        self.setup_timers()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        splitter.addWidget(self.tab_widget)
        
        # Add tabs
        self.dashboard_widget = DashboardWidget()
        self.telegram_widget = TelegramManagerWidget()
        self.parser_widget = ParserConfigWidget()
        self.mt5_widget = MT5ConfigWidget()
        
        self.tab_widget.addTab(self.dashboard_widget, "Dashboard")
        self.tab_widget.addTab(self.telegram_widget, "Telegram")
        self.tab_widget.addTab(self.parser_widget, "Parser")
        self.tab_widget.addTab(self.mt5_widget, "MT5")
        
        # Add health monitor widget to the right side
        self.health_widget = HealthMonitorWidget()
        splitter.addWidget(self.health_widget)
        
        # Set splitter proportions
        splitter.setSizes([800, 400])
    
    def init_menu_bar(self):
        """Initialize the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Import config action
        import_action = QAction('&Import Config...', self)
        import_action.setShortcut(QKeySequence.Open)
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        # Export config action
        export_action = QAction('&Export Config...', self)
        export_action.setShortcut(QKeySequence.SaveAs)
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        # Shadow mode toggle
        shadow_action = QAction('&Shadow Mode', self)
        shadow_action.setCheckable(True)
        shadow_action.setChecked(settings.shadow_mode)
        shadow_action.triggered.connect(self.toggle_shadow_mode)
        tools_menu.addAction(shadow_action)
        
        # Offline mode toggle
        offline_action = QAction('&Offline Mode', self)
        offline_action.setCheckable(True)
        offline_action.setChecked(settings.offline_mode)
        offline_action.triggered.connect(self.toggle_offline_mode)
        tools_menu.addAction(offline_action)
        
        tools_menu.addSeparator()
        
        # Preferences action
        prefs_action = QAction('&Preferences...', self)
        prefs_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(prefs_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = QAction('&About SignalOS', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_status_bar(self):
        """Initialize the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setStyleSheet("color: red;")
        self.status_bar.addPermanentWidget(self.connection_label)
    
    def setup_timers(self):
        """Setup periodic update timers"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def check_authentication(self):
        """Check if user is authenticated"""
        if not auth_manager.is_authenticated():
            self.show_login_dialog()
    
    def show_login_dialog(self):
        """Show the login dialog"""
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == LoginDialog.Accepted:
            self.on_login_success()
        else:
            # User cancelled login, close application
            self.close()
    
    def on_login_success(self):
        """Handle successful login"""
        self.status_updated.emit("Login successful")
        
        # Sync configuration from server
        self.sync_configuration()
        
        # Update connection status
        self.update_connection_status()
    
    def sync_configuration(self):
        """Sync configuration from server"""
        try:
            self.progress_bar.setVisible(True)
            self.status_updated.emit("Syncing configuration...")
            
            success, config_data = auth_manager.sync_user_config()
            if success and config_data:
                # Update local configuration
                settings.load_config()
                self.status_updated.emit("Configuration synced successfully")
            else:
                self.status_updated.emit("Using local configuration")
                
        except Exception as e:
            logger.error(f"Error syncing configuration: {e}")
            self.status_updated.emit("Configuration sync failed")
        finally:
            self.progress_bar.setVisible(False)
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.setText(message)
    
    def update_connection_status(self):
        """Update connection status indicator"""
        if auth_manager.is_authenticated():
            self.connection_label.setText("Connected")
            self.connection_label.setStyleSheet("color: green;")
        else:
            self.connection_label.setText("Disconnected")
            self.connection_label.setStyleSheet("color: red;")
    
    def import_config(self):
        """Import configuration from file"""
        from PySide2.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if settings.import_config(file_path):
                QMessageBox.information(self, "Success", "Configuration imported successfully!")
                self.refresh_all_widgets()
            else:
                QMessageBox.critical(self, "Error", "Failed to import configuration!")
    
    def export_config(self):
        """Export configuration to file"""
        from PySide2.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            "signalos_config.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if settings.export_config(file_path):
                QMessageBox.information(self, "Success", "Configuration exported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to export configuration!")
    
    def toggle_shadow_mode(self, checked: bool):
        """Toggle shadow mode"""
        settings.shadow_mode = checked
        settings.save_config()
        self.status_updated.emit(f"Shadow mode {'enabled' if checked else 'disabled'}")
    
    def toggle_offline_mode(self, checked: bool):
        """Toggle offline mode"""
        settings.offline_mode = checked
        settings.save_config()
        self.status_updated.emit(f"Offline mode {'enabled' if checked else 'disabled'}")
    
    def show_preferences(self):
        """Show preferences dialog"""
        QMessageBox.information(self, "Preferences", "Preferences dialog not implemented yet")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SignalOS",
            """<h2>SignalOS v1.0.0</h2>
            <p>Advanced Forex Signal Automation Platform</p>
            <p>Features:</p>
            <ul>
            <li>Telegram signal monitoring</li>
            <li>AI-powered signal parsing</li>
            <li>MT5 integration</li>
            <li>Real-time health monitoring</li>
            </ul>
            <p>© 2025 SignalOS Ltd. All rights reserved.</p>"""
        )
    
    def refresh_all_widgets(self):
        """Refresh all widget data"""
        self.dashboard_widget.refresh_data()
        self.telegram_widget.refresh_data()
        self.parser_widget.refresh_data()
        self.mt5_widget.refresh_data()
        self.health_widget.refresh_data()
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(
            self,
            "Exit SignalOS",
            "Are you sure you want to exit SignalOS?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cleanup()
            event.accept()
        else:
            event.ignore()
    
    def cleanup(self):
        """Cleanup resources before exit"""
        logger.info("Application shutting down...")
        
        # Stop timers
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Cleanup widgets
        try:
            self.dashboard_widget.cleanup()
            self.telegram_widget.cleanup()
            self.parser_widget.cleanup()
            self.mt5_widget.cleanup()
            self.health_widget.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # Save configuration
        settings.save_config()
