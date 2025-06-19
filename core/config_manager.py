"""
Configuration manager for handling application settings and synchronization
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from config.settings import settings, AppSettings
from config.auth import auth_manager
from core.logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """Manages application configuration and synchronization"""
    
    def __init__(self):
        self.settings = settings
        self.backup_dir = settings.app_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_config(self, description: str = "") -> bool:
        """Create a backup of current configuration"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            # Create backup data
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'description': description,
                'version': '1.0.0',
                'config': self.export_config_data()
            }
            
            # Write backup
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up configuration: {e}")
            return False
    
    def restore_config(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Load backup data
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validate backup
            if not self.validate_backup(backup_data):
                logger.error("Invalid backup file format")
                return False
            
            # Create current backup before restoring
            self.backup_config("Before restore operation")
            
            # Restore configuration
            config_data = backup_data.get('config', {})
            return self.import_config_data(config_data)
            
        except Exception as e:
            logger.error(f"Error restoring configuration: {e}")
            return False
    
    def validate_backup(self, backup_data: Dict[str, Any]) -> bool:
        """Validate backup file format"""
        required_fields = ['timestamp', 'version', 'config']
        
        for field in required_fields:
            if field not in backup_data:
                return False
        
        # Check if config has expected structure
        config = backup_data.get('config', {})
        expected_sections = ['telegram', 'parser', 'mt5', 'execution']
        
        for section in expected_sections:
            if section not in config:
                return False
        
        return True
    
    def export_config_data(self) -> Dict[str, Any]:
        """Export current configuration data"""
        from dataclasses import asdict
        
        return {
            'telegram': asdict(self.settings.telegram),
            'parser': asdict(self.settings.parser),
            'mt5': asdict(self.settings.mt5),
            'execution': asdict(self.settings.execution),
            'app_settings': {
                'offline_mode': self.settings.offline_mode,
                'shadow_mode': self.settings.shadow_mode
            }
        }
    
    def import_config_data(self, config_data: Dict[str, Any]) -> bool:
        """Import configuration data"""
        try:
            from config.settings import TelegramConfig, ParserConfig, MT5Config, ExecutionConfig
            
            # Import each section
            if 'telegram' in config_data:
                self.settings.telegram = TelegramConfig(**config_data['telegram'])
            
            if 'parser' in config_data:
                self.settings.parser = ParserConfig(**config_data['parser'])
            
            if 'mt5' in config_data:
                self.settings.mt5 = MT5Config(**config_data['mt5'])
            
            if 'execution' in config_data:
                self.settings.execution = ExecutionConfig(**config_data['execution'])
            
            # Import app settings
            app_settings = config_data.get('app_settings', {})
            self.settings.offline_mode = app_settings.get('offline_mode', False)
            self.settings.shadow_mode = app_settings.get('shadow_mode', False)
            
            # Save the imported configuration
            return self.settings.save_config()
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
    
    def sync_with_server(self) -> bool:
        """Synchronize configuration with server"""
        try:
            if not auth_manager.is_authenticated():
                logger.warning("Not authenticated, skipping server sync")
                return False
            
            # Get server configuration
            success, server_config = auth_manager.sync_user_config()
            
            if success and server_config:
                # Backup current config before syncing
                self.backup_config("Before server sync")
                
                # Import server configuration
                if self.import_config_data(server_config):
                    logger.info("Configuration synced from server")
                    return True
                else:
                    logger.error("Failed to import server configuration")
                    return False
            else:
                logger.warning("No server configuration available")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing with server: {e}")
            return False
    
    def upload_to_server(self) -> bool:
        """Upload current configuration to server"""
        try:
            if not auth_manager.is_authenticated():
                logger.warning("Not authenticated, cannot upload to server")
                return False
            
            # Export current configuration
            config_data = self.export_config_data()
            
            # Upload to server
            if auth_manager.upload_config(config_data):
                logger.info("Configuration uploaded to server")
                return True
            else:
                logger.error("Failed to upload configuration to server")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading to server: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        try:
            # Backup current configuration
            self.backup_config("Before reset to defaults")
            
            # Reset settings
            self.settings.reset_to_defaults()
            
            # Save default configuration
            return self.settings.save_config()
            
        except Exception as e:
            logger.error(f"Error resetting to defaults: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate Telegram configuration
            telegram_validation = self.validate_telegram_config()
            validation_result['errors'].extend(telegram_validation['errors'])
            validation_result['warnings'].extend(telegram_validation['warnings'])
            
            # Validate MT5 configuration
            mt5_validation = self.validate_mt5_config()
            validation_result['errors'].extend(mt5_validation['errors'])
            validation_result['warnings'].extend(mt5_validation['warnings'])
            
            # Validate Parser configuration
            parser_validation = self.validate_parser_config()
            validation_result['errors'].extend(parser_validation['errors'])
            validation_result['warnings'].extend(parser_validation['warnings'])
            
            # Set overall validity
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def validate_telegram_config(self) -> Dict[str, list]:
        """Validate Telegram configuration"""
        errors = []
        warnings = []
        
        # Check API credentials
        if not self.settings.telegram.api_id:
            errors.append("Telegram API ID is not configured")
        
        if not self.settings.telegram.api_hash:
            errors.append("Telegram API Hash is not configured")
        
        if not self.settings.telegram.phone_number:
            warnings.append("Phone number is not configured")
        
        # Check channels
        if not self.settings.telegram.channels:
            warnings.append("No Telegram channels configured for monitoring")
        
        return {'errors': errors, 'warnings': warnings}
    
    def validate_mt5_config(self) -> Dict[str, list]:
        """Validate MT5 configuration"""
        errors = []
        warnings = []
        
        # Check terminal path
        if not self.settings.mt5.terminal_path:
            errors.append("MT5 terminal path is not configured")
        elif not Path(self.settings.mt5.terminal_path).exists():
            errors.append("MT5 terminal path does not exist")
        
        # Check login credentials
        if not self.settings.mt5.login:
            warnings.append("MT5 login is not configured")
        
        if not self.settings.mt5.password:
            warnings.append("MT5 password is not configured")
        
        if not self.settings.mt5.server:
            warnings.append("MT5 server is not configured")
        
        # Check EA path
        if not self.settings.mt5.expert_path:
            warnings.append("Expert Advisor path is not configured")
        elif not Path(self.settings.mt5.expert_path).exists():
            warnings.append("Expert Advisor file does not exist")
        
        return {'errors': errors, 'warnings': warnings}
    
    def validate_parser_config(self) -> Dict[str, list]:
        """Validate Parser configuration"""
        errors = []
        warnings = []
        
        # Check confidence threshold
        if not 0.1 <= self.settings.parser.confidence_threshold <= 1.0:
            errors.append("Parser confidence threshold must be between 0.1 and 1.0")
        
        # Check buffer pips
        if not 0 <= self.settings.parser.buffer_pips <= 50:
            warnings.append("Buffer pips should be between 0 and 50")
        
        return {'errors': errors, 'warnings': warnings}
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'telegram': {
                'configured': bool(self.settings.telegram.api_id and self.settings.telegram.api_hash),
                'channels_count': len(self.settings.telegram.channels),
                'auto_join': self.settings.telegram.auto_join
            },
            'parser': {
                'enabled': self.settings.parser.enabled,
                'model': self.settings.parser.model_name,
                'confidence_threshold': self.settings.parser.confidence_threshold,
                'ocr_enabled': self.settings.parser.ocr_enabled
            },
            'mt5': {
                'configured': bool(self.settings.mt5.terminal_path and self.settings.mt5.login),
                'auto_restart': self.settings.mt5.auto_restart,
                'magic_number': self.settings.mt5.magic_number
            },
            'execution': {
                'enabled': self.settings.execution.enabled,
                'stealth_mode': self.settings.execution.stealth_mode,
                'max_risk_percent': self.settings.execution.max_risk_percent
            },
            'app': {
                'offline_mode': self.settings.offline_mode,
                'shadow_mode': self.settings.shadow_mode
            }
        }
    
    def get_available_backups(self) -> List[Dict[str, Any]]:
        """Get list of available configuration backups"""
        backups = []
        
        try:
            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    backup_info = {
                        'file_path': str(backup_file),
                        'filename': backup_file.name,
                        'timestamp': backup_data.get('timestamp'),
                        'description': backup_data.get('description', ''),
                        'version': backup_data.get('version', 'Unknown'),
                        'size': backup_file.stat().st_size
                    }
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logger.error(f"Error reading backup file {backup_file}: {e}")
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting available backups: {e}")
        
        return backups

# Global config manager instance
config_manager = ConfigManager()
