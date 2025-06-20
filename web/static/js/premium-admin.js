// Premium SignalOS Admin Panel - Modern Management Interface
class PremiumAdminPanel {
    constructor() {
        this.charts = {};
        this.currentTab = 'dashboard';
        this.metricsInterval = null;
        this.initialize();
    }

    async initialize() {
        await this.initializeFeatherIcons();
        this.setupEventListeners();
        this.setupCharts();
        this.startMetricsPolling();
        this.loadDashboardData();
    }

    async initializeFeatherIcons() {
        if (typeof feather !== 'undefined') {
            feather.replace();
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
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        try {
            switch (tabName) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'users':
                    await this.loadUsersData();
                    break;
                case 'signals':
                    await this.loadSignalsData();
                    break;
                case 'system':
                    await this.loadSystemData();
                    break;
                case 'logs':
                    await this.loadLogsData();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${tabName} data:`, error);
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/admin/api/system-metrics');
            if (response.ok) {
                const data = await response.json();
                this.updateDashboardMetrics(data);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    updateDashboardMetrics(data) {
        const metrics = {
            'admin-total-users': data.total_users || 0,
            'admin-daily-signals': data.daily_signals || 0,
            'admin-total-trades': data.total_trades || 0,
            'admin-system-uptime': `${data.uptime || 99.9}%`
        };

        Object.entries(metrics).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateValue(element, element.textContent, value);
            }
        });

        // Update system health indicators
        this.updateSystemHealthIndicators(data);
    }

    updateSystemHealthIndicators(data) {
        const healthData = data.health || {};
        
        // Database status
        const dbStatus = document.getElementById('admin-db-status');
        if (dbStatus) {
            const isHealthy = healthData.database === 'connected';
            dbStatus.className = `status-badge ${isHealthy ? 'status-online' : 'status-offline'}`;
            dbStatus.textContent = isHealthy ? 'Healthy' : 'Issues';
        }

        // Update specific metrics
        this.updateElement('db-active-connections', healthData.db_connections || 5);
        this.updateElement('db-pool-size', healthData.db_pool_size || 10);
        this.updateElement('parser-accuracy', `${healthData.parser_accuracy || 95}%`);
        this.updateElement('parser-queue', healthData.parser_queue || 0);
        this.updateElement('ws-clients', healthData.ws_clients || 12);
        this.updateElement('memory-used', healthData.memory_used || '156 MB');
        this.updateElement('memory-available', healthData.memory_available || '2.8 GB');
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
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

    setupCharts() {
        // Signal Performance Chart
        const signalCtx = document.getElementById('signal-performance-chart');
        if (signalCtx) {
            this.charts.signalPerformance = new Chart(signalCtx, {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{
                        label: 'Signals Processed',
                        data: [45, 78, 125, 89, 156, 203],
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: this.getChartOptions('Signals per Hour')
            });
        }

        // User Activity Chart
        const userCtx = document.getElementById('user-activity-chart');
        if (userCtx) {
            this.charts.userActivity = new Chart(userCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Active Users', 'Idle Users', 'Offline Users'],
                    datasets: [{
                        data: [45, 15, 12],
                        backgroundColor: [
                            'rgb(34, 197, 94)',
                            'rgb(245, 158, 11)',
                            'rgb(107, 114, 128)'
                        ],
                        borderWidth: 0
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
                    }
                }
            });
        }

        // System Metrics Chart
        const systemCtx = document.getElementById('system-metrics-chart');
        if (systemCtx) {
            this.charts.systemMetrics = new Chart(systemCtx, {
                type: 'bar',
                data: {
                    labels: ['CPU Usage', 'Memory', 'Disk I/O', 'Network', 'Database'],
                    datasets: [{
                        label: 'System Load (%)',
                        data: [35, 45, 12, 28, 18],
                        backgroundColor: [
                            'rgba(34, 197, 94, 0.8)',
                            'rgba(34, 197, 94, 0.6)',
                            'rgba(34, 197, 94, 0.4)',
                            'rgba(34, 197, 94, 0.6)',
                            'rgba(34, 197, 94, 0.8)'
                        ],
                        borderColor: 'rgb(34, 197, 94)',
                        borderWidth: 1
                    }]
                },
                options: this.getChartOptions('System Performance')
            });
        }
    }

    getChartOptions(title) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
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
        };
    }

    startMetricsPolling() {
        // Update metrics every 30 seconds
        this.metricsInterval = setInterval(() => {
            if (this.currentTab === 'dashboard') {
                this.loadDashboardData();
            }
        }, 30000);
    }

    async loadUsersData() {
        try {
            const response = await fetch('/admin/api/users');
            if (response.ok) {
                const users = await response.json();
                this.renderUsersTable(users);
            }
        } catch (error) {
            console.error('Error loading users data:', error);
        }
    }

    renderUsersTable(users) {
        const tbody = document.getElementById('users-table');
        if (tbody) {
            tbody.innerHTML = users.map(user => `
                <tr class="table-row">
                    <td>${user.id}</td>
                    <td>${user.email}</td>
                    <td>
                        <span class="status-badge ${user.active ? 'status-online' : 'status-offline'}">
                            ${user.license_type || 'Free'}
                        </span>
                    </td>
                    <td>
                        <span class="status-badge ${user.active ? 'status-online' : 'status-offline'}">
                            ${user.active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td style="color: var(--dark-400);">${user.last_login || 'Never'}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding: 0.5rem 1rem; font-size: 0.75rem;" 
                                onclick="editUser(${user.id})">Edit</button>
                    </td>
                </tr>
            `).join('');
        }
    }

    async loadLogsData() {
        try {
            const response = await fetch('/admin/api/logs');
            if (response.ok) {
                const logs = await response.json();
                this.renderLogs(logs);
            }
        } catch (error) {
            console.error('Error loading logs data:', error);
        }
    }

    renderLogs(logs) {
        const container = document.getElementById('logs-container');
        if (container) {
            container.innerHTML = logs.map(log => `
                <div style="padding: 0.75rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-family: 'Courier New', monospace; font-size: 0.875rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: var(--dark-400);">${log.timestamp}</span>
                        <span class="status-badge ${this.getLogLevelClass(log.level)}">${log.level}</span>
                    </div>
                    <div style="color: var(--dark-200);">${log.message}</div>
                    ${log.details ? `<div style="color: var(--dark-400); font-size: 0.75rem; margin-top: 0.25rem;">${log.details}</div>` : ''}
                </div>
            `).join('');
        }
    }

    getLogLevelClass(level) {
        switch (level.toLowerCase()) {
            case 'error': return 'status-offline';
            case 'warning': return 'status-warning';
            case 'info': return 'status-online';
            default: return 'status-badge';
        }
    }

    showLoading(show = true) {
        const overlay = document.getElementById('admin-loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }
}

// Global Admin Functions
function showAdminTab(tabName) {
    if (window.adminPanel) {
        window.adminPanel.showTab(tabName);
    }
}

function refreshSystemMetrics() {
    if (window.adminPanel) {
        window.adminPanel.showLoading(true);
        window.adminPanel.loadDashboardData().finally(() => {
            window.adminPanel.showLoading(false);
        });
    }
}

function debugSignalPipeline() {
    if (window.adminPanel) {
        window.adminPanel.showLoading(true);
        
        fetch('/admin/api/debug-pipeline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Pipeline debug result:', data);
            alert('Pipeline test completed. Check console for details.');
        })
        .catch(error => {
            console.error('Error debugging pipeline:', error);
            alert('Pipeline test failed. Check console for details.');
        })
        .finally(() => {
            window.adminPanel.showLoading(false);
        });
    }
}

function editUser(userId) {
    alert(`Edit user functionality would open for user ID: ${userId}`);
}

// Initialize admin panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new PremiumAdminPanel();
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
    if (window.adminPanel && window.adminPanel.charts) {
        Object.values(window.adminPanel.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }
});