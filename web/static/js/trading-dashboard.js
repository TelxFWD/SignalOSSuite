/**
 * SignalOS Trading Dashboard
 * Advanced trading management interface
 */

class TradingDashboard {
    constructor() {
        this.currentTab = 'signals';
        this.init();
    }

    init() {
        console.log('Trading Dashboard initializing...');
        
        this.setupTabs();
        this.setupForms();
        this.loadInitialData();
        
        console.log('Trading Dashboard initialized');
    }

    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                
                // Update active button
                tabButtons.forEach(btn => {
                    btn.classList.remove('active', 'bg-primary', 'text-white');
                    btn.classList.add('text-gray-400');
                });
                button.classList.add('active', 'bg-primary', 'text-white');
                button.classList.remove('text-gray-400');
                
                // Show correct content
                tabContents.forEach(content => {
                    content.classList.add('hidden');
                });
                document.getElementById(`${tabName}-tab`).classList.remove('hidden');
                
                this.currentTab = tabName;
                this.loadTabData(tabName);
            });
        });
    }

    setupForms() {
        // Signal Parser Form
        const signalForm = document.getElementById('signal-parser-form');
        if (signalForm) {
            signalForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.parseSignal();
            });
        }

        // Telegram Session Form
        const telegramForm = document.getElementById('telegram-session-form');
        if (telegramForm) {
            telegramForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addTelegramSession();
            });
        }

        // Strategy Form
        const strategyForm = document.getElementById('strategy-form');
        if (strategyForm) {
            strategyForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createStrategy();
            });
        }

        // Stealth Form
        const stealthForm = document.getElementById('stealth-form');
        if (stealthForm) {
            stealthForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateStealthSettings();
            });
        }

        // Add Channel Button
        const addChannelBtn = document.getElementById('add-channel-btn');
        if (addChannelBtn) {
            addChannelBtn.addEventListener('click', () => {
                this.addTelegramChannel();
            });
        }

        // Refresh Orders Button
        const refreshBtn = document.getElementById('refresh-orders');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadActiveOrders();
            });
        }
    }

    async parseSignal() {
        const signalText = document.getElementById('signal-text').value;
        const providerId = document.getElementById('provider-id').value;
        const applyStrategy = document.getElementById('apply-strategy').checked;
        const applyStealth = document.getElementById('apply-stealth').checked;

        if (!signalText.trim()) {
            this.showError('Please enter signal text');
            return;
        }

        try {
            this.showLoading('parse-results');

            const response = await fetch('/api/signals/advanced-parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: signalText,
                    provider_id: providerId,
                    apply_strategy: applyStrategy,
                    apply_stealth: applyStealth
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.displayParseResults(result);
                this.showSuccess('Signal parsed successfully!');
            } else {
                this.showError(result.error || 'Failed to parse signal');
            }

        } catch (error) {
            console.error('Parse error:', error);
            this.showError('Network error occurred');
        }
    }

    displayParseResults(result) {
        const container = document.getElementById('parse-results');
        const original = result.original_parse;
        const processed = result.processed_signal;

        const html = `
            <div class="space-y-4">
                <div class="border-l-4 border-primary pl-4">
                    <h4 class="font-semibold text-primary">Original Parse</h4>
                    <div class="text-sm space-y-1 mt-2">
                        <div><span class="text-gray-400">Signal ID:</span> ${original.signal_id}</div>
                        <div><span class="text-gray-400">Confidence:</span> 
                            <span class="px-2 py-1 rounded text-xs ${this.getConfidenceColor(original.confidence)}">${original.confidence}</span>
                        </div>
                        <div><span class="text-gray-400">Type:</span> ${original.signal_type}</div>
                        <div><span class="text-gray-400">Pair:</span> ${original.pair || 'N/A'}</div>
                        <div><span class="text-gray-400">Action:</span> ${original.action || 'N/A'}</div>
                    </div>
                </div>

                <div class="border-l-4 border-accent pl-4">
                    <h4 class="font-semibold text-accent">Processed Signal</h4>
                    <div class="text-sm space-y-1 mt-2">
                        <div><span class="text-gray-400">Pair:</span> ${processed.pair || 'N/A'}</div>
                        <div><span class="text-gray-400">Action:</span> ${processed.action || 'N/A'}</div>
                        <div><span class="text-gray-400">Entry:</span> ${processed.entry || 'Market'}</div>
                        <div><span class="text-gray-400">Stop Loss:</span> ${processed.sl || 'N/A'}</div>
                        <div><span class="text-gray-400">Take Profit:</span> ${processed.tp || 'N/A'}</div>
                        <div><span class="text-gray-400">Lot Size:</span> ${processed.lot_size || 'N/A'}</div>
                    </div>
                </div>

                ${processed.stealth_actions ? `
                <div class="border-l-4 border-warning pl-4">
                    <h4 class="font-semibold text-warning">Stealth Actions</h4>
                    <div class="text-xs space-y-1 mt-2">
                        ${processed.stealth_actions.map(action => `<div>• ${action}</div>`).join('')}
                    </div>
                </div>
                ` : ''}

                <div class="flex space-x-2 mt-4">
                    <button onclick="tradingDashboard.executeSignal('${processed.id}')" 
                            class="px-3 py-1 bg-accent hover:bg-green-600 rounded text-sm transition-colors">
                        Execute Signal
                    </button>
                    <button onclick="tradingDashboard.saveSignal('${processed.id}')" 
                            class="px-3 py-1 bg-primary hover:bg-blue-600 rounded text-sm transition-colors">
                        Save for Later
                    </button>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    getConfidenceColor(confidence) {
        switch (confidence) {
            case 'HIGH': return 'bg-accent text-white';
            case 'MEDIUM': return 'bg-warning text-white';
            case 'LOW': return 'bg-danger text-white';
            default: return 'bg-gray-600 text-white';
        }
    }

    async addTelegramSession() {
        const phone = document.getElementById('phone').value;
        const apiId = document.getElementById('api-id').value;
        const apiHash = document.getElementById('api-hash').value;

        if (!phone || !apiId || !apiHash) {
            this.showError('Please fill all fields');
            return;
        }

        try {
            const response = await fetch('/api/telegram/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: `session_${Date.now()}`,
                    phone: phone,
                    api_id: apiId,
                    api_hash: apiHash
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess('Telegram session added successfully!');
                document.getElementById('telegram-session-form').reset();
                this.loadTelegramSessions();
            } else {
                this.showError(result.message || 'Failed to add session');
            }

        } catch (error) {
            console.error('Session error:', error);
            this.showError('Network error occurred');
        }
    }

    async createStrategy() {
        const name = document.getElementById('strategy-name').value;
        const type = document.getElementById('strategy-type').value;
        const description = document.getElementById('strategy-description').value;

        if (!name || !type) {
            this.showError('Please fill required fields');
            return;
        }

        try {
            const response = await fetch('/api/strategies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    strategy_id: `strategy_${Date.now()}`,
                    name: name,
                    strategy_type: type,
                    description: description
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess('Strategy created successfully!');
                document.getElementById('strategy-form').reset();
                this.loadStrategies();
            } else {
                this.showError(result.message || 'Failed to create strategy');
            }

        } catch (error) {
            console.error('Strategy error:', error);
            this.showError('Network error occurred');
        }
    }

    async updateStealthSettings() {
        const settings = {
            enabled: document.getElementById('stealth-enabled').checked,
            random_delay_min: parseFloat(document.getElementById('delay-min').value),
            random_delay_max: parseFloat(document.getElementById('delay-max').value),
            lot_randomization_percent: parseFloat(document.getElementById('lot-randomization').value),
            max_lots_per_pair: parseFloat(document.getElementById('max-lots-per-pair').value),
            remove_comments: document.getElementById('remove-comments').checked,
            mask_sl_tp: document.getElementById('mask-sl-tp').checked,
            synthetic_trades: document.getElementById('synthetic-trades').checked
        };

        try {
            const response = await fetch('/api/stealth/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess('Stealth settings updated successfully!');
                this.loadStealthStats();
            } else {
                this.showError(result.message || 'Failed to update settings');
            }

        } catch (error) {
            console.error('Stealth error:', error);
            this.showError('Network error occurred');
        }
    }

    async loadInitialData() {
        this.loadTabData(this.currentTab);
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'telegram':
                this.loadTelegramSessions();
                this.loadTelegramChannels();
                break;
            case 'strategies':
                this.loadStrategies();
                break;
            case 'stealth':
                this.loadStealthStats();
                break;
            case 'orders':
                this.loadActiveOrders();
                break;
        }
    }

    async loadTelegramSessions() {
        try {
            const response = await fetch('/api/telegram/sessions');
            const result = await response.json();

            const container = document.getElementById('sessions-list');
            if (result.total_sessions === 0) {
                container.innerHTML = '<div class="text-gray-400 text-center py-4">No sessions configured</div>';
                return;
            }

            const html = `
                <div class="space-y-3">
                    <div class="text-sm">
                        <div class="flex justify-between">
                            <span>Total Sessions:</span>
                            <span class="text-accent">${result.total_sessions}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Active:</span>
                            <span class="text-accent">${result.active_sessions}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Monitoring:</span>
                            <span class="${result.monitoring_active ? 'text-accent' : 'text-danger'}">
                                ${result.monitoring_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = html;

        } catch (error) {
            console.error('Load sessions error:', error);
        }
    }

    async loadTelegramChannels() {
        try {
            const response = await fetch('/api/telegram/channels');
            const result = await response.json();

            const container = document.getElementById('channels-list');
            if (!result.channels || result.channels.length === 0) {
                container.innerHTML = '<div class="text-gray-400 text-center py-4">No channels configured</div>';
                return;
            }

            const html = result.channels.map(channel => `
                <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                    <div>
                        <div class="font-medium">${channel.name}</div>
                        <div class="text-sm text-gray-400">${channel.username}</div>
                        <div class="text-xs text-gray-500">Signals: ${channel.signal_count}</div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-1 rounded text-xs ${channel.enabled ? 'bg-accent' : 'bg-gray-600'}">
                            ${channel.enabled ? 'Active' : 'Inactive'}
                        </span>
                        <button onclick="tradingDashboard.removeChannel('${channel.channel_id}')" 
                                class="text-danger hover:bg-red-600/20 p-1 rounded">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
            `).join('');

            container.innerHTML = html;
            lucide.createIcons();

        } catch (error) {
            console.error('Load channels error:', error);
        }
    }

    async loadStrategies() {
        try {
            const response = await fetch('/api/strategies');
            const result = await response.json();

            const container = document.getElementById('strategies-list');
            if (!result.strategies || result.strategies.length === 0) {
                container.innerHTML = '<div class="text-gray-400 text-center py-4">No strategies created</div>';
                return;
            }

            const html = result.strategies.map(strategy => `
                <div class="p-4 bg-gray-800 rounded-lg">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-medium">${strategy.name}</h4>
                        <span class="px-2 py-1 rounded text-xs ${strategy.active ? 'bg-accent' : 'bg-gray-600'}">
                            ${strategy.active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                    <div class="text-sm text-gray-400 mb-2">${strategy.description}</div>
                    <div class="text-xs space-y-1">
                        <div>Type: <span class="text-primary">${strategy.strategy_type}</span></div>
                        <div>Rules: <span class="text-accent">${strategy.rules_count}</span></div>
                        <div>Created: ${new Date(strategy.created_at).toLocaleDateString()}</div>
                    </div>
                    <div class="flex space-x-2 mt-3">
                        <button onclick="tradingDashboard.editStrategy('${strategy.strategy_id}')" 
                                class="px-2 py-1 bg-primary hover:bg-blue-600 rounded text-xs transition-colors">
                            Edit
                        </button>
                        <button onclick="tradingDashboard.deleteStrategy('${strategy.strategy_id}')" 
                                class="px-2 py-1 bg-danger hover:bg-red-600 rounded text-xs transition-colors">
                            Delete
                        </button>
                    </div>
                </div>
            `).join('');

            container.innerHTML = html;

        } catch (error) {
            console.error('Load strategies error:', error);
        }
    }

    async loadStealthStats() {
        try {
            const response = await fetch('/api/stealth/settings');
            const result = await response.json();

            const container = document.getElementById('stealth-stats');
            
            const html = `
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span>Stealth Mode:</span>
                        <span class="${result.stealth_enabled ? 'text-accent' : 'text-danger'}">
                            ${result.stealth_enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                    
                    ${result.trades_last_24h !== undefined ? `
                    <div>
                        <div class="text-sm text-gray-400 mb-2">Last 24 Hours</div>
                        <div class="space-y-1 text-sm">
                            <div class="flex justify-between">
                                <span>Total Trades:</span>
                                <span>${result.trades_last_24h}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Stealth Applied:</span>
                                <span>${result.stealth_trades_percentage?.toFixed(1) || 0}%</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Synthetic Trades:</span>
                                <span>${result.synthetic_trades || 0}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}

                    ${result.pair_exposures && Object.keys(result.pair_exposures).length > 0 ? `
                    <div>
                        <div class="text-sm text-gray-400 mb-2">Pair Exposures</div>
                        <div class="space-y-1 text-sm">
                            ${Object.entries(result.pair_exposures).map(([pair, exposure]) => `
                                <div class="flex justify-between">
                                    <span>${pair}:</span>
                                    <span>${exposure} lots</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}

                    ${result.settings ? `
                    <div>
                        <div class="text-sm text-gray-400 mb-2">Current Settings</div>
                        <div class="space-y-1 text-xs">
                            <div>Delay Range: ${result.settings.random_delay_range}</div>
                            <div>Lot Randomization: ${result.settings.lot_randomization}</div>
                            <div>Max Lots/Pair: ${result.settings.max_lots_per_pair}</div>
                            <div>Synthetic Frequency: ${result.settings.synthetic_frequency}</div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;

            container.innerHTML = html;

        } catch (error) {
            console.error('Load stealth stats error:', error);
        }
    }

    async loadActiveOrders() {
        try {
            const response = await fetch('/api/trading/orders');
            const result = await response.json();

            const container = document.getElementById('orders-list');
            if (!result.orders || result.orders.length === 0) {
                container.innerHTML = '<div class="text-gray-400 text-center py-8">No active orders</div>';
                return;
            }

            const html = `
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="border-b border-gray-700">
                                <th class="text-left py-2">Pair</th>
                                <th class="text-left py-2">Type</th>
                                <th class="text-left py-2">Size</th>
                                <th class="text-left py-2">Entry</th>
                                <th class="text-left py-2">SL</th>
                                <th class="text-left py-2">TP</th>
                                <th class="text-left py-2">Status</th>
                                <th class="text-left py-2">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.orders.map(order => `
                                <tr class="border-b border-gray-800">
                                    <td class="py-2 font-medium">${order.pair}</td>
                                    <td class="py-2">
                                        <span class="px-2 py-1 rounded text-xs ${order.type === 'BUY' ? 'bg-accent' : 'bg-danger'}">
                                            ${order.type}
                                        </span>
                                    </td>
                                    <td class="py-2">${order.lot_size}</td>
                                    <td class="py-2">${order.entry_price}</td>
                                    <td class="py-2">${order.stop_loss || '-'}</td>
                                    <td class="py-2">${order.take_profits?.join(', ') || '-'}</td>
                                    <td class="py-2">
                                        <span class="px-2 py-1 rounded text-xs bg-primary">
                                            ${order.status}
                                        </span>
                                    </td>
                                    <td class="py-2">
                                        <button onclick="tradingDashboard.closeOrder('${order.id}')" 
                                                class="px-2 py-1 bg-danger hover:bg-red-600 rounded text-xs transition-colors">
                                            Close
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            container.innerHTML = html;

        } catch (error) {
            console.error('Load orders error:', error);
        }
    }

    // Utility methods
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<div class="text-center py-4"><div class="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full mx-auto"></div></div>';
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-accent' : 'bg-danger'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Placeholder methods for future implementation
    async executeSignal(signalId) {
        this.showSuccess(`Signal ${signalId} queued for execution`);
    }

    async saveSignal(signalId) {
        this.showSuccess(`Signal ${signalId} saved`);
    }

    async removeChannel(channelId) {
        this.showSuccess('Channel removed');
        this.loadTelegramChannels();
    }

    async editStrategy(strategyId) {
        this.showSuccess('Strategy editor coming soon');
    }

    async deleteStrategy(strategyId) {
        if (confirm('Are you sure you want to delete this strategy?')) {
            this.showSuccess('Strategy deleted');
            this.loadStrategies();
        }
    }

    async closeOrder(orderId) {
        if (confirm('Are you sure you want to close this order?')) {
            this.showSuccess('Order closed');
            this.loadActiveOrders();
        }
    }

    async addTelegramChannel() {
        const name = document.getElementById('channel-name').value;
        const username = document.getElementById('channel-username').value;

        if (!name || !username) {
            this.showError('Please fill channel name and username');
            return;
        }

        // Simulate adding channel
        this.showSuccess('Channel added successfully');
        document.getElementById('channel-name').value = '';
        document.getElementById('channel-username').value = '';
        this.loadTelegramChannels();
    }
}

// Initialize dashboard
const tradingDashboard = new TradingDashboard();