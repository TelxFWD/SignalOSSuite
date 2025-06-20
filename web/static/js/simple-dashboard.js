
// SignalOS Dashboard JavaScript
console.log('SignalOS Dashboard loading...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Load initial data
    loadDashboardData();
    
    // Setup navigation
    setupNavigation();
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
    
    console.log('Simple dashboard initializing...');
});

function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    // Load analytics
    fetch('/api/analytics/daily')
        .then(response => response.json())
        .then(data => {
            console.log('Analytics loaded:', data);
            updateDashboardStats(data);
        })
        .catch(error => console.error('Analytics error:', error));
    
    // Load health status
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log('Health loaded:', data);
            updateSystemHealth(data);
        })
        .catch(error => console.error('Health error:', error));
}

function updateDashboardStats(data) {
    // Update main statistics
    updateElement('trades-today', data.trades_today || 0);
    updateElement('total-pips', data.total_pips || 0);
    updateElement('win-rate', (data.win_rate || 0) + '%');
    updateElement('active-signals', data.active_signals || 0);
    
    // Update change indicators
    updateElement('trades-change', data.trades_change || '+0% from yesterday');
    updateElement('pips-change', data.pips_change || '+0 this week');
    updateElement('win-rate-change', 'Last 30 days');
    updateElement('signals-change', 'Processing');
    
    console.log('Stats updated successfully');
}

function updateSystemHealth(data) {
    const statusElement = document.getElementById('system-status');
    if (statusElement) {
        const isHealthy = data.status === 'healthy';
        statusElement.className = 'status-badge ' + (isHealthy ? 'status-online' : 'status-warning');
        
        const dotClass = isHealthy ? 'green' : 'yellow';
        const statusText = isHealthy ? 'All Systems Online' : 'Some Issues Detected';
        statusElement.innerHTML = '<div class="pulse-dot ' + dotClass + '"></div><span>' + statusText + '</span>';
    }
    
    // Update service statuses
    if (data.services) {
        updateServiceStatus('db-status', data.services.database);
        updateServiceStatus('telegram-status', data.services.telegram);
        updateServiceStatus('mt5-status', data.services.mt5);
    }
    
    console.log('Health updated successfully');
}

function updateElement(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = text;
    }
}

function updateServiceStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        const isConnected = status === true;
        element.className = 'status-badge ' + (isConnected ? 'status-online' : 'status-offline');
        element.textContent = isConnected ? 'Connected' : 'Disconnected';
    }
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            if (tabName) {
                showTab(tabName);
            }
        });
    });
}

function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active from nav items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(nav => nav.classList.remove('active'));
    
    // Show selected tab
    const targetTab = document.getElementById('tab-' + tabName);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Activate nav item
    const activeNav = document.querySelector('[data-tab="' + tabName + '"]');
    if (activeNav) {
        activeNav.classList.add('active');
    }
}

// Dashboard action functions
function setupTelegram() {
    alert('Telegram setup functionality - Coming soon!');
}

function addMT5Terminal() {
    alert('MT5 terminal setup functionality - Coming soon!');
}

function createStrategy() {
    alert('Strategy creation functionality - Coming soon!');
}

function simulateSignal() {
    fetch('/api/simulate-signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: 'XAUUSD BUY at 2050 SL 2045 TP 2060' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Signal simulated:', data);
        alert('Signal simulated successfully!');
        loadDashboardData();
    })
    .catch(error => {
        console.error('Signal simulation error:', error);
        alert('Signal simulation failed!');
    });
}

function toggleShadowMode() {
    fetch('/api/toggle-shadow-mode', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        console.log('Shadow mode toggled:', data);
        const button = document.querySelector('[onclick="toggleShadowMode()"]');
        if (button && data.shadow_mode !== undefined) {
            button.textContent = data.shadow_mode ? 'Disable Shadow Mode' : 'Enable Shadow Mode';
        }
        alert('Shadow mode ' + (data.shadow_mode ? 'enabled' : 'disabled'));
    })
    .catch(error => {
        console.error('Shadow mode error:', error);
        alert('Shadow mode toggle failed!');
    });
}
