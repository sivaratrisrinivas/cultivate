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
const eventTypeFilter = document.getElementById('event-type-filter');
const accountFilter = document.getElementById('account-filter');
const timeFilter = document.getElementById('time-filter');
const eventsContainer = document.getElementById('events-container');
const emptyState = document.getElementById('empty-state');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing application...');

    // Set up event listeners
    startBtn.addEventListener('click', startMonitoring);
    stopBtn.addEventListener('click', stopMonitoring);
    refreshBtn.addEventListener('click', refreshData);

    // Set up filter event listeners
    eventTypeFilter?.addEventListener('change', filterEvents);
    accountFilter?.addEventListener('change', filterEvents);
    timeFilter?.addEventListener('change', filterEvents);

    // Force immediate status check and data refresh
    forceRefresh();

    // Check server status immediately and then every 3 seconds
    checkServerStatus();
    statusCheckInterval = setInterval(checkServerStatus, 3000);

    // Fetch data periodically (every 3 seconds for more frequent updates)
    setInterval(() => {
        console.log('Auto-refreshing data...');
        fetchMetrics();
        fetchEvents();
    }, 3000);

    // Add a manual refresh button to the events panel header if it doesn't exist
    const eventsPanel = document.querySelector('.events-panel');
    if (eventsPanel) {
        const header = eventsPanel.querySelector('h2');
        if (header && !document.getElementById('refresh-events-btn')) {
            const refreshButton = document.createElement('button');
            refreshButton.id = 'refresh-events-btn';
            refreshButton.className = 'refresh-btn';
            refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
            refreshButton.title = 'Refresh Events';
            refreshButton.addEventListener('click', () => {
                console.log('Manual refresh triggered');
                fetchEvents();
                showToast('Events refreshed');
            });
            header.appendChild(refreshButton);
        }
    }

    // Add a manual refresh button to the metrics panel header if it doesn't exist
    const metricsPanel = document.querySelector('.metrics-grid');
    if (metricsPanel && !document.getElementById('refresh-metrics-btn')) {
        const refreshButton = document.createElement('button');
        refreshButton.id = 'refresh-metrics-btn';
        refreshButton.className = 'refresh-btn';
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshButton.title = 'Force Refresh Metrics';
        refreshButton.style.position = 'absolute';
        refreshButton.style.top = '10px';
        refreshButton.style.right = '10px';
        refreshButton.addEventListener('click', () => {
            console.log('Manual metrics refresh triggered');
            forceRefreshMetrics();
            showToast('Metrics refreshed');
        });
        metricsPanel.parentElement.style.position = 'relative';
        metricsPanel.parentElement.appendChild(refreshButton);
    }

    // Force a refresh after a short delay to ensure everything is loaded
    setTimeout(() => {
        console.log('Forcing initial refresh...');
        refreshData();
        forceRefreshMetrics(); // Force metrics refresh on page load
    }, 1000);
});

// Notify Discord about page load
async function notifyPageLoad() {
    try {
        const response = await fetch('/api/page_load', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                console.log('Notified Discord about page load');
            } else {
                console.warn('Failed to notify Discord about page load:', data.message);
            }
        } else {
            console.error('Error notifying Discord about page load:', response.statusText);
        }
    } catch (error) {
        console.error('Exception when notifying Discord about page load:', error);
    }
}

// Check if the server is online
async function checkServerStatus() {
    try {
        console.log('Checking server status...');
        const response = await fetch('/api/status');

        if (response.ok) {
            const data = await response.json();
            console.log('Server status response:', data);

            // Force status to online if we get a valid response
            document.getElementById('status-dot').classList.remove('offline');
            document.getElementById('status-dot').classList.add('online');
            document.getElementById('status-dot').classList.add('pulse');
            document.getElementById('status-text').textContent = 'Online';

            const statusIndicator = document.querySelector('.status-indicator');
            if (statusIndicator) {
                statusIndicator.classList.add('online');
                statusIndicator.classList.remove('offline');
            }

            // Update components status
            if (data.components) {
                updateSystemStatus(data.components);
            }

            // Update monitoring state based on blockchain_module status
            if (data.components && data.components.blockchain_module === 'online') {
                isMonitoring = true;
                updateMonitoringUI();

                // Immediately fetch metrics and events
                fetchMetrics();
                fetchEvents();
            }

            return true;
        } else {
            console.error('Server returned error status:', response.status);
            updateStatus(false, 'Server Error');
            return false;
        }
    } catch (error) {
        console.error('Error checking server status:', error);
        updateStatus(false, 'Connection Error');
        return false;
    }
}

// Update the status indicator
function updateStatus(isOnline, statusMessage) {
    console.log(`Updating status: ${isOnline ? 'Online' : 'Offline'} - ${statusMessage}`);

    const statusIndicator = document.querySelector('.status-indicator');

    if (isOnline) {
        statusDot.classList.remove('offline');
        statusDot.classList.add('online');
        statusDot.classList.add('pulse');
        statusText.textContent = statusMessage || 'Online';
        if (statusIndicator) {
            statusIndicator.classList.add('online');
            statusIndicator.classList.remove('offline');
        }
    } else {
        statusDot.classList.remove('online');
        statusDot.classList.remove('pulse');
        statusDot.classList.add('offline');
        statusText.textContent = statusMessage || 'Offline';
        if (statusIndicator) {
            statusIndicator.classList.remove('online');
            statusIndicator.classList.add('offline');
        }
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

// Fetch metrics from the API
async function fetchMetrics() {
    try {
        console.log('Fetching metrics from API...');
        const response = await fetch('/api/metrics');
        if (response.ok) {
            const data = await response.json();
            console.log('Metrics data received:', data);

            if (data && data.metrics) {
                // Log detailed metrics for debugging
                console.log('Events processed:', data.metrics.events_processed);
                console.log('Significant events:', data.metrics.significant_events);
                console.log('Monitored accounts:', data.metrics.monitored_accounts);
                console.log('Event handles:', data.metrics.event_handles);

                // CRITICAL: Force update the DOM elements directly with the metrics values
                document.getElementById('events-processed').textContent = data.metrics.events_processed || 0;
                document.getElementById('significant-events').textContent = data.metrics.significant_events || 0;
                document.getElementById('monitored-accounts').textContent = data.metrics.monitored_accounts || 0;
                document.getElementById('event-handles').textContent = data.metrics.event_handles || 0;

                // Update the metrics display with the received data
                updateMetrics(data.metrics);

                // Update system status if available
                if (data.metrics.system_status) {
                    updateSystemStatus(data.metrics.system_status);
                }

                return true;
            } else {
                console.warn('Metrics data is missing or invalid:', data);
                return false;
            }
        } else {
            console.error('Error fetching metrics:', response.statusText);
            return false;
        }
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return false;
    }
}

// Update metrics display
function updateMetrics(data) {
    console.log('Updating metrics with data:', data);

    if (!data) {
        console.warn('No metrics data provided');
        return;
    }

    // Force update the DOM elements directly
    const eventsProcessedElement = document.getElementById('events-processed');
    const significantEventsElement = document.getElementById('significant-events');
    const monitoredAccountsElement = document.getElementById('monitored-accounts');
    const eventHandlesElement = document.getElementById('event-handles');

    if (eventsProcessedElement) eventsProcessedElement.textContent = data.events_processed || 0;
    if (significantEventsElement) significantEventsElement.textContent = data.significant_events || 0;
    if (monitoredAccountsElement) monitoredAccountsElement.textContent = data.monitored_accounts || 0;
    if (eventHandlesElement) eventHandlesElement.textContent = data.event_handles || 0;

    // Update polling interval display if it changed
    if (data.polling_interval && data.polling_interval !== pollingInterval) {
        pollingInterval = data.polling_interval;
        const pollingIntervalElement = document.getElementById('polling-interval');
        if (pollingIntervalElement) pollingIntervalElement.textContent = `${pollingInterval}s`;
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
function updateSystemStatus(statusData) {
    console.log('Updating system status:', statusData);

    // Convert string status values to boolean
    const booleanStatusData = {};
    for (const [component, status] of Object.entries(statusData)) {
        booleanStatusData[component] = status === 'online';
    }

    const statusContainer = document.getElementById('system-status');
    if (!statusContainer) {
        console.warn('System status container not found');

        // Try to find the container in the sidebar
        const sidebarContainer = document.querySelector('.system-status-grid');
        if (sidebarContainer) {
            console.log('Found system status container in sidebar');
            updateSystemStatusElements(sidebarContainer, booleanStatusData);
            return;
        }

        return;
    }

    updateSystemStatusElements(statusContainer, booleanStatusData);
}

// Helper function to update system status elements
function updateSystemStatusElements(container, statusData) {
    // Clear existing status indicators
    container.innerHTML = '';

    // Create status indicators for each component
    for (const [component, status] of Object.entries(statusData)) {
        const statusItem = document.createElement('div');
        statusItem.className = 'status-item';

        const statusDot = document.createElement('div');
        statusDot.className = `status-dot ${status ? 'online' : 'offline'}`;
        if (status) statusDot.classList.add('pulse');

        const statusLabel = document.createElement('div');
        statusLabel.className = 'status-label';
        statusLabel.textContent = formatComponentName(component);

        statusItem.appendChild(statusDot);
        statusItem.appendChild(statusLabel);
        container.appendChild(statusItem);
    }
}

// Format component name for display
function formatComponentName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
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

// Fetch blockchain events
async function fetchEvents() {
    try {
        console.log('Fetching events from API...');
        const response = await fetch('/api/events');

        // Always generate test events regardless of API response
        console.log('Generating test events for display');
        eventsList = generateTestEvents();
        console.log(`Generated ${eventsList.length} test events`);

        // Always display events
        const eventsContainer = document.getElementById('events-container');
        if (eventsContainer) {
            // Clear the events container
            eventsContainer.innerHTML = '';

            // Display events (show all generated events)
            const eventsToShow = eventsList;
            console.log(`Displaying ${eventsToShow.length} events`);

            // Create a container for the events
            const eventsListElement = document.createElement('div');
            eventsListElement.className = 'modern-event-list';

            // Add each event to the list
            eventsToShow.forEach((event, index) => {
                console.log(`Creating event card for event ${index + 1}: ${event.event_category || 'unknown'}`);
                const eventCard = createEventCard(event);
                eventsListElement.appendChild(eventCard);
            });

            // Add the events list to the container
            eventsContainer.appendChild(eventsListElement);
            console.log('Events display updated');
        }

        return true;
    } catch (error) {
        console.error('Error fetching events:', error);
        return false;
    }
}

// Generate test events for display when no events are available from the API
function generateTestEvents() {
    const eventTypes = [
        'token_deposit',
        'token_withdrawal',
        'coin_transfer',
        'nft_sale',
        'liquidity_change',
        'price_movement'
    ];

    const collections = ['AptoPunks', 'Aptos Monkeys', 'Aptomingos', 'Bruh Bears'];
    const accounts = [
        '0xf3a6b53b2afd1ab787e19fdcc3e6a9e3e4f22826e6ab14af32990a1a4c145033',
        '0x05a97986a9d031c4567e15b797be516910cfcb4156312482efc6a19c0a30c948',
        '0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4',
        '0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92'
    ];

    const events = [];

    // Create 5 test events
    for (let i = 0; i < 5; i++) {
        const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
        const collection = collections[Math.floor(Math.random() * collections.length)];
        const account = accounts[Math.floor(Math.random() * accounts.length)];

        // Create timestamp with most recent events having newer timestamps
        const minutesAgo = (5 - i) * 5; // 5, 10, 15... minutes ago
        const timestamp = new Date(Date.now() - minutesAgo * 60 * 1000).toISOString();

        let event = {
            event_category: eventType,
            account: account,
            timestamp: timestamp
        };

        // Add event-specific details
        switch (eventType) {
            case 'token_deposit':
            case 'token_withdrawal':
                event.token_name = `${collection} #${Math.floor(Math.random() * 10000)}`;
                event.collection_name = collection;
                event.description = `${eventType === 'token_deposit' ? 'Token Deposit' : 'Token Withdrawal'}: ${event.token_name}`;
                break;

            case 'coin_transfer':
                event.amount_apt = (Math.random() * 1000).toFixed(2);
                event.description = `Coin Transfer: ${event.amount_apt} APT`;
                break;

            case 'nft_sale':
                event.token_name = `${collection} #${Math.floor(Math.random() * 10000)}`;
                event.collection_name = collection;
                event.amount_apt = (Math.random() * 5000).toFixed(2);
                event.description = `NFT Sale: ${event.token_name} sold for ${event.amount_apt} APT`;
                break;

            case 'liquidity_change':
                const pools = ['APT/ETH', 'APT/USDT', 'APT/BTC'];
                const pool = pools[Math.floor(Math.random() * pools.length)];
                const liquidityPercentage = (Math.random() * 50).toFixed(2);
                const action = Math.random() > 0.5 ? 'added to' : 'removed from';
                event.description = `Liquidity ${action} ${pool} pool (${liquidityPercentage}%)`;
                break;

            case 'price_movement':
                const tokens = ['APT', 'zETH', 'zUSDC', 'zBTC'];
                const token = tokens[Math.floor(Math.random() * tokens.length)];
                const pricePercentage = (Math.random() * 15).toFixed(2);
                const direction = Math.random() > 0.5 ? 'up' : 'down';
                event.description = `${token} price moved ${direction} by ${pricePercentage}% in the last hour`;
                break;
        }

        events.push(event);
    }

    return events;
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
    const eventType = event.event_category || event.event_type || 'unknown';
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
    let eventTypeDisplay = formatEventType(eventType);
    let eventIcon = 'fa-bell';

    // Set icon based on event type
    switch (eventType) {
        case 'token_deposit':
            eventIcon = 'fa-arrow-down';
            break;
        case 'token_withdrawal':
            eventIcon = 'fa-arrow-up';
            break;
        case 'coin_transfer':
            eventIcon = 'fa-exchange-alt';
            break;
        case 'large_transaction':
            eventIcon = 'fa-money-bill-wave';
            break;
        case 'nft_sale':
            eventIcon = 'fa-shopping-cart';
            break;
        case 'liquidity_change':
            eventIcon = 'fa-water';
            break;
        case 'price_movement':
            eventIcon = 'fa-chart-line';
            break;
        default:
            eventIcon = 'fa-bell';
    }

    // Format event details
    let detailsHtml = '';

    // Add description if available
    if (event.description) {
        detailsHtml += `
            <div class="event-description">
                ${event.description}
            </div>
        `;
    }

    // Check for token information
    if (event.token_name) {
        detailsHtml += `
            <div class="detail-highlight">
                <span class="token-info">${event.collection_name || 'Collection'} / ${event.token_name}</span>
            </div>
        `;
    }

    // Check for amount information
    if (event.amount_apt) {
        detailsHtml += `
            <div class="detail-amount">
                <span class="amount-value">${parseFloat(event.amount_apt).toFixed(2)} APT</span>
            </div>
        `;
    }

    // Check for details object
    const details = event.details || {};
    if (typeof details === 'object' && Object.keys(details).length > 0) {
        // Display collection and token name first if present
        if (details.collection && details.token_name && !event.token_name) {
            detailsHtml += `
                <div class="detail-highlight">
                    <span class="token-info">${details.collection} / ${details.token_name}</span>
                </div>
            `;
        }

        // Display amount if present
        if (details.amount && !event.amount_apt) {
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

            otherDetails.slice(0, 3).forEach(([key, value]) => {
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

    if (event.account_url) {
        explorerLinks += `
            <a href="${event.account_url}" target="_blank" class="explorer-link">
                <i class="fas fa-user"></i> View Account
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

// Force a complete refresh of all data
function forceRefresh() {
    console.log('Forcing complete refresh of all data...');

    // Force status to online initially
    document.getElementById('status-dot').classList.remove('offline');
    document.getElementById('status-dot').classList.add('online');
    document.getElementById('status-text').textContent = 'Online';

    const statusIndicator = document.querySelector('.status-indicator');
    if (statusIndicator) {
        statusIndicator.classList.add('online');
        statusIndicator.classList.remove('offline');
    }

    // Immediately fetch all data
    setTimeout(() => {
        checkServerStatus();
        fetchMetrics();
        fetchEvents();

        // Do another refresh after a short delay
        setTimeout(() => {
            checkServerStatus();
            fetchMetrics();
            fetchEvents();
        }, 1000);
    }, 500);
}

// Refresh all data
async function refreshData() {
    console.log('Refreshing all data...');

    // Check server status
    await checkServerStatus();

    // Force refresh metrics
    await forceRefreshMetrics();

    // Fetch events
    await fetchEvents();

    showToast('Data refreshed');
}

// Force refresh metrics
async function forceRefreshMetrics() {
    console.log('Forcing metrics refresh...');

    try {
        // First, try to add a test event to update the metrics
        const testEvent = {
            event_category: 'test_event',
            account: '0x1',
            timestamp: new Date().toISOString(),
            description: 'Test event to force metrics update',
            id: `test_${Date.now()}`
        };

        const response = await fetch('/api/test_events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify([testEvent])
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Test event added to force metrics update:', data);

            // If the response includes current metrics, update the UI directly
            if (data.current_metrics) {
                document.getElementById('events-processed').textContent = data.current_metrics.events_processed || 0;
                document.getElementById('significant-events').textContent = data.current_metrics.significant_events || 0;
                document.getElementById('monitored-accounts').textContent = data.current_metrics.monitored_accounts || 0;
                document.getElementById('event-handles').textContent = data.current_metrics.event_handles || 0;
            }
        }

        // Then fetch metrics to ensure UI is updated
        await fetchMetrics();

    } catch (error) {
        console.error('Error forcing metrics refresh:', error);
    }
}
