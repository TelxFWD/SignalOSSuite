// Premium SignalOS Dashboard - Modern Trading Platform Interface
class PremiumDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.currentTab = 'overview';
        this.isLoggedIn = false;
        this.userProfile = null;
        this.initialize();
    }

    async initialize() {
        await this.initializeFeatherIcons();
        this.setupSocketIO();
        this.setupEventListeners();
        this.loadUserProfile();
        this.updateSystemHealth();
        this.startHealthMonitoring();
        this.setupCharts();
        this.loadDashboardData();
    }

    async initializeFeatherIcons() {
        // Initialize Feather icons with timeout
        try {
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        } catch (error) {
            console.log('Feather icons not available:', error);
        }
    }

    setupSocketIO() {
        try {
            this.socket = io({
                timeout: 5000,
                transports: ['polling', 'websocket']
            });
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
            });

            this.socket.on('connect_error', (error) => {
                console.log('WebSocket connection error:', error);
                this.updateConnectionStatus(false);
            });

            this.socket.on('health_update', (data) => {
                this.updateSystemHealth(data);
            });

            this.socket.on('signal_update', (data) => {
                this.handleSignalUpdate(data);
            });

            this.socket.on('trade_update', (data) => {
                this.handleTradeUpdate(data);
            });
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = item.dataset.tab;
                if (tab) {
                    this.showTab(tab);
                }
            });
        });

        // Settings toggles
        const shadowModeToggle = document.getElementById('shadow-mode');
        if (shadowModeToggle) {
            shadowModeToggle.addEventListener('change', (e) => {
                this.toggleShadowMode(e.target.checked);
            });
        }

        // Responsive sidebar
        this.setupResponsiveSidebar();
    }

    setupResponsiveSidebar() {
        if (window.innerWidth <= 768) {
            document.body.addEventListener('click', (e) => {
                const sidebar = document.querySelector('.sidebar');
                if (!sidebar.contains(e.target) && !e.target.closest('.menu-toggle')) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }

    showTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });
        
        const targetTab = document.getElementById(`tab-${tabName}`);
        if (targetTab) {
            targetTab.classList.add('active');
            targetTab.style.display = 'block';
            
            // Add slide animation
            targetTab.style.opacity = '0';
            targetTab.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                targetTab.style.transition = 'all 0.3s ease';
                targetTab.style.opacity = '1';
                targetTab.style.transform = 'translateY(0)';
            }, 10);
        }

        this.currentTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        try {
            switch (tabName) {
                case 'overview':
                    await this.loadOverviewData();
                    break;
                case 'telegram':
                    await this.loadTelegramData();
                    break;
                case 'mt5':
                    await this.loadMT5Data();
                    break;
                case 'strategies':
                    await this.loadStrategiesData();
                    break;
                case 'analytics':
                    await this.loadAnalyticsData();
                    break;
                case 'settings':
                    await this.loadSettingsData();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${tabName} data:`, error);
        }
    }

    async loadOverviewData() {
        try {
            const response = await fetch('/api/analytics/daily');
            if (response.ok) {
                const data = await response.json();
                this.updateOverviewStats(data);
            }
        } catch (error) {
            console.error('Error loading overview data:', error);
        }
    }

    updateOverviewStats(data) {
        const elements = {
            'trades-today': data.trades_today || 0,
            'total-pips': data.total_pips || 0,
            'win-rate': `${data.win_rate || 0}%`,
            'active-signals': data.active_signals || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateValue(element, element.textContent, value);
            }
        });

        // Update change indicators
        this.updateChangeIndicators(data);
    }

    updateChangeIndicators(data) {
        const changes = {
            'trades-change': data.trades_change || '+0% from yesterday',
            'pips-change': data.pips_change || '+0 this week',
            'win-rate-change': 'Last 30 days',
            'signals-change': 'Processing'
        };

        Object.entries(changes).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                
                // Add appropriate class based on change
                if (value.includes('+')) {
                    element.className = 'stat-change positive';
                } else if (value.includes('-')) {
                    element.className = 'stat-change negative';
                } else {
                    element.className = 'stat-change';
                }
            }
        });
    }

    animateValue(element, start, end) {
        const startValue = parseInt(start) || 0;
        const endValue = parseInt(end) || 0;
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(startValue + (endValue - startValue) * progress);
            element.textContent = typeof end === 'string' && end.includes('%') 
                ? `${current}%` 
                : current;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    async updateSystemHealth(data = null) {
        if (!data) {
            try {
                const response = await fetch('/api/health');
                if (response.ok) {
                    data = await response.json();
                }
            } catch (error) {
                console.error('Error fetching health data:', error);
                data = { status: 'error', services: {} };
            }
        }

        this.updateHealthIndicators(data);
        this.updateSystemStatusBadge(data);
    }

    updateHealthIndicators(data) {
        const services = data.services || {};
        
        const healthMap = {
            'db-status': services.database || 'Unknown',
            'telegram-status': services.telegram || 'Disconnected',
            'mt5-status': services.mt5 || 'Disconnected'
        };

        Object.entries(healthMap).forEach(([id, status]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = status;
                element.className = `status-badge ${this.getStatusClass(status)}`;
            }
        });
    }

    getStatusClass(status) {
        const statusLower = status.toLowerCase();
        if (statusLower.includes('connected') || statusLower.includes('online')) {
            return 'status-online';
        } else if (statusLower.includes('warning') || statusLower.includes('partial')) {
            return 'status-warning';
        } else {
            return 'status-offline';
        }
    }

    updateSystemStatusBadge(data) {
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            const isHealthy = data.status === 'healthy';
            statusElement.className = `status-badge ${isHealthy ? 'status-online' : 'status-warning'}`;
            statusElement.innerHTML = `
                <div class="pulse-dot ${isHealthy ? 'green' : 'yellow'}"></div>
                <span>${isHealthy ? 'All Systems Online' : 'Some Issues Detected'}</span>
            `;
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('system-status');
        if (statusElement && !connected) {
            statusElement.className = 'status-badge status-offline';
            statusElement.innerHTML = `
                <div class="pulse-dot red"></div>
                <span>Connection Lost</span>
            `;
        }
    }

    startHealthMonitoring() {
        // Update health every 30 seconds
        setInterval(() => {
            this.updateSystemHealth();
        }, 30000);
    }

    setupCharts() {
        // Setup performance chart with error handling
        try {
            const ctx = document.getElementById('performance-chart');
            if (ctx && typeof Chart !== 'undefined') {
                this.charts.performance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Daily Pips',
                        data: [0, 0, 0, 0, 0, 0, 0],
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#f1f5f9'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            }
                        },
                        y: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            }
                        }
                    }
                }
            });
        }
    }

    async loadUserProfile() {
        try {
            // In a real application, this would fetch user data
            this.userProfile = {
                name: 'Demo User',
                plan: 'Pro Plan',
                avatar: 'DU'
            };
        } catch (error) {
            console.error('Error loading user profile:', error);
        }
    }

    async loadDashboardData() {
        try {
            await this.loadOverviewData();
            this.addActivityLog('System', 'Dashboard loaded successfully', 'success');
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.addActivityLog('System', 'Error loading dashboard data', 'error');
        }
    }

    addActivityLog(event, details, status) {
        const activityLog = document.getElementById('activity-log');
        if (activityLog) {
            const time = new Date().toLocaleTimeString();
            const statusClass = status === 'success' ? 'status-online' : 
                               status === 'error' ? 'status-offline' : 'status-warning';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="color: var(--dark-400);">${time}</td>
                <td>${event}</td>
                <td><span class="status-badge ${statusClass}">${status}</span></td>
                <td style="color: var(--dark-300);">${details}</td>
            `;
            
            // Remove "No recent activity" message if it exists
            const noActivity = activityLog.querySelector('td[colspan="3"]');
            if (noActivity) {
                noActivity.parentElement.remove();
            }
            
            activityLog.insertBefore(row, activityLog.firstChild);
            
            // Keep only last 10 entries
            while (activityLog.children.length > 10) {
                activityLog.removeChild(activityLog.lastChild);
            }
        }
    }

    handleSignalUpdate(data) {
        this.addActivityLog('Signal', `${data.action} ${data.symbol}`, 'success');
        
        // Update active signals count
        const activeSignalsElement = document.getElementById('active-signals');
        if (activeSignalsElement) {
            const current = parseInt(activeSignalsElement.textContent) || 0;
            this.animateValue(activeSignalsElement, current, current + 1);
        }
    }

    handleTradeUpdate(data) {
        this.addActivityLog('Trade', `${data.action} ${data.symbol} - ${data.status}`, 
                          data.status === 'completed' ? 'success' : 'warning');
        
        // Update trades today count
        const tradesElement = document.getElementById('trades-today');
        if (tradesElement && data.status === 'completed') {
            const current = parseInt(tradesElement.textContent) || 0;
            this.animateValue(tradesElement, current, current + 1);
        }
    }

    async toggleShadowMode(enabled) {
        try {
            const response = await fetch('/api/toggle-shadow-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled: enabled })
            });

            if (response.ok) {
                this.addActivityLog('Settings', `Shadow mode ${enabled ? 'enabled' : 'disabled'}`, 'success');
            } else {
                throw new Error('Failed to toggle shadow mode');
            }
        } catch (error) {
            console.error('Error toggling shadow mode:', error);
            this.addActivityLog('Settings', 'Error updating shadow mode', 'error');
        }
    }

    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    // API Integration Methods
    async loadTelegramData() {
        try {
            const response = await fetch('/api/telegram/sessions');
            if (response.ok) {
                const data = await response.json();
                this.renderTelegramSessions(data);
            }
        } catch (error) {
            console.error('Error loading Telegram data:', error);
        }
    }

    async loadMT5Data() {
        try {
            const response = await fetch('/api/mt5/terminals');
            if (response.ok) {
                const data = await response.json();
                this.renderMT5Terminals(data);
            }
        } catch (error) {
            console.error('Error loading MT5 data:', error);
        }
    }

    async loadStrategiesData() {
        try {
            const response = await fetch('/api/strategies');
            if (response.ok) {
                const data = await response.json();
                this.renderStrategies(data);
            }
        } catch (error) {
            console.error('Error loading strategies data:', error);
        }
    }

    renderTelegramSessions(sessions) {
        // Implementation for rendering Telegram sessions
        console.log('Telegram sessions:', sessions);
    }

    renderMT5Terminals(terminals) {
        // Implementation for rendering MT5 terminals
        console.log('MT5 terminals:', terminals);
    }

    renderStrategies(strategies) {
        // Implementation for rendering strategies
        console.log('Strategies:', strategies);
    }
}

// Global Functions
function showTab(tabName) {
    if (window.dashboard) {
        window.dashboard.showTab(tabName);
    }
}

function simulateSignal() {
    if (window.dashboard) {
        window.dashboard.showLoading(true);
        
        fetch('/api/simulate-signal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: 'XAUUSD',
                action: 'BUY',
                entry: 2000.00
            })
        })
        .then(response => response.json())
        .then(data => {
            window.dashboard.addActivityLog('Test', 'Signal simulation completed', 'success');
        })
        .catch(error => {
            console.error('Error simulating signal:', error);
            window.dashboard.addActivityLog('Test', 'Signal simulation failed', 'error');
        })
        .finally(() => {
            window.dashboard.showLoading(false);
        });
    }
}

function setupTelegram() {
    if (window.dashboard) {
        window.dashboard.addActivityLog('Telegram', 'Setup initiated', 'warning');
        // Implementation for Telegram setup
    }
}

function addMT5Terminal() {
    if (window.dashboard) {
        window.dashboard.addActivityLog('MT5', 'Terminal setup initiated', 'warning');
        // Implementation for MT5 terminal setup
    }
}

function createStrategy() {
    if (window.dashboard) {
        window.dashboard.addActivityLog('Strategy', 'Strategy creation initiated', 'warning');
        // Implementation for strategy creation
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PremiumDashboard();
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
    if (window.dashboard) {
        window.dashboard.setupResponsiveSidebar();
    }
});