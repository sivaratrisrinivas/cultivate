// Global variables
let isMonitoring = false;
let startTime = null;
let eventsList = [];
let pollingInterval = 60; // Default polling interval in seconds
let uptimeInterval = null;
let statusCheckInterval = null;

// DOM Elements
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const eventsProcessed = document.getElementById('events-processed');
const significantEvents = document.getElementById('significant-events');
const monitoredAccounts = document.getElementById('monitored-accounts');
const eventHandles = document.getElementById('event-handles');
const uptime = document.getElementById('uptime');
const pollingIntervalDisplay = document.getElementById('polling-interval');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const refreshBtn = document.getElementById('refresh-btn');
const pollingIntervalInput = document.getElementById('polling-interval-input');
const setIntervalBtn = document.getElementById('set-interval-btn');
const eventTypeFilter = document.getElementById('event-type-filter');
const accountFilter = document.getElementById('account-filter');
const timeFilter = document.getElementById('time-filter');
const eventsContainer = document.getElementById('events-container');
const emptyState = document.getElementById('empty-state');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    startBtn.addEventListener('click', startMonitoring);
    stopBtn.addEventListener('click', stopMonitoring);
    refreshBtn.addEventListener('click', refreshData);
    setIntervalBtn.addEventListener('click', updatePollingInterval);
    
    // Set up filter event listeners
    eventTypeFilter.addEventListener('change', filterEvents);
    accountFilter.addEventListener('change', filterEvents);
    timeFilter.addEventListener('change', filterEvents);
    
    // Check server status immediately and then every 5 seconds
    checkServerStatus();
    statusCheckInterval = setInterval(checkServerStatus, 5000);
    
    // Initial data load
    fetchMetrics();
    fetchEvents();
    
    // Fetch data periodically (every 10 seconds)
    setInterval(() => {
        fetchMetrics();
        fetchEvents();
    }, 10000);
});

// Check if the server is online
async function checkServerStatus() {
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            updateStatus(true, data.status);
            
            // Update components status
            if (data.components) {
                const componentsStatus = Object.values(data.components);
                const allOnline = componentsStatus.every(status => status === 'online');
                
                if (allOnline) {
                    updateStatus(true, 'All Systems Operational');
                } else {
                    updateStatus(true, 'Partially Operational');
                }
            }
            
            // Update monitoring state based on blockchain_module status
            if (data.components && data.components.blockchain_module === 'online') {
                isMonitoring = true;
                updateMonitoringUI();
            }
        } else {
            updateStatus(false, 'Server Error');
        }
    } catch (error) {
        updateStatus(false, 'Connection Error');
    }
}

// Update the status indicator
function updateStatus(isOnline, statusMessage) {
    if (isOnline) {
        statusDot.classList.remove('offline');
        statusText.textContent = statusMessage || 'Online';
    } else {
        statusDot.classList.add('offline');
        statusText.textContent = statusMessage || 'Offline';
    }
}

// Start monitoring
async function startMonitoring() {
    try {
        const response = await fetch('/api/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'start' })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                isMonitoring = true;
                updateMonitoringUI();
                startTime = new Date();
                startUptimeCounter();
                showToast('Monitoring started successfully');
                
                // Immediately fetch new data
                fetchMetrics();
                fetchEvents();
            } else {
                showToast(data.message || 'Failed to start monitoring', true);
            }
        } else {
            showToast('Failed to start monitoring', true);
        }
    } catch (error) {
        showToast('Connection error', true);
    }
}

// Stop monitoring
async function stopMonitoring() {
    try {
        const response = await fetch('/api/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'stop' })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                isMonitoring = false;
                updateMonitoringUI();
                stopUptimeCounter();
                showToast('Monitoring stopped');
            } else {
                showToast(data.message || 'Failed to stop monitoring', true);
            }
        } else {
            showToast('Failed to stop monitoring', true);
        }
    } catch (error) {
        showToast('Connection error', true);
    }
}

// Update UI based on monitoring state
function updateMonitoringUI() {
    if (isMonitoring) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusDot.classList.add('pulse');
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusDot.classList.remove('pulse');
    }
}

// Start the uptime counter
function startUptimeCounter() {
    if (uptimeInterval) {
        clearInterval(uptimeInterval);
    }
    
    updateUptime();
    uptimeInterval = setInterval(updateUptime, 1000);
}

// Stop the uptime counter
function stopUptimeCounter() {
    if (uptimeInterval) {
        clearInterval(uptimeInterval);
        uptimeInterval = null;
    }
    uptime.textContent = '0s';
}

// Update the uptime display
function updateUptime() {
    if (!startTime) return;
    
    const now = new Date();
    const diff = Math.floor((now - startTime) / 1000);
    
    if (diff < 60) {
        uptime.textContent = `${diff}s`;
    } else if (diff < 3600) {
        const minutes = Math.floor(diff / 60);
        const seconds = diff % 60;
        uptime.textContent = `${minutes}m ${seconds}s`;
    } else {
        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        uptime.textContent = `${hours}h ${minutes}m`;
    }
}

// Update the polling interval
async function updatePollingInterval() {
    const newInterval = parseInt(pollingIntervalInput.value);
    
    if (isNaN(newInterval) || newInterval < 10) {
        showToast('Interval must be at least 10 seconds', true);
        return;
    }
    
    try {
        const response = await fetch('/api/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                action: 'update_interval',
                interval: newInterval 
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                pollingInterval = newInterval;
                pollingIntervalDisplay.textContent = `${pollingInterval}s`;
                showToast(`Polling interval updated to ${pollingInterval}s`);
                
                // Immediately fetch new data
                fetchMetrics();
            } else {
                showToast(data.message || 'Failed to update interval', true);
            }
        } else {
            showToast('Failed to update interval', true);
        }
    } catch (error) {
        showToast('Connection error', true);
    }
}

// Refresh data
function refreshData() {
    fetchMetrics();
    fetchEvents();
    showToast('Data refreshed');
}

// Fetch metrics from the server
async function fetchMetrics() {
    try {
        const response = await fetch('/api/metrics');
        if (response.ok) {
            const data = await response.json();
            updateMetrics(data.metrics);
            
            // Update polling interval display if it changed
            if (data.metrics.polling_interval !== pollingInterval) {
                pollingInterval = data.metrics.polling_interval;
                pollingIntervalDisplay.textContent = `${pollingInterval}s`;
                pollingIntervalInput.value = pollingInterval;
            }
            
            // Populate account filter if we have accounts
            if (data.metrics.monitored_accounts > 0) {
                populateAccountFilter(data.metrics.account_list || []);
            }
        }
    } catch (error) {
        console.error('Error fetching metrics:', error);
    }
}

// Update metrics display
function updateMetrics(data) {
    if (!data) return;
    
    // Update basic metrics
    eventsProcessed.textContent = data.events_processed || 0;
    significantEvents.textContent = data.significant_events || 0;
    monitoredAccounts.textContent = data.monitored_accounts || 0;
    eventHandles.textContent = data.event_handles || 0;
    
    // Update polling interval display if it changed
    if (data.polling_interval !== pollingInterval) {
        pollingInterval = data.polling_interval;
        pollingIntervalDisplay.textContent = `${pollingInterval}s`;
        pollingIntervalInput.value = pollingInterval;
    }
    
    // Update blockchain version if available
    if (data.latest_version) {
        const blockchainVersion = document.getElementById('blockchain-version');
        if (blockchainVersion) {
            blockchainVersion.textContent = formatNumber(data.latest_version);
        } else {
            // Create version display if it doesn't exist
            const metricsGrid = document.querySelector('.metrics-grid');
            if (metricsGrid) {
                const versionCard = document.createElement('div');
                versionCard.className = 'metric-card';
                versionCard.innerHTML = `
                    <div class="metric-icon"><i class="fas fa-cube"></i></div>
                    <div class="metric-value" id="blockchain-version">${formatNumber(data.latest_version)}</div>
                    <div class="metric-label">Blockchain Version</div>
                `;
                metricsGrid.appendChild(versionCard);
            }
        }
    }
    
    // Update monitoring status indicator
    const statusIndicator = document.getElementById('status-indicator');
    if (statusIndicator) {
        if (data.is_monitoring) {
            statusIndicator.className = 'status-indicator active';
            statusIndicator.title = 'Monitoring Active';
        } else {
            statusIndicator.className = 'status-indicator inactive';
            statusIndicator.title = 'Monitoring Inactive';
        }
    }
    
    // Update uptime if available and we don't have a local timer running
    if (data.uptime && !uptimeInterval) {
        const seconds = data.uptime;
        if (seconds < 60) {
            uptime.textContent = `${seconds}s`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const secondsRemainder = seconds % 60;
            uptime.textContent = `${minutes}m ${secondsRemainder}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            uptime.textContent = `${hours}h ${minutes}m`;
        }
    }
    
    // Populate account filter if we have accounts
    if (data.monitored_accounts > 0 && data.account_list && data.account_list.length > 0) {
        populateAccountFilter(data.account_list);
    }
    
    // Update system status indicators if available
    if (data.system_status) {
        updateSystemStatus(data.system_status);
    }
}

// Helper function to format large numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Update system status indicators
function updateSystemStatus(status) {
    const statusContainer = document.querySelector('.system-status');
    if (!statusContainer) {
        // Create status container if it doesn't exist
        const metricsPanel = document.querySelector('.metrics-panel');
        if (metricsPanel) {
            const container = document.createElement('div');
            container.className = 'system-status';
            container.innerHTML = '<h3>System Status</h3><div class="status-grid"></div>';
            metricsPanel.appendChild(container);
            updateSystemStatus(status);
            return;
        }
    }
    
    const statusGrid = statusContainer?.querySelector('.status-grid');
    if (statusGrid) {
        statusGrid.innerHTML = '';
        
        for (const [key, value] of Object.entries(status)) {
            const statusItem = document.createElement('div');
            statusItem.className = 'status-item';
            
            const displayName = key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            const statusClass = value === 'online' ? 'online' : 'offline';
            
            statusItem.innerHTML = `
                <span class="status-name">${displayName}:</span>
                <span class="status-value ${statusClass}">${value}</span>
            `;
            
            statusGrid.appendChild(statusItem);
        }
    }
}

// Populate account filter with available accounts
function populateAccountFilter(accounts) {
    // Skip if we already have options or no accounts
    if (accountFilter.options.length > 1 || !accounts || !accounts.length) return;
    
    // Clear existing options except the first one (All)
    while (accountFilter.options.length > 1) {
        accountFilter.remove(1);
    }
    
    // Add options for each account
    accounts.forEach(account => {
        const option = document.createElement('option');
        option.value = account;
        
        // Format the account address for display
        if (account.length > 10) {
            option.textContent = `${account.substring(0, 6)}...${account.substring(account.length - 4)}`;
        } else {
            option.textContent = account;
        }
        
        accountFilter.appendChild(option);
    });
}

// Fetch events from the server
async function fetchEvents() {
    try {
        const response = await fetch('/api/events');
        if (response.ok) {
            const data = await response.json();
            if (data.events && Array.isArray(data.events)) {
                eventsList = data.events;
                filterEvents(); // Apply filters and display
            }
        }
    } catch (error) {
        console.error('Error fetching events:', error);
    }
}

// Filter events based on selected filters
function filterEvents() {
    if (!eventsList || !eventsList.length) {
        displayEvents([]);
        return;
    }
    
    let filtered = [...eventsList];
    
    // Filter by event type
    const eventType = eventTypeFilter.value;
    if (eventType && eventType !== 'all') {
        filtered = filtered.filter(event => {
            const type = event.event_type || event.type || '';
            return type.includes(eventType);
        });
    }
    
    // Filter by account
    const account = accountFilter.value;
    if (account && account !== 'all') {
        filtered = filtered.filter(event => {
            const eventAccount = event.account || '';
            return eventAccount === account;
        });
    }
    
    // Filter by time
    const timeRange = timeFilter.value;
    if (timeRange && timeRange !== 'all') {
        const now = new Date();
        let cutoff;
        
        switch (timeRange) {
            case 'hour':
                cutoff = new Date(now.getTime() - (60 * 60 * 1000)); // 1 hour
                break;
            case 'day':
                cutoff = new Date(now.getTime() - (24 * 60 * 60 * 1000)); // 24 hours
                break;
            case 'week':
                cutoff = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000)); // 7 days
                break;
            default:
                cutoff = new Date(0); // Beginning of time
        }
        
        filtered = filtered.filter(event => {
            const timestamp = event.timestamp || event.created_at;
            if (!timestamp) return true; // Keep if no timestamp
            
            const eventTime = new Date(timestamp);
            return eventTime >= cutoff;
        });
    }
    
    // Sort by timestamp, newest first
    filtered.sort((a, b) => {
        const timeA = new Date(a.timestamp || a.created_at || 0);
        const timeB = new Date(b.timestamp || b.created_at || 0);
        return timeB - timeA;
    });
    
    // Limit to the latest 3 events
    filtered = filtered.slice(0, 3);
    
    // Display filtered events
    displayEvents(filtered);
}

// Display events in the UI
function displayEvents(events) {
    // Clear existing events
    eventsContainer.innerHTML = '';
    
    if (!events || events.length === 0) {
        eventsContainer.appendChild(createEmptyState());
        return;
    }
    
    // Create a modern event list container
    const eventListContainer = document.createElement('div');
    eventListContainer.className = 'modern-event-list';
    
    // Add each event to the container
    events.forEach(event => {
        const eventCard = createEventCard(event);
        eventListContainer.appendChild(eventCard);
    });
    
    eventsContainer.appendChild(eventListContainer);
}

// Create an empty state element
function createEmptyState() {
    const emptyDiv = document.createElement('div');
    emptyDiv.className = 'empty-state';
    emptyDiv.innerHTML = `
        <div class="icon">📊</div>
        <h3>No Events Found</h3>
        <p>No blockchain events match your current filters.</p>
    `;
    return emptyDiv;
}

// Create an event card element
function createEventCard(event) {
    const card = document.createElement('div');
    card.className = 'event-card modern-card';
    
    // Determine event type and set appropriate class
    const eventType = event.event_type || 'unknown';
    card.classList.add(`event-type-${eventType.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    
    // Format timestamp
    let timestampStr = 'Unknown time';
    let timeAgo = '';
    if (event.timestamp) {
        const timestamp = new Date(event.timestamp);
        timestampStr = timestamp.toLocaleString();
        timeAgo = getTimeAgo(timestamp);
    }
    
    // Format account
    const account = event.account || 'Unknown account';
    const formattedAccount = formatAccount(account);
    
    // Format event type for display
    let eventTypeDisplay = eventType;
    let eventIcon = 'fa-bell';
    
    if (eventType === 'token_deposit') {
        eventTypeDisplay = 'Token Deposit';
        eventIcon = 'fa-arrow-down';
    } else if (eventType === 'token_withdrawal') {
        eventTypeDisplay = 'Token Withdrawal';
        eventIcon = 'fa-arrow-up';
    } else if (eventType === 'coin_transfer') {
        eventTypeDisplay = 'Coin Transfer';
        eventIcon = 'fa-exchange-alt';
    }
    
    // Format event details
    let detailsHtml = '';
    const details = event.details || {};
    
    if (typeof details === 'object' && Object.keys(details).length > 0) {
        // Display collection and token name first if present
        if (details.collection && details.token_name) {
            detailsHtml += `
                <div class="detail-highlight">
                    <span class="token-info">${details.collection} / ${details.token_name}</span>
                </div>
            `;
        }
        
        // Display amount if present
        if (details.amount) {
            detailsHtml += `
                <div class="detail-amount">
                    <span class="amount-value">${details.amount}</span>
                </div>
            `;
        }
        
        // Display other important details
        const otherDetails = Object.entries(details).filter(([key]) => 
            !['collection', 'token_name', 'amount'].includes(key));
            
        if (otherDetails.length > 0) {
            detailsHtml += '<div class="other-details">';
            
            otherDetails.slice(0, 2).forEach(([key, value]) => {
                detailsHtml += `
                    <div class="detail-item">
                        <span class="detail-key">${formatKey(key)}</span>
                        <span class="detail-value">${formatValue(value)}</span>
                    </div>
                `;
            });
            
            detailsHtml += '</div>';
        }
    }
    
    // Create links to explorer if applicable
    let explorerLinks = '';
    
    if (event.transaction_url) {
        explorerLinks += `
            <a href="${event.transaction_url}" target="_blank" class="explorer-link">
                <i class="fas fa-external-link-alt"></i> View Transaction
            </a>
        `;
    }
    
    // Construct the card HTML with a more modern design
    card.innerHTML = `
        <div class="event-icon">
            <i class="fas ${eventIcon}"></i>
        </div>
        <div class="event-content">
            <div class="event-header">
                <div class="event-type">${eventTypeDisplay}</div>
                <div class="event-time" title="${timestampStr}">${timeAgo}</div>
            </div>
            <div class="event-account" title="${account}">
                <i class="fas fa-user"></i> ${formattedAccount}
            </div>
            <div class="event-details">
                ${detailsHtml}
            </div>
            <div class="event-actions">
                ${explorerLinks}
            </div>
        </div>
    `;
    
    return card;
}

// Get time ago string from timestamp
function getTimeAgo(timestamp) {
    const now = new Date();
    const diff = Math.floor((now - timestamp) / 1000);
    
    if (diff < 60) {
        return `${diff}s ago`;
    } else if (diff < 3600) {
        return `${Math.floor(diff / 60)}m ago`;
    } else if (diff < 86400) {
        return `${Math.floor(diff / 3600)}h ago`;
    } else {
        return `${Math.floor(diff / 86400)}d ago`;
    }
}

// Format event type for display
function formatEventType(type) {
    if (!type) return 'Unknown Event';
    
    // Convert snake_case or camelCase to Title Case with spaces
    return type
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/\s+/g, ' ')
        .trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

// Format account address for display
function formatAccount(account) {
    if (!account) return 'Unknown';
    
    if (account.startsWith('0x') && account.length > 10) {
        const shortAccount = `${account.substring(0, 6)}...${account.substring(account.length - 4)}`;
        return `<span title="${account}">${shortAccount}</span>`;
    }
    
    return account;
}

// Format key for display
function formatKey(key) {
    if (!key) return '';
    
    // Convert snake_case or camelCase to Title Case with spaces
    return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Format value for display
function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';
    
    if (typeof value === 'object') {
        try {
            return `<pre>${JSON.stringify(value, null, 2)}</pre>`;
        } catch (e) {
            return String(value);
        }
    }
    
    if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
    }
    
    return String(value);
}

// Show a toast notification
function showToast(message, isError = false) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (isError) {
        toast.classList.add('toast-error');
    }
    
    // Add icon based on type
    const icon = isError ? '❌' : '✅';
    
    // Set content
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-message">${message}</div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Show with animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Remove after timeout
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}
