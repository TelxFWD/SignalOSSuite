// Simple SignalOS Dashboard - Direct DOM Updates
// Add global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple dashboard initializing...');
    
    // Show the dashboard immediately
    showDashboard();
    
    // Load data immediately
    loadDashboardData();
    
    // Setup navigation
    setupNavigation();
    
    // Setup real-time updates
    setTimeout(loadDashboardData, 2000);
    setInterval(loadDashboardData, 30000);
});

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