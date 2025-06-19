"""
Database models for SignalOS
"""

from datetime import datetime
from enum import Enum
import os
try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.dialects.postgresql import UUID
    import uuid
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # Mock SQLAlchemy components when not available
    SQLALCHEMY_AVAILABLE = False
    
    class MockBase:
        pass
    
    def declarative_base():
        return MockBase
    
    def Column(*args, **kwargs):
        return None
    
    def Integer():
        return None
    
    def String(length=None):
        return None
    
    def Float():
        return None
    
    def Boolean():
        return None
    
    def DateTime():
        return None
    
    def Text():
        return None
    
    def ForeignKey(ref):
        return None
    
    def relationship(model, **kwargs):
        return None
    
    def sessionmaker(**kwargs):
        return lambda: None
    
    def create_engine(url):
        return None
    
    class SQLEnum:
        def __init__(self, enum_class):
            self.enum_class = enum_class

Base = declarative_base()

# Create database engine
if SQLALCHEMY_AVAILABLE:
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        try:
            engine = create_engine(DATABASE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        except Exception as e:
            print(f"Database connection failed: {e}")
            engine = None
            SessionLocal = None
    else:
        engine = None
        SessionLocal = None
else:
    engine = None
    SessionLocal = None

class SignalStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SignalAction(Enum):
    BUY = "buy"
    SELL = "sell"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    license_type = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    telegram_sessions = relationship("TelegramSession", back_populates="user")
    mt5_terminals = relationship("MT5Terminal", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    trades = relationship("Trade", back_populates="user")

class TelegramSession(Base):
    __tablename__ = "telegram_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    api_id = Column(String(50), nullable=False)
    api_hash = Column(String(255), nullable=False)
    session_string = Column(Text)
    status = Column(String(20), default="disconnected")
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="telegram_sessions")
    channels = relationship("TelegramChannel", back_populates="session")

class TelegramChannel(Base):
    __tablename__ = "telegram_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("telegram_sessions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    channel_id = Column(String(50))
    enabled = Column(Boolean, default=True)
    last_signal = Column(DateTime)
    total_signals = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("TelegramSession", back_populates="channels")
    signals = relationship("Signal", back_populates="channel")

class MT5Terminal(Base):
    __tablename__ = "mt5_terminals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    server = Column(String(255), nullable=False)
    login = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    terminal_path = Column(String(500))
    status = Column(String(20), default="disconnected")
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    risk_type = Column(String(20), default="fixed")  # fixed, percent_balance, percent_equity
    risk_value = Column(Float, default=0.1)
    enable_sl_override = Column(Boolean, default=False)
    enable_tp_override = Column(Boolean, default=False)
    enable_be_logic = Column(Boolean, default=True)
    sl_buffer = Column(Integer, default=5)
    trade_delay = Column(Integer, default=0)
    max_spread = Column(Float, default=3.0)
    enable_trailing = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="mt5_terminals")
    trades = relationship("Trade", back_populates="terminal")

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(20), nullable=False)  # beginner, pro
    active = Column(Boolean, default=True)
    
    # Beginner mode settings
    partial_tp = Column(Boolean, default=False)
    sl_to_be = Column(Boolean, default=True)
    trailing_stop = Column(Boolean, default=False)
    max_risk = Column(Float, default=1.0)
    tp_ratio = Column(Float, default=2.0)
    
    # Custom rules (JSON stored as text for pro mode)
    custom_rules = Column(Text)
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pips = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="strategies")

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("telegram_channels.id"), nullable=False)
    
    # Signal content
    raw_text = Column(Text, nullable=False)
    parsed_pair = Column(String(10))
    parsed_action = Column(SQLEnum(SignalAction))
    parsed_entry = Column(Float)
    parsed_sl = Column(Float)
    parsed_tp = Column(Float)
    parsed_tp2 = Column(Float)
    parsed_tp3 = Column(Float)
    
    # Processing info
    confidence_score = Column(Float, default=0.0)
    status = Column(SQLEnum(SignalStatus), default=SignalStatus.PENDING)
    error_message = Column(Text)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    executed_at = Column(DateTime)
    
    # Relationships
    channel = relationship("TelegramChannel", back_populates="signals")
    trades = relationship("Trade", back_populates="signal")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    terminal_id = Column(Integer, ForeignKey("mt5_terminals.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    
    # Trade details
    pair = Column(String(10), nullable=False)
    action = Column(SQLEnum(SignalAction), nullable=False)
    lot_size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    sl_price = Column(Float)
    tp_price = Column(Float)
    
    # Trade results
    pips = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)
    status = Column(String(20), default="open")  # open, closed, cancelled
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # MT5 specific
    mt5_ticket = Column(String(50))
    mt5_magic = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    terminal = relationship("MT5Terminal", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")

class SymbolMapping(Base):
    __tablename__ = "symbol_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_symbol = Column(String(50), nullable=False)
    mt5_symbol = Column(String(50), nullable=False)
    multiplier = Column(Float, default=1.0)
    pip_value = Column(Float, default=0.0001)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemHealth(Base):
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float, default=0.0)
    memory_percent = Column(Float, default=0.0)
    telegram_connected = Column(Boolean, default=False)
    mt5_connected = Column(Boolean, default=False)
    parser_running = Column(Boolean, default=False)
    signals_processed_today = Column(Integer, default=0)
    errors_today = Column(Integer, default=0)

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # General settings
    theme = Column(String(20), default="dark")
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    auto_sync = Column(Boolean, default=True)
    notifications = Column(Boolean, default=True)
    
    # Trading settings
    default_risk = Column(Float, default=1.0)
    max_daily_loss = Column(Float, default=5.0)
    trading_hours_start = Column(String(10), default="08:00")
    trading_hours_end = Column(String(10), default="17:00")
    enable_shadow_mode = Column(Boolean, default=False)
    confirm_trades = Column(Boolean, default=True)
    
    # Notification settings
    telegram_notifications = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=True)
    webhook_url = Column(String(500))
    
    # Security settings
    two_factor_auth = Column(Boolean, default=False)
    session_timeout = Column(Integer, default=30)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def create_tables():
    """Create all database tables"""
    if SQLALCHEMY_AVAILABLE and engine:
        Base.metadata.create_all(bind=engine)
    else:
        print("Database not available - tables not created")

def get_db():
    """Get database session"""
    if SQLALCHEMY_AVAILABLE and SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!" if SQLALCHEMY_AVAILABLE else "Database not available")