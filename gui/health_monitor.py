"""
System health monitoring widget
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QGroupBox, QProgressBar, QListWidget,
                               QListWidgetItem, QPushButton, QFrame)
from PySide2.QtCore import Qt, QTimer, Signal
from PySide2.QtGui import QFont, QPalette

from core.health_monitor import HealthMonitor
from core.logger import get_logger

logger = get_logger(__name__)

class HealthCard(QFrame):
    """Health status card widget"""
    
    def __init__(self, title, status="Unknown", color="#95a5a6"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: #7f8c8d; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Status
        self.status_label = QLabel(status)
        self.status_label.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Store color for updates
        self.color = color
    
    def update_status(self, status, color=None):
        """Update the card status"""
        if color:
            self.color = color
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"font-size: 14px; color: {self.color}; font-weight: bold;")

class HealthMonitorWidget(QWidget):
    """Widget for monitoring system health"""
    
    status_updated = Signal(str, str)  # component, status
    
    def __init__(self):
        super().__init__()
        self.health_monitor = HealthMonitor()
        self.init_ui()
        self.setup_timers()
        self.load_initial_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("System Health")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Health Status Cards
        status_group = QGroupBox("Component Status")
        status_layout = QVBoxLayout(status_group)
        
        self.telegram_card = HealthCard("Telegram", "Disconnected", "#e74c3c")
        self.parser_card = HealthCard("Parser", "Stopped", "#e74c3c")
        self.mt5_card = HealthCard("MT5", "Disconnected", "#e74c3c")
        self.ea_card = HealthCard("Expert Advisor", "Not Running", "#e74c3c")
        
        status_layout.addWidget(self.telegram_card)
        status_layout.addWidget(self.parser_card)
        status_layout.addWidget(self.mt5_card)
        status_layout.addWidget(self.ea_card)
        
        layout.addWidget(status_group)
        
        # System Performance Group
        performance_group = QGroupBox("Performance")
        performance_layout = QVBoxLayout(performance_group)
        
        # CPU Usage
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU:"))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximumHeight(20)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setMinimumWidth(40)
        cpu_layout.addWidget(self.cpu_bar)
        cpu_layout.addWidget(self.cpu_label)
        performance_layout.addLayout(cpu_layout)
        
        # Memory Usage
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory:"))
        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximumHeight(20)
        self.memory_label = QLabel("0 MB")
        self.memory_label.setMinimumWidth(40)
        memory_layout.addWidget(self.memory_bar)
        memory_layout.addWidget(self.memory_label)
        performance_layout.addLayout(memory_layout)
        
        layout.addWidget(performance_group)
        
        # Signal Queue Group
        queue_group = QGroupBox("Signal Queue")
        queue_layout = QVBoxLayout(queue_group)
        
        # Queue stats
        queue_stats_layout = QHBoxLayout()
        self.queue_pending_label = QLabel("Pending: 0")
        self.queue_processed_label = QLabel("Processed: 0")
        queue_stats_layout.addWidget(self.queue_pending_label)
        queue_stats_layout.addStretch()
        queue_stats_layout.addWidget(self.queue_processed_label)
        queue_layout.addLayout(queue_stats_layout)
        
        # Recent signals
        self.recent_signals_list = QListWidget()
        self.recent_signals_list.setMaximumHeight(100)
        queue_layout.addWidget(self.recent_signals_list)
        
        layout.addWidget(queue_group)
        
        # Error Log Group
        errors_group = QGroupBox("Recent Errors")
        errors_layout = QVBoxLayout(errors_group)
        
        self.errors_list = QListWidget()
        self.errors_list.setMaximumHeight(100)
        errors_layout.addWidget(self.errors_list)
        
        # Clear errors button
        clear_errors_button = QPushButton("Clear Errors")
        clear_errors_button.clicked.connect(self.clear_errors)
        errors_layout.addWidget(clear_errors_button)
        
        layout.addWidget(errors_group)
        
        # Recovery Actions Group
        recovery_group = QGroupBox("Recovery Actions")
        recovery_layout = QVBoxLayout(recovery_group)
        
        self.restart_all_button = QPushButton("Restart All Services")
        self.restart_all_button.clicked.connect(self.restart_all_services)
        recovery_layout.addWidget(self.restart_all_button)
        
        self.reset_connections_button = QPushButton("Reset Connections")
        self.reset_connections_button.clicked.connect(self.reset_connections)
        recovery_layout.addWidget(self.reset_connections_button)
        
        layout.addWidget(recovery_group)
        
        layout.addStretch()
    
    def setup_timers(self):
        """Setup update timers"""
        # Fast update timer for real-time data
        self.fast_timer = QTimer()
        self.fast_timer.timeout.connect(self.update_fast_data)
        self.fast_timer.start(2000)  # Update every 2 seconds
        
        # Slow update timer for less critical data
        self.slow_timer = QTimer()
        self.slow_timer.timeout.connect(self.update_slow_data)
        self.slow_timer.start(10000)  # Update every 10 seconds
    
    def load_initial_data(self):
        """Load initial health data"""
        self.update_component_status()
        self.update_performance_data()
        self.update_signal_queue()
        self.update_error_log()
    
    def update_fast_data(self):
        """Update fast-changing data"""
        self.update_component_status()
        self.update_performance_data()
        self.update_signal_queue()
    
    def update_slow_data(self):
        """Update slow-changing data"""
        self.update_error_log()
    
    def update_component_status(self):
        """Update component status cards"""
        try:
            status_data = self.health_monitor.get_component_status()
            
            # Update Telegram status
            telegram_status = status_data.get('telegram', {})
            if telegram_status.get('connected', False):
                self.telegram_card.update_status("Connected", "#27ae60")
            else:
                self.telegram_card.update_status("Disconnected", "#e74c3c")
            
            # Update Parser status
            parser_status = status_data.get('parser', {})
            if parser_status.get('running', False):
                self.parser_card.update_status("Running", "#27ae60")
            else:
                self.parser_card.update_status("Stopped", "#e74c3c")
            
            # Update MT5 status
            mt5_status = status_data.get('mt5', {})
            if mt5_status.get('connected', False):
                self.mt5_card.update_status("Connected", "#27ae60")
            else:
                self.mt5_card.update_status("Disconnected", "#e74c3c")
            
            # Update EA status
            ea_status = status_data.get('ea', {})
            if ea_status.get('running', False):
                self.ea_card.update_status("Running", "#27ae60")
            else:
                self.ea_card.update_status("Not Running", "#e74c3c")
                
        except Exception as e:
            logger.error(f"Error updating component status: {e}")
    
    def update_performance_data(self):
        """Update performance metrics"""
        try:
            perf_data = self.health_monitor.get_performance_data()
            
            # Update CPU usage
            cpu_percent = perf_data.get('cpu_percent', 0)
            self.cpu_bar.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            # Color code CPU bar
            if cpu_percent > 80:
                self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            elif cpu_percent > 60:
                self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            
            # Update Memory usage
            memory_mb = perf_data.get('memory_mb', 0)
            memory_percent = perf_data.get('memory_percent', 0)
            self.memory_bar.setValue(int(memory_percent))
            self.memory_label.setText(f"{memory_mb:.0f} MB")
            
            # Color code memory bar
            if memory_percent > 80:
                self.memory_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            elif memory_percent > 60:
                self.memory_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.memory_bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
                
        except Exception as e:
            logger.error(f"Error updating performance data: {e}")
    
    def update_signal_queue(self):
        """Update signal queue information"""
        try:
            queue_data = self.health_monitor.get_queue_status()
            
            # Update queue stats
            pending = queue_data.get('pending', 0)
            processed = queue_data.get('processed', 0)
            
            self.queue_pending_label.setText(f"Pending: {pending}")
            self.queue_processed_label.setText(f"Processed: {processed}")
            
            # Update recent signals list
            recent_signals = queue_data.get('recent_signals', [])
            
            # Clear and repopulate recent signals
            self.recent_signals_list.clear()
            for signal in recent_signals[-5:]:  # Show last 5 signals
                timestamp = signal.get('timestamp', '00:00:00')
                pair = signal.get('pair', 'Unknown')
                action = signal.get('action', 'Unknown')
                
                item_text = f"{timestamp} - {pair} {action}"
                item = QListWidgetItem(item_text)
                self.recent_signals_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error updating signal queue: {e}")
    
    def update_error_log(self):
        """Update error log"""
        try:
            errors = self.health_monitor.get_recent_errors()
            
            # Clear and repopulate errors
            self.errors_list.clear()
            for error in errors[-10:]:  # Show last 10 errors
                timestamp = error.get('timestamp', '00:00:00')
                component = error.get('component', 'System')
                message = error.get('message', 'Unknown error')
                
                item_text = f"{timestamp} [{component}] {message}"
                item = QListWidgetItem(item_text)
                item.setForeground(Qt.red)
                self.errors_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error updating error log: {e}")
    
    def clear_errors(self):
        """Clear the error log"""
        try:
            self.health_monitor.clear_errors()
            self.errors_list.clear()
        except Exception as e:
            logger.error(f"Error clearing errors: {e}")
    
    def restart_all_services(self):
        """Restart all services"""
        try:
            logger.info("Restarting all services...")
            self.health_monitor.restart_all_services()
            
            # Update status after restart
            QTimer.singleShot(3000, self.update_component_status)
            
        except Exception as e:
            logger.error(f"Error restarting services: {e}")
    
    def reset_connections(self):
        """Reset all connections"""
        try:
            logger.info("Resetting all connections...")
            self.health_monitor.reset_connections()
            
            # Update status after reset
            QTimer.singleShot(2000, self.update_component_status)
            
        except Exception as e:
            logger.error(f"Error resetting connections: {e}")
    
    def add_error(self, component, message):
        """Add an error to the display"""
        timestamp = "12:34:56"  # Would use actual timestamp
        item_text = f"{timestamp} [{component}] {message}"
        item = QListWidgetItem(item_text)
        item.setForeground(Qt.red)
        
        self.errors_list.insertItem(0, item)
        
        # Keep only last 10 errors
        while self.errors_list.count() > 10:
            self.errors_list.takeItem(self.errors_list.count() - 1)
    
    def refresh_data(self):
        """Refresh all health data"""
        self.load_initial_data()
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'fast_timer'):
            self.fast_timer.stop()
        
        if hasattr(self, 'slow_timer'):
            self.slow_timer.stop()
        
        if self.health_monitor:
            self.health_monitor.cleanup()
