"""
SignalOS Flask Application Entry Point
Simplified app.py for proper Flask/SQLAlchemy integration
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static')

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # Fallback to SQLite for development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///signalos.db"

# Initialize extensions
db.init_app(app)
CORS(app, origins=["*"])
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Import models and create tables
with app.app_context():
    try:
        import models
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")