#!/usr/bin/env python3
"""
Database setup and initialization script for SignalOS
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from models import (
        create_tables, get_db, User, TelegramSession, TelegramChannel, 
        MT5Terminal, Strategy, Signal, Trade, SymbolMapping, SystemHealth, UserSettings
    )
    from werkzeug.security import generate_password_hash
    DATABASE_AVAILABLE = True
    print("Database modules loaded successfully")
except ImportError as e:
    print(f"Database modules not available: {e}")
    DATABASE_AVAILABLE = False
    exit(1)

def create_sample_data():
    """Create sample data for testing and demonstration"""
    db = next(get_db())
    
    try:
        # Create sample user
        demo_user = db.query(User).filter(User.email == 'demo@signalos.com').first()
        if not demo_user:
            demo_user = User(
                email='demo@signalos.com',
                name='Demo User',
                password_hash=generate_password_hash('demo'),
                license_type='pro'
            )
            db.add(demo_user)
            db.commit()
            print("Created demo user")
        
        # Create user settings
        settings = db.query(UserSettings).filter(UserSettings.user_id == demo_user.id).first()
        if not settings:
            settings = UserSettings(user_id=demo_user.id)
            db.add(settings)
            db.commit()
            print("Created user settings")
        
        # Create sample Telegram session
        session = db.query(TelegramSession).filter(TelegramSession.user_id == demo_user.id).first()
        if not session:
            session = TelegramSession(
                user_id=demo_user.id,
                phone_number='+1234567890',
                api_id='12345',
                api_hash='sample_hash',
                status='connected',
                last_activity=datetime.utcnow()
            )
            db.add(session)
            db.commit()
            print("Created Telegram session")
        
        # Create sample channels
        if db.query(TelegramChannel).count() == 0:
            channels = [
                TelegramChannel(
                    session_id=session.id,
                    name='Forex Signals Pro',
                    url='@forex_signals',
                    enabled=True,
                    last_signal=datetime.utcnow() - timedelta(hours=2),
                    total_signals=25
                ),
                TelegramChannel(
                    session_id=session.id,
                    name='Gold Trading Group',
                    url='@gold_trading',
                    enabled=True,
                    last_signal=datetime.utcnow() - timedelta(hours=1),
                    total_signals=18
                )
            ]
            for channel in channels:
                db.add(channel)
            db.commit()
            print("Created sample channels")
        
        # Create sample MT5 terminals
        if db.query(MT5Terminal).count() == 0:
            terminals = [
                MT5Terminal(
                    user_id=demo_user.id,
                    name='MT5 Demo',
                    server='MetaQuotes-Demo',
                    login='12345',
                    password_hash=generate_password_hash('demo123'),
                    balance=10000.0,
                    equity=10150.5,
                    status='connected',
                    risk_type='fixed',
                    risk_value=0.1,
                    last_heartbeat=datetime.utcnow()
                ),
                MT5Terminal(
                    user_id=demo_user.id,
                    name='MT5 Live',
                    server='ICMarkets-Live',
                    login='67890',
                    password_hash=generate_password_hash('live123'),
                    balance=5000.0,
                    equity=4950.0,
                    status='disconnected',
                    risk_type='percent_balance',
                    risk_value=2.0
                )
            ]
            for terminal in terminals:
                db.add(terminal)
            db.commit()
            print("Created sample MT5 terminals")
        
        # Create sample strategies
        if db.query(Strategy).count() == 0:
            strategies = [
                Strategy(
                    user_id=demo_user.id,
                    name='Scalper Pro',
                    description='Quick trades with tight SL/TP',
                    strategy_type='template',
                    active=True,
                    partial_tp=True,
                    sl_to_be=True,
                    trailing_stop=False,
                    max_risk=1.0,
                    tp_ratio=1.5,
                    total_trades=28,
                    winning_trades=20,
                    total_pips=142.5,
                    total_profit=1425.0
                ),
                Strategy(
                    user_id=demo_user.id,
                    name='Swing Trader',
                    description='Medium-term position trading',
                    strategy_type='custom',
                    active=False,
                    partial_tp=False,
                    sl_to_be=True,
                    trailing_stop=True,
                    max_risk=2.0,
                    tp_ratio=3.0,
                    total_trades=17,
                    winning_trades=11,
                    total_pips=89.2,
                    total_profit=892.0
                )
            ]
            for strategy in strategies:
                db.add(strategy)
            db.commit()
            print("Created sample strategies")
        
        # Create sample symbol mappings
        if db.query(SymbolMapping).count() == 0:
            mappings = [
                SymbolMapping(signal_symbol='Gold', mt5_symbol='XAUUSD', pip_value=0.01),
                SymbolMapping(signal_symbol='Silver', mt5_symbol='XAGUSD', pip_value=0.001),
                SymbolMapping(signal_symbol='EURUSD', mt5_symbol='EURUSD', pip_value=0.0001),
                SymbolMapping(signal_symbol='GBPUSD', mt5_symbol='GBPUSD', pip_value=0.0001),
                SymbolMapping(signal_symbol='USDJPY', mt5_symbol='USDJPY', pip_value=0.01)
            ]
            for mapping in mappings:
                db.add(mapping)
            db.commit()
            print("Created symbol mappings")
        
        # Create sample trades for analytics
        if db.query(Trade).count() == 0:
            terminal_id = db.query(MT5Terminal).first().id
            trades_data = [
                ('EURUSD', 'buy', 0.1, 1.0850, 1.0920, 70, 140.0, 'closed'),
                ('XAUUSD', 'sell', 0.02, 2018.50, 2015.30, 32, 320.0, 'closed'),
                ('GBPUSD', 'buy', 0.1, 1.2650, 1.2720, 70, 140.0, 'closed'),
                ('USDJPY', 'sell', 0.1, 149.50, 149.20, 30, 60.0, 'closed'),
                ('EURUSD', 'buy', 0.1, 1.0880, None, 0, 0.0, 'open')
            ]
            
            for i, (pair, action, lot_size, entry, exit_price, pips, profit, status) in enumerate(trades_data):
                trade = Trade(
                    user_id=demo_user.id,
                    terminal_id=terminal_id,
                    pair=pair,
                    action=action,
                    lot_size=lot_size,
                    entry_price=entry,
                    exit_price=exit_price,
                    pips=pips,
                    profit=profit,
                    status=status,
                    opened_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    closed_at=datetime.utcnow() - timedelta(days=random.randint(0, 15)) if status == 'closed' else None,
                    mt5_ticket=f'1234{i+1}',
                    mt5_magic=123456
                )
                db.add(trade)
            db.commit()
            print("Created sample trades")
        
        # Create system health entry
        health = SystemHealth(
            cpu_percent=15.2,
            memory_percent=45.8,
            telegram_connected=True,
            mt5_connected=True,
            parser_running=True,
            signals_processed_today=12,
            errors_today=0
        )
        db.add(health)
        db.commit()
        print("Created system health entry")
        
        print("Sample data creation completed successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main setup function"""
    print("Starting SignalOS database setup...")
    
    if not DATABASE_AVAILABLE:
        print("Database modules not available. Please install dependencies:")
        print("pip install sqlalchemy psycopg2-binary")
        return
    
    # Check database connection
    try:
        db = next(get_db())
        db.execute('SELECT 1')
        print("Database connection successful")
        db.close()
    except Exception as e:
        print(f"Database connection failed: {e}")
        return
    
    # Create tables
    try:
        create_tables()
        print("Database tables created/verified")
    except Exception as e:
        print(f"Error creating tables: {e}")
        return
    
    # Create sample data
    create_sample_data()
    
    print("\nDatabase setup completed!")
    print("Demo login credentials:")
    print("Email: demo@signalos.com")
    print("Password: demo")

if __name__ == "__main__":
    main()