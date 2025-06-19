"""
Main dashboard widget
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QFrame, QGroupBox,
                               QListWidget, QListWidgetItem, QProgressBar,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide2.QtCore import Qt, QTimer, Signal
from PySide2.QtGui import QFont, QPalette

from config.settings import settings
from core.logger import get_logger

logger = get_logger(__name__)

class StatsCard(QFrame):
    """Statistics card widget"""
    
    def __init__(self, title, value, color="#3498db"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #7f8c8d; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        layout.setSpacing(5)
    
    def update_value(self, value):
        """Update the card value"""
        self.value_label.setText(str(value))

class DashboardWidget(QWidget):
    """Main dashboard widget"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timers()
        self.load_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Statistics cards
        stats_layout = QHBoxLayout()
        
        self.signals_card = StatsCard("Signals Today", "0", "#27ae60")
        self.trades_card = StatsCard("Trades Executed", "0", "#3498db")
        self.profit_card = StatsCard("Profit (Pips)", "+0", "#e74c3c")
        self.success_card = StatsCard("Success Rate", "0%", "#f39c12")
        
        stats_layout.addWidget(self.signals_card)
        stats_layout.addWidget(self.trades_card)
        stats_layout.addWidget(self.profit_card)
        stats_layout.addWidget(self.success_card)
        
        layout.addLayout(stats_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left column
        left_column = QVBoxLayout()
        
        # Recent signals group
        signals_group = QGroupBox("Recent Signals")
        signals_layout = QVBoxLayout(signals_group)
        
        self.signals_list = QListWidget()
        self.signals_list.setMaximumHeight(200)
        signals_layout.addWidget(self.signals_list)
        
        left_column.addWidget(signals_group)
        
        # Active trades group
        trades_group = QGroupBox("Active Trades")
        trades_layout = QVBoxLayout(trades_group)
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(5)
        self.trades_table.setHorizontalHeaderLabels(["Pair", "Type", "Size", "Entry", "P/L"])
        self.trades_table.horizontalHeader().setStretchLastSection(True)
        self.trades_table.setMaximumHeight(200)
        trades_layout.addWidget(self.trades_table)
        
        left_column.addWidget(trades_group)
        
        content_layout.addLayout(left_column, 2)
        
        # Right column
        right_column = QVBoxLayout()
        
        # System status group
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        
        # Status indicators
        self.telegram_status = self.create_status_indicator("Telegram", "Disconnected", False)
        self.parser_status = self.create_status_indicator("Parser", "Stopped", False)
        self.mt5_status = self.create_status_indicator("MT5", "Disconnected", False)
        self.ea_status = self.create_status_indicator("Expert Advisor", "Not Running", False)
        
        status_layout.addWidget(self.telegram_status)
        status_layout.addWidget(self.parser_status)
        status_layout.addWidget(self.mt5_status)
        status_layout.addWidget(self.ea_status)
        
        right_column.addWidget(status_group)
        
        # Quick actions group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.start_button = QPushButton("Start All Services")
        self.start_button.clicked.connect(self.start_all_services)
        actions_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop All Services")
        self.stop_button.clicked.connect(self.stop_all_services)
        actions_layout.addWidget(self.stop_button)
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connections)
        actions_layout.addWidget(self.test_button)
        
        right_column.addWidget(actions_group)
        
        content_layout.addLayout(right_column, 1)
        
        layout.addLayout(content_layout)
    
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
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def load_data(self):
        """Load initial dashboard data"""
        # Load recent signals
        self.load_recent_signals()
        
        # Load active trades
        self.load_active_trades()
        
        # Update statistics
        self.update_statistics()
        
        # Update system status
        self.update_system_status()
    
    def load_recent_signals(self):
        """Load recent signals"""
        self.signals_list.clear()
        
        # Placeholder data - replace with actual signal data
        recent_signals = [
            "EURUSD BUY @ 1.0850 - 10 minutes ago",
            "GBPUSD SELL @ 1.2450 - 25 minutes ago",
            "USDJPY BUY @ 148.50 - 1 hour ago"
        ]
        
        for signal in recent_signals:
            item = QListWidgetItem(signal)
            self.signals_list.addItem(item)
    
    def load_active_trades(self):
        """Load active trades"""
        self.trades_table.setRowCount(0)
        
        # Placeholder data - replace with actual trade data
        active_trades = [
            ["EURUSD", "BUY", "0.1", "1.0850", "+15"],
            ["GBPUSD", "SELL", "0.1", "1.2450", "-8"],
        ]
        
        for i, trade in enumerate(active_trades):
            self.trades_table.insertRow(i)
            for j, value in enumerate(trade):
                item = QTableWidgetItem(str(value))
                if j == 4:  # P/L column
                    if value.startswith('+'):
                        item.setForeground(Qt.green)
                    elif value.startswith('-'):
                        item.setForeground(Qt.red)
                self.trades_table.setItem(i, j, item)
    
    def update_statistics(self):
        """Update statistics cards"""
        # These would be calculated from actual data
        self.signals_card.update_value("12")
        self.trades_card.update_value("8")
        self.profit_card.update_value("+45")
        self.success_card.update_value("75%")
    
    def update_system_status(self):
        """Update system status indicators"""
        # These would check actual service status
        self.update_status_indicator(self.telegram_status, "Connected", True)
        self.update_status_indicator(self.parser_status, "Running", True)
        self.update_status_indicator(self.mt5_status, "Connected", True)
        self.update_status_indicator(self.ea_status, "Running", True)
    
    def update_status_indicator(self, widget, status, is_active):
        """Update a status indicator"""
        widget.dot.setStyleSheet(f"color: {'#27ae60' if is_active else '#e74c3c'}; font-size: 16px;")
        widget.status_label.setText(status)
    
    def update_dashboard(self):
        """Periodic dashboard update"""
        self.update_statistics()
        self.update_system_status()
    
    def start_all_services(self):
        """Start all services"""
        logger.info("Starting all services...")
        # Implement service startup logic
        
    def stop_all_services(self):
        """Stop all services"""
        logger.info("Stopping all services...")
        # Implement service shutdown logic
        
    def test_connections(self):
        """Test all connections"""
        logger.info("Testing connections...")
        # Implement connection testing logic
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        self.load_data()
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
