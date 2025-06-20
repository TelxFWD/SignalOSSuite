
// Simple SignalOS Dashboard - Direct DOM Updates
// Add global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple dashboard initializing...');
    
    // Replace loading screen with dashboard immediately
    createDashboard();
    
    // Load data immediately
    loadDashboardData();
    
    // Setup navigation
    setupNavigation();
    
    // Setup real-time updates
    setTimeout(loadDashboardData, 2000);
    setInterval(loadDashboardData, 30000);
});

function createDashboard() {
    // Replace the entire app content with dashboard
    const app = document.getElementById('app');
    if (app) {
        app.innerHTML = `
            <div class="dashboard-container">
                <!-- Navigation -->
                <nav class="sidebar">
                    <div class="nav-header">
                        <h1>SignalOS</h1>
                    </div>
                    <ul class="nav-menu">
                        <li class="nav-item active" data-tab="overview">
                            <span>📊 Overview</span>
                        </li>
                        <li class="nav-item" data-tab="signals">
                            <span>📡 Signals</span>
                        </li>
                        <li class="nav-item" data-tab="telegram">
                            <span>📱 Telegram</span>
                        </li>
                        <li class="nav-item" data-tab="mt5">
                            <span>💹 MT5</span>
                        </li>
                        <li class="nav-item" data-tab="strategies">
                            <span>🎯 Strategies</span>
                        </li>
                    </ul>
                </nav>

                <!-- Main Content -->
                <main class="main-content">
                    <!-- Overview Tab -->
                    <div id="tab-overview" class="tab-content active">
                        <div class="dashboard-header">
                            <h2>Dashboard Overview</h2>
                            <div id="system-status" class="status-badge status-online">
                                <div class="pulse-dot green"></div>
                                <span>All Systems Online</span>
                            </div>
                        </div>

                        <!-- Stats Grid -->
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-header">
                                    <h3>Trades Today</h3>
                                    <span class="stat-icon">📈</span>
                                </div>
                                <div class="stat-value" id="trades-today">0</div>
                                <div class="stat-change" id="trades-change">+0% from yesterday</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-header">
                                    <h3>Total Pips</h3>
                                    <span class="stat-icon">💎</span>
                                </div>
                                <div class="stat-value" id="total-pips">0</div>
                                <div class="stat-change" id="pips-change">+0 this week</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-header">
                                    <h3>Win Rate</h3>
                                    <span class="stat-icon">🎯</span>
                                </div>
                                <div class="stat-value" id="win-rate">0%</div>
                                <div class="stat-change" id="win-rate-change">Last 30 days</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-header">
                                    <h3>Active Signals</h3>
                                    <span class="stat-icon">📡</span>
                                </div>
                                <div class="stat-value" id="active-signals">0</div>
                                <div class="stat-change" id="signals-change">Processing</div>
                            </div>
                        </div>

                        <!-- Services Status -->
                        <div class="services-grid">
                            <div class="service-card">
                                <h4>Database</h4>
                                <div id="db-status" class="status-badge status-offline">Disconnected</div>
                            </div>
                            <div class="service-card">
                                <h4>Telegram</h4>
                                <div id="telegram-status" class="status-badge status-offline">Disconnected</div>
                            </div>
                            <div class="service-card">
                                <h4>MT5</h4>
                                <div id="mt5-status" class="status-badge status-offline">Disconnected</div>
                            </div>
                        </div>

                        <!-- Quick Actions -->
                        <div class="actions-grid">
                            <button class="action-btn" onclick="simulateSignal()">
                                🔄 Simulate Signal
                            </button>
                            <button class="action-btn" onclick="setupTelegram()">
                                📱 Setup Telegram
                            </button>
                            <button class="action-btn" onclick="addMT5Terminal()">
                                💹 Add MT5 Terminal
                            </button>
                            <button class="action-btn" onclick="createStrategy()">
                                🎯 Create Strategy
                            </button>
                        </div>
                    </div>

                    <!-- Other Tabs (Placeholder) -->
                    <div id="tab-signals" class="tab-content" style="display: none;">
                        <h2>Signal Management</h2>
                        <p>Signal configuration and monitoring tools.</p>
                    </div>

                    <div id="tab-telegram" class="tab-content" style="display: none;">
                        <h2>Telegram Setup</h2>
                        <p>Configure Telegram bot and channels.</p>
                    </div>

                    <div id="tab-mt5" class="tab-content" style="display: none;">
                        <h2>MT5 Configuration</h2>
                        <p>Connect and configure MT5 terminals.</p>
                    </div>

                    <div id="tab-strategies" class="tab-content" style="display: none;">
                        <h2>Strategy Builder</h2>
                        <p>Create and manage trading strategies.</p>
                    </div>
                </main>
            </div>
        `;
    }

    console.log('Dashboard UI created successfully');
}

function showDashboard() {
    // Show overview tab
    const overviewTab = document.getElementById('tab-overview');
    if (overviewTab) {
        overviewTab.style.display = 'block';
        overviewTab.classList.add('active');
    }
    
    // Hide other tabs
    const allTabs = document.querySelectorAll('.tab-content');
    allTabs.forEach(tab => {
        if (tab.id !== 'tab-overview') {
            tab.style.display = 'none';
        }
    });
    
    // Set active navigation
    const overviewNav = document.querySelector('[data-tab="overview"]');
    if (overviewNav) {
        overviewNav.classList.add('active');
    }
}

function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    // Load analytics data
    fetch('/api/analytics/daily')
        .then(response => response.json())
        .then(data => {
            console.log('Analytics loaded:', data);
            updateStats(data);
        })
        .catch(error => {
            console.error('Analytics error:', error);
            setDefaultStats();
        });
    
    // Load health data
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log('Health loaded:', data);
            updateHealth(data);
        })
        .catch(error => {
            console.error('Health error:', error);
        });
}

function updateStats(data) {
    // Update main statistics
    setText('trades-today', data.trades_today || 0);
    setText('total-pips', data.total_pips || 0);
    setText('win-rate', (data.win_rate || 0) + '%');
    setText('active-signals', data.active_signals || 0);
    
    // Update change indicators
    setText('trades-change', data.trades_change || '+0% from yesterday');
    setText('pips-change', data.pips_change || '+0 this week');
    setText('win-rate-change', 'Last 30 days');
    setText('signals-change', 'Processing');
    
    console.log('Stats updated successfully');
}

function updateHealth(data) {
    // Update system status
    const statusElement = document.getElementById('system-status');
    if (statusElement) {
        const isHealthy = data.status === 'healthy';
        statusElement.className = 'status-badge ' + (isHealthy ? 'status-online' : 'status-warning');
        statusElement.innerHTML = '<div class="pulse-dot ' + (isHealthy ? 'green' : 'yellow') + '"></div><span>' + 
                                  (isHealthy ? 'All Systems Online' : 'Some Issues Detected') + '</span>';
    }
    
    // Update service statuses
    if (data.services) {
        updateServiceStatus('db-status', data.services.database);
        updateServiceStatus('telegram-status', data.services.telegram);
        updateServiceStatus('mt5-status', data.services.mt5);
    }
    
    console.log('Health updated successfully');
}

function updateServiceStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        let statusText, statusClass;
        
        if (typeof status === 'boolean') {
            statusText = status ? 'Connected' : 'Disconnected';
            statusClass = status ? 'status-online' : 'status-offline';
        } else {
            statusText = status || 'Unknown';
            statusClass = 'status-offline';
        }
        
        element.textContent = statusText;
        element.className = 'status-badge ' + statusClass;
    }
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function setDefaultStats() {
    setText('trades-today', '0');
    setText('total-pips', '0');
    setText('win-rate', '0%');
    setText('active-signals', '0');
    setText('trades-change', '+0% from yesterday');
    setText('pips-change', '+0 this week');
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            if (tab) {
                showTab(tab);
            }
        });
    });
}

function showTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeNav = document.querySelector('[data-tab="' + tabName + '"]');
    if (activeNav) {
        activeNav.classList.add('active');
    }
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
        tab.classList.remove('active');
    });
    
    const targetTab = document.getElementById('tab-' + tabName);
    if (targetTab) {
        targetTab.style.display = 'block';
        targetTab.classList.add('active');
    }
    
    console.log('Switched to tab:', tabName);
}

// Global functions for buttons
function simulateSignal() {
    console.log('Simulating signal...');
    fetch('/api/simulate-signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: 'XAUUSD', action: 'BUY', entry: 2000.00 })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Signal simulation completed');
        alert('Signal simulation completed successfully!');
    })
    .catch(error => {
        console.error('Signal simulation failed:', error);
        alert('Signal simulation failed. Check console for details.');
    });
}

function setupTelegram() {
    showTab('telegram');
}

function addMT5Terminal() {
    showTab('mt5');
}

function createStrategy() {
    showTab('strategies');
}

// Initialize icons if available
setTimeout(function() {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}, 1000);
