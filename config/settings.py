"""
Application settings and configuration management
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TelegramConfig:
    """Telegram configuration settings"""
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    phone_number: Optional[str] = None
    session_name: str = "signalos_session"
    channels: list = None
    auto_join: bool = True
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = []

@dataclass
class ParserConfig:
    """Signal parser configuration"""
    enabled: bool = True
    model_name: str = "en_core_web_sm"
    confidence_threshold: float = 0.8
    ocr_enabled: bool = True
    fallback_rules: bool = True
    buffer_pips: int = 5
    
@dataclass
class MT5Config:
    """MetaTrader 5 configuration"""
    terminal_path: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    server: Optional[str] = None
    expert_path: Optional[str] = None
    magic_number: int = 123456
    auto_restart: bool = True
    heartbeat_interval: int = 30

@dataclass
class ExecutionConfig:
    """Trade execution configuration"""
    enabled: bool = True
    stealth_mode: bool = False
    delay_seconds: int = 0
    remove_sl_tp: bool = False
    remove_comments: bool = False
    max_risk_percent: float = 2.0
    multi_tp_enabled: bool = True

class AppSettings:
    """Main application settings manager"""
    
    def __init__(self):
        self.app_dir = Path.home() / ".signalos"
        self.config_file = self.app_dir / "config.json"
        self.logs_dir = self.app_dir / "logs"
        self.sessions_dir = self.app_dir / "sessions"
        
        # Create directories if they don't exist
        self.app_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Configuration objects
        self.telegram = TelegramConfig()
        self.parser = ParserConfig()
        self.mt5 = MT5Config()
        self.execution = ExecutionConfig()
        
        # Application settings
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.offline_mode: bool = False
        self.shadow_mode: bool = False
        
        # Load existing configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load each configuration section
                if 'telegram' in data:
                    self.telegram = TelegramConfig(**data['telegram'])
                if 'parser' in data:
                    self.parser = ParserConfig(**data['parser'])
                if 'mt5' in data:
                    self.mt5 = MT5Config(**data['mt5'])
                if 'execution' in data:
                    self.execution = ExecutionConfig(**data['execution'])
                
                # Load app settings
                self.auth_token = data.get('auth_token')
                self.user_id = data.get('user_id')
                self.offline_mode = data.get('offline_mode', False)
                self.shadow_mode = data.get('shadow_mode', False)
                
                return True
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            config_data = {
                'telegram': asdict(self.telegram),
                'parser': asdict(self.parser),
                'mt5': asdict(self.mt5),
                'execution': asdict(self.execution),
                'auth_token': self.auth_token,
                'user_id': self.user_id,
                'offline_mode': self.offline_mode,
                'shadow_mode': self.shadow_mode
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def export_config(self, filepath: str) -> bool:
        """Export configuration to specified file"""
        try:
            config_data = {
                'telegram': asdict(self.telegram),
                'parser': asdict(self.parser),
                'mt5': asdict(self.mt5),
                'execution': asdict(self.execution)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """Import configuration from specified file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import each configuration section
            if 'telegram' in data:
                self.telegram = TelegramConfig(**data['telegram'])
            if 'parser' in data:
                self.parser = ParserConfig(**data['parser'])
            if 'mt5' in data:
                self.mt5 = MT5Config(**data['mt5'])
            if 'execution' in data:
                self.execution = ExecutionConfig(**data['execution'])
            
            # Save the imported configuration
            return self.save_config()
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def get_api_credentials(self) -> tuple:
        """Get API credentials from environment or config"""
        api_id = os.getenv('TELEGRAM_API_ID', self.telegram.api_id)
        api_hash = os.getenv('TELEGRAM_API_HASH', self.telegram.api_hash)
        return api_id, api_hash
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.telegram = TelegramConfig()
        self.parser = ParserConfig()
        self.mt5 = MT5Config()
        self.execution = ExecutionConfig()
        self.auth_token = None
        self.user_id = None
        self.offline_mode = False
        self.shadow_mode = False

# Global settings instance
settings = AppSettings()
