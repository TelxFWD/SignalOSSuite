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

try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Installing Flask dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio"])
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_socketio import SocketIO, emit

from core.logger import setup_logging, get_signalos_logger
from config.settings import AppSettings
from core.health_monitor import HealthMonitor
from core.signal_engine import SignalEngine
from models.signal_model import SignalStatus

class SignalOSWebApp:
    """Main web application class for SignalOS"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        template_folder='web/templates',
                        static_folder='web/static')
        self.app.config['SECRET_KEY'] = 'signalos-secret-key-2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.settings = AppSettings()
        self.health_monitor = HealthMonitor()
        self.signal_engine = SignalEngine()
        self.logger = get_signalos_logger(__name__)
        
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard"""
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
                host='0.0.0.0',
                port=5000,
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
