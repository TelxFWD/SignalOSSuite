// Fixed SignalOS Dashboard - Robust Loading
class SignalOSDashboard {
    constructor() {
        this.socket = null;
        this.isInitialized = false;
        this.initialize();
    }

    async initialize() {
        try {
            console.log('Initializing SignalOS Dashboard...');
            
            // Initialize UI first
            this.initializeUI();
            
            // Setup navigation
            this.setupNavigation();
            
            // Load data
            await this.loadInitialData();
            
            // Setup WebSocket (non-blocking)
            this.setupWebSocket();
            
            // Setup icons if available
            this.initializeIcons();
            
            this.isInitialized = true;
            console.log('Dashboard initialization complete');
            
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showErrorFallback();
        }
    }

    initializeUI() {
        // Show the dashboard immediately
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.style.display = 'none';
        });
        
        const overviewTab = document.getElementById('tab-overview');
        if (overviewTab) {
            overviewTab.style.display = 'block';
            overviewTab.classList.add('active');
        }
        
        // Add fade-in animation
        document.body.style.opacity = '0';
        setTimeout(() => {
            document.body.style.transition = 'opacity 0.5s ease';
            document.body.style.opacity = '1';
        }, 100);
    }

    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = item.dataset.tab;
                if (tab) {
                    this.showTab(tab);
                }
            });
        });
    }

    showTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
            content.classList.remove('active');
        });
        
        const targetTab = document.getElementById(`tab-${tabName}`);
        if (targetTab) {
            targetTab.style.display = 'block';
            targetTab.classList.add('active');
        }

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadInitialData() {
        try {
            // Load health status
            const healthResponse = await fetch('/api/health');
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                this.updateSystemHealth(healthData);
            }

            // Load analytics
            try {
                const analyticsResponse = await fetch('/api/analytics/daily');
                if (analyticsResponse.ok) {
                    const analyticsData = await analyticsResponse.json();
                    console.log('Analytics data loaded:', analyticsData);
                    this.updateDashboardStats(analyticsData);
                } else {
                    console.error('Analytics API failed with status:', analyticsResponse.status);
                    this.updateDashboardStats({
                        trades_today: 0,
                        total_pips: 0,
                        win_rate: 0,
                        active_signals: 0
                    });
                }
            } catch (analyticsError) {
                console.error('Analytics fetch error:', analyticsError);
                this.updateDashboardStats({
                    trades_today: 0,
                    total_pips: 0,
                    win_rate: 0,
                    active_signals: 0
                });
            }

            this.addActivityLog('System', 'Dashboard loaded successfully', 'success');

        } catch (error) {
            console.error('Error loading initial data:', error);
            this.updateDashboardStats({
                trades_today: 0,
                total_pips: 0,
                win_rate: 0,
                active_signals: 0
            });
            this.addActivityLog('System', 'Dashboard loaded with limited functionality', 'warning');
        }
    }

    updateDashboardStats(data) {
        const stats = {
            'trades-today': data.trades_today || 0,
            'total-pips': data.total_pips || 0,
            'win-rate': `${data.win_rate || 0}%`,
            'active-signals': data.active_signals || 0
        };

        Object.entries(stats).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                // Add animation
                element.style.opacity = '0';
                setTimeout(() => {
                    element.style.transition = 'opacity 0.3s ease';
                    element.style.opacity = '1';
                }, 100);
            }
        });

        // Update change indicators with default values
        this.updateElement('trades-change', '+0% from yesterday');
        this.updateElement('pips-change', '+0 this week');
        this.updateElement('win-rate-change', 'Last 30 days');
        this.updateElement('signals-change', 'Processing');
    }

    updateSystemHealth(data) {
        // Update main system status
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            const isHealthy = data.status === 'healthy';
            statusElement.className = `status-badge ${isHealthy ? 'status-online' : 'status-warning'}`;
            statusElement.innerHTML = `
                <div class="pulse-dot ${isHealthy ? 'green' : 'yellow'}"></div>
                <span>${isHealthy ? 'All Systems Online' : 'Some Issues Detected'}</span>
            `;
        }

        // Update individual service statuses
        const services = data.services || {};
        this.updateServiceStatus('db-status', services.database || 'Unknown');
        this.updateServiceStatus('telegram-status', services.telegram || 'Disconnected');
        this.updateServiceStatus('mt5-status', services.mt5 || 'Disconnected');
    }

    updateServiceStatus(elementId, status) {
        const element = document.getElementById(elementId);
        if (element) {
            // Convert boolean or other types to proper status string
            const statusText = this.formatStatusText(status);
            element.textContent = statusText;
            const statusClass = this.getStatusClass(status);
            element.className = `status-badge ${statusClass}`;
        }
    }

    formatStatusText(status) {
        if (typeof status === 'boolean') {
            return status ? 'Connected' : 'Disconnected';
        }
        if (typeof status === 'string') {
            return status;
        }
        return 'Unknown';
    }

    getStatusClass(status) {
        // Handle boolean values
        if (typeof status === 'boolean') {
            return status ? 'status-online' : 'status-offline';
        }
        
        // Handle string values
        if (typeof status === 'string') {
            const statusLower = status.toLowerCase();
            if (statusLower.includes('connected') || statusLower.includes('online') || statusLower.includes('healthy')) {
                return 'status-online';
            } else if (statusLower.includes('warning') || statusLower.includes('partial')) {
                return 'status-warning';
            } else {
                return 'status-offline';
            }
        }
        
        // Default for unknown types
        return 'status-offline';
    }

    setupWebSocket() {
        try {
            if (typeof io !== 'undefined') {
                this.socket = io({
                    timeout: 5000,
                    transports: ['polling'],
                    forceNew: true
                });

                this.socket.on('connect', () => {
                    console.log('WebSocket connected');
                    this.addActivityLog('WebSocket', 'Connected successfully', 'success');
                });

                this.socket.on('disconnect', () => {
                    console.log('WebSocket disconnected');
                });

                this.socket.on('connect_error', (error) => {
                    console.log('WebSocket connection error (non-critical):', error);
                });
            }
        } catch (error) {
            console.log('WebSocket setup skipped (non-critical):', error);
        }
    }

    initializeIcons() {
        try {
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        } catch (error) {
            console.log('Icons not available (non-critical):', error);
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    addActivityLog(event, details, status = 'info') {
        const activityLog = document.getElementById('activity-log');
        if (activityLog) {
            const time = new Date().toLocaleTimeString();
            const statusClass = status === 'success' ? 'status-online' : 
                               status === 'error' ? 'status-offline' : 'status-warning';
            
            // Remove "No recent activity" message if it exists
            const noActivity = activityLog.querySelector('td[colspan="3"]');
            if (noActivity) {
                noActivity.parentElement.remove();
            }
            
            const row = document.createElement('tr');
            row.className = 'table-row';
            row.innerHTML = `
                <td style="color: var(--dark-400);">${time}</td>
                <td>${event}</td>
                <td><span class="status-badge ${statusClass}">${status}</span></td>
                <td style="color: var(--dark-300);">${details}</td>
            `;
            
            activityLog.insertBefore(row, activityLog.firstChild);
            
            // Keep only last 10 entries
            while (activityLog.children.length > 10) {
                activityLog.removeChild(activityLog.lastChild);
            }
        }
    }

    async loadTabData(tabName) {
        try {
            switch (tabName) {
                case 'telegram':
                    this.addActivityLog('Navigation', 'Telegram tab opened', 'info');
                    break;
                case 'mt5':
                    this.addActivityLog('Navigation', 'MT5 tab opened', 'info');
                    break;
                case 'strategies':
                    this.addActivityLog('Navigation', 'Strategies tab opened', 'info');
                    break;
                case 'analytics':
                    this.addActivityLog('Navigation', 'Analytics tab opened', 'info');
                    break;
                case 'settings':
                    this.addActivityLog('Navigation', 'Settings tab opened', 'info');
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${tabName} data:`, error);
        }
    }

    showErrorFallback() {
        document.body.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--dark-950);">
                <div style="text-align: center; color: white;">
                    <h1 style="font-size: 2rem; margin-bottom: 1rem; color: var(--primary-400);">SignalOS</h1>
                    <p style="margin-bottom: 2rem; color: var(--dark-300);">Dashboard initialization failed</p>
                    <button onclick="location.reload()" style="padding: 1rem 2rem; background: var(--primary-500); color: white; border: none; border-radius: 0.5rem; cursor: pointer;">
                        Reload Dashboard
                    </button>
                </div>
            </div>
        `;
    }
}

// Global functions for UI interactions
function showTab(tabName) {
    if (window.signalOSDashboard) {
        window.signalOSDashboard.showTab(tabName);
    }
}

function simulateSignal() {
    if (window.signalOSDashboard) {
        window.signalOSDashboard.addActivityLog('Test', 'Signal simulation started', 'info');
        
        fetch('/api/simulate-signal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: 'XAUUSD', action: 'BUY', entry: 2000.00 })
        })
        .then(response => response.json())
        .then(() => {
            window.signalOSDashboard.addActivityLog('Test', 'Signal simulation completed', 'success');
        })
        .catch(() => {
            window.signalOSDashboard.addActivityLog('Test', 'Signal simulation failed', 'error');
        });
    }
}

function setupTelegram() {
    if (window.signalOSDashboard) {
        window.signalOSDashboard.addActivityLog('Telegram', 'Setup initiated', 'info');
    }
}

function addMT5Terminal() {
    if (window.signalOSDashboard) {
        window.signalOSDashboard.addActivityLog('MT5', 'Terminal setup initiated', 'info');
    }
}

function createStrategy() {
    if (window.signalOSDashboard) {
        window.signalOSDashboard.addActivityLog('Strategy', 'Strategy creation initiated', 'info');
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing dashboard...');
    window.signalOSDashboard = new SignalOSDashboard();
});

// Fallback initialization
setTimeout(() => {
    if (!window.signalOSDashboard) {
        console.log('Fallback initialization...');
        window.signalOSDashboard = new SignalOSDashboard();
    }
}, 1000);