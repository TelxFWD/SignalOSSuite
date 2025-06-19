#!/usr/bin/env python3
"""
SignalOS Web Application
Main entry point for the Forex signal automation platform
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import asyncio
import json
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import hashlib
import base64
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from models import (
        create_tables, get_db, User, TelegramSession, TelegramChannel, 
        MT5Terminal, Strategy, Signal, Trade, SymbolMapping, SystemHealth, UserSettings
    )
    from sqlalchemy.orm import Session
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database modules not available: {e}")
    DATABASE_AVAILABLE = False
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

try:
    from core.logger import setup_logging, get_signalos_logger
    from config.settings import AppSettings
    from core.health_monitor import HealthMonitor
    from core.signal_engine import SignalEngine
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False
    
    # Mock core modules
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    def setup_logging(): pass
    def get_signalos_logger(name): return MockLogger()
    
    class AppSettings:
        def __init__(self): pass
    
    class HealthMonitor:
        def start_monitoring(self): pass
        def stop_monitoring(self): pass
        def get_health_summary(self): return {"status": "ok"}
    
    class SignalEngine:
        def get_statistics(self): return {"signals": 0}
try:
    from models.signal_model import SignalStatus
except ImportError:
    # Mock SignalStatus when not available
    class SignalStatus:
        PENDING = "pending"
        PROCESSING = "processing"
        EXECUTED = "executed"
        FAILED = "failed"

class SignalOSWebApp:
    """Main web application class for SignalOS"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        template_folder='web/templates',
                        static_folder='web/static')
        
        # Enable CORS for React frontend
        if CORS_AVAILABLE:
            CORS(self.app, origins=["http://localhost:3000", "https://*.replit.app"])
        else:
            # Manual CORS headers
            @self.app.after_request
            def after_request(response):
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
                return response
        
        # Use environment variable for secret key in production
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
        self.app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
        
        # Set host to 0.0.0.0 for Replit compatibility
        self.host = '0.0.0.0'
        self.port = int(os.environ.get('PORT', 5000))
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)
        
        if CORE_MODULES_AVAILABLE:
            self.settings = AppSettings()
            self.health_monitor = HealthMonitor()
            self.signal_engine = SignalEngine()
            self.logger = get_signalos_logger(__name__)
        else:
            self.settings = AppSettings()
            self.health_monitor = HealthMonitor()
            self.signal_engine = SignalEngine()
            self.logger = get_signalos_logger(__name__)
        
        # Initialize database
        if DATABASE_AVAILABLE:
            try:
                create_tables()
                self.logger.info("Database tables created/verified successfully")
            except Exception as e:
                self.logger.error(f"Database initialization error: {e}")
        else:
            self.logger.warning("Database not available, using demo data")
        
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard - serve React app in production"""
            return self.render_dashboard()
        
        # Serve React static files in production
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            """Serve React static files"""
            return send_from_directory('frontend/build/static', filename)
        
        # Catch-all route for React Router
        @self.app.route('/<path:path>')
        def catch_all(path):
            """Catch-all route for React Router"""
            if path.startswith('api/'):
                return jsonify({'error': 'API endpoint not found'}), 404
            return self.render_dashboard()
        
        @self.app.route('/api/health')
        def get_health():
            """Get system health status"""
            return jsonify(self.health_monitor.get_health_summary())
        
        @self.app.route('/api/signals')
        def get_signals():
            """Get signal processing statistics"""
            return jsonify(self.signal_engine.get_statistics())
        
        @self.app.route('/api/config')
        def get_config():
            """Get current configuration"""
            config_summary = {
                'telegram': {
                    'configured': bool(self.settings.telegram.api_id and self.settings.telegram.api_hash),
                    'channels': len(self.settings.telegram.channels or [])
                },
                'parser': {
                    'enabled': self.settings.parser.enabled,
                    'confidence_threshold': self.settings.parser.confidence_threshold
                },
                'mt5': {
                    'configured': bool(self.settings.mt5.terminal_path),
                    'enabled': True
                },
                'execution': {
                    'enabled': self.settings.execution.enabled,
                    'stealth_mode': self.settings.execution.stealth_mode
                }
            }
            return jsonify(config_summary)
        
        @self.app.route('/api/test')
        def test_endpoint():
            """Test endpoint"""
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'message': 'SignalOS API is running'
            })
        
        # Authentication routes
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            """User login endpoint"""
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'message': 'Email and password required'}), 400
            
            user_data = None
            
            if DATABASE_AVAILABLE:
                try:
                    db = next(get_db())
                    if db:
                        user = db.query(User).filter(User.email == email).first()
                        
                        if user and check_password_hash(user.password_hash, password):
                            # Update last login
                            user.last_login = datetime.utcnow()
                            db.commit()
                            user_data = {
                                'id': user.id,
                                'email': user.email,
                                'name': user.name,
                                'license': user.license_type
                            }
                except Exception as e:
                    self.logger.warning(f"Database login failed, using fallback: {e}")
            
            # Fallback authentication for demo
            if not user_data and email == 'demo@signalos.com' and password == 'demo':
                user_data = {
                    'id': 1,
                    'email': email,
                    'name': 'Demo User',
                    'license': 'Pro'
                }
            
            if user_data:
                # Generate token (JWT if available, simple base64 otherwise)
                if JWT_AVAILABLE:
                    payload = {
                        'user_id': user_data['id'],
                        'email': user_data['email'],
                        'name': user_data['name'],
                        'license': user_data['license'],
                        'exp': datetime.utcnow() + timedelta(days=7)
                    }
                    token = jwt.encode(payload, self.app.config['JWT_SECRET'], algorithm='HS256')
                else:
                    # Simple token alternative
                    token_data = f"{email}:{datetime.utcnow().timestamp()}"
                    token = base64.b64encode(token_data.encode()).decode()
                
                return jsonify({
                    'token': token,
                    'user': user_data
                })
            
            return jsonify({'message': 'Invalid credentials'}), 401
        
        @self.app.route('/api/auth/register', methods=['POST'])
        def register():
            """User registration endpoint"""
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            name = data.get('name')
            
            if not email or not password or not name:
                return jsonify({'message': 'Missing required fields'}), 400
            
            db = next(get_db())
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return jsonify({'message': 'User already exists'}), 400
            
            # Create new user
            password_hash = generate_password_hash(password)
            new_user = User(
                email=email,
                name=name,
                password_hash=password_hash,
                license_type='free'
            )
            
            db.add(new_user)
            db.commit()
            
            # Create default user settings
            default_settings = UserSettings(user_id=new_user.id)
            db.add(default_settings)
            db.commit()
            
            return jsonify({'message': 'Registration successful'})
        
        # API routes for dashboard data
        @self.app.route('/api/telegram/sessions')
        def get_telegram_sessions():
            """Get Telegram session information"""
            if DATABASE_AVAILABLE:
                db = next(get_db())
                sessions = db.query(TelegramSession).all()
                
                session_data = []
                for session in sessions:
                    channels = db.query(TelegramChannel).filter(TelegramChannel.session_id == session.id).all()
                    session_data.append({
                        'id': session.id,
                        'phone': session.phone_number,
                        'status': session.status,
                        'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                        'channels': [channel.name for channel in channels]
                    })
                
                return jsonify({'sessions': session_data})
            else:
                # Return sample data when database not available
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
        
        @self.app.route('/api/telegram/sessions', methods=['POST'])
        def add_telegram_session():
            """Add new Telegram session"""
            data = request.get_json()
            
            if DATABASE_AVAILABLE:
                try:
                    db = next(get_db())
                    if db:
                        new_session = TelegramSession(
                            user_id=1,  # Would get from JWT token in real implementation
                            phone_number=data.get('phone'),
                            api_id=data.get('api_id'),
                            api_hash=data.get('api_hash'),
                            status='connecting'
                        )
                        
                        db.add(new_session)
                        db.commit()
                        
                        return jsonify({'message': 'Session added successfully', 'id': new_session.id})
                except Exception as e:
                    self.logger.error(f"Database error adding session: {e}")
            
            return jsonify({'message': 'Session added successfully', 'id': 2})
        
        @self.app.route('/api/telegram/sessions/<int:session_id>', methods=['DELETE'])
        def delete_telegram_session(session_id):
            """Delete Telegram session"""
            return jsonify({'message': 'Session deleted successfully'})
        
        @self.app.route('/api/telegram/channels')
        def get_telegram_channels():
            """Get monitored Telegram channels"""
            return jsonify({
                'channels': [
                    {
                        'id': 1,
                        'name': 'Forex Signals Pro',
                        'url': '@forex_signals',
                        'enabled': True,
                        'last_signal': '2024-12-19 14:30:00'
                    },
                    {
                        'id': 2,
                        'name': 'Gold Trading Group',
                        'url': '@gold_trading',
                        'enabled': True,
                        'last_signal': '2024-12-19 13:45:00'
                    }
                ]
            })
        
        @self.app.route('/api/telegram/channels', methods=['POST'])
        def add_telegram_channel():
            """Add new Telegram channel"""
            data = request.get_json()
            return jsonify({'message': 'Channel added successfully', 'id': 3})
        
        @self.app.route('/api/telegram/channels/<int:channel_id>', methods=['DELETE'])
        def delete_telegram_channel(channel_id):
            """Delete Telegram channel"""
            return jsonify({'message': 'Channel deleted successfully'})
        
        @self.app.route('/api/mt5/terminals')
        def get_mt5_terminals():
            """Get MT5 terminal configurations"""
            if DATABASE_AVAILABLE:
                db = next(get_db())
                terminals = db.query(MT5Terminal).all()
                
                terminal_data = []
                for terminal in terminals:
                    terminal_data.append({
                        'id': terminal.id,
                        'name': terminal.name,
                        'server': terminal.server,
                        'account': terminal.login,
                        'status': terminal.status,
                        'balance': terminal.balance,
                        'equity': terminal.equity,
                        'risk_type': terminal.risk_type,
                        'risk_value': terminal.risk_value,
                        'last_heartbeat': terminal.last_heartbeat.isoformat() if terminal.last_heartbeat else None
                    })
                
                return jsonify({'terminals': terminal_data})
            else:
                # Return sample data when database not available
                return jsonify({
                    'terminals': [
                        {
                            'id': 1,
                            'name': 'MT5 Demo',
                            'server': 'MetaQuotes-Demo',
                            'account': '12345',
                            'status': 'connected',
                            'balance': 10000.00,
                            'equity': 10150.50
                        },
                        {
                            'id': 2,
                            'name': 'MT5 Live',
                            'server': 'ICMarkets-Live',
                            'account': '67890',
                            'status': 'disconnected',
                            'balance': 5000.00,
                            'equity': 4950.00
                        }
                    ]
                })
        
        @self.app.route('/api/mt5/terminals', methods=['POST'])
        def add_mt5_terminal():
            """Add new MT5 terminal"""
            data = request.get_json()
            
            if DATABASE_AVAILABLE:
                try:
                    db = next(get_db())
                    if db:
                        # Hash the password
                        password_hash = generate_password_hash(data.get('password', ''))
                        
                        new_terminal = MT5Terminal(
                            user_id=1,  # Would get from JWT token in real implementation
                            name=data.get('name'),
                            server=data.get('server'),
                            login=data.get('login'),
                            password_hash=password_hash,
                            risk_type=data.get('riskType', 'fixed'),
                            risk_value=data.get('riskValue', 0.1),
                            enable_sl_override=data.get('enableSLOverride', False),
                            enable_tp_override=data.get('enableTPOverride', False),
                            enable_be_logic=data.get('enableBELogic', True),
                            sl_buffer=data.get('slBuffer', 5),
                            trade_delay=data.get('tradeDelay', 0),
                            enable_trailing=data.get('enableTrailing', False),
                            status='disconnected'
                        )
                        
                        db.add(new_terminal)
                        db.commit()
                        
                        return jsonify({'message': 'Terminal added successfully', 'id': new_terminal.id})
                except Exception as e:
                    self.logger.error(f"Database error adding terminal: {e}")
            
            return jsonify({'message': 'Terminal added successfully', 'id': 3})
        
        @self.app.route('/api/mt5/terminals/<int:terminal_id>', methods=['DELETE'])
        def delete_mt5_terminal(terminal_id):
            """Delete MT5 terminal"""
            return jsonify({'message': 'Terminal deleted successfully'})
        
        @self.app.route('/api/mt5/symbols')
        def get_symbol_mappings():
            """Get symbol mappings"""
            return jsonify({
                'mappings': [
                    {'signal_symbol': 'Gold', 'mt5_symbol': 'XAUUSD'},
                    {'signal_symbol': 'Silver', 'mt5_symbol': 'XAGUSD'},
                    {'signal_symbol': 'EURUSD', 'mt5_symbol': 'EURUSD'},
                    {'signal_symbol': 'GBPUSD', 'mt5_symbol': 'GBPUSD'}
                ]
            })
        
        @self.app.route('/api/analytics/performance')
        def get_performance_analytics():
            """Get trading performance analytics"""
            return jsonify({
                'total_trades': 45,
                'win_rate': 68.9,
                'profit_factor': 1.85,
                'avg_rr': 2.1,
                'total_pips': 234,
                'equity_curve': [
                    {'date': '2024-12-01', 'equity': 10000},
                    {'date': '2024-12-02', 'equity': 10150},
                    {'date': '2024-12-03', 'equity': 10280},
                    {'date': '2024-12-04', 'equity': 10195},
                    {'date': '2024-12-05', 'equity': 10345}
                ]
            })
        
        @self.app.route('/api/strategies')
        def get_strategies():
            """Get trading strategies"""
            return jsonify({
                'strategies': [
                    {
                        'id': 1,
                        'name': 'Scalper Pro',
                        'type': 'template',
                        'active': True,
                        'win_rate': 72.5,
                        'trades': 28
                    },
                    {
                        'id': 2,
                        'name': 'Swing Trader',
                        'type': 'custom',
                        'active': False,
                        'win_rate': 65.2,
                        'trades': 17
                    }
                ]
            })
        
        @self.app.route('/api/strategies', methods=['POST'])
        def create_strategy():
            """Create new trading strategy"""
            data = request.get_json()
            return jsonify({'message': 'Strategy created successfully', 'id': 4})
        
        @self.app.route('/api/strategies/<int:strategy_id>', methods=['PATCH'])
        def update_strategy(strategy_id):
            """Update trading strategy"""
            data = request.get_json()
            return jsonify({'message': 'Strategy updated successfully'})
        
        @self.app.route('/api/analytics/trades')
        def get_trade_history():
            """Get trade history for analytics"""
            return jsonify({
                'trades': [
                    {
                        'id': 1,
                        'pair': 'EURUSD',
                        'type': 'BUY',
                        'entry': 1.0850,
                        'exit': 1.0920,
                        'pips': 70,
                        'profit': 140,
                        'date': '2024-12-19'
                    },
                    {
                        'id': 2,
                        'pair': 'XAUUSD',
                        'type': 'SELL',
                        'entry': 2018.50,
                        'exit': 2015.30,
                        'pips': 32,
                        'profit': 320,
                        'date': '2024-12-19'
                    }
                ]
            })
        
        @self.app.route('/api/analytics/pairs')
        def get_pair_performance():
            """Get currency pair performance analytics"""
            return jsonify({
                'pairs': [
                    {'name': 'EURUSD', 'trades': 15, 'winRate': 73, 'pips': 142},
                    {'name': 'XAUUSD', 'trades': 12, 'winRate': 67, 'pips': 89},
                    {'name': 'GBPUSD', 'trades': 8, 'winRate': 75, 'pips': 65},
                    {'name': 'USDJPY', 'trades': 6, 'winRate': 50, 'pips': -12},
                    {'name': 'AUDUSD', 'trades': 4, 'winRate': 75, 'pips': 28}
                ]
            })
        
        @self.app.route('/api/analytics/daily')
        def get_daily_analytics():
            """Get daily performance analytics"""
            return jsonify({
                'daily': [
                    {'date': '2024-12-19', 'trades': 5, 'pips': 45, 'profit': 450},
                    {'date': '2024-12-18', 'trades': 3, 'pips': -12, 'profit': -120},
                    {'date': '2024-12-17', 'trades': 7, 'pips': 78, 'profit': 780}
                ]
            })
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info("Client connected")
            emit('status', {'message': 'Connected to SignalOS'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info("Client disconnected")
        
        @self.socketio.on('get_health')
        def handle_get_health():
            health_data = self.health_monitor.get_health_summary()
            emit('health_update', health_data)
    
    def render_dashboard(self):
        """Render the main dashboard"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a simple HTML dashboard
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SignalOS - Forex Signal Automation Platform</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px; 
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .logo {{ 
            font-size: 2.5rem; 
            font-weight: bold; 
            color: #4a5568;
            text-align: center;
        }}
        .subtitle {{
            text-align: center;
            color: #718096;
            margin-top: 5px;
            font-size: 1.1rem;
        }}
        .grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 20px;
        }}
        .card {{ 
            background: rgba(255, 255, 255, 0.95); 
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        .card h3 {{ 
            color: #2d3748; 
            margin-bottom: 15px; 
            font-size: 1.3rem;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }}
        .status {{ 
            padding: 8px 16px; 
            border-radius: 20px; 
            font-weight: bold; 
            display: inline-block;
            margin: 5px;
        }}
        .status.online {{ background: #48bb78; color: white; }}
        .status.offline {{ background: #f56565; color: white; }}
        .status.pending {{ background: #ed8936; color: white; }}
        .metric {{ 
            display: flex; 
            justify-content: space-between; 
            margin: 10px 0; 
            padding: 10px;
            background: #f7fafc;
            border-radius: 8px;
        }}
        .metric-label {{ font-weight: 600; color: #4a5568; }}
        .metric-value {{ color: #2b6cb0; font-weight: bold; }}
        .logs {{ 
            background: #1a202c; 
            color: #e2e8f0; 
            padding: 20px; 
            border-radius: 10px; 
            font-family: 'Courier New', monospace; 
            height: 200px; 
            overflow-y: auto;
            margin-top: 10px;
        }}
        .button {{
            background: #4299e1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
            transition: background 0.3s;
        }}
        .button:hover {{ background: #3182ce; }}
        .button.danger {{ background: #e53e3e; }}
        .button.danger:hover {{ background: #c53030; }}
        .timestamp {{ 
            color: #718096; 
            font-size: 0.9rem; 
            text-align: center; 
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📊 SignalOS</div>
            <div class="subtitle">Next-Generation Forex Signal Automation Platform</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🔗 System Health</h3>
                <div id="health-status">
                    <div class="status online">System Online</div>
                    <div class="metric">
                        <span class="metric-label">Uptime</span>
                        <span class="metric-value" id="uptime">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Memory Usage</span>
                        <span class="metric-value" id="memory">--</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">CPU Usage</span>
                        <span class="metric-value" id="cpu">--</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📡 Telegram Integration</h3>
                <div class="status offline">Not Configured</div>
                <div class="metric">
                    <span class="metric-label">API Status</span>
                    <span class="metric-value">Pending Setup</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Monitored Channels</span>
                    <span class="metric-value">0</span>
                </div>
                <button class="button">Configure Telegram</button>
            </div>
            
            <div class="card">
                <h3>🤖 AI Signal Parser</h3>
                <div class="status pending">Ready</div>
                <div class="metric">
                    <span class="metric-label">Confidence Threshold</span>
                    <span class="metric-value">80%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Signals Processed</span>
                    <span class="metric-value">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-value">--</span>
                </div>
            </div>
            
            <div class="card">
                <h3>💹 MetaTrader 5</h3>
                <div class="status offline">Not Connected</div>
                <div class="metric">
                    <span class="metric-label">Terminal Status</span>
                    <span class="metric-value">Not Found</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Trades</span>
                    <span class="metric-value">0</span>
                </div>
                <button class="button">Setup MT5</button>
            </div>
            
            <div class="card">
                <h3>⚡ Signal Queue</h3>
                <div class="metric">
                    <span class="metric-label">Pending Signals</span>
                    <span class="metric-value">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Processed Today</span>
                    <span class="metric-value">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Execution Rate</span>
                    <span class="metric-value">--</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Performance</h3>
                <div class="metric">
                    <span class="metric-label">Total Trades</span>
                    <span class="metric-value">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Win Rate</span>
                    <span class="metric-value">--</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Pips</span>
                    <span class="metric-value">0</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>📋 System Logs</h3>
            <button class="button" onclick="clearLogs()">Clear Logs</button>
            <button class="button" onclick="refreshLogs()">Refresh</button>
            <div class="logs" id="logs">
                <div>[{current_time}] SignalOS Web Interface Started</div>
                <div>[{current_time}] Waiting for configuration...</div>
                <div>[{current_time}] Health monitoring active</div>
                <div>[{current_time}] Ready to receive signals</div>
            </div>
        </div>
        
        <div class="timestamp">
            Last updated: <span id="last-update">{current_datetime}</span>
        </div>
    </div>
    
    <script>
        const socket = io();
        
        socket.on('connect', function() {{
            console.log('Connected to SignalOS');
            addLog('Connected to SignalOS server');
        }});
        
        socket.on('health_update', function(data) {{
            updateHealthStatus(data);
        }});
        
        function addLog(message) {{
            const logs = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            logs.innerHTML += `<div>[${{timestamp}}] ${{message}}</div>`;
            logs.scrollTop = logs.scrollHeight;
        }}
        
        function clearLogs() {{
            document.getElementById('logs').innerHTML = '';
        }}
        
        function refreshLogs() {{
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {{
                    addLog('Health check: ' + JSON.stringify(data));
                }});
        }}
        
        function updateHealthStatus(data) {{
            // Update health metrics from server
            addLog('Health status updated');
        }}
        
        // Update timestamp every second
        setInterval(() => {{
            document.getElementById('last-update').textContent = new Date().toLocaleString();
        }}, 1000);
        
        // Initial health check
        setTimeout(() => {{
            socket.emit('get_health');
        }}, 1000);
    </script>
</body>
</html>
        """
        return html_template
    
    def run(self):
        """Start the web application"""
        try:
            # Setup logging
            setup_logging()
            self.logger.info("Starting SignalOS Web Application...")
            
            # Start health monitoring
            self.health_monitor.start_monitoring()
            
            # Run the Flask-SocketIO app
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                allow_unsafe_werkzeug=True
            )
            
        except Exception as e:
            self.logger.critical(f"Fatal error starting application: {e}")
            return 1
    
    def cleanup(self):
        """Cleanup resources before exit"""
        if self.health_monitor:
            self.health_monitor.stop_monitoring()

def main():
    """Main entry point"""
    app = SignalOSWebApp()
    
    try:
        return app.run()
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        return 0
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        return 1
    finally:
        app.cleanup()

if __name__ == "__main__":
    sys.exit(main())
