"""
SignalOS Stealth Mode Implementation
Advanced shadow trading with comment masking and SL/TP removal
"""
from typing import Dict, Any, Optional
from datetime import datetime
from models import UserSettings, db
from app import app

class StealthModeManager:
    """Manages stealth/shadow mode trading functionality"""
    
    def __init__(self):
        self.stealth_comments = [
            "Market Analysis",
            "Technical Review", 
            "Strategy Update",
            "Portfolio Adjustment",
            "Risk Management",
            "Systematic Trade",
            "Algorithm Signal",
            "Model Prediction"
        ]
    
    def is_stealth_enabled(self, user_id: int = 1) -> bool:
        """Check if stealth mode is enabled for user"""
        try:
            with app.app_context():
                settings = UserSettings.query.filter(UserSettings.user_id == user_id).first()
                return settings.enable_shadow_mode if settings else False
        except Exception:
            return False
    
    def apply_stealth_settings(self, trade_data: Dict[str, Any], user_id: int = 1) -> Dict[str, Any]:
        """Apply stealth mode transformations to trade data"""
        if not self.is_stealth_enabled(user_id):
            return trade_data
        
        stealth_trade = trade_data.copy()
        
        # Remove or mask stop loss and take profit
        if 'stop_loss' in stealth_trade:
            stealth_trade['stop_loss'] = None
            stealth_trade['stealth_sl_hidden'] = True
        
        if 'take_profit' in stealth_trade:
            stealth_trade['take_profit'] = None  
            stealth_trade['stealth_tp_hidden'] = True
        
        # Replace comment with generic stealth comment
        import random
        stealth_trade['comment'] = random.choice(self.stealth_comments)
        stealth_trade['original_comment'] = trade_data.get('comment', '')
        
        # Add stealth mode indicators
        stealth_trade['stealth_mode'] = True
        stealth_trade['stealth_applied_at'] = datetime.utcnow().isoformat()
        
        # Log stealth transformation
        self._log_stealth_application(trade_data, stealth_trade)
        
        return stealth_trade
    
    def _log_stealth_application(self, original: Dict, stealth: Dict):
        """Log stealth mode application for debugging"""
        try:
            with app.app_context():
                from models import SystemLog
                
                log_message = (
                    f"Stealth mode applied - "
                    f"Original: SL={original.get('stop_loss')}, TP={original.get('take_profit')}, "
                    f"Comment='{original.get('comment', '')}' | "
                    f"Stealth: SL={stealth.get('stop_loss')}, TP={stealth.get('take_profit')}, "
                    f"Comment='{stealth.get('comment', '')}'"
                )
                
                log_entry = SystemLog(
                    level='INFO',
                    category='STEALTH_MODE',
                    message=log_message,
                    timestamp=datetime.utcnow()
                )
                db.session.add(log_entry)
                db.session.commit()
                
        except Exception as e:
            print(f"Failed to log stealth application: {e}")
    
    def get_stealth_status(self, user_id: int = 1) -> Dict[str, Any]:
        """Get current stealth mode status and statistics"""
        try:
            with app.app_context():
                settings = UserSettings.query.filter(UserSettings.user_id == user_id).first()
                
                # Get stealth trade count from logs
                from models import SystemLog
                stealth_logs = SystemLog.query.filter(
                    SystemLog.category == 'STEALTH_MODE'
                ).count()
                
                return {
                    'enabled': settings.enable_shadow_mode if settings else False,
                    'trades_masked': stealth_logs,
                    'last_updated': settings.updated_at.isoformat() if settings and hasattr(settings, 'updated_at') else None,
                    'available_comments': len(self.stealth_comments),
                    'status': 'active' if (settings and settings.enable_shadow_mode) else 'disabled'
                }
                
        except Exception as e:
            return {
                'enabled': False,
                'error': str(e),
                'status': 'error'
            }
    
    def update_stealth_settings(self, user_id: int, enabled: bool, custom_comments: Optional[list] = None) -> bool:
        """Update stealth mode settings"""
        try:
            with app.app_context():
                settings = UserSettings.query.filter(UserSettings.user_id == user_id).first()
                
                if not settings:
                    settings = UserSettings(
                        user_id=user_id,
                        enable_shadow_mode=enabled
                    )
                    db.session.add(settings)
                else:
                    settings.enable_shadow_mode = enabled
                
                # Update custom comments if provided
                if custom_comments:
                    self.stealth_comments.extend(custom_comments)
                
                db.session.commit()
                
                # Log settings change
                self._log_settings_change(user_id, enabled)
                
                return True
                
        except Exception as e:
            print(f"Failed to update stealth settings: {e}")
            return False
    
    def _log_settings_change(self, user_id: int, enabled: bool):
        """Log stealth settings changes"""
        try:
            with app.app_context():
                from models import SystemLog
                
                log_entry = SystemLog(
                    level='INFO',
                    category='STEALTH_SETTINGS',
                    message=f"User {user_id} {'enabled' if enabled else 'disabled'} stealth mode",
                    user_id=user_id,
                    timestamp=datetime.utcnow()
                )
                db.session.add(log_entry)
                db.session.commit()
                
        except Exception as e:
            print(f"Failed to log settings change: {e}")


# Global stealth manager instance
stealth_manager = StealthModeManager()


def apply_stealth_to_trade(trade_data: Dict[str, Any], user_id: int = 1) -> Dict[str, Any]:
    """Main entry point for applying stealth mode to trades"""
    return stealth_manager.apply_stealth_settings(trade_data, user_id)


def get_stealth_status(user_id: int = 1) -> Dict[str, Any]:
    """Get stealth mode status"""
    return stealth_manager.get_stealth_status(user_id)


if __name__ == "__main__":
    # Test stealth mode functionality
    test_trade = {
        'symbol': 'EURUSD',
        'action': 'BUY',
        'volume': 0.01,
        'entry_price': 1.0850,
        'stop_loss': 1.0800,
        'take_profit': 1.0900,
        'comment': 'Signal from Telegram channel XYZ'
    }
    
    print("=== Stealth Mode Test ===")
    print(f"Original trade: {test_trade}")
    
    stealth_trade = apply_stealth_to_trade(test_trade)
    print(f"Stealth trade: {stealth_trade}")
    
    status = get_stealth_status()
    print(f"Stealth status: {status}")