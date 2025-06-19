"""
MetaTrader 5 configuration widget
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QGroupBox, QLabel,
                               QCheckBox, QSpinBox, QFileDialog, QComboBox,
                               QListWidget, QListWidgetItem, QMessageBox,
                               QProgressBar, QTextEdit)
from PySide2.QtCore import Qt, QThread, Signal, QTimer
from PySide2.QtGui import QFont
from pathlib import Path
import os

from config.settings import settings
from core.mt5_sync import MT5Sync
from core.logger import get_logger

logger = get_logger(__name__)

class MT5Worker(QThread):
    """Worker thread for MT5 operations"""
    
    operation_completed = Signal(bool, str)
    terminals_found = Signal(list)
    
    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        """Execute MT5 operation"""
        try:
            if self.operation == "scan_terminals":
                self.scan_terminals()
            elif self.operation == "test_connection":
                self.test_connection()
            elif self.operation == "install_ea":
                self.install_ea()
            elif self.operation == "sync_ea":
                self.sync_ea()
        except Exception as e:
            self.operation_completed.emit(False, str(e))
    
    def scan_terminals(self):
        """Scan for MT5 terminals"""
        try:
            mt5_sync = MT5Sync()
            terminals = mt5_sync.scan_terminals()
            self.terminals_found.emit(terminals)
            self.operation_completed.emit(True, f"Found {len(terminals)} terminals")
        except Exception as e:
            self.operation_completed.emit(False, f"Scan error: {str(e)}")
    
    def test_connection(self):
        """Test MT5 connection"""
        try:
            mt5_sync = MT5Sync()
            if mt5_sync.test_connection():
                self.operation_completed.emit(True, "Connection successful")
            else:
                self.operation_completed.emit(False, "Connection failed")
        except Exception as e:
            self.operation_completed.emit(False, f"Connection error: {str(e)}")
    
    def install_ea(self):
        """Install Expert Advisor"""
        try:
            mt5_sync = MT5Sync()
            if mt5_sync.install_ea():
                self.operation_completed.emit(True, "EA installed successfully")
            else:
                self.operation_completed.emit(False, "EA installation failed")
        except Exception as e:
            self.operation_completed.emit(False, f"Installation error: {str(e)}")
    
    def sync_ea(self):
        """Sync with Expert Advisor"""
        try:
            mt5_sync = MT5Sync()
            if mt5_sync.sync_ea():
                self.operation_completed.emit(True, "EA sync successful")
            else:
                self.operation_completed.emit(False, "EA sync failed")
        except Exception as e:
            self.operation_completed.emit(False, f"Sync error: {str(e)}")

class MT5ConfigWidget(QWidget):
    """Widget for configuring MetaTrader 5 integration"""
    
    def __init__(self):
        super().__init__()
        self.mt5_worker = None
        self.init_ui()
        self.load_settings()
        self.setup_timers()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("MetaTrader 5 Configuration")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Main content layout
        content_layout = QHBoxLayout()
        
        # Left column - Configuration
        left_column = QVBoxLayout()
        
        # Terminal Settings Group
        terminal_group = QGroupBox("Terminal Settings")
        terminal_layout = QFormLayout(terminal_group)
        
        # Terminal path
        terminal_path_layout = QHBoxLayout()
        self.terminal_path_edit = QLineEdit()
        self.terminal_path_edit.setPlaceholderText("Select MT5 terminal path...")
        terminal_path_layout.addWidget(self.terminal_path_edit)
        
        self.browse_terminal_button = QPushButton("Browse")
        self.browse_terminal_button.clicked.connect(self.browse_terminal_path)
        terminal_path_layout.addWidget(self.browse_terminal_button)
        
        terminal_layout.addRow("Terminal Path:", terminal_path_layout)
        
        # Scan terminals button
        self.scan_button = QPushButton("Scan for Terminals")
        self.scan_button.clicked.connect(self.scan_terminals)
        terminal_layout.addRow("", self.scan_button)
        
        left_column.addWidget(terminal_group)
        
        # Login Credentials Group
        login_group = QGroupBox("Login Credentials")
        login_layout = QFormLayout(login_group)
        
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Enter MT5 login")
        login_layout.addRow("Login:", self.login_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter password")
        login_layout.addRow("Password:", self.password_edit)
        
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("Enter server name")
        login_layout.addRow("Server:", self.server_edit)
        
        left_column.addWidget(login_group)
        
        # Expert Advisor Settings Group
        ea_group = QGroupBox("Expert Advisor Settings")
        ea_layout = QFormLayout(ea_group)
        
        # Expert path
        expert_path_layout = QHBoxLayout()
        self.expert_path_edit = QLineEdit()
        self.expert_path_edit.setPlaceholderText("Path to SignalOS EA...")
        expert_path_layout.addWidget(self.expert_path_edit)
        
        self.browse_ea_button = QPushButton("Browse")
        self.browse_ea_button.clicked.connect(self.browse_ea_path)
        expert_path_layout.addWidget(self.browse_ea_button)
        
        ea_layout.addRow("EA Path:", expert_path_layout)
        
        # Magic number
        self.magic_spinbox = QSpinBox()
        self.magic_spinbox.setRange(100000, 999999)
        self.magic_spinbox.setValue(settings.mt5.magic_number)
        self.magic_spinbox.valueChanged.connect(self.update_magic_number)
        ea_layout.addRow("Magic Number:", self.magic_spinbox)
        
        # Auto restart
        self.auto_restart_checkbox = QCheckBox()
        self.auto_restart_checkbox.setChecked(settings.mt5.auto_restart)
        self.auto_restart_checkbox.stateChanged.connect(self.update_auto_restart)
        ea_layout.addRow("Auto Restart:", self.auto_restart_checkbox)
        
        # Heartbeat interval
        self.heartbeat_spinbox = QSpinBox()
        self.heartbeat_spinbox.setRange(10, 300)
        self.heartbeat_spinbox.setSuffix(" sec")
        self.heartbeat_spinbox.setValue(settings.mt5.heartbeat_interval)
        self.heartbeat_spinbox.valueChanged.connect(self.update_heartbeat)
        ea_layout.addRow("Heartbeat Interval:", self.heartbeat_spinbox)
        
        left_column.addWidget(ea_group)
        
        # Connection Management Group
        connection_group = QGroupBox("Connection Management")
        connection_layout = QVBoxLayout(connection_group)
        
        connection_buttons_layout = QHBoxLayout()
        
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_connection)
        connection_buttons_layout.addWidget(self.test_connection_button)
        
        self.install_ea_button = QPushButton("Install EA")
        self.install_ea_button.clicked.connect(self.install_ea)
        connection_buttons_layout.addWidget(self.install_ea_button)
        
        connection_layout.addLayout(connection_buttons_layout)
        
        sync_buttons_layout = QHBoxLayout()
        
        self.sync_ea_button = QPushButton("Sync EA")
        self.sync_ea_button.clicked.connect(self.sync_ea)
        sync_buttons_layout.addWidget(self.sync_ea_button)
        
        self.restart_ea_button = QPushButton("Restart EA")
        self.restart_ea_button.clicked.connect(self.restart_ea)
        sync_buttons_layout.addWidget(self.restart_ea_button)
        
        connection_layout.addLayout(sync_buttons_layout)
        
        left_column.addWidget(connection_group)
        
        content_layout.addLayout(left_column, 1)
        
        # Right column - Status and Logs
        right_column = QVBoxLayout()
        
        # Available Terminals Group
        terminals_group = QGroupBox("Available Terminals")
        terminals_layout = QVBoxLayout(terminals_group)
        
        self.terminals_list = QListWidget()
        self.terminals_list.setMaximumHeight(150)
        self.terminals_list.itemDoubleClicked.connect(self.select_terminal)
        terminals_layout.addWidget(self.terminals_list)
        
        right_column.addWidget(terminals_group)
        
        # Connection Status Group
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        # Status indicators
        self.connection_status = self.create_status_indicator("MT5 Connection", "Disconnected", False)
        self.ea_status = self.create_status_indicator("Expert Advisor", "Not Running", False)
        self.sync_status = self.create_status_indicator("EA Sync", "Not Synced", False)
        
        status_layout.addWidget(self.connection_status)
        status_layout.addWidget(self.ea_status)
        status_layout.addWidget(self.sync_status)
        
        right_column.addWidget(status_group)
        
        # EA Logs Group
        logs_group = QGroupBox("EA Communication Log")
        logs_layout = QVBoxLayout(logs_group)
        
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setMaximumHeight(150)
        logs_layout.addWidget(self.logs_display)
        
        clear_logs_button = QPushButton("Clear Logs")
        clear_logs_button.clicked.connect(self.clear_logs)
        logs_layout.addWidget(clear_logs_button)
        
        right_column.addWidget(logs_group)
        
        content_layout.addLayout(right_column, 1)
        
        layout.addLayout(content_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def create_status_indicator(self, name, status, is_active):
        """Create a status indicator widget"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {'#27ae60' if is_active else '#e74c3c'}; font-size: 16px;")
        layout.addWidget(dot)
        
        # Name label
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Status label
        status_label = QLabel(status)
        status_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(status_label)
        
        # Store references for updates
        widget.dot = dot
        widget.status_label = status_label
        
        return widget
    
    def setup_timers(self):
        """Setup update timers"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(10000)  # Update every 10 seconds
    
    def load_settings(self):
        """Load settings from configuration"""
        self.terminal_path_edit.setText(settings.mt5.terminal_path or "")
        self.login_edit.setText(settings.mt5.login or "")
        self.password_edit.setText(settings.mt5.password or "")
        self.server_edit.setText(settings.mt5.server or "")
        self.expert_path_edit.setText(settings.mt5.expert_path or "")
        self.magic_spinbox.setValue(settings.mt5.magic_number)
        self.auto_restart_checkbox.setChecked(settings.mt5.auto_restart)
        self.heartbeat_spinbox.setValue(settings.mt5.heartbeat_interval)
    
    def save_settings(self):
        """Save current settings"""
        settings.mt5.terminal_path = self.terminal_path_edit.text().strip()
        settings.mt5.login = self.login_edit.text().strip()
        settings.mt5.password = self.password_edit.text().strip()
        settings.mt5.server = self.server_edit.text().strip()
        settings.mt5.expert_path = self.expert_path_edit.text().strip()
        settings.mt5.magic_number = self.magic_spinbox.value()
        settings.mt5.auto_restart = self.auto_restart_checkbox.isChecked()
        settings.mt5.heartbeat_interval = self.heartbeat_spinbox.value()
        
        settings.save_config()
    
    def browse_terminal_path(self):
        """Browse for MT5 terminal executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MT5 Terminal",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            self.terminal_path_edit.setText(file_path)
            self.save_settings()
    
    def browse_ea_path(self):
        """Browse for Expert Advisor file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SignalOS EA",
            "",
            "Expert Advisor Files (*.ex5 *.mq5);;All Files (*)"
        )
        
        if file_path:
            self.expert_path_edit.setText(file_path)
            self.save_settings()
    
    def scan_terminals(self):
        """Scan for available MT5 terminals"""
        self.set_operation_state(True, "Scanning for terminals...")
        
        self.mt5_worker = MT5Worker("scan_terminals")
        self.mt5_worker.operation_completed.connect(self.on_operation_completed)
        self.mt5_worker.terminals_found.connect(self.on_terminals_found)
        self.mt5_worker.start()
    
    def test_connection(self):
        """Test MT5 connection"""
        if not self.validate_settings():
            return
        
        self.set_operation_state(True, "Testing connection...")
        
        self.mt5_worker = MT5Worker("test_connection")
        self.mt5_worker.operation_completed.connect(self.on_operation_completed)
        self.mt5_worker.start()
    
    def install_ea(self):
        """Install Expert Advisor"""
        if not self.validate_settings():
            return
        
        self.set_operation_state(True, "Installing EA...")
        
        self.mt5_worker = MT5Worker("install_ea")
        self.mt5_worker.operation_completed.connect(self.on_operation_completed)
        self.mt5_worker.start()
    
    def sync_ea(self):
        """Sync with Expert Advisor"""
        self.set_operation_state(True, "Syncing EA...")
        
        self.mt5_worker = MT5Worker("sync_ea")
        self.mt5_worker.operation_completed.connect(self.on_operation_completed)
        self.mt5_worker.start()
    
    def restart_ea(self):
        """Restart Expert Advisor"""
        reply = QMessageBox.question(
            self,
            "Restart EA",
            "This will restart the Expert Advisor. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Restarting Expert Advisor...")
            # Implement EA restart logic
    
    def validate_settings(self):
        """Validate MT5 settings"""
        if not self.terminal_path_edit.text().strip():
            QMessageBox.warning(self, "Warning", "Please select MT5 terminal path")
            return False
        
        if not all([
            self.login_edit.text().strip(),
            self.password_edit.text().strip(),
            self.server_edit.text().strip()
        ]):
            QMessageBox.warning(self, "Warning", "Please fill in all login credentials")
            return False
        
        return True
    
    def select_terminal(self, item):
        """Select a terminal from the list"""
        terminal_path = item.text()
        self.terminal_path_edit.setText(terminal_path)
        self.save_settings()
    
    def on_terminals_found(self, terminals):
        """Handle terminals discovery"""
        self.terminals_list.clear()
        
        for terminal in terminals:
            item = QListWidgetItem(terminal)
            self.terminals_list.addItem(item)
    
    def on_operation_completed(self, success, message):
        """Handle operation completion"""
        self.set_operation_state(False, message)
        
        if success:
            self.status_label.setStyleSheet("color: green;")
            self.update_status()
            self.add_log_entry(message)
        else:
            self.status_label.setStyleSheet("color: red;")
            self.add_log_entry(f"Error: {message}")
    
    def set_operation_state(self, is_running, message=""):
        """Set UI state during operations"""
        self.test_connection_button.setEnabled(not is_running)
        self.install_ea_button.setEnabled(not is_running)
        self.sync_ea_button.setEnabled(not is_running)
        self.restart_ea_button.setEnabled(not is_running)
        self.scan_button.setEnabled(not is_running)
        self.progress_bar.setVisible(is_running)
        
        if is_running:
            self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.status_label.setText(message)
    
    def update_status(self):
        """Update connection status indicators"""
        # These would check actual status
        self.update_status_indicator(self.connection_status, "Connected", True)
        self.update_status_indicator(self.ea_status, "Running", True)
        self.update_status_indicator(self.sync_status, "Synced", True)
    
    def update_status_indicator(self, widget, status, is_active):
        """Update a status indicator"""
        widget.dot.setStyleSheet(f"color: {'#27ae60' if is_active else '#e74c3c'}; font-size: 16px;")
        widget.status_label.setText(status)
    
    def add_log_entry(self, message):
        """Add entry to logs"""
        timestamp = "12:34:56"  # Would use actual timestamp
        log_entry = f"[{timestamp}] {message}"
        self.logs_display.append(log_entry)
    
    def clear_logs(self):
        """Clear the logs display"""
        self.logs_display.clear()
    
    def update_magic_number(self, value):
        """Update magic number"""
        settings.mt5.magic_number = value
        settings.save_config()
    
    def update_auto_restart(self, state):
        """Update auto restart setting"""
        settings.mt5.auto_restart = state == Qt.Checked
        settings.save_config()
    
    def update_heartbeat(self, value):
        """Update heartbeat interval"""
        settings.mt5.heartbeat_interval = value
        settings.save_config()
    
    def refresh_data(self):
        """Refresh widget data"""
        self.load_settings()
        self.update_status()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.mt5_worker and self.mt5_worker.isRunning():
            self.mt5_worker.terminate()
            self.mt5_worker.wait()
        
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
