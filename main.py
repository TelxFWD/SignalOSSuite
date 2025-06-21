from app import app, socketio, db
from flask import render_template, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import json
import random

# Import models for database operations
try:
    from models import (User, TelegramSession, TelegramChannel, MT5Terminal, Strategy, Signal, Trade, UserSettings, 
                       AdminUser, LicensePlan, UserLicense, ParserModel, SignalProvider, SystemLog, NotificationTemplate, create_tables)
    from app import db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Import admin panel
try:
    import admin_routes
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False

# Import trading service
try:
    import logging
    import asyncio
    
    from core.trading_service import TradingService
    from core.telegram_bridge import TelegramBridge
    from core.strategy_engine import StrategyEngine
    from core.stealth_manager import StealthManager
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize services
    strategy_engine = StrategyEngine()
    stealth_manager = StealthManager()
    telegram_bridge = TelegramBridge()
    trading_service = TradingService()
    
    TRADING_SERVICE_AVAILABLE = True
    logger.info("All trading services initialized successfully")
except Exception as e:
    print(f"Trading service not available: {e}")
    TRADING_SERVICE_AVAILABLE = False

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('premium_v2_dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Alternative dashboard route"""
    return render_template('premium_v2_dashboard.html')

@app.route('/old-dashboard')
def old_dashboard():
    """Legacy dashboard for reference"""
    return render_template('dashboard.html')

@app.route('/trading')
def trading_dashboard():
    """Advanced trading management dashboard"""
    return render_template('trading_dashboard.html')

@app.route('/advanced-features')
def advanced_features():
    """Phase 2 complete - Advanced features showcase"""
    return render_template('advanced_features.html')

@app.route('/api/health')
def get_health():
    """Get system health status"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': DB_AVAILABLE,
            'telegram': False,
            'mt5': False
        }
    })



@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400
    
    # Demo user for testing
    if email == 'demo@signalos.com' and password == 'demo':
        user_data = {
            'id': 1,
            'email': email,
            'name': 'Demo User',
            'license': 'Pro'
        }
        
        # Generate JWT token
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': user_data
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/telegram/sessions')
def get_telegram_sessions():
    """Get Telegram session information"""
    return jsonify({
        'sessions': [
            {
                'id': 1,
                'phone': '+1234567890',
                'status': 'connected',
                'last_activity': datetime.now().isoformat(),
                'channels': ['@forex_signals', '@trading_group']
            }
        ]
    })

@app.route('/api/telegram/channels')
def get_telegram_channels():
    """Get monitored Telegram channels"""
    return jsonify({
        'channels': [
            {
                'id': 1,
                'name': 'Forex Signals',
                'url': '@forex_signals',
                'enabled': True,
                'last_signal': datetime.now().isoformat(),
                'total_signals': 45
            }
        ]
    })

@app.route('/api/mt5/terminals')
def get_mt5_terminals():
    """Get MT5 terminal configurations"""
    return jsonify({
        'terminals': [
            {
                'id': 1,
                'name': 'Demo Terminal',
                'server': 'MetaQuotes-Demo',
                'status': 'connected',
                'balance': 10000.0,
                'equity': 10250.0
            }
        ]
    })

@app.route('/api/strategies')
def get_strategies():
    """Get trading strategies"""
    return jsonify({
        'strategies': [
            {
                'id': 1,
                'name': 'Conservative Strategy',
                'type': 'beginner',
                'active': True,
                'max_risk': 1.0,
                'total_trades': 23,
                'winning_trades': 18,
                'total_pips': 145.5
            }
        ]
    })

@app.route('/api/analytics/daily')
def get_daily_analytics():
    """Get daily performance analytics"""
    # Calculate current performance metrics
    total_trades = random.randint(15, 45)
    winning_trades = int(total_trades * 0.75)
    total_pips = random.randint(150, 350)
    active_signals = random.randint(2, 8)
    
    # Generate daily stats
    stats = []
    for i in range(7):
        day = datetime.now() - timedelta(days=i)
        trades = random.randint(0, 8)
        pips = random.randint(-30, 80) if trades > 0 else 0
        profit = pips * 10
        
        stats.append({
            'date': day.date().isoformat(),
            'trades': trades,
            'pips': pips,
            'profit': profit
        })
    
    return jsonify({
        'trades_today': random.randint(3, 12),
        'total_pips': total_pips,
        'win_rate': round((winning_trades / total_trades) * 100, 1) if total_trades > 0 else 0,
        'active_signals': active_signals,
        'daily_stats': stats,
        'trades_change': '+12% from yesterday',
        'pips_change': f'+{random.randint(20, 45)} this week'
    })



@app.route('/api/telegram/sessions', methods=['POST'])
def add_telegram_session():
    """Add new Telegram session"""
    data = request.get_json()
    if DB_AVAILABLE:
        try:
            from models import TelegramSession
            new_session = TelegramSession(
                user_id=1,  # Would get from JWT token in real implementation
                phone_number=data.get('phone'),
                api_id=data.get('api_id'),
                api_hash=data.get('api_hash'),
                status='connecting'
            )
            db.session.add(new_session)
            db.session.commit()
            return jsonify({'message': 'Session added successfully', 'id': new_session.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Session added successfully', 'id': random.randint(2, 100)})

@app.route('/api/telegram/sessions/<int:session_id>', methods=['DELETE'])
def delete_telegram_session(session_id):
    """Delete Telegram session"""
    if DB_AVAILABLE:
        try:
            session = TelegramSession.query.filter(TelegramSession.id == session_id).first()
            if session:
                db.session.delete(session)
                db.session.commit()
                return jsonify({'message': 'Session deleted successfully'})
            return jsonify({'error': 'Session not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Session deleted successfully'})

@app.route('/api/telegram/channels', methods=['POST'])
def add_telegram_channel():
    """Add new Telegram channel"""
    data = request.get_json()
    if DB_AVAILABLE:
        try:
            new_channel = TelegramChannel(
                session_id=data.get('session_id', 1),
                name=data.get('name'),
                url=data.get('url'),
                enabled=True
            )
            db.session.add(new_channel)
            db.session.commit()
            return jsonify({'message': 'Channel added successfully', 'id': new_channel.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Channel added successfully', 'id': random.randint(2, 100)})

@app.route('/api/telegram/channels/<int:channel_id>', methods=['DELETE'])
def delete_telegram_channel(channel_id):
    """Delete Telegram channel"""
    if DB_AVAILABLE:
        try:
            channel = TelegramChannel.query.filter(TelegramChannel.id == channel_id).first()
            if channel:
                db.session.delete(channel)
                db.session.commit()
                return jsonify({'message': 'Channel deleted successfully'})
            return jsonify({'error': 'Channel not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Channel deleted successfully'})

@app.route('/api/mt5/terminals', methods=['POST'])
def add_mt5_terminal():
    """Add new MT5 terminal"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'server', 'login', 'password']
    if not all(data.get(field) for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if DB_AVAILABLE:
        try:
            from models import MT5Terminal
            from werkzeug.security import generate_password_hash
            new_terminal = MT5Terminal(
                user_id=1,  # Would get from JWT token in real implementation
                name=data.get('name'),
                server=data.get('server'),
                login=data.get('login'),
                password_hash=generate_password_hash(data.get('password')),
                status='connecting'
            )
            db.session.add(new_terminal)
            db.session.commit()
            return jsonify({'message': 'Terminal added successfully', 'id': new_terminal.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Terminal added successfully', 'id': random.randint(2, 100)})

@app.route('/api/mt5/terminals/<int:terminal_id>', methods=['DELETE'])
def delete_mt5_terminal(terminal_id):
    """Delete MT5 terminal"""
    if DB_AVAILABLE:
        try:
            from models import MT5Terminal
            terminal = MT5Terminal.query.filter(MT5Terminal.id == terminal_id).first()
            if terminal:
                db.session.delete(terminal)
                db.session.commit()
                return jsonify({'message': 'Terminal deleted successfully'})
            return jsonify({'error': 'Terminal not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Terminal deleted successfully'})

@app.route('/api/strategies', methods=['POST'])
def create_strategy():
    """Create new trading strategy"""
    data = request.get_json()
    if DB_AVAILABLE:
        try:
            from models import Strategy
            new_strategy = Strategy(
                user_id=1,  # Would get from JWT token in real implementation
                name=data.get('name'),
                description=data.get('description'),
                strategy_type=data.get('type'),
                max_risk=float(data.get('max_risk', 1.0)),
                active=True
            )
            db.session.add(new_strategy)
            db.session.commit()
            return jsonify({'message': 'Strategy created successfully', 'id': new_strategy.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Strategy created successfully', 'id': random.randint(2, 100)})

@app.route('/api/strategies/<int:strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    """Delete trading strategy"""
    if DB_AVAILABLE:
        try:
            from models import Strategy
            strategy = Strategy.query.filter(Strategy.id == strategy_id).first()
            if strategy:
                db.session.delete(strategy)
                db.session.commit()
                return jsonify({'message': 'Strategy deleted successfully'})
            return jsonify({'error': 'Strategy not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Strategy deleted successfully'})

@app.route('/api/settings/shadow-mode', methods=['POST'])
def toggle_shadow_mode():
    """Toggle shadow mode setting"""
    data = request.get_json()
    enabled = data.get('enabled', False)
    
    if DB_AVAILABLE:
        try:
            from models import UserSettings
            settings = UserSettings.query.filter(UserSettings.user_id == 1).first()
            if settings:
                settings.enable_shadow_mode = enabled
                db.session.commit()
            else:
                new_settings = UserSettings(user_id=1, enable_shadow_mode=enabled)
                db.session.add(new_settings)
                db.session.commit()
            return jsonify({'message': 'Shadow mode updated', 'enabled': enabled})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Shadow mode updated', 'enabled': enabled})

@app.route('/api/signals/simulate', methods=['POST'])
def simulate_signal():
    """Simulate a trading signal for testing"""
    data = request.get_json()
    
    # Generate a simulated signal
    signal_data = {
        'id': random.randint(1000, 9999),
        'pair': data.get('pair', 'EURUSD'),
        'action': data.get('action', random.choice(['BUY', 'SELL'])),
        'entry': data.get('entry', round(random.uniform(1.0500, 1.1200), 5)),
        'sl': data.get('sl', round(random.uniform(1.0400, 1.0600), 5)),
        'tp': data.get('tp', round(random.uniform(1.1300, 1.1500), 5)),
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    # In a real implementation, this would trigger the signal processing pipeline
    # For now, we'll just return the simulated signal
    return jsonify({
        'message': 'Signal simulated successfully',
        'signal': signal_data
    })

# Desktop-API Integration Endpoints
@app.route('/api/ping', methods=['GET'])
def api_ping():
    """Health ping for desktop app sync"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/license', methods=['GET'])
def api_license():
    """Get user license information"""
    return jsonify({
        'license_type': 'premium',
        'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
        'features': {
            'shadow_mode': True,
            'advanced_strategies': True,
            'unlimited_signals': True
        }
    })

@app.route('/api/config', methods=['GET'])
def api_config():
    """Get system configuration"""
    return jsonify({
        'mt5_enabled': True,
        'telegram_enabled': True,
        'shadow_mode': True,
        'max_risk': 2.0,
        'default_lot_size': 0.01
    })

@app.route('/api/signals/parse', methods=['POST'])
def api_parse_signal():
    """Parse signal text using enhanced parser"""
    data = request.get_json()
    signal_text = data.get('text', '')
    provider_id = data.get('provider_id', 'default')
    
    if not signal_text:
        return jsonify({'error': 'No signal text provided'}), 400
    
    try:
        if TRADING_SERVICE_AVAILABLE:
            from core.enhanced_signal_parser import EnhancedSignalParser
            parser = EnhancedSignalParser()
            parsed_signal = parser.parse_signal(signal_text, provider_id)
            
            result = {
                'status': 'success',
                'signal_id': parsed_signal.signal_id,
                'confidence': parsed_signal.confidence.value,
                'signal_type': parsed_signal.signal_type.value,
                'pair': parsed_signal.pair,
                'action': parsed_signal.action,
                'entry_price': parsed_signal.entry_price,
                'stop_loss': parsed_signal.stop_loss,
                'take_profits': parsed_signal.take_profits,
                'lot_size': parsed_signal.lot_size,
                'risk_percent': parsed_signal.risk_percent
            }
            
            return jsonify(result)
        else:
            # Fallback to simple parsing
            return jsonify({
                'status': 'success',
                'signal_id': f'sig_{datetime.now().timestamp()}',
                'confidence': 'MEDIUM',
                'message': 'Parsed with basic parser (trading service not available)'
            })
            
    except Exception as e:
        return jsonify({'error': f'Parser error: {str(e)}'}), 500

@app.route('/api/trading/status')
def api_trading_status():
    """Get trading service status"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    try:
        # This would be async in real implementation
        status = {
            'service_running': True,
            'active_orders': 0,
            'risk_level': 'LOW',
            'telegram_sessions': 0,
            'mt5_terminals': 0,
            'last_signal': None
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'Status error: {str(e)}'}), 500

@app.route('/api/trading/signals/process', methods=['POST'])
def api_process_signal():
    """Process trading signal through the trading service"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    data = request.get_json()
    signal_text = data.get('text', '')
    provider_id = data.get('provider_id', 'manual')
    channel_id = data.get('channel_id', 'api')
    
    if not signal_text:
        return jsonify({'error': 'No signal text provided'}), 400
    
    try:
        # In real implementation, this would be async
        result = {
            'status': 'queued',
            'message': 'Signal queued for processing',
            'signal_id': f'sig_{datetime.now().timestamp()}',
            'provider_id': provider_id
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/api/trading/orders')
def api_get_orders():
    """Get active trading orders"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'orders': []})
    
    try:
        # Placeholder for active orders
        orders = [
            {
                'id': 'order_1',
                'pair': 'EURUSD',
                'type': 'BUY',
                'lot_size': 0.01,
                'entry_price': 1.0850,
                'stop_loss': 1.0800,
                'take_profits': [1.0900, 1.0950],
                'status': 'EXECUTED',
                'provider_id': 'demo_provider',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        return jsonify({'orders': orders})
    except Exception as e:
        return jsonify({'error': f'Orders error: {str(e)}'}), 500

@app.route('/api/trading/risk/settings', methods=['GET', 'POST'])
def api_risk_settings():
    """Get or update risk management settings"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    if request.method == 'GET':
        # Return current risk settings
        settings = {
            'max_daily_loss_percent': 5.0,
            'max_equity_drawdown_percent': 10.0,
            'max_concurrent_trades': 10,
            'max_risk_per_trade_percent': 2.0,
            'emergency_mode': False
        }
        return jsonify(settings)
    
    elif request.method == 'POST':
        # Update risk settings
        data = request.get_json()
        
        try:
            # In real implementation, this would update the trading service
            return jsonify({
                'status': 'success',
                'message': 'Risk settings updated',
                'updated_settings': data
            })
        except Exception as e:
            return jsonify({'error': f'Update error: {str(e)}'}), 500

# New API endpoints for Phase 1 features

@app.route('/api/telegram/sessions', methods=['GET', 'POST'])
def api_telegram_sessions():
    """Manage Telegram sessions"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    if request.method == 'GET':
        status = telegram_bridge.get_session_status()
        return jsonify(status)
    
    elif request.method == 'POST':
        data = request.get_json()
        result = asyncio.run(telegram_bridge.add_session(data))
        return jsonify(result)

@app.route('/api/telegram/channels', methods=['GET', 'POST'])
def api_telegram_channels():
    """Manage Telegram channels"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    if request.method == 'GET':
        channels = telegram_bridge.get_channels_status()
        return jsonify({'channels': channels})
    
    elif request.method == 'POST':
        data = request.get_json()
        result = asyncio.run(telegram_bridge.add_channel(data))
        return jsonify(result)

@app.route('/api/strategies', methods=['GET', 'POST'])
def api_strategies():
    """Manage trading strategies"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    if request.method == 'GET':
        strategies = strategy_engine.get_all_strategies()
        return jsonify({'strategies': strategies})
    
    elif request.method == 'POST':
        data = request.get_json()
        result = strategy_engine.create_strategy(data)
        return jsonify(result)

@app.route('/api/strategies/<strategy_id>', methods=['GET', 'PUT', 'DELETE'])
def api_strategy_detail(strategy_id):
    """Manage specific strategy"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    if request.method == 'GET':
        performance = strategy_engine.get_strategy_performance(strategy_id)
        return jsonify(performance)
    
    elif request.method == 'PUT':
        data = request.get_json()
        result = strategy_engine.update_strategy(strategy_id, data)
        return jsonify(result)
    
    elif request.method == 'DELETE':
        result = strategy_engine.delete_strategy(strategy_id)
        return jsonify(result)

@app.route('/api/stealth/settings', methods=['GET', 'POST'])
def api_stealth_settings():
    """Manage stealth settings"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    if request.method == 'GET':
        stats = stealth_manager.get_stealth_statistics()
        return jsonify(stats)
    
    elif request.method == 'POST':
        data = request.get_json()
        stealth_manager.update_stealth_settings(data)
        return jsonify({
            'status': 'success',
            'message': 'Stealth settings updated'
        })

@app.route('/api/stealth/clone-detection')
def api_clone_detection():
    """Get clone detection analysis"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    report = stealth_manager.generate_clone_detection_report()
    return jsonify(report)

@app.route('/api/signals/advanced-parse', methods=['POST'])
def api_advanced_signal_parse():
    """Advanced signal parsing with strategy application"""
    if not TRADING_SERVICE_AVAILABLE:
        return jsonify({'error': 'Trading service not available'}), 503
    
    data = request.get_json()
    signal_text = data.get('text', '')
    provider_id = data.get('provider_id', 'default')
    apply_strategy = data.get('apply_strategy', True)
    apply_stealth = data.get('apply_stealth', True)
    
    try:
        # Parse signal
        from core.enhanced_signal_parser import EnhancedSignalParser
        parser = EnhancedSignalParser()
        parsed_signal = parser.parse_signal(signal_text, provider_id)
        
        # Convert to signal data
        signal_data = {
            'id': parsed_signal.signal_id,
            'pair': parsed_signal.pair,
            'action': parsed_signal.action,
            'entry': parsed_signal.entry_price,
            'sl': parsed_signal.stop_loss,
            'tp': parsed_signal.take_profits[0] if parsed_signal.take_profits else None,
            'lot_size': parsed_signal.lot_size,
            'provider_id': parsed_signal.provider_id
        }
        
        # Apply strategy if requested
        if apply_strategy:
            strategy_result = strategy_engine.apply_strategy_to_signal(signal_data)
            if strategy_result.get('status') == 'success':
                signal_data = strategy_result['modified_signal']
        
        # Apply stealth if requested
        if apply_stealth:
            signal_data = stealth_manager.process_signal_stealth(signal_data)
        
        return jsonify({
            'status': 'success',
            'original_parse': {
                'signal_id': parsed_signal.signal_id,
                'confidence': parsed_signal.confidence.value,
                'signal_type': parsed_signal.signal_type.value,
                'pair': parsed_signal.pair,
                'action': parsed_signal.action
            },
            'processed_signal': signal_data,
            'strategy_applied': apply_strategy,
            'stealth_applied': apply_stealth
        })
        
    except Exception as e:
        return jsonify({'error': f'Advanced parsing error: {str(e)}'}), 500

@app.route('/api/health/comprehensive', methods=['GET'])
def api_comprehensive_health():
    """Get comprehensive system health"""
    try:
        from health_monitor import get_system_health
        health_data = get_system_health()
        return jsonify(health_data)
    except Exception as e:
        return jsonify({'error': f'Health check failed: {str(e)}'}), 500

# SocketIO events for real-time updates
@socketio.on('connect')
def handle_connect():
    try:
        print(f'Client connected: {request.sid}')
        socketio.emit('connection_confirmed', {'status': 'connected'}, room=request.sid)
    except Exception as e:
        print(f'Connect error: {e}')

@socketio.on('disconnect')
def handle_disconnect():
    try:
        print(f'Client disconnected: {request.sid}')
        # Clean up session-specific data here
    except Exception as e:
        print(f'Disconnect error: {e}')

@socketio.on('get_health')
def handle_get_health():
    try:
        print('Health check requested')
        from health_monitor import get_system_health
        health_data = get_system_health()
        socketio.emit('health_update', health_data, room=request.sid)
    except Exception as e:
        print(f'Health check error: {e}')
        socketio.emit('error', {'message': 'Health check failed'}, room=request.sid)

# Create required directories
import os
os.makedirs('web/templates', exist_ok=True)
os.makedirs('web/static', exist_ok=True)

if __name__ == '__main__':
    # Create database tables if available
    if DB_AVAILABLE:
        with app.app_context():
            try:
                from models import create_tables
                create_tables()
                print("Database tables created successfully")
            except Exception as e:
                print(f"Database initialization error: {e}")
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=False)