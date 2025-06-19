from app import app, socketio
from flask import render_template, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import random

# Import models for database operations
try:
    from models import User, TelegramSession, TelegramChannel, MT5Terminal, Strategy, Signal, Trade, get_db, create_tables
    from app import db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

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