"""
User login dialog
"""

from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QLabel, QTabWidget,
                               QWidget, QTextEdit, QCheckBox, QProgressBar,
                               QMessageBox)
from PySide2.QtCore import Qt, QThread, Signal
from PySide2.QtGui import QFont, QPixmap

from config.auth import auth_manager
from core.logger import get_logger

logger = get_logger(__name__)

class LoginWorker(QThread):
    """Worker thread for login operations"""
    
    login_completed = Signal(bool, str)
    
    def __init__(self, username, password, token=None):
        super().__init__()
        self.username = username
        self.password = password
        self.token = token
    
    def run(self):
        """Perform login operation"""
        try:
            if self.token:
                success, message = auth_manager.login_with_token(self.token)
            else:
                success, message = auth_manager.login(self.username, self.password)
            
            self.login_completed.emit(success, message)
        except Exception as e:
            self.login_completed.emit(False, str(e))

class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SignalOS Login")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # Remove window controls
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # Worker thread
        self.login_worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title label
        title_label = QLabel("SignalOS")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Forex Signal Automation Platform")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(subtitle_label)
        
        # Tab widget for different login methods
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Username/Password tab
        self.create_credentials_tab()
        
        # Token tab
        self.create_token_tab()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.perform_login)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
    def create_credentials_tab(self):
        """Create username/password login tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Username field
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        layout.addRow("Username:", self.username_edit)
        
        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        layout.addRow("Password:", self.password_edit)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        layout.addRow("", self.remember_checkbox)
        
        self.tab_widget.addTab(widget, "Credentials")
    
    def create_token_tab(self):
        """Create token login tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel("Paste your authentication token below:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Token field
        self.token_edit = QTextEdit()
        self.token_edit.setPlaceholderText("Paste your JWT token here...")
        self.token_edit.setMaximumHeight(100)
        layout.addWidget(self.token_edit)
        
        self.tab_widget.addTab(widget, "Token")
    
    def perform_login(self):
        """Perform the login operation"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Credentials tab
            username = self.username_edit.text().strip()
            password = self.password_edit.text().strip()
            
            if not username or not password:
                self.show_error("Please enter both username and password")
                return
                
            self.start_login(username, password)
            
        elif current_tab == 1:  # Token tab
            token = self.token_edit.toPlainText().strip()
            
            if not token:
                self.show_error("Please enter a valid token")
                return
                
            self.start_token_login(token)
    
    def start_login(self, username, password):
        """Start login with credentials"""
        self.set_login_state(True)
        
        self.login_worker = LoginWorker(username, password)
        self.login_worker.login_completed.connect(self.on_login_completed)
        self.login_worker.start()
    
    def start_token_login(self, token):
        """Start login with token"""
        self.set_login_state(True)
        
        self.login_worker = LoginWorker(None, None, token)
        self.login_worker.login_completed.connect(self.on_login_completed)
        self.login_worker.start()
    
    def on_login_completed(self, success, message):
        """Handle login completion"""
        self.set_login_state(False)
        
        if success:
            self.accept()
        else:
            self.show_error(message)
    
    def set_login_state(self, logging_in):
        """Set UI state during login"""
        self.login_button.setEnabled(not logging_in)
        self.cancel_button.setEnabled(not logging_in)
        self.tab_widget.setEnabled(not logging_in)
        self.progress_bar.setVisible(logging_in)
        
        if logging_in:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_label.setText("Logging in...")
            self.status_label.setStyleSheet("color: blue; font-size: 12px;")
        else:
            self.progress_bar.setRange(0, 100)
            self.status_label.setText("")
    
    def show_error(self, message):
        """Show error message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: red; font-size: 12px;")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.perform_login()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait()
        event.accept()
