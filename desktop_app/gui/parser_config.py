"""
Signal parser configuration widget
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QGroupBox, QLabel,
                               QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox,
                               QTextEdit, QSlider, QProgressBar, QListWidget,
                               QListWidgetItem, QMessageBox, QFileDialog)
from PySide2.QtCore import Qt, QThread, Signal, QTimer
from PySide2.QtGui import QFont

from config.settings import settings
from core.signal_parser import SignalParser
from core.logger import get_logger

logger = get_logger(__name__)

class ParserTestWorker(QThread):
    """Worker thread for testing parser"""
    
    test_completed = Signal(bool, str, dict)
    
    def __init__(self, test_text, config):
        super().__init__()
        self.test_text = test_text
        self.config = config
    
    def run(self):
        """Run parser test"""
        try:
            parser = SignalParser()
            result = parser.parse_signal(self.test_text)
            
            if result:
                self.test_completed.emit(True, "Parse successful", result)
            else:
                self.test_completed.emit(False, "Parse failed", {})
        except Exception as e:
            self.test_completed.emit(False, f"Parse error: {str(e)}", {})

class ParserConfigWidget(QWidget):
    """Widget for configuring the signal parser"""
    
    def __init__(self):
        super().__init__()
        self.parser_worker = None
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Signal Parser Configuration")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Main content layout
        content_layout = QHBoxLayout()
        
        # Left column - Configuration
        left_column = QVBoxLayout()
        
        # General Settings Group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)
        
        # Enable parser
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(settings.parser.enabled)
        self.enabled_checkbox.stateChanged.connect(self.update_enabled)
        general_layout.addRow("Enable Parser:", self.enabled_checkbox)
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "en_core_web_sm",
            "en_core_web_md", 
            "en_core_web_lg"
        ])
        self.model_combo.setCurrentText(settings.parser.model_name)
        self.model_combo.currentTextChanged.connect(self.update_model)
        general_layout.addRow("NLP Model:", self.model_combo)
        
        # Confidence threshold
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(50, 95)
        self.confidence_slider.setValue(int(settings.parser.confidence_threshold * 100))
        self.confidence_slider.valueChanged.connect(self.update_confidence)
        
        self.confidence_label = QLabel(f"{settings.parser.confidence_threshold:.2f}")
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_label)
        
        general_layout.addRow("Confidence Threshold:", confidence_layout)
        
        left_column.addWidget(general_group)
        
        # OCR Settings Group
        ocr_group = QGroupBox("OCR Settings")
        ocr_layout = QFormLayout(ocr_group)
        
        # Enable OCR
        self.ocr_checkbox = QCheckBox()
        self.ocr_checkbox.setChecked(settings.parser.ocr_enabled)
        self.ocr_checkbox.stateChanged.connect(self.update_ocr_enabled)
        ocr_layout.addRow("Enable OCR:", self.ocr_checkbox)
        
        left_column.addWidget(ocr_group)
        
        # Execution Settings Group
        execution_group = QGroupBox("Execution Settings")
        execution_layout = QFormLayout(execution_group)
        
        # Fallback rules
        self.fallback_checkbox = QCheckBox()
        self.fallback_checkbox.setChecked(settings.parser.fallback_rules)
        self.fallback_checkbox.stateChanged.connect(self.update_fallback)
        execution_layout.addRow("Use Fallback Rules:", self.fallback_checkbox)
        
        # Buffer pips
        self.buffer_spinbox = QSpinBox()
        self.buffer_spinbox.setRange(0, 20)
        self.buffer_spinbox.setValue(settings.parser.buffer_pips)
        self.buffer_spinbox.valueChanged.connect(self.update_buffer_pips)
        execution_layout.addRow("Buffer Pips:", self.buffer_spinbox)
        
        left_column.addWidget(execution_group)
        
        # Test Section
        test_group = QGroupBox("Parser Testing")
        test_layout = QVBoxLayout(test_group)
        
        # Test input
        test_layout.addWidget(QLabel("Test Signal Text:"))
        self.test_input = QTextEdit()
        self.test_input.setMaximumHeight(100)
        self.test_input.setPlaceholderText("Enter signal text to test parser...")
        test_layout.addWidget(self.test_input)
        
        # Test button
        self.test_button = QPushButton("Test Parser")
        self.test_button.clicked.connect(self.test_parser)
        test_layout.addWidget(self.test_button)
        
        left_column.addWidget(test_group)
        
        content_layout.addLayout(left_column, 1)
        
        # Right column - Results and Logs
        right_column = QVBoxLayout()
        
        # Parse Results Group
        results_group = QGroupBox("Parse Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setMaximumHeight(200)
        results_layout.addWidget(self.results_display)
        
        right_column.addWidget(results_group)
        
        # Recent Parses Group
        recent_group = QGroupBox("Recent Parses")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(150)
        recent_layout.addWidget(self.recent_list)
        
        # Clear button
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.clear_history)
        recent_layout.addWidget(clear_button)
        
        right_column.addWidget(recent_group)
        
        # Parser Stats Group
        stats_group = QGroupBox("Parser Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.total_parsed_label = QLabel("0")
        stats_layout.addRow("Total Parsed:", self.total_parsed_label)
        
        self.success_rate_label = QLabel("0%")
        stats_layout.addRow("Success Rate:", self.success_rate_label)
        
        self.avg_confidence_label = QLabel("0%")
        stats_layout.addRow("Avg Confidence:", self.avg_confidence_label)
        
        right_column.addWidget(stats_group)
        
        content_layout.addLayout(right_column, 1)
        
        layout.addLayout(content_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def load_settings(self):
        """Load settings from configuration"""
        self.enabled_checkbox.setChecked(settings.parser.enabled)
        self.model_combo.setCurrentText(settings.parser.model_name)
        self.confidence_slider.setValue(int(settings.parser.confidence_threshold * 100))
        self.confidence_label.setText(f"{settings.parser.confidence_threshold:.2f}")
        self.ocr_checkbox.setChecked(settings.parser.ocr_enabled)
        self.fallback_checkbox.setChecked(settings.parser.fallback_rules)
        self.buffer_spinbox.setValue(settings.parser.buffer_pips)
        
        # Load some example recent parses
        self.load_recent_parses()
        self.update_statistics()
    
    def save_settings(self):
        """Save current settings"""
        settings.parser.enabled = self.enabled_checkbox.isChecked()
        settings.parser.model_name = self.model_combo.currentText()
        settings.parser.confidence_threshold = self.confidence_slider.value() / 100.0
        settings.parser.ocr_enabled = self.ocr_checkbox.isChecked()
        settings.parser.fallback_rules = self.fallback_checkbox.isChecked()
        settings.parser.buffer_pips = self.buffer_spinbox.value()
        
        settings.save_config()
    
    def update_enabled(self, state):
        """Update parser enabled state"""
        settings.parser.enabled = state == Qt.Checked
        settings.save_config()
    
    def update_model(self, model_name):
        """Update NLP model"""
        settings.parser.model_name = model_name
        settings.save_config()
    
    def update_confidence(self, value):
        """Update confidence threshold"""
        threshold = value / 100.0
        settings.parser.confidence_threshold = threshold
        self.confidence_label.setText(f"{threshold:.2f}")
        settings.save_config()
    
    def update_ocr_enabled(self, state):
        """Update OCR enabled state"""
        settings.parser.ocr_enabled = state == Qt.Checked
        settings.save_config()
    
    def update_fallback(self, state):
        """Update fallback rules state"""
        settings.parser.fallback_rules = state == Qt.Checked
        settings.save_config()
    
    def update_buffer_pips(self, value):
        """Update buffer pips"""
        settings.parser.buffer_pips = value
        settings.save_config()
    
    def test_parser(self):
        """Test the parser with input text"""
        test_text = self.test_input.toPlainText().strip()
        
        if not test_text:
            QMessageBox.warning(self, "Warning", "Please enter test text")
            return
        
        self.set_test_state(True, "Testing parser...")
        
        # Create test configuration
        test_config = {
            'model': self.model_combo.currentText(),
            'confidence': self.confidence_slider.value() / 100.0,
            'ocr_enabled': self.ocr_checkbox.isChecked(),
            'fallback_rules': self.fallback_checkbox.isChecked()
        }
        
        self.parser_worker = ParserTestWorker(test_text, test_config)
        self.parser_worker.test_completed.connect(self.on_test_completed)
        self.parser_worker.start()
    
    def on_test_completed(self, success, message, result):
        """Handle test completion"""
        self.set_test_state(False, message)
        
        if success:
            self.display_parse_result(result)
            self.add_to_recent_parses(self.test_input.toPlainText().strip(), result)
            self.status_label.setStyleSheet("color: green;")
        else:
            self.results_display.setText(f"Parse failed: {message}")
            self.status_label.setStyleSheet("color: red;")
    
    def display_parse_result(self, result):
        """Display parse result"""
        if not result:
            self.results_display.setText("No result")
            return
        
        result_text = "Parse Result:\n\n"
        
        for key, value in result.items():
            result_text += f"{key.title()}: {value}\n"
        
        self.results_display.setText(result_text)
    
    def add_to_recent_parses(self, text, result):
        """Add to recent parses list"""
        timestamp = "12:34:56"  # Would use actual timestamp
        pair = result.get('pair', 'Unknown')
        action = result.get('action', 'Unknown')
        
        item_text = f"{timestamp} - {pair} {action}"
        item = QListWidgetItem(item_text)
        
        self.recent_list.insertItem(0, item)
        
        # Keep only last 20 items
        while self.recent_list.count() > 20:
            self.recent_list.takeItem(self.recent_list.count() - 1)
        
        self.update_statistics()
    
    def load_recent_parses(self):
        """Load recent parses (placeholder data)"""
        self.recent_list.clear()
        
        # Placeholder recent parses
        recent_parses = [
            "12:30:45 - EURUSD BUY",
            "12:25:12 - GBPUSD SELL", 
            "12:20:33 - USDJPY BUY"
        ]
        
        for parse in recent_parses:
            item = QListWidgetItem(parse)
            self.recent_list.addItem(item)
    
    def update_statistics(self):
        """Update parser statistics"""
        # Placeholder statistics
        self.total_parsed_label.setText("156")
        self.success_rate_label.setText("87%")
        self.avg_confidence_label.setText("82%")
    
    def clear_history(self):
        """Clear parse history"""
        reply = QMessageBox.question(
            self,
            "Clear History", 
            "Clear all parse history?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.recent_list.clear()
            self.results_display.clear()
            self.update_statistics()
    
    def set_test_state(self, is_testing, message=""):
        """Set UI state during testing"""
        self.test_button.setEnabled(not is_testing)
        self.progress_bar.setVisible(is_testing)
        
        if is_testing:
            self.progress_bar.setRange(0, 0)  # Indeterminate
        
        self.status_label.setText(message)
    
    def refresh_data(self):
        """Refresh widget data"""
        self.load_settings()
        self.load_recent_parses()
        self.update_statistics()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.parser_worker and self.parser_worker.isRunning():
            self.parser_worker.terminate()
            self.parser_worker.wait()
