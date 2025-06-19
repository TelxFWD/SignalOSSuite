"""
SignalOS Admin Panel
Comprehensive admin interface with Flask-Admin
"""

from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Field
from flask import session, redirect, url_for, request, flash, jsonify
from werkzeug.security import check_password_hash
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, NumberRange
import json
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
import pandas as pd

from app import app, db
from flask import session, redirect, url_for, request, flash, jsonify
from models import (User, AdminUser, LicensePlan, UserLicense, ParserModel, SignalProvider, 
                   SystemLog, NotificationTemplate, TelegramSession, TelegramChannel, 
                   MT5Terminal, Strategy, Signal, Trade, SystemHealth)


class AdminAuthMixin:
    """Mixin for admin authentication"""
    
    def is_accessible(self):
        """Check if current user has admin access"""
        if 'admin_user_id' not in session:
            return False
        
        admin_user = AdminUser.query.filter_by(user_id=session['admin_user_id']).first()
        return admin_user is not None
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect to admin login if not accessible"""
        return redirect(url_for('admin_login'))


class AdminDashboardView(AdminIndexView, AdminAuthMixin):
    """Custom admin dashboard with metrics and charts"""
    
    @expose('/')
    def index(self):
        """Admin dashboard with comprehensive metrics"""
        # Get key metrics
        total_users = User.query.count()
        active_users = User.query.filter_by(active=True).count()
        total_signals = Signal.query.count()
        total_trades = Trade.query.count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_signals = Signal.query.filter(Signal.received_at >= week_ago).count()
        recent_trades = Trade.query.filter(Trade.opened_at >= week_ago).count()
        
        # License distribution
        license_stats = db.session.query(
            LicensePlan.name, 
            db.func.count(UserLicense.id).label('count')
        ).join(UserLicense).group_by(LicensePlan.name).all()
        
        # System health data
        latest_health = SystemHealth.query.order_by(SystemHealth.timestamp.desc()).first()
        
        # Create charts
        charts = self._create_dashboard_charts()
        
        return self.render('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_signals=total_signals,
                         total_trades=total_trades,
                         recent_signals=recent_signals,
                         recent_trades=recent_trades,
                         license_stats=license_stats,
                         latest_health=latest_health,
                         charts=charts)
    
    def _create_dashboard_charts(self):
        """Create dashboard charts using Plotly"""
        charts = {}
        
        # Signals processed over time (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        signals_data = db.session.query(
            db.func.date(Signal.received_at).label('date'),
            db.func.count(Signal.id).label('count')
        ).filter(Signal.received_at >= thirty_days_ago).group_by(
            db.func.date(Signal.received_at)
        ).all()
        
        if signals_data:
            df = pd.DataFrame(signals_data, columns=['date', 'count'])
            fig = go.Figure(data=go.Scatter(x=df['date'], y=df['count']))
            fig.update_layout(title='Signals Processed (Last 30 Days)')
            charts['signals_chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # User license distribution
        license_data = db.session.query(
            LicensePlan.name,
            db.func.count(UserLicense.id).label('count')
        ).join(UserLicense).group_by(LicensePlan.name).all()
        
        if license_data:
            labels, values = zip(*license_data)
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(title='License Plan Distribution')
            charts['license_chart'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return charts


class UserAdminView(ModelView, AdminAuthMixin):
    """Admin view for user management"""
    
    column_list = ['id', 'email', 'name', 'license_type', 'active', 'created_at', 'last_login']
    column_searchable_list = ['email', 'name']
    column_filters = ['active', 'license_type', 'created_at']
    column_editable_list = ['active', 'license_type']
    
    form_excluded_columns = ['password_hash', 'telegram_sessions', 'mt5_terminals', 'strategies', 'trades']
    
    def on_model_change(self, form, model, is_created):
        """Log user changes"""
        if not is_created:
            log_entry = SystemLog(
                level='INFO',
                category='admin',
                message=f'User {model.email} updated by admin',
                user_id=model.id,
                additional_data=json.dumps({
                    'admin_user': session.get('admin_user_id'),
                    'changes': 'User profile updated'
                })
            )
            db.session.add(log_entry)


class LicensePlanAdminView(ModelView, AdminAuthMixin):
    """Admin view for license plan management"""
    
    column_list = ['name', 'price', 'duration_days', 'max_terminals', 'max_channels', 'active']
    form_columns = ['name', 'description', 'price', 'duration_days', 'max_terminals', 
                   'max_channels', 'max_strategies', 'features', 'active']
    
    form_overrides = {
        'features': TextAreaField
    }
    
    form_widget_args = {
        'features': {
            'placeholder': 'JSON format: {"shadow_mode": true, "advanced_strategies": true}'
        }
    }


class SystemLogAdminView(ModelView, AdminAuthMixin):
    """Admin view for system logs"""
    
    can_create = False
    can_edit = False
    can_delete = True
    
    column_list = ['timestamp', 'level', 'category', 'message', 'user_id']
    column_filters = ['level', 'category', 'timestamp']
    column_searchable_list = ['message']
    column_default_sort = ('timestamp', True)
    
    page_size = 50


class SignalAdminView(ModelView, AdminAuthMixin):
    """Admin view for signal management and debugging"""
    
    column_list = ['id', 'received_at', 'parsed_pair', 'parsed_action', 'status', 'confidence_score']
    column_filters = ['status', 'parsed_action', 'received_at']
    column_searchable_list = ['raw_text', 'parsed_pair']
    
    form_excluded_columns = ['trades']
    
    @expose('/debug/<int:signal_id>')
    def debug_signal(self, signal_id):
        """Debug signal processing pipeline"""
        signal = Signal.query.get_or_404(signal_id)
        
        # Get related trades
        trades = Trade.query.filter_by(signal_id=signal_id).all()
        
        # Get processing logs
        logs = SystemLog.query.filter_by(signal_id=signal_id).order_by(SystemLog.timestamp).all()
        
        return self.render('admin/signal_debug.html', 
                         signal=signal, trades=trades, logs=logs)


class ParserModelAdminView(ModelView, AdminAuthMixin):
    """Admin view for parser model management"""
    
    column_list = ['version', 'name', 'accuracy', 'training_samples', 'active', 'created_at']
    column_filters = ['active', 'created_at']
    
    form_columns = ['version', 'name', 'description', 'model_file_path', 
                   'accuracy', 'training_samples', 'active']
    
    @expose('/retrain')
    def retrain_model(self):
        """Trigger model retraining"""
        # This would integrate with your training pipeline
        flash('Model retraining triggered', 'success')
        return redirect(url_for('.index_view'))


class NotificationAdminView(ModelView, AdminAuthMixin):
    """Admin view for notification templates"""
    
    column_list = ['name', 'type', 'active', 'created_at']
    column_filters = ['type', 'active']
    
    form_overrides = {
        'message_template': TextAreaField,
        'variables': TextAreaField
    }


# Initialize admin
admin = Admin(app, name='SignalOS Admin', 
              template_mode='bootstrap4',
              index_view=AdminDashboardView())

# Add model views
admin.add_view(UserAdminView(User, db.session, name='Users'))
admin.add_view(LicensePlanAdminView(LicensePlan, db.session, name='License Plans'))
admin.add_view(ModelView(UserLicense, db.session, name='User Licenses'))
admin.add_view(ModelView(TelegramSession, db.session, name='Telegram Sessions'))
admin.add_view(ModelView(TelegramChannel, db.session, name='Telegram Channels'))
admin.add_view(ModelView(MT5Terminal, db.session, name='MT5 Terminals'))
admin.add_view(ModelView(Strategy, db.session, name='Strategies'))
admin.add_view(SignalAdminView(Signal, db.session, name='Signals'))
admin.add_view(ModelView(Trade, db.session, name='Trades'))
admin.add_view(ParserModelAdminView(ParserModel, db.session, name='Parser Models'))
admin.add_view(ModelView(SignalProvider, db.session, name='Signal Providers'))
admin.add_view(SystemLogAdminView(SystemLog, db.session, name='System Logs'))
admin.add_view(NotificationAdminView(NotificationTemplate, db.session, name='Notifications'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login endpoint"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # Check if user is admin
            admin_user = AdminUser.query.filter_by(user_id=user.id).first()
            if admin_user:
                session['admin_user_id'] = user.id
                session['admin_role'] = admin_user.role
                return redirect(url_for('admin.index'))
            else:
                flash('Access denied. Admin privileges required.', 'error')
        else:
            flash('Invalid credentials', 'error')
    
    return '''
    <form method="post" style="max-width: 400px; margin: 100px auto; padding: 20px; border: 1px solid #ddd;">
        <h2>SignalOS Admin Login</h2>
        <div style="margin: 10px 0;">
            <input type="email" name="email" placeholder="Email" required style="width: 100%; padding: 10px;">
        </div>
        <div style="margin: 10px 0;">
            <input type="password" name="password" placeholder="Password" required style="width: 100%; padding: 10px;">
        </div>
        <button type="submit" style="width: 100%; padding: 10px; background: #007bff; color: white; border: none;">
            Login
        </button>
    </form>
    '''


@app.route('/admin/logout')
def admin_logout():
    """Admin logout endpoint"""
    session.pop('admin_user_id', None)
    session.pop('admin_role', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/api/system-metrics')
def admin_system_metrics():
    """API endpoint for real-time system metrics"""
    if 'admin_user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get current system metrics
    latest_health = SystemHealth.query.order_by(SystemHealth.timestamp.desc()).first()
    
    # Get signal processing stats for today
    today = datetime.utcnow().date()
    signals_today = Signal.query.filter(
        db.func.date(Signal.received_at) == today
    ).count()
    
    trades_today = Trade.query.filter(
        db.func.date(Trade.opened_at) == today
    ).count()
    
    # Get error count for today
    errors_today = SystemLog.query.filter(
        db.func.date(SystemLog.timestamp) == today,
        SystemLog.level == 'ERROR'
    ).count()
    
    return jsonify({
        'cpu_usage': latest_health.cpu_percent if latest_health else 0,
        'memory_usage': latest_health.memory_percent if latest_health else 0,
        'signals_today': signals_today,
        'trades_today': trades_today,
        'errors_today': errors_today,
        'telegram_connected': latest_health.telegram_connected if latest_health else False,
        'mt5_connected': latest_health.mt5_connected if latest_health else False
    })