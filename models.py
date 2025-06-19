"""
Database models for SignalOS
"""
from datetime import datetime
from enum import Enum
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class SignalStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SignalAction(Enum):
    BUY = "buy"
    SELL = "sell"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    license_type = db.Column(db.String(50), default="free")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    telegram_sessions = db.relationship("TelegramSession", back_populates="user")
    mt5_terminals = db.relationship("MT5Terminal", back_populates="user")
    strategies = db.relationship("Strategy", back_populates="user")
    trades = db.relationship("Trade", back_populates="user")

class TelegramSession(db.Model):
    __tablename__ = "telegram_sessions"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    api_id = db.Column(db.String(50), nullable=False)
    api_hash = db.Column(db.String(255), nullable=False)
    session_string = db.Column(db.Text)
    status = db.Column(db.String(20), default="disconnected")
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", back_populates="telegram_sessions")
    channels = db.relationship("TelegramChannel", back_populates="session")

class TelegramChannel(db.Model):
    __tablename__ = "telegram_channels"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("telegram_sessions.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    channel_id = db.Column(db.String(50))
    enabled = db.Column(db.Boolean, default=True)
    last_signal = db.Column(db.DateTime)
    total_signals = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    session = db.relationship("TelegramSession", back_populates="channels")
    signals = db.relationship("Signal", back_populates="channel")

class MT5Terminal(db.Model):
    __tablename__ = "mt5_terminals"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    server = db.Column(db.String(255), nullable=False)
    login = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    terminal_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default="disconnected")
    balance = db.Column(db.Float, default=0.0)
    equity = db.Column(db.Float, default=0.0)
    risk_type = db.Column(db.String(20), default="fixed")
    risk_value = db.Column(db.Float, default=0.1)
    enable_sl_override = db.Column(db.Boolean, default=False)
    enable_tp_override = db.Column(db.Boolean, default=False)
    enable_be_logic = db.Column(db.Boolean, default=True)
    sl_buffer = db.Column(db.Integer, default=5)
    trade_delay = db.Column(db.Integer, default=0)
    max_spread = db.Column(db.Float, default=3.0)
    enable_trailing = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_heartbeat = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship("User", back_populates="mt5_terminals")
    trades = db.relationship("Trade", back_populates="terminal")

class Strategy(db.Model):
    __tablename__ = "strategies"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    strategy_type = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    # Risk management
    partial_tp = db.Column(db.Boolean, default=False)
    sl_to_be = db.Column(db.Boolean, default=True)
    trailing_stop = db.Column(db.Boolean, default=False)
    max_risk = db.Column(db.Float, default=1.0)
    tp_ratio = db.Column(db.Float, default=2.0)
    
    # Custom rules
    custom_rules = db.Column(db.Text)
    
    # Performance tracking
    total_trades = db.Column(db.Integer, default=0)
    winning_trades = db.Column(db.Integer, default=0)
    total_pips = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", back_populates="strategies")

class Signal(db.Model):
    __tablename__ = "signals"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    channel_id = db.Column(db.Integer, db.ForeignKey("telegram_channels.id"), nullable=False)
    
    # Raw signal data
    raw_text = db.Column(db.Text, nullable=False)
    parsed_pair = db.Column(db.String(10))
    parsed_action = db.Column(db.Enum(SignalAction))
    parsed_entry = db.Column(db.Float)
    parsed_sl = db.Column(db.Float)
    parsed_tp = db.Column(db.Float)
    parsed_tp2 = db.Column(db.Float)
    parsed_tp3 = db.Column(db.Float)
    
    # Processing metadata
    confidence_score = db.Column(db.Float, default=0.0)
    status = db.Column(db.Enum(SignalStatus), default=SignalStatus.PENDING)
    error_message = db.Column(db.Text)
    
    # Timestamps
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    executed_at = db.Column(db.DateTime)
    
    # Relationships
    channel = db.relationship("TelegramChannel", back_populates="signals")
    trades = db.relationship("Trade", back_populates="signal")

class Trade(db.Model):
    __tablename__ = "trades"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    terminal_id = db.Column(db.Integer, db.ForeignKey("mt5_terminals.id"), nullable=False)
    signal_id = db.Column(db.Integer, db.ForeignKey("signals.id"))
    
    # Trade details
    pair = db.Column(db.String(10), nullable=False)
    action = db.Column(db.Enum(SignalAction), nullable=False)
    lot_size = db.Column(db.Float, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float)
    sl_price = db.Column(db.Float)
    tp_price = db.Column(db.Float)
    
    # Performance
    pips = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="open")
    
    # Timestamps
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # MT5 integration
    mt5_ticket = db.Column(db.String(50))
    mt5_magic = db.Column(db.Integer)
    
    # Relationships
    user = db.relationship("User", back_populates="trades")
    terminal = db.relationship("MT5Terminal", back_populates="trades")
    signal = db.relationship("Signal", back_populates="trades")

class SymbolMapping(db.Model):
    __tablename__ = "symbol_mappings"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    signal_symbol = db.Column(db.String(50), nullable=False)
    mt5_symbol = db.Column(db.String(50), nullable=False)
    multiplier = db.Column(db.Float, default=1.0)
    pip_value = db.Column(db.Float, default=0.0001)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemHealth(db.Model):
    __tablename__ = "system_health"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_percent = db.Column(db.Float, default=0.0)
    memory_percent = db.Column(db.Float, default=0.0)
    telegram_connected = db.Column(db.Boolean, default=False)
    mt5_connected = db.Column(db.Boolean, default=False)
    parser_running = db.Column(db.Boolean, default=False)
    signals_processed_today = db.Column(db.Integer, default=0)
    errors_today = db.Column(db.Integer, default=0)

class UserSettings(db.Model):
    __tablename__ = "user_settings"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    
    # UI preferences
    theme = db.Column(db.String(20), default="dark")
    language = db.Column(db.String(10), default="en")
    timezone = db.Column(db.String(50), default="UTC")
    auto_sync = db.Column(db.Boolean, default=True)
    notifications = db.Column(db.Boolean, default=True)
    
    # Trading preferences
    default_risk = db.Column(db.Float, default=1.0)
    max_daily_loss = db.Column(db.Float, default=5.0)
    trading_hours_start = db.Column(db.String(10), default="08:00")
    trading_hours_end = db.Column(db.String(10), default="17:00")
    enable_shadow_mode = db.Column(db.Boolean, default=False)
    confirm_trades = db.Column(db.Boolean, default=True)
    
    # Notification settings
    telegram_notifications = db.Column(db.Boolean, default=True)
    email_alerts = db.Column(db.Boolean, default=True)
    webhook_url = db.Column(db.String(500))
    
    # Security settings
    two_factor_auth = db.Column(db.Boolean, default=False)
    session_timeout = db.Column(db.Integer, default=30)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Utility functions
def create_tables():
    """Create all database tables"""
    db.create_all()

def get_db():
    """Get database session"""
    return db.session