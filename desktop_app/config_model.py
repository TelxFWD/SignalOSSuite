"""
Configuration data models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path

class ThemeMode(Enum):
    """Application theme modes"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ExecutionMode(Enum):
    """Signal execution modes"""
    LIVE = "live"
    DEMO = "demo"
    PAPER = "paper"
    DISABLED = "disabled"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    enabled: bool = False
    host: str = "localhost"
    port: int = 5432
    database: str = "signalos"
    username: str = ""
    password: str = ""
    ssl_mode: str = "prefer"
    connection_pool_size: int = 5
    timeout_seconds: int = 30

@dataclass
class ApiConfig:
    """API configuration"""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    api_key: str = ""
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

@dataclass
class NotificationConfig:
    """Notification configuration"""
    enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    push_enabled: bool = True
    desktop_enabled: bool = True
    
    # Email settings
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    
    # SMS settings
    sms_provider: str = ""
    sms_api_key: str = ""
    sms_from: str = ""
    sms_to: List[str] = field(default_factory=list)
    
    # Notification filters
    notify_on_signal: bool = True
    notify_on_trade: bool = True
    notify_on_error: bool = True
    notify_on_connection_lost: bool = True
    min_confidence_threshold: float = 0.7

@dataclass
class BackupConfig:
    """Backup and restore configuration"""
    enabled: bool = True
    auto_backup: bool = True
    backup_interval_hours: int = 24
    max_backups: int = 30
    backup_location: str = ""
    include_logs: bool = False
    include_media: bool = False
    compress_backups: bool = True
    cloud_backup_enabled: bool = False
    cloud_provider: str = ""  # aws, gcp, azure, dropbox
    cloud_credentials: Dict[str, str] = field(default_factory=dict)

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_enabled: bool = True
    encryption_algorithm: str = "AES-256"
    session_timeout_minutes: int = 480  # 8 hours
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    require_2fa: bool = False
    allowed_ip_ranges: List[str] = field(default_factory=list)
    api_key_rotation_days: int = 90
    
    # Password requirements
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True

@dataclass
class PerformanceConfig:
    """Performance and optimization configuration"""
    max_worker_threads: int = 4
    signal_queue_size: int = 1000
    batch_processing_size: int = 10
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    memory_limit_mb: int = 512
    cpu_usage_limit_percent: int = 80
    
    # Monitoring settings
    health_check_interval_seconds: int = 30
    performance_metrics_enabled: bool = True
    detailed_logging: bool = False
    profiling_enabled: bool = False

@dataclass
class IntegrationConfig:
    """Third-party integration configuration"""
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_secret: str = ""
    webhook_events: List[str] = field(default_factory=lambda: ["signal", "trade", "error"])
    
    # Trading platforms
    mt4_enabled: bool = False
    mt4_path: str = ""
    ctrader_enabled: bool = False
    ctrader_path: str = ""
    
    # Analytics platforms
    google_analytics_enabled: bool = False
    google_analytics_id: str = ""
    mixpanel_enabled: bool = False
    mixpanel_token: str = ""

@dataclass
class UIConfig:
    """User interface configuration"""
    theme: ThemeMode = ThemeMode.LIGHT
    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    currency_display: str = "USD"
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    remember_window_state: bool = True
    
    # Display options
    show_tooltips: bool = True
    show_animations: bool = True
    grid_lines: bool = True
    auto_refresh_interval_seconds: int = 5
    
    # Chart settings
    chart_type: str = "candlestick"
    chart_timeframe: str = "1h"
    chart_indicators: List[str] = field(default_factory=list)

@dataclass
class AdvancedConfig:
    """Advanced configuration options"""
    debug_mode: bool = False
    log_level: LogLevel = LogLevel.INFO
    log_retention_days: int = 30
    max_log_file_size_mb: int = 10
    
    # Development settings
    developer_mode: bool = False
    api_documentation_enabled: bool = False
    test_mode: bool = False
    mock_data_enabled: bool = False
    
    # Experimental features
    experimental_features_enabled: bool = False
    beta_features: List[str] = field(default_factory=list)
    feature_flags: Dict[str, bool] = field(default_factory=dict)

@dataclass
class ProfileConfig:
    """User profile configuration"""
    user_id: str = ""
    username: str = ""
    email: str = ""
    full_name: str = ""
    avatar_url: str = ""
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    # Preferences
    preferred_pairs: List[str] = field(default_factory=list)
    risk_tolerance: str = "medium"  # low, medium, high
    default_lot_size: float = 0.01
    max_concurrent_trades: int = 5
    
    # Subscription info
    subscription_type: str = "free"  # free, basic, premium, enterprise
    subscription_expires: Optional[datetime] = None
    features_enabled: List[str] = field(default_factory=list)

@dataclass
class AppConfig:
    """Main application configuration container"""
    # Core configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)
    profile: ProfileConfig = field(default_factory=ProfileConfig)
    
    # Metadata
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    config_schema_version: str = "1.0"
    
    def update_timestamp(self):
        """Update the configuration timestamp"""
        self.updated_at = datetime.now()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate database config
        if self.database.enabled:
            if not self.database.host:
                errors.append("Database host is required when database is enabled")
            if not self.database.database:
                errors.append("Database name is required when database is enabled")
        
        # Validate API config
        if self.api.enabled:
            if not (1024 <= self.api.port <= 65535):
                errors.append("API port must be between 1024 and 65535")
        
        # Validate notification config
        if self.notifications.email_enabled:
            if not self.notifications.smtp_server:
                errors.append("SMTP server is required for email notifications")
            if not self.notifications.email_from:
                errors.append("From email is required for email notifications")
        
        # Validate backup config
        if self.backup.enabled and self.backup.auto_backup:
            if not self.backup.backup_location:
                errors.append("Backup location is required for auto backup")
        
        # Validate security config
        if self.security.session_timeout_minutes < 5:
            errors.append("Session timeout must be at least 5 minutes")
        
        # Validate performance config
        if self.performance.max_worker_threads < 1:
            errors.append("Max worker threads must be at least 1")
        if self.performance.memory_limit_mb < 64:
            errors.append("Memory limit must be at least 64 MB")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        from dataclasses import asdict
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary"""
        # This would need proper deserialization logic
        # For now, return a basic instance
        return cls()

@dataclass
class ConfigTemplate:
    """Configuration template for easy setup"""
    name: str
    description: str
    category: str  # beginner, intermediate, advanced, custom
    config_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def apply_to_config(self, config: AppConfig) -> AppConfig:
        """Apply template to existing configuration"""
        # This would merge template data with existing config
        # Implementation would depend on specific merge strategy
        return config

# Predefined configuration templates
BEGINNER_TEMPLATE = ConfigTemplate(
    name="Beginner Setup",
    description="Safe configuration for new users",
    category="beginner",
    tags=["safe", "conservative", "simple"]
)

AGGRESSIVE_TEMPLATE = ConfigTemplate(
    name="Aggressive Trading",
    description="High-frequency trading configuration",
    category="advanced",
    tags=["aggressive", "high-frequency", "advanced"]
)

DEMO_TEMPLATE = ConfigTemplate(
    name="Demo Mode",
    description="Configuration for demo trading",
    category="demo",
    tags=["demo", "testing", "safe"]
)

# Configuration validation functions
def validate_config_section(config_section: Any, section_name: str) -> List[str]:
    """Validate a specific configuration section"""
    errors = []
    
    if hasattr(config_section, 'validate'):
        try:
            section_errors = config_section.validate()
            errors.extend([f"{section_name}: {error}" for error in section_errors])
        except Exception as e:
            errors.append(f"{section_name}: Validation error - {str(e)}")
    
    return errors

def merge_configs(base_config: AppConfig, override_config: Dict[str, Any]) -> AppConfig:
    """Merge configuration with overrides"""
    # This would implement deep merging of configuration
    # For now, return the base config
    return base_config

def export_config_schema() -> Dict[str, Any]:
    """Export configuration schema for validation"""
    return {
        "type": "object",
        "properties": {
            "database": {"type": "object"},
            "api": {"type": "object"},
            "notifications": {"type": "object"},
            "backup": {"type": "object"},
            "security": {"type": "object"},
            "performance": {"type": "object"},
            "integrations": {"type": "object"},
            "ui": {"type": "object"},
            "advanced": {"type": "object"},
            "profile": {"type": "object"}
        }
    }

