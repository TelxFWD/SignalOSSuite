"""
Admin Panel Sample Data Creation
Creates sample data to demonstrate the comprehensive admin functionality
"""

from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json
import random

from app import app, db
from models import (User, AdminUser, LicensePlan, UserLicense, ParserModel, SignalProvider, 
                   SystemLog, NotificationTemplate, TelegramSession, TelegramChannel, 
                   MT5Terminal, Strategy, Signal, Trade, SystemHealth, SignalStatus, SignalAction)


def create_admin_sample_data():
    """Create comprehensive sample data for admin panel demonstration"""
    
    with app.app_context():
        # Create license plans
        plans = [
            {
                'name': 'Free Trial',
                'description': 'Basic features for getting started',
                'price': 0.0,
                'duration_days': 7,
                'max_terminals': 1,
                'max_channels': 2,
                'max_strategies': 1,
                'features': json.dumps({
                    'shadow_mode': True,
                    'basic_strategies': True,
                    'telegram_channels': 2,
                    'support': 'community'
                })
            },
            {
                'name': 'Basic',
                'description': 'Standard trading features',
                'price': 29.99,
                'duration_days': 30,
                'max_terminals': 2,
                'max_channels': 5,
                'max_strategies': 3,
                'features': json.dumps({
                    'shadow_mode': True,
                    'advanced_strategies': True,
                    'telegram_channels': 5,
                    'email_support': True,
                    'signal_filtering': True
                })
            },
            {
                'name': 'Pro',
                'description': 'Professional trading with advanced features',
                'price': 79.99,
                'duration_days': 30,
                'max_terminals': 5,
                'max_channels': 15,
                'max_strategies': 10,
                'features': json.dumps({
                    'shadow_mode': True,
                    'custom_strategies': True,
                    'unlimited_channels': True,
                    'priority_support': True,
                    'advanced_analytics': True,
                    'risk_management': True,
                    'provider_tools': True
                })
            },
            {
                'name': 'Elite',
                'description': 'Enterprise-level features and support',
                'price': 199.99,
                'duration_days': 30,
                'max_terminals': 20,
                'max_channels': 50,
                'max_strategies': 50,
                'features': json.dumps({
                    'all_features': True,
                    'white_label': True,
                    'dedicated_support': True,
                    'custom_integrations': True,
                    'api_access': True,
                    'multi_account': True
                })
            }
        ]
        
        for plan_data in plans:
            if not LicensePlan.query.filter_by(name=plan_data['name']).first():
                plan = LicensePlan(**plan_data)
                db.session.add(plan)
        
        # Create admin user
        admin_email = 'admin@signalos.com'
        if not User.query.filter_by(email=admin_email).first():
            admin_user = User(
                email=admin_email,
                name='Admin User',
                password_hash=generate_password_hash('admin123'),
                license_type='Elite',
                active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin_user)
            db.session.flush()  # Get the ID
            
            # Create admin profile
            admin_profile = AdminUser(
                user_id=admin_user.id,
                role='super_admin',
                permissions=json.dumps({
                    'user_management': True,
                    'license_management': True,
                    'system_configuration': True,
                    'signal_debugging': True,
                    'parser_training': True,
                    'provider_management': True,
                    'system_logs': True
                })
            )
            db.session.add(admin_profile)
        
        # Create parser models
        models = [
            {
                'version': 'v1.0.0',
                'name': 'Basic Signal Parser',
                'description': 'Initial release of the signal parsing model',
                'accuracy': 0.78,
                'training_samples': 5000,
                'active': False
            },
            {
                'version': 'v1.2.5',
                'name': 'Enhanced Signal Parser',
                'description': 'Improved accuracy with Gold/XAU support',
                'accuracy': 0.85,
                'training_samples': 12000,
                'active': False
            },
            {
                'version': 'v2.1.0',
                'name': 'Advanced AI Parser',
                'description': 'Latest model with multi-language support',
                'accuracy': 0.91,
                'training_samples': 25000,
                'active': True
            }
        ]
        
        for model_data in models:
            if not ParserModel.query.filter_by(version=model_data['version']).first():
                model = ParserModel(**model_data)
                db.session.add(model)
        
        # Create signal providers
        providers = [
            {
                'name': 'Forex Signals Pro',
                'description': 'Professional forex signals with high accuracy',
                'telegram_channel': '@forexsignalspro',
                'website_url': 'https://forexsignalspro.com',
                'verified': True,
                'active': True
            },
            {
                'name': 'Gold Trading Experts',
                'description': 'Specialized in precious metals trading',
                'telegram_channel': '@goldtradingexperts',
                'website_url': 'https://goldexperts.com',
                'verified': True,
                'active': True
            },
            {
                'name': 'Crypto Forex Hub',
                'description': 'Multi-asset trading signals',
                'telegram_channel': '@cryptoforexhub',
                'verified': False,
                'active': True
            }
        ]
        
        for provider_data in providers:
            if not SignalProvider.query.filter_by(name=provider_data['name']).first():
                provider = SignalProvider(**provider_data)
                db.session.add(provider)
        
        # Create notification templates
        templates = [
            {
                'name': 'Signal Failed',
                'type': 'telegram',
                'subject': 'Signal Processing Failed',
                'message_template': '🚨 Signal Processing Failed\n\nPair: {pair}\nReason: {error_message}\nTime: {timestamp}',
                'variables': json.dumps(['pair', 'error_message', 'timestamp'])
            },
            {
                'name': 'EA Offline',
                'type': 'telegram',
                'subject': 'EA Connection Lost',
                'message_template': '⚠️ MT5 EA Offline\n\nTerminal: {terminal_name}\nLast seen: {last_heartbeat}',
                'variables': json.dumps(['terminal_name', 'last_heartbeat'])
            },
            {
                'name': 'License Expiry Warning',
                'type': 'email',
                'subject': 'License Expiring Soon',
                'message_template': 'Your SignalOS license expires in {days_remaining} days. Please renew to continue using our services.',
                'variables': json.dumps(['days_remaining', 'plan_name', 'expiry_date'])
            }
        ]
        
        for template_data in templates:
            if not NotificationTemplate.query.filter_by(name=template_data['name']).first():
                template = NotificationTemplate(**template_data)
                db.session.add(template)
        
        db.session.commit()
        
        # Create sample system logs
        log_categories = ['parser', 'mt5', 'telegram', 'system', 'admin']
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        log_messages = [
            'Signal parsing completed successfully',
            'MT5 connection established',
            'Telegram session authenticated',
            'System health check passed',
            'User login attempt',
            'Signal execution failed - insufficient margin',
            'Parser model updated to v2.1.0',
            'Database backup completed',
            'License validation successful',
            'Trade executed: EURUSD BUY 0.1 lots'
        ]
        
        # Create logs for the past 30 days
        for i in range(200):
            log_time = datetime.utcnow() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            log = SystemLog(
                level=random.choice(log_levels),
                category=random.choice(log_categories),
                message=random.choice(log_messages),
                timestamp=log_time,
                additional_data=json.dumps({
                    'ip_address': f'192.168.1.{random.randint(1, 254)}',
                    'user_agent': 'SignalOS/1.0'
                })
            )
            db.session.add(log)
        
        # Create sample system health records
        for i in range(48):  # Last 48 hours
            health_time = datetime.utcnow() - timedelta(hours=i)
            
            health = SystemHealth(
                timestamp=health_time,
                cpu_percent=random.uniform(10, 80),
                memory_percent=random.uniform(20, 70),
                telegram_connected=random.choice([True, True, True, False]),  # 75% uptime
                mt5_connected=random.choice([True, True, False]),  # 66% uptime
                parser_running=True,
                signals_processed_today=random.randint(5, 50),
                errors_today=random.randint(0, 5)
            )
            db.session.add(health)
        
        db.session.commit()
        print("Admin sample data created successfully!")


if __name__ == '__main__':
    create_admin_sample_data()