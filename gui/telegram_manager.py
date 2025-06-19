"""
Telegram manager widget for handling Telegram integration
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QListWidget, QGroupBox,
                               QLabel, QTextEdit, QCheckBox, QSpinBox,
                               QMessageBox, QProgressBar, QListWidgetItem,
                               QInputDialog, QMenu)
from PySide2.QtCore import Qt, QThread, Signal, QTimer
from PySide2.QtGui import QFont

from config.settings import settings
from core.telegram_listener import TelegramListener
from core.logger import get_logger

logger = get_logger(__name__)

class TelegramWorker(QThread):
    """Worker thread for Telegram operations"""
    
    operation_completed = Signal(bool, str)
    session_created = Signal(str)
    
    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        """Execute the telegram operation"""
        try:
            if self.operation == "create_session":
                self.create_session()
            elif self.operation == "test_connection":
                self.test_connection()
            elif self.operation == "discover_channels":
                self.discover_channels()
        except Exception as e:
            self.operation_completed.emit(False, str(e))
    
    def create_session(self):
        """Create a new Telegram session"""
        try:
            listener = TelegramListener()
            success = listener.create_session(
                self.kwargs.get('phone'),
                self.kwargs.get('api_id'),
                self.kwargs.get('api_hash')
            )
            
            if success:
                self.operation_completed.emit(True, "Session created successfully")
            else:
                self.operation_completed.emit(False, "Failed to create session")
        except Exception as e:
            self.operation_completed.emit(False, f"Session creation error: {str(e)}")
    
    def test_connection(self):
        """Test Telegram connection"""
        try:
            listener = TelegramListener()
            if listener.test_connection():
                self.operation_completed.emit(True, "Connection test successful")
            else:
                self.operation_completed.emit(False, "Connection test failed")
        except Exception as e:
            self.operation_completed.emit(False, f"Connection error: {str(e)}")
    
    def discover_channels(self):
        """Discover available channels"""
        try:
            listener = TelegramListener()
            channels = listener.discover_channels()
            if channels:
                self.operation_completed.emit(True, f"Found {len(channels)} channels")
            else:
                self.operation_completed.emit(False, "No channels found")
        except Exception as e:
            self.operation_completed.emit(False, f"Discovery error: {str(e)}")

class TelegramManagerWidget(QWidget):
    """Widget for managing Telegram configuration and connections"""
    
    def __init__(self):
        super().__init__()
        self.telegram_worker = None
        self.telegram_listener = None
        self.init_ui()
        self.load_settings()
        self.setup_timers()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Telegram Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Main content in horizontal layout
        content_layout = QHBoxLayout()
        
        # Left column - Configuration
        left_column = QVBoxLayout()
        
        # API Configuration Group
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout(api_group)
        
        self.api_id_edit = QLineEdit()
        self.api_id_edit.setPlaceholderText("Enter Telegram API ID")
        api_layout.addRow("API ID:", self.api_id_edit)
        
        self.api_hash_edit = QLineEdit()
        self.api_hash_edit.setPlaceholderText("Enter Telegram API Hash")
        api_layout.addRow("API Hash:", self.api_hash_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+1234567890")
        api_layout.addRow("Phone Number:", self.phone_edit)
        
        left_column.addWidget(api_group)
        
        # Session Management Group
        session_group = QGroupBox("Session Management")
        session_layout = QVBoxLayout(session_group)
        
        session_buttons_layout = QHBoxLayout()
        
        self.create_session_button = QPushButton("Create Session")
        self.create_session_button.clicked.connect(self.create_session)
        session_buttons_layout.addWidget(self.create_session_button)
        
        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_connection)
        session_buttons_layout.addWidget(self.test_connection_button)
        
        session_layout.addLayout(session_buttons_layout)
        
        # Connection status
        self.connection_status = QLabel("Status: Not Connected")
        self.connection_status.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        session_layout.addWidget(self.connection_status)
        
        left_column.addWidget(session_group)
        
        # Channel Settings Group
        channel_group = QGroupBox("Channel Settings")
        channel_layout = QVBoxLayout(channel_group)
        
        # Auto-join checkbox
        self.auto_join_checkbox = QCheckBox("Auto-join discovered channels")
        self.auto_join_checkbox.setChecked(settings.telegram.auto_join)
        self.auto_join_checkbox.stateChanged.connect(self.update_auto_join)
        channel_layout.addWidget(self.auto_join_checkbox)
        
        # Discover channels button
        self.discover_button = QPushButton("Discover Channels")
        self.discover_button.clicked.connect(self.discover_channels)
        channel_layout.addWidget(self.discover_button)
        
        left_column.addWidget(channel_group)
        
        content_layout.addLayout(left_column, 1)
        
        # Right column - Channels List
        right_column = QVBoxLayout()
        
        # Monitored Channels Group
        channels_group = QGroupBox("Monitored Channels")
        channels_layout = QVBoxLayout(channels_group)
        
        # Channels list
        self.channels_list = QListWidget()
        self.channels_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.channels_list.customContextMenuRequested.connect(self.show_channel_context_menu)
        channels_layout.addWidget(self.channels_list)
        
        # Channel management buttons
        channel_buttons_layout = QHBoxLayout()
        
        self.add_channel_button = QPushButton("Add Channel")
        self.add_channel_button.clicked.connect(self.add_channel)
        channel_buttons_layout.addWidget(self.add_channel_button)
        
        self.remove_channel_button = QPushButton("Remove Channel")
        self.remove_channel_button.clicked.connect(self.remove_channel)
        channel_buttons_layout.addWidget(self.remove_channel_button)
        
        channels_layout.addLayout(channel_buttons_layout)
        
        right_column.addWidget(channels_group)
        
        # Message Log Group
        log_group = QGroupBox("Recent Messages")
        log_layout = QVBoxLayout(log_group)
        
        self.message_log = QTextEdit()
        self.message_log.setMaximumHeight(150)
        self.message_log.setReadOnly(True)
        log_layout.addWidget(self.message_log)
        
        right_column.addWidget(log_group)
        
        content_layout.addLayout(right_column, 1)
        
        layout.addLayout(content_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def setup_timers(self):
        """Setup update timers"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(10000)  # Update every 10 seconds
    
    def load_settings(self):
        """Load settings from configuration"""
        self.api_id_edit.setText(settings.telegram.api_id or "")
        self.api_hash_edit.setText(settings.telegram.api_hash or "")
        self.phone_edit.setText(settings.telegram.phone_number or "")
        self.auto_join_checkbox.setChecked(settings.telegram.auto_join)
        
        # Load channels
        self.channels_list.clear()
        for channel in settings.telegram.channels:
            item = QListWidgetItem(channel)
            self.channels_list.addItem(item)
    
    def save_settings(self):
        """Save current settings"""
        settings.telegram.api_id = self.api_id_edit.text().strip()
        settings.telegram.api_hash = self.api_hash_edit.text().strip()
        settings.telegram.phone_number = self.phone_edit.text().strip()
        settings.telegram.auto_join = self.auto_join_checkbox.isChecked()
        
        # Save channels
        settings.telegram.channels = []
        for i in range(self.channels_list.count()):
            item = self.channels_list.item(i)
            settings.telegram.channels.append(item.text())
        
        settings.save_config()
    
    def create_session(self):
        """Create a new Telegram session"""
        api_id = self.api_id_edit.text().strip()
        api_hash = self.api_hash_edit.text().strip()
        phone = self.phone_edit.text().strip()
        
        if not all([api_id, api_hash, phone]):
            QMessageBox.warning(self, "Warning", "Please fill in all required fields")
            return
        
        self.set_operation_state(True, "Creating session...")
        
        self.telegram_worker = TelegramWorker(
            "create_session",
            api_id=api_id,
            api_hash=api_hash,
            phone=phone
        )
        self.telegram_worker.operation_completed.connect(self.on_operation_completed)
        self.telegram_worker.start()
    
    def test_connection(self):
        """Test Telegram connection"""
        self.set_operation_state(True, "Testing connection...")
        
        self.telegram_worker = TelegramWorker("test_connection")
        self.telegram_worker.operation_completed.connect(self.on_operation_completed)
        self.telegram_worker.start()
    
    def discover_channels(self):
        """Discover available channels"""
        self.set_operation_state(True, "Discovering channels...")
        
        self.telegram_worker = TelegramWorker("discover_channels")
        self.telegram_worker.operation_completed.connect(self.on_operation_completed)
        self.telegram_worker.start()
    
    def add_channel(self):
        """Add a new channel to monitor"""
        channel, ok = QInputDialog.getText(
            self, 
            "Add Channel",
            "Enter channel username or ID:"
        )
        
        if ok and channel.strip():
            channel = channel.strip()
            if not channel.startswith('@'):
                channel = '@' + channel
            
            # Check if channel already exists
            for i in range(self.channels_list.count()):
                if self.channels_list.item(i).text() == channel:
                    QMessageBox.warning(self, "Warning", "Channel already exists")
                    return
            
            item = QListWidgetItem(channel)
            self.channels_list.addItem(item)
            self.save_settings()
    
    def remove_channel(self):
        """Remove selected channel"""
        current_item = self.channels_list.currentItem()
        if current_item:
            reply = QMessageBox.question(
                self,
                "Remove Channel",
                f"Remove channel '{current_item.text()}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                row = self.channels_list.row(current_item)
                self.channels_list.takeItem(row)
                self.save_settings()
    
    def show_channel_context_menu(self, position):
        """Show context menu for channels list"""
        item = self.channels_list.itemAt(position)
        if item:
            menu = QMenu(self)
            
            join_action = menu.addAction("Join Channel")
            leave_action = menu.addAction("Leave Channel")
            menu.addSeparator()
            remove_action = menu.addAction("Remove from List")
            
            action = menu.exec_(self.channels_list.mapToGlobal(position))
            
            if action == join_action:
                self.join_channel(item.text())
            elif action == leave_action:
                self.leave_channel(item.text())
            elif action == remove_action:
                self.remove_channel()
    
    def join_channel(self, channel):
        """Join a specific channel"""
        logger.info(f"Joining channel: {channel}")
        # Implement channel joining logic
        
    def leave_channel(self, channel):
        """Leave a specific channel"""
        logger.info(f"Leaving channel: {channel}")
        # Implement channel leaving logic
    
    def update_auto_join(self, state):
        """Update auto-join setting"""
        settings.telegram.auto_join = state == Qt.Checked
        settings.save_config()
    
    def on_operation_completed(self, success, message):
        """Handle operation completion"""
        self.set_operation_state(False, message)
        
        if success:
            self.status_label.setStyleSheet("color: green;")
            self.update_connection_status()
        else:
            self.status_label.setStyleSheet("color: red;")
    
    def set_operation_state(self, is_running, message=""):
        """Set UI state during operations"""
        self.create_session_button.setEnabled(not is_running)
        self.test_connection_button.setEnabled(not is_running)
        self.discover_button.setEnabled(not is_running)
        self.progress_bar.setVisible(is_running)
        
        if is_running:
            self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.status_label.setText(message)
    
    def update_connection_status(self):
        """Update connection status display"""
        try:
            if self.telegram_listener:
                if self.telegram_listener.is_connected():
                    self.connection_status.setText("Status: Connected")
                    self.connection_status.setStyleSheet(
                        "padding: 10px; background-color: #d4edda; border-radius: 4px; color: #155724;"
                    )
                else:
                    self.connection_status.setText("Status: Disconnected")
                    self.connection_status.setStyleSheet(
                        "padding: 10px; background-color: #f8d7da; border-radius: 4px; color: #721c24;"
                    )
            else:
                self.connection_status.setText("Status: Not Initialized")
                self.connection_status.setStyleSheet(
                    "padding: 10px; background-color: #fff3cd; border-radius: 4px; color: #856404;"
                )
        except Exception as e:
            logger.error(f"Error updating connection status: {e}")
    
    def refresh_data(self):
        """Refresh widget data"""
        self.load_settings()
        self.update_connection_status()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.telegram_worker and self.telegram_worker.isRunning():
            self.telegram_worker.terminate()
            self.telegram_worker.wait()
        
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        if self.telegram_listener:
            self.telegram_listener.stop()
