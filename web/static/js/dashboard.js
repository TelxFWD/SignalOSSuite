// SignalOS Dashboard JavaScript
class SignalOSDashboard {
    constructor() {
        this.currentUser = null;
        this.authToken = null;
        this.socket = null;
        this.currentView = 'overview';
        this.init();
    }

    init() {
        this.checkAuthStatus();
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();
    }

    checkAuthStatus() {
        const token = localStorage.getItem('signalos_token');
        const user = localStorage.getItem('signalos_user');
        
        if (token && user) {
            this.authToken = token;
            this.currentUser = JSON.parse(user);
            this.showDashboard();
        } else {
            this.showLogin();
        }
    }

    showLogin() {
        document.body.innerHTML = `
            <div class="login-container" style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--background);">
                <div class="login-card" style="background: var(--surface); padding: 2rem; border-radius: 0.5rem; width: 100%; max-width: 400px; border: 1px solid var(--border);">
                    <h2 style="text-align: center; margin-bottom: 2rem; color: var(--primary-color);">SignalOS Login</h2>
                    <form id="loginForm">
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" id="email" class="form-input" value="demo@signalos.com" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" id="password" class="form-input" value="demo" required>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                        <div id="loginError" class="alert alert-error hidden" style="margin-top: 1rem;"></div>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
    }

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.authToken = data.token;
                this.currentUser = data.user;
                localStorage.setItem('signalos_token', data.token);
                localStorage.setItem('signalos_user', JSON.stringify(data.user));
                this.showDashboard();
            } else {
                errorDiv.textContent = data.message || 'Login failed';
                errorDiv.classList.remove('hidden');
            }
        } catch (error) {
            errorDiv.textContent = 'Connection error';
            errorDiv.classList.remove('hidden');
        }
    }

    showDashboard() {
        document.body.innerHTML = `
            <link rel="stylesheet" href="/static/css/dashboard.css">
            <div class="dashboard">
                <aside class="sidebar">
                    <div class="sidebar-header">
                        <h2>SignalOS</h2>
                    </div>
                    <nav class="sidebar-nav">
                        <button class="nav-item active" data-view="overview">📊 Overview</button>
                        <button class="nav-item" data-view="telegram">📱 Telegram</button>
                        <button class="nav-item" data-view="mt5">💹 MT5 Terminals</button>
                        <button class="nav-item" data-view="strategies">🎯 Strategies</button>
                        <button class="nav-item" data-view="analytics">📈 Analytics</button>
                        <button class="nav-item" data-view="settings">⚙️ Settings</button>
                        <button class="nav-item" data-view="health">🏥 Health Monitor</button>
                    </nav>
                </aside>
                <main class="main-content">
                    <header class="header">
                        <div class="header-content">
                            <h1 id="pageTitle">Dashboard Overview</h1>
                            <div class="user-info">
                                <span class="status-badge connected">Online</span>
                                <span>${this.currentUser.name}</span>
                                <button class="btn btn-secondary btn-sm" onclick="dashboard.logout()">Logout</button>
                            </div>
                        </div>
                    </header>
                    <div class="content" id="mainContent">
                        <div class="loading">
                            <div class="spinner"></div>
                        </div>
                    </div>
                </main>
            </div>
        `;

        this.setupDashboardEventListeners();
        this.loadView('overview');
    }

    setupEventListeners() {
        // Initial setup for login/dashboard switching
    }

    setupDashboardEventListeners() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                e.target.classList.add('active');
                this.loadView(e.target.dataset.view);
            });
        });
    }

    async loadView(view) {
        this.currentView = view;
        const content = document.getElementById('mainContent');
        const title = document.getElementById('pageTitle');

        // Update title
        const titles = {
            overview: 'Dashboard Overview',
            telegram: 'Telegram Management',
            mt5: 'MT5 Terminals',
            strategies: 'Trading Strategies',
            analytics: 'Performance Analytics',
            settings: 'Settings',
            health: 'Health Monitor'
        };
        title.textContent = titles[view] || 'Dashboard';

        // Show loading
        content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

        // Load view content
        try {
            switch (view) {
                case 'overview':
                    await this.loadOverviewView();
                    break;
                case 'telegram':
                    await this.loadTelegramView();
                    break;
                case 'mt5':
                    await this.loadMT5View();
                    break;
                case 'strategies':
                    await this.loadStrategiesView();
                    break;
                case 'analytics':
                    await this.loadAnalyticsView();
                    break;
                case 'settings':
                    await this.loadSettingsView();
                    break;
                case 'health':
                    await this.loadHealthView();
                    break;
            }
        } catch (error) {
            content.innerHTML = `<div class="alert alert-error">Failed to load ${view}: ${error.message}</div>`;
        }
    }

    async loadOverviewView() {
        const [health, analytics] = await Promise.all([
            this.fetchAPI('/api/health'),
            this.fetchAPI('/api/analytics/daily')
        ]);

        const todayStats = analytics.daily_stats?.[0] || { trades: 0, pips: 0, profit: 0 };

        document.getElementById('mainContent').innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${todayStats.trades}</div>
                    <div class="stat-label">Trades Today</div>
                </div>
                <div class="stat-card ${todayStats.pips >= 0 ? 'positive' : 'negative'}">
                    <div class="stat-value">${todayStats.pips >= 0 ? '+' : ''}${todayStats.pips}</div>
                    <div class="stat-label">Total Pips</div>
                </div>
                <div class="stat-card ${todayStats.profit >= 0 ? 'positive' : 'negative'}">
                    <div class="stat-value">${todayStats.profit >= 0 ? '+' : ''}$${Math.abs(todayStats.profit)}</div>
                    <div class="stat-label">Profit/Loss</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${health.status === 'healthy' ? '🟢' : '🔴'}</div>
                    <div class="stat-label">System Status</div>
                </div>
            </div>
            
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3>System Health</h3>
                    </div>
                    <div class="card-body">
                        <div class="health-indicator">
                            <div class="health-dot ${health.services.database ? 'healthy' : 'unhealthy'}"></div>
                            <span>Database: ${health.services.database ? 'Connected' : 'Disconnected'}</span>
                        </div>
                        <div class="health-indicator">
                            <div class="health-dot ${health.services.telegram ? 'healthy' : 'unhealthy'}"></div>
                            <span>Telegram: ${health.services.telegram ? 'Connected' : 'Disconnected'}</span>
                        </div>
                        <div class="health-indicator">
                            <div class="health-dot ${health.services.mt5 ? 'healthy' : 'unhealthy'}"></div>
                            <span>MT5: ${health.services.mt5 ? 'Connected' : 'Disconnected'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Quick Actions</h3>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-primary" style="width: 100%; margin-bottom: 1rem;" onclick="dashboard.loadView('telegram')">
                            Setup Telegram
                        </button>
                        <button class="btn btn-primary" style="width: 100%; margin-bottom: 1rem;" onclick="dashboard.loadView('mt5')">
                            Add MT5 Terminal
                        </button>
                        <button class="btn btn-primary" style="width: 100%;" onclick="dashboard.loadView('strategies')">
                            Create Strategy
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async loadTelegramView() {
        const sessions = await this.fetchAPI('/api/telegram/sessions');
        const channels = await this.fetchAPI('/api/telegram/channels');

        document.getElementById('mainContent').innerHTML = `
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3>Telegram Sessions</h3>
                        <button class="btn btn-primary btn-sm" onclick="dashboard.showAddSessionModal()">Add Session</button>
                    </div>
                    <div class="card-body">
                        ${sessions.sessions.length > 0 ? `
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Phone</th>
                                        <th>Status</th>
                                        <th>Channels</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${sessions.sessions.map(session => `
                                        <tr>
                                            <td>${session.phone}</td>
                                            <td><span class="status-badge ${session.status === 'connected' ? 'connected' : 'disconnected'}">${session.status}</span></td>
                                            <td>${session.channels.length}</td>
                                            <td>
                                                <button class="btn btn-danger btn-sm" onclick="dashboard.deleteSession(${session.id})">Delete</button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        ` : '<p>No Telegram sessions configured. Add one to get started.</p>'}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Monitored Channels</h3>
                        <button class="btn btn-primary btn-sm" onclick="dashboard.showAddChannelModal()">Add Channel</button>
                    </div>
                    <div class="card-body">
                        ${channels.channels.length > 0 ? `
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>URL</th>
                                        <th>Signals</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${channels.channels.map(channel => `
                                        <tr>
                                            <td>${channel.name}</td>
                                            <td>${channel.url}</td>
                                            <td>${channel.total_signals}</td>
                                            <td>
                                                <label class="toggle-switch">
                                                    <input type="checkbox" ${channel.enabled ? 'checked' : ''} onchange="dashboard.toggleChannel(${channel.id})">
                                                    <span class="toggle-slider"></span>
                                                </label>
                                            </td>
                                            <td>
                                                <button class="btn btn-danger btn-sm" onclick="dashboard.deleteChannel(${channel.id})">Delete</button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        ` : '<p>No channels configured. Add channels to monitor for trading signals.</p>'}
                    </div>
                </div>
            </div>
        `;
    }

    async loadMT5View() {
        const terminals = await this.fetchAPI('/api/mt5/terminals');

        document.getElementById('mainContent').innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>MT5 Terminals</h3>
                    <button class="btn btn-primary" onclick="dashboard.showAddTerminalModal()">Add Terminal</button>
                </div>
                <div class="card-body">
                    ${terminals.terminals.length > 0 ? `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Server</th>
                                    <th>Balance</th>
                                    <th>Equity</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${terminals.terminals.map(terminal => `
                                    <tr>
                                        <td>${terminal.name}</td>
                                        <td>${terminal.server}</td>
                                        <td>$${terminal.balance.toFixed(2)}</td>
                                        <td>$${terminal.equity.toFixed(2)}</td>
                                        <td><span class="status-badge ${terminal.status === 'connected' ? 'connected' : 'disconnected'}">${terminal.status}</span></td>
                                        <td>
                                            <button class="btn btn-secondary btn-sm" onclick="dashboard.editTerminal(${terminal.id})">Edit</button>
                                            <button class="btn btn-danger btn-sm" onclick="dashboard.deleteTerminal(${terminal.id})">Delete</button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No MT5 terminals configured. Add a terminal to start automated trading.</p>'}
                </div>
            </div>
        `;
    }

    async loadStrategiesView() {
        const strategies = await this.fetchAPI('/api/strategies');

        document.getElementById('mainContent').innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>Trading Strategies</h3>
                    <button class="btn btn-primary" onclick="dashboard.showCreateStrategyModal()">Create Strategy</button>
                </div>
                <div class="card-body">
                    ${strategies.strategies.length > 0 ? `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Type</th>
                                    <th>Max Risk</th>
                                    <th>Trades</th>
                                    <th>Win Rate</th>
                                    <th>Total Pips</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${strategies.strategies.map(strategy => {
                                    const winRate = strategy.total_trades > 0 ? ((strategy.winning_trades / strategy.total_trades) * 100).toFixed(1) : 0;
                                    return `
                                        <tr>
                                            <td>${strategy.name}</td>
                                            <td><span class="status-badge ${strategy.type === 'beginner' ? 'connected' : 'disconnected'}">${strategy.type}</span></td>
                                            <td>${strategy.max_risk}%</td>
                                            <td>${strategy.total_trades}</td>
                                            <td>${winRate}%</td>
                                            <td>${strategy.total_pips}</td>
                                            <td>
                                                <label class="toggle-switch">
                                                    <input type="checkbox" ${strategy.active ? 'checked' : ''} onchange="dashboard.toggleStrategy(${strategy.id})">
                                                    <span class="toggle-slider"></span>
                                                </label>
                                            </td>
                                            <td>
                                                <button class="btn btn-secondary btn-sm" onclick="dashboard.editStrategy(${strategy.id})">Edit</button>
                                                <button class="btn btn-danger btn-sm" onclick="dashboard.deleteStrategy(${strategy.id})">Delete</button>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No strategies configured. Create a strategy to define your trading rules.</p>'}
                </div>
            </div>
        `;
    }

    async loadAnalyticsView() {
        const analytics = await this.fetchAPI('/api/analytics/daily');
        
        document.getElementById('mainContent').innerHTML = `
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3>Performance Overview</h3>
                    </div>
                    <div class="card-body">
                        <canvas id="performanceChart" width="400" height="200"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Weekly Summary</h3>
                    </div>
                    <div class="card-body">
                        ${analytics.daily_stats ? `
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Trades</th>
                                        <th>Pips</th>
                                        <th>Profit</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${analytics.daily_stats.map(stat => `
                                        <tr>
                                            <td>${new Date(stat.date).toLocaleDateString()}</td>
                                            <td>${stat.trades}</td>
                                            <td>${stat.pips}</td>
                                            <td class="${stat.profit >= 0 ? 'text-success' : 'text-danger'}">$${stat.profit}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        ` : '<p>No analytics data available.</p>'}
                    </div>
                </div>
            </div>
        `;
    }

    async loadSettingsView() {
        document.getElementById('mainContent').innerHTML = `
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3>General Settings</h3>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">Shadow Mode</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="shadowMode" onchange="dashboard.toggleShadowMode()">
                                <span class="toggle-slider"></span>
                            </label>
                            <small style="color: var(--text-secondary);">Enable to test strategies without real trading</small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Max Daily Risk (%)</label>
                            <input type="number" class="form-input" value="5" min="0" max="100">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Trading Hours</label>
                            <div style="display: flex; gap: 1rem;">
                                <input type="time" class="form-input" value="08:00">
                                <input type="time" class="form-input" value="17:00">
                            </div>
                        </div>
                        
                        <button class="btn btn-primary">Save Settings</button>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Configuration Backup</h3>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-secondary" style="width: 100%; margin-bottom: 1rem;" onclick="dashboard.exportConfig()">
                            Export Configuration
                        </button>
                        <button class="btn btn-secondary" style="width: 100%;" onclick="dashboard.importConfig()">
                            Import Configuration
                        </button>
                        <input type="file" id="configFileInput" style="display: none;" accept=".json" onchange="dashboard.handleConfigImport(event)">
                    </div>
                </div>
            </div>
        `;
    }

    async loadHealthView() {
        const health = await this.fetchAPI('/api/health');
        
        document.getElementById('mainContent').innerHTML = `
            <div class="grid grid-3">
                <div class="card">
                    <div class="card-header">
                        <h3>System Status</h3>
                    </div>
                    <div class="card-body">
                        <div class="health-indicator">
                            <div class="health-dot ${health.services.database ? 'healthy' : 'unhealthy'}"></div>
                            <span>Database: ${health.services.database ? 'Connected' : 'Disconnected'}</span>
                        </div>
                        <div class="health-indicator">
                            <div class="health-dot ${health.services.telegram ? 'healthy' : 'unhealthy'}"></div>
                            <span>Telegram: ${health.services.telegram ? 'Connected' : 'Disconnected'}</span>
                        </div>
                        <div class="health-indicator">
                            <div class="health-dot ${health.services.mt5 ? 'healthy' : 'unhealthy'}"></div>
                            <span>MT5: ${health.services.mt5 ? 'Connected' : 'Disconnected'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Signal Processing</h3>
                    </div>
                    <div class="card-body">
                        <p>Signals Today: <strong>0</strong></p>
                        <p>Processed: <strong>0</strong></p>
                        <p>Failed: <strong>0</strong></p>
                        <p>Queue: <strong>0</strong></p>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>System Resources</h3>
                    </div>
                    <div class="card-body">
                        <p>CPU Usage: <strong>15%</strong></p>
                        <p>Memory: <strong>45%</strong></p>
                        <p>Uptime: <strong>2h 30m</strong></p>
                    </div>
                </div>
            </div>
        `;
    }

    // Modal and utility functions
    showAddSessionModal() {
        this.showModal('Add Telegram Session', `
            <form id="addSessionForm">
                <div class="form-group">
                    <label class="form-label">Phone Number</label>
                    <input type="tel" name="phone" class="form-input" placeholder="+1234567890" required>
                </div>
                <div class="form-group">
                    <label class="form-label">API ID</label>
                    <input type="text" name="api_id" class="form-input" required>
                </div>
                <div class="form-group">
                    <label class="form-label">API Hash</label>
                    <input type="text" name="api_hash" class="form-input" required>
                </div>
            </form>
        `, [
            { text: 'Cancel', class: 'btn-secondary', action: 'close' },
            { text: 'Add Session', class: 'btn-primary', action: () => this.submitSessionForm() }
        ]);
    }

    showAddTerminalModal() {
        this.showModal('Add MT5 Terminal', `
            <form id="addTerminalForm">
                <div class="form-group">
                    <label class="form-label">Terminal Name</label>
                    <input type="text" name="name" class="form-input" placeholder="My MT5 Terminal" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Server</label>
                    <input type="text" name="server" class="form-input" placeholder="MetaQuotes-Demo" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Login</label>
                    <input type="text" name="login" class="form-input" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-input" required>
                </div>
            </form>
        `, [
            { text: 'Cancel', class: 'btn-secondary', action: 'close' },
            { text: 'Add Terminal', class: 'btn-primary', action: () => this.submitTerminalForm() }
        ]);
    }

    showCreateStrategyModal() {
        this.showModal('Create Trading Strategy', `
            <form id="createStrategyForm">
                <div class="form-group">
                    <label class="form-label">Strategy Name</label>
                    <input type="text" name="name" class="form-input" placeholder="Conservative Strategy" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Strategy Type</label>
                    <select name="type" class="form-input" required>
                        <option value="beginner">Beginner (Predefined Rules)</option>
                        <option value="pro">Professional (Custom Rules)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Max Risk per Trade (%)</label>
                    <input type="number" name="max_risk" class="form-input" value="1" min="0.1" max="10" step="0.1" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Description</label>
                    <textarea name="description" class="form-input" rows="3" placeholder="Strategy description..."></textarea>
                </div>
            </form>
        `, [
            { text: 'Cancel', class: 'btn-secondary', action: 'close' },
            { text: 'Create Strategy', class: 'btn-primary', action: () => this.submitStrategyForm() }
        ]);
    }

    showModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button onclick="this.closest('.modal').remove()" style="background: none; border: none; color: var(--text-secondary); font-size: 1.5rem; cursor: pointer;">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${buttons.map(btn => `
                        <button class="btn ${btn.class}" onclick="${btn.action === 'close' ? 'this.closest(\'.modal\').remove()' : `(${btn.action})(); this.closest('.modal').remove();`}">
                            ${btn.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async submitSessionForm() {
        const form = document.getElementById('addSessionForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            await this.fetchAPI('/api/telegram/sessions', 'POST', data);
            this.showAlert('Telegram session added successfully', 'success');
            this.loadView('telegram');
        } catch (error) {
            this.showAlert('Failed to add session: ' + error.message, 'error');
        }
    }

    async submitTerminalForm() {
        const form = document.getElementById('addTerminalForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            await this.fetchAPI('/api/mt5/terminals', 'POST', data);
            this.showAlert('MT5 terminal added successfully', 'success');
            this.loadView('mt5');
        } catch (error) {
            this.showAlert('Failed to add terminal: ' + error.message, 'error');
        }
    }

    async submitStrategyForm() {
        const form = document.getElementById('createStrategyForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            await this.fetchAPI('/api/strategies', 'POST', data);
            this.showAlert('Strategy created successfully', 'success');
            this.loadView('strategies');
        } catch (error) {
            this.showAlert('Failed to create strategy: ' + error.message, 'error');
        }
    }

    // Missing function implementations for dashboard actions
    async deleteSession(sessionId) {
        try {
            await this.fetchAPI(`/api/telegram/sessions/${sessionId}`, 'DELETE');
            this.showAlert('Session deleted successfully', 'success');
            this.loadView('telegram');
        } catch (error) {
            this.showAlert('Failed to delete session: ' + error.message, 'error');
        }
    }

    async deleteChannel(channelId) {
        try {
            await this.fetchAPI(`/api/telegram/channels/${channelId}`, 'DELETE');
            this.showAlert('Channel deleted successfully', 'success');
            this.loadView('telegram');
        } catch (error) {
            this.showAlert('Failed to delete channel: ' + error.message, 'error');
        }
    }

    async deleteTerminal(terminalId) {
        try {
            await this.fetchAPI(`/api/mt5/terminals/${terminalId}`, 'DELETE');
            this.showAlert('Terminal deleted successfully', 'success');
            this.loadView('mt5');
        } catch (error) {
            this.showAlert('Failed to delete terminal: ' + error.message, 'error');
        }
    }

    async deleteStrategy(strategyId) {
        try {
            await this.fetchAPI(`/api/strategies/${strategyId}`, 'DELETE');
            this.showAlert('Strategy deleted successfully', 'success');
            this.loadView('strategies');
        } catch (error) {
            this.showAlert('Failed to delete strategy: ' + error.message, 'error');
        }
    }

    async editTerminal(terminalId) {
        this.showAlert('Edit terminal functionality coming soon', 'info');
    }

    async editStrategy(strategyId) {
        this.showAlert('Edit strategy functionality coming soon', 'info');
    }

    async toggleChannel(channelId) {
        this.showAlert('Channel toggle functionality coming soon', 'info');
    }

    async toggleStrategy(strategyId) {
        this.showAlert('Strategy toggle functionality coming soon', 'info');
    }

    showAddChannelModal() {
        this.showModal('Add Telegram Channel', `
            <form id="addChannelForm">
                <div class="form-group">
                    <label class="form-label">Channel Name</label>
                    <input type="text" name="name" class="form-input" placeholder="Forex Signals" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Channel URL</label>
                    <input type="text" name="url" class="form-input" placeholder="@forex_signals" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Session</label>
                    <select name="session_id" class="form-input" required>
                        <option value="1">Default Session</option>
                    </select>
                </div>
            </form>
        `, [
            { text: 'Cancel', class: 'btn-secondary', action: 'close' },
            { text: 'Add Channel', class: 'btn-primary', action: () => this.submitChannelForm() }
        ]);
    }

    async submitChannelForm() {
        const form = document.getElementById('addChannelForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            await this.fetchAPI('/api/telegram/channels', 'POST', data);
            this.showAlert('Channel added successfully', 'success');
            this.loadView('telegram');
        } catch (error) {
            this.showAlert('Failed to add channel: ' + error.message, 'error');
        }
    }

    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        document.body.appendChild(alert);
        
        setTimeout(() => alert.remove(), 5000);
    }

    async fetchAPI(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.authToken}`
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return response.json();
    }

    connectWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
            });

            this.socket.on('signal_update', (data) => {
                console.log('Signal update:', data);
                // Handle real-time signal updates
            });

            this.socket.on('health_update', (data) => {
                console.log('Health update:', data);
                // Update health indicators in real-time
            });
        } catch (error) {
            console.log('WebSocket not available:', error);
        }
    }

    async loadInitialData() {
        // Load any initial data needed for the dashboard
    }

    toggleShadowMode() {
        const checkbox = document.getElementById('shadowMode');
        console.log('Shadow mode toggled:', checkbox.checked);
        // Implement shadow mode toggle
    }

    exportConfig() {
        const config = {
            user: this.currentUser,
            timestamp: new Date().toISOString(),
            version: '2.0'
        };
        
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'signalos-config.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    importConfig() {
        document.getElementById('configFileInput').click();
    }

    handleConfigImport(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const config = JSON.parse(e.target.result);
                    console.log('Imported config:', config);
                    this.showAlert('Configuration imported successfully', 'success');
                } catch (error) {
                    this.showAlert('Invalid configuration file', 'error');
                }
            };
            reader.readAsText(file);
        }
    }

    logout() {
        localStorage.removeItem('signalos_token');
        localStorage.removeItem('signalos_user');
        location.reload();
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new SignalOSDashboard();
});