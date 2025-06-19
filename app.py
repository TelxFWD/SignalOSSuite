"""
SignalOS Flask Application Entry Point
Simplified app.py for proper Flask/SQLAlchemy integration
"""

import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
    
    # Proxy fix for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)