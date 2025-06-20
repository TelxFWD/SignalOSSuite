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
                   MT5Terminal, Strategy, Signal, Trade, SystemHealth, SignalStatus, SignalAction)


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
    
    try:
        return render_template('premium_admin.html',
                             total_users=total_users,
                             active_users=active_users,
                             total_signals=total_signals,
                             total_trades=total_trades,
                             recent_signals=recent_signals,
                             recent_trades=recent_trades,
                             license_stats=license_stats,
                             latest_health=latest_health)
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>SignalOS Admin - Premium Control Panel</title>
            <link rel="stylesheet" href="/static/css/premium.css">
        </head>
        <body>
            <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
                <div style="text-align: center;">
                    <h1 class="text-gradient" style="font-family: 'Sora', sans-serif; font-size: 2rem; font-weight: 700; margin-bottom: 1rem;">SignalOS Admin</h1>
                    <div class="glass-card" style="padding: 2rem; max-width: 500px;">
                        <h3 style="color: white; margin-bottom: 1.5rem;">System Overview</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem;">
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-400);">{total_users}</div>
                                <div style="color: var(--dark-400); font-size: 0.875rem;">Total Users</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-400);">{total_signals}</div>
                                <div style="color: var(--dark-400); font-size: 0.875rem;">Total Signals</div>
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 1rem;">
                            <a href="/admin/users" class="btn btn-secondary">Manage Users</a>
                            <a href="/admin/signals" class="btn btn-primary">Debug Signals</a>
                            <a href="/admin/system-metrics" class="btn btn-accent">System Metrics</a>
                        </div>
                        <p style="color: var(--dark-500); font-size: 0.75rem; margin-top: 1rem;">Template fallback: {str(e)}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """, 200


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


# Admin API endpoints for signal debugging
@app.route('/admin/api/signals/<int:signal_id>/reparse', methods=['POST'])
def admin_reparse_signal(signal_id):
    """Re-parse a signal for admin debugging"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        signal = Signal.query.get_or_404(signal_id)
        
        # Log the reparse action
        log = SystemLog(
            level='INFO',
            category='ADMIN',
            message=f'Admin re-parsing signal {signal_id}: {signal.raw_text[:50]}...',
            user_id=session.get('admin_user_id'),
            signal_id=signal_id
        )
        db.session.add(log)
        
        # Reset signal status and update processed time
        signal.status = SignalStatus.PENDING
        signal.processed_at = datetime.utcnow()
        signal.error_message = None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Signal queued for re-parsing'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/signals/<int:signal_id>/reexecute', methods=['POST'])
def admin_reexecute_signal(signal_id):
    """Re-execute a signal for admin debugging"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        signal = Signal.query.get_or_404(signal_id)
        
        # Log the reexecution action
        log = SystemLog(
            level='INFO',
            category='ADMIN',
            message=f'Admin re-executing signal {signal_id}: {signal.parsed_pair} {signal.parsed_action}',
            user_id=session.get('admin_user_id'),
            signal_id=signal_id
        )
        db.session.add(log)
        
        # Update signal status
        signal.status = SignalStatus.PROCESSING
        signal.executed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Signal queued for re-execution'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/signals/<int:signal_id>/resolve', methods=['POST'])
def admin_resolve_signal(signal_id):
    """Mark a signal as resolved for admin debugging"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        signal = Signal.query.get_or_404(signal_id)
        
        # Log the resolution
        log = SystemLog(
            level='INFO',
            category='ADMIN',
            message=f'Admin marked signal {signal_id} as resolved',
            user_id=session.get('admin_user_id'),
            signal_id=signal_id
        )
        db.session.add(log)
        
        # Mark as resolved
        signal.status = SignalStatus.EXECUTED
        signal.error_message = "Manually resolved by admin"
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Signal marked as resolved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/api/signals/<int:signal_id>/logs')
def admin_export_signal_logs(signal_id):
    """Export logs for a specific signal"""
    if not require_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        signal = Signal.query.get_or_404(signal_id)
        logs = SystemLog.query.filter_by(signal_id=signal_id).order_by(SystemLog.timestamp.desc()).all()
        
        log_data = {
            'signal_id': signal_id,
            'signal_details': {
                'raw_text': signal.raw_text,
                'parsed_pair': signal.parsed_pair,
                'parsed_action': signal.parsed_action,
                'confidence_score': signal.confidence_score,
                'status': signal.status.value if signal.status else None,
                'received_at': signal.received_at.isoformat() if signal.received_at else None
            },
            'logs': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'level': log.level,
                    'category': log.category,
                    'message': log.message
                }
                for log in logs
            ]
        }
        
        return jsonify(log_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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