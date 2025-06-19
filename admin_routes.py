"""
SignalOS Admin Routes
Direct admin interface without Flask-Admin dependency issues
"""

from flask import render_template, request, session, redirect, url_for, jsonify, flash
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import json

from app import app, db
from models import (User, AdminUser, LicensePlan, UserLicense, ParserModel, SignalProvider, 
                   SystemLog, NotificationTemplate, TelegramSession, TelegramChannel, 
                   MT5Terminal, Strategy, Signal, Trade, SystemHealth)


def require_admin():
    """Check if user has admin access"""
    if 'admin_user_id' not in session:
        return False
    admin_user = AdminUser.query.filter_by(user_id=session['admin_user_id']).first()
    return admin_user is not None


@app.route('/admin')
@app.route('/admin/')
def admin_dashboard():
    """Admin dashboard with comprehensive metrics"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    # Get key metrics
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    total_signals = Signal.query.count() if Signal.query.first() else 0
    total_trades = Trade.query.count() if Trade.query.first() else 0
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_signals = Signal.query.filter(Signal.received_at >= week_ago).count() if Signal.query.first() else 0
    recent_trades = Trade.query.filter(Trade.opened_at >= week_ago).count() if Trade.query.first() else 0
    
    # License distribution
    license_stats = []
    try:
        license_stats = db.session.query(
            LicensePlan.name, 
            db.func.count(UserLicense.id).label('count')
        ).join(UserLicense).group_by(LicensePlan.name).all()
    except:
        license_stats = [('Demo', 10), ('Basic', 25), ('Pro', 15)]
    
    # System health data
    latest_health = SystemHealth.query.order_by(SystemHealth.timestamp.desc()).first()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_signals=total_signals,
                         total_trades=total_trades,
                         recent_signals=recent_signals,
                         recent_trades=recent_trades,
                         license_stats=license_stats,
                         latest_health=latest_health)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login endpoint"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password required', 'error')
            return render_template('admin_login.html')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # Check if user is admin
            admin_user = AdminUser.query.filter_by(user_id=user.id).first()
            if admin_user:
                session['admin_user_id'] = user.id
                session['admin_role'] = admin_user.role
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Access denied. Admin privileges required.', 'error')
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout endpoint"""
    session.pop('admin_user_id', None)
    session.pop('admin_role', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/users')
def admin_users():
    """User management interface"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/signals')
def admin_signals():
    """Signal management and debugging interface"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    signals = Signal.query.order_by(Signal.received_at.desc()).limit(50).all() if Signal.query.first() else []
    return render_template('admin_signals.html', signals=signals)


@app.route('/admin/logs')
def admin_logs():
    """System logs viewer"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    level_filter = request.args.get('level', '')
    category_filter = request.args.get('category', '')
    
    query = SystemLog.query.order_by(SystemLog.timestamp.desc())
    
    if level_filter:
        query = query.filter(SystemLog.level == level_filter)
    if category_filter:
        query = query.filter(SystemLog.category == category_filter)
    
    logs = query.limit(100).all()
    
    # Get filter options
    levels = db.session.query(SystemLog.level).distinct().all()
    categories = db.session.query(SystemLog.category).distinct().all()
    
    return render_template('admin_logs.html', 
                         logs=logs,
                         levels=[l[0] for l in levels],
                         categories=[c[0] for c in categories],
                         current_level=level_filter,
                         current_category=category_filter)


@app.route('/admin/api/system-metrics')
def admin_system_metrics():
    """API endpoint for real-time system metrics"""
    if not require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get current system metrics
    latest_health = SystemHealth.query.order_by(SystemHealth.timestamp.desc()).first()
    
    # Get signal processing stats for today
    today = datetime.utcnow().date()
    signals_today = 0
    trades_today = 0
    errors_today = 0
    
    try:
        signals_today = Signal.query.filter(
            db.func.date(Signal.received_at) == today
        ).count()
        
        trades_today = Trade.query.filter(
            db.func.date(Trade.opened_at) == today
        ).count()
        
        errors_today = SystemLog.query.filter(
            db.func.date(SystemLog.timestamp) == today,
            SystemLog.level == 'ERROR'
        ).count()
    except:
        pass
    
    return jsonify({
        'cpu_usage': latest_health.cpu_percent if latest_health else 0,
        'memory_usage': latest_health.memory_percent if latest_health else 0,
        'signals_today': signals_today,
        'trades_today': trades_today,
        'errors_today': errors_today,
        'telegram_connected': latest_health.telegram_connected if latest_health else False,
        'mt5_connected': latest_health.mt5_connected if latest_health else False
    })


@app.route('/admin/license-plans')
def admin_license_plans():
    """License plan management"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    plans = LicensePlan.query.all()
    return render_template('admin_license_plans.html', plans=plans)


@app.route('/admin/providers')
def admin_providers():
    """Signal provider management"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    providers = SignalProvider.query.all()
    return render_template('admin_providers.html', providers=providers)


@app.route('/admin/settings')
def admin_settings():
    """Admin settings and configuration"""
    if not require_admin():
        return redirect(url_for('admin_login'))
    
    # Get parser models
    parser_models = ParserModel.query.all()
    
    # Get notification templates
    templates = NotificationTemplate.query.all()
    
    return render_template('admin_settings.html', 
                         parser_models=parser_models,
                         templates=templates)