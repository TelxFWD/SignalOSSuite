/**
 * SignalOS Premium V2 Dashboard
 * Modern dark theme with glassmorphism and animations
 */

class PremiumDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.isLoading = false;
        this.shadowMode = true;
        
        this.init();
    }

    init() {
        console.log('SignalOS Premium Dashboard V2 loading...');
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        this.loadDashboardData();
        
        // Setup auto-refresh
        this.setupAutoRefresh();
        
        // Initialize WebSocket
        this.initializeWebSocket();
        
        // Initialize charts
        this.initializeCharts();

        console.log('Dashboard initialized');
    }

    setupEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(item.dataset.tab);
            });
        });

        // Shadow mode toggle
        const shadowToggle = document.getElementById('toggle-shadow-mode');
        if (shadowToggle) {
            shadowToggle.addEventListener('click', () => {
                this.toggleShadowMode();
            });
        }

        // Simulate signal button
        const simulateBtn = document.getElementById('simulate-signal');
        if (simulateBtn) {
            simulateBtn.addEventListener('click', () => {
                this.simulateSignal();
            });
        }
    }

    switchTab(tabName) {
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active', 'bg-primary/20', 'text-primary', 'border', 'border-primary/30');
            item.classList.add('text-text-secondary');
        });

        const activeItem = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeItem) {
            activeItem.classList.add('active', 'bg-primary/20', 'text-primary', 'border', 'border-primary/30');
            activeItem.classList.remove('text-text-secondary');
        }

        // Load tab content (placeholder for now)
        this.showToast(`Switched to ${tabName} tab`, 'info');
    }

    async loadDashboardData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        console.log('Loading dashboard data...');

        try {
            const [healthData, analyticsData] = await Promise.all([
                this.fetchData('/api/health'),
                this.fetchData('/api/analytics/daily')
            ]);

            if (healthData) {
                this.updateSystemHealth(healthData);
            }

            if (analyticsData) {
                this.updateAnalytics(analyticsData);
                this.updateChart(analyticsData.daily_stats);
            }

            this.updateLastUpdated();
            console.log('Dashboard data loaded successfully');

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showToast('Failed to load dashboard data', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    async fetchData(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Fetch error for ${url}:`, error);
            return null;
        }
    }

    updateAnalytics(data) {
        // Animate stats updates
        this.animateNumber('total-pips', data.total_pips || 0);
        this.animateNumber('win-rate', data.win_rate || 0, '%');
        this.animateNumber('trades-today', data.trades_today || 0);
        this.animateNumber('active-signals', data.active_signals || 0);

        // Update change indicators
        this.updateElement('pips-change', data.pips_change || '--');
        this.updateElement('trades-change', data.trades_change || '--');

        console.log('Analytics updated:', data);
    }

    updateSystemHealth(data) {
        const statusElement = document.getElementById('system-status');
        const healthContainer = document.getElementById('health-status');
        
        if (statusElement) {
            const isHealthy = data.status === 'healthy';
            const statusText = isHealthy ? 'All Systems Online' : 'System Issues Detected';
            const statusClass = isHealthy ? 'status-online' : 'status-warning';
            
            statusElement.innerHTML = `
                <span class="status-dot ${statusClass}"></span>
                <span class="text-sm font-medium">${statusText}</span>
            `;
        }

        if (healthContainer && data.services) {
            healthContainer.innerHTML = '';
            
            const services = [
                { name: 'Database', status: data.services.database, icon: 'database' },
                { name: 'MT5 Terminal', status: data.services.mt5, icon: 'monitor' },
                { name: 'Telegram API', status: data.services.telegram, icon: 'message-circle' }
            ];

            services.forEach(service => {
                const serviceElement = this.createHealthCard(service);
                healthContainer.appendChild(serviceElement);
            });
        }

        console.log('Health updated:', data);
    }

    createHealthCard(service) {
        const div = document.createElement('div');
        div.className = 'glass-card p-4 rounded-lg animate-fade-in';
        
        const statusClass = service.status ? 'text-success' : 'text-danger';
        const statusText = service.status ? 'Connected' : 'Disconnected';
        const statusBadge = service.status ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger';

        div.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 ${statusBadge} rounded-lg flex items-center justify-center">
                        <i data-lucide="${service.icon}" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <p class="font-medium">${service.name}</p>
                        <p class="text-sm text-text-secondary">Service Status</p>
                    </div>
                </div>
                <span class="px-3 py-1 rounded-full text-xs font-medium ${statusBadge}">
                    ${statusText}
                </span>
            </div>
        `;

        // Re-initialize icons for the new element
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        return div;
    }

    animateNumber(elementId, value, suffix = '') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startValue = parseInt(element.textContent) || 0;
        const endValue = parseInt(value) || 0;
        const duration = 1000;
        const steps = 60;
        const stepValue = (endValue - startValue) / steps;
        let currentStep = 0;

        const animation = setInterval(() => {
            currentStep++;
            const currentValue = Math.round(startValue + (stepValue * currentStep));
            element.textContent = currentValue + suffix;

            if (currentStep >= steps) {
                clearInterval(animation);
                element.textContent = endValue + suffix;
            }
        }, duration / steps);
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateLastUpdated() {
        const element = document.getElementById('last-updated');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }

    initializeCharts() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Profit/Loss',
                    data: [],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(55, 65, 81, 0.3)'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(55, 65, 81, 0.3)'
                        },
                        ticks: {
                            color: '#9CA3AF'
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 4,
                        hoverRadius: 6
                    }
                }
            }
        });
    }

    updateChart(dailyStats) {
        if (!this.charts.performance || !dailyStats) return;

        const labels = dailyStats.map(stat => {
            const date = new Date(stat.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        
        const data = dailyStats.map(stat => stat.profit || 0);

        this.charts.performance.data.labels = labels;
        this.charts.performance.data.datasets[0].data = data;
        this.charts.performance.update('active');
    }

    toggleShadowMode() {
        this.shadowMode = !this.shadowMode;
        
        const button = document.getElementById('toggle-shadow-mode');
        if (button) {
            if (this.shadowMode) {
                button.classList.add('bg-primary/20');
                button.classList.remove('bg-gray-600/20');
            } else {
                button.classList.remove('bg-primary/20');
                button.classList.add('bg-gray-600/20');
            }
        }

        this.showToast(`Shadow Mode ${this.shadowMode ? 'Enabled' : 'Disabled'}`, 'success');
        
        // Send to API
        fetch('/api/settings/shadow-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: this.shadowMode })
        }).catch(console.error);
    }

    async simulateSignal() {
        this.showToast('Simulating signal...', 'info');
        
        try {
            const response = await fetch('/api/signals/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pair: 'EURUSD',
                    action: 'BUY'
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.showToast('Signal simulated successfully!', 'success');
                console.log('Signal simulated:', data);
            } else {
                throw new Error('Failed to simulate signal');
            }
        } catch (error) {
            console.error('Simulate signal error:', error);
            this.showToast('Failed to simulate signal', 'error');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        const typeClasses = {
            success: 'bg-success/20 border-success/30 text-success',
            error: 'bg-danger/20 border-danger/30 text-danger',
            warning: 'bg-warning/20 border-warning/30 text-warning',
            info: 'bg-primary/20 border-primary/30 text-primary'
        };

        toast.className = `glass-card p-4 rounded-lg border ${typeClasses[type]} animate-slide-up max-w-sm`;
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <i data-lucide="${this.getToastIcon(type)}" class="w-5 h-5"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;

        container.appendChild(toast);
        
        // Re-initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        return icons[type] || 'info';
    }

    setupAutoRefresh() {
        // Refresh data every 30 seconds
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    initializeWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('WebSocket connected');
                this.showToast('Real-time connection established', 'success');
            });

            this.socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.showToast('Real-time connection lost', 'warning');
            });

            this.socket.on('status_update', (data) => {
                this.updateSystemHealth(data);
            });

            this.socket.on('new_signal', (data) => {
                this.showToast(`New signal: ${data.pair} ${data.action}`, 'info');
            });

        } catch (error) {
            console.error('WebSocket initialization error:', error);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PremiumDashboard();
});