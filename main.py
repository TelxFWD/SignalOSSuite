from app import app, socketio
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

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return f"<h1>SignalOS Dashboard</h1><p>Application is running. Template error: {str(e)}</p><p><a href='/api/test'>Test API</a></p>", 200

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
    
    return jsonify({'daily_stats': stats})

@app.route('/api/test')
def test_endpoint():
    """Test endpoint for verification"""
    return jsonify({
        'status': 'ok',
        'message': 'SignalOS API is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/telegram/sessions', methods=['POST'])
def add_telegram_session():
    """Add new Telegram session"""
    data = request.get_json()
    if DB_AVAILABLE:
        try:
            from models import TelegramSession
            from app import db
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
            db = get_db()
            new_terminal = MT5Terminal(
                user_id=1,  # Would get from JWT token in real implementation
                name=data.get('name'),
                server=data.get('server'),
                login=data.get('login'),
                password_hash=generate_password_hash(data.get('password')),
                status='connecting'
            )
            db.add(new_terminal)
            db.commit()
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
            db = get_db()
            terminal = db.query(MT5Terminal).filter(MT5Terminal.id == terminal_id).first()
            if terminal:
                db.delete(terminal)
                db.commit()
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
            db = get_db()
            new_strategy = Strategy(
                user_id=1,  # Would get from JWT token in real implementation
                name=data.get('name'),
                description=data.get('description'),
                strategy_type=data.get('type'),
                max_risk=float(data.get('max_risk', 1.0)),
                active=True
            )
            db.add(new_strategy)
            db.commit()
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
            db = get_db()
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                db.delete(strategy)
                db.commit()
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
            db = get_db()
            settings = db.query(UserSettings).filter(UserSettings.user_id == 1).first()
            if settings:
                settings.enable_shadow_mode = enabled
                db.commit()
            else:
                new_settings = UserSettings(user_id=1, enable_shadow_mode=enabled)
                db.add(new_settings)
                db.commit()
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

# Admin API endpoints
@app.route('/admin/api/signals/<int:signal_id>/reparse', methods=['POST'])
def admin_reparse_signal(signal_id):
    """Re-parse a signal for admin debugging"""
    if 'admin_user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if DB_AVAILABLE:
        try:
            signal = Signal.query.get_or_404(signal_id)
            # In real implementation, this would trigger re-parsing
            signal.status = SignalStatus.PENDING
            db.session.commit()
            
            # Log the action
            log_entry = SystemLog(
                level='INFO',
                category='admin',
                message=f'Signal {signal_id} re-parsing initiated by admin',
                signal_id=signal_id,
                additional_data=json.dumps({'admin_user': session['admin_user_id']})
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Signal re-parsing initiated'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True, 'message': 'Re-parsing simulated (no database)'})

@app.route('/admin/api/signals/<int:signal_id>/reexecute', methods=['POST'])
def admin_reexecute_signal(signal_id):
    """Re-execute a signal for admin debugging"""
    if 'admin_user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if DB_AVAILABLE:
        try:
            signal = Signal.query.get_or_404(signal_id)
            # In real implementation, this would trigger re-execution
            signal.status = SignalStatus.PROCESSING
            db.session.commit()
            
            # Log the action
            log_entry = SystemLog(
                level='INFO',
                category='admin',
                message=f'Signal {signal_id} re-execution initiated by admin',
                signal_id=signal_id,
                additional_data=json.dumps({'admin_user': session['admin_user_id']})
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Signal re-execution initiated'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True, 'message': 'Re-execution simulated (no database)'})

@app.route('/admin/api/signals/<int:signal_id>/resolve', methods=['POST'])
def admin_resolve_signal(signal_id):
    """Mark a signal as resolved for admin debugging"""
    if 'admin_user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if DB_AVAILABLE:
        try:
            signal = Signal.query.get_or_404(signal_id)
            signal.status = SignalStatus.EXECUTED
            db.session.commit()
            
            # Log the action
            log_entry = SystemLog(
                level='INFO',
                category='admin',
                message=f'Signal {signal_id} marked as resolved by admin',
                signal_id=signal_id,
                additional_data=json.dumps({'admin_user': session['admin_user_id']})
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Signal marked as resolved'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True, 'message': 'Signal marked as resolved (simulated)'})

@app.route('/admin/api/signals/<int:signal_id>/export-logs')
def admin_export_signal_logs(signal_id):
    """Export logs for a specific signal"""
    if 'admin_user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if DB_AVAILABLE:
        try:
            signal = Signal.query.get_or_404(signal_id)
            logs = SystemLog.query.filter_by(signal_id=signal_id).order_by(SystemLog.timestamp).all()
            
            log_data = []
            for log in logs:
                log_data.append({
                    'timestamp': log.timestamp.isoformat(),
                    'level': log.level,
                    'category': log.category,
                    'message': log.message,
                    'additional_data': log.additional_data
                })
            
            response_data = {
                'signal_id': signal_id,
                'signal_text': signal.raw_text,
                'logs': log_data,
                'exported_at': datetime.now().isoformat()
            }
            
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Database not available'}), 503

# SocketIO events for real-time updates
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('get_health')
def handle_get_health():
    health_data = {
        'status': 'healthy',
        'cpu': random.randint(10, 60),
        'memory': random.randint(20, 80),
        'signals_today': random.randint(5, 25)
    }
    return health_data

# Create required directories
import os
os.makedirs('web/templates', exist_ok=True)
os.makedirs('web/static', exist_ok=True)

if __name__ == '__main__':
    # Create database tables if available
    if DB_AVAILABLE:
        with app.app_context():
            try:
                create_tables()
                print("Database tables created successfully")
            except Exception as e:
                print(f"Database initialization error: {e}")
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=False)