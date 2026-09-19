// app.js - Main JavaScript file for NIDS Dashboard

// Socket.io connection
let socket;
// Chart objects
let trafficChart;
let protocolChart;
// Data storage
let trafficData = [];
let alertsList = [];
let protocolData = {
    labels: ['TCP', 'UDP', 'ICMP', 'Other'],
    datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'],
        borderWidth: 0
    }]
};
// UI state
let selectedTimeWindow = 5; // minutes
let isMonitoring = false;

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing NIDS Dashboard...');
    
    // Initialize Socket.io connection
    initSocketConnection();
    
    // Initialize charts
    initCharts();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load network interfaces
    loadNetworkInterfaces();
    
    // Check initial system status
    checkSystemStatus();
});

// Initialize Socket.io connection
function initSocketConnection() {
    socket = io();
    
    // Socket event handlers
    socket.on('connect', () => {
        console.log('Connected to server');
        showToast('info', 'Connected to server');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showToast('error', 'Lost connection to server');
        updateUIStatus('offline');
    });
    
    socket.on('new_alert', (alert) => {
        console.log('New alert received:', alert);
        addNewAlert(alert);
    });
    
    socket.on('stats_update', (stats) => {
        console.log('Stats update received:', stats);
        updateStats(stats);
    });
    
    socket.on('model_trained', (result) => {
        console.log('Model training completed:', result);
        if (result.status === 'success') {
            showToast('success', 'Model trained successfully');
            document.getElementById('model-loaded').textContent = 'Ready';
            document.getElementById('model-loaded').className = 'badge success';
            document.getElementById('save-model-btn').disabled = false;
        } else {
            showToast('error', 'Model training failed');
            document.getElementById('model-loaded').textContent = 'Error';
            document.getElementById('model-loaded').className = 'badge error';
        }
    });
}

// Initialize charts
function initCharts() {
    // Protocol distribution chart
    const protocolCtx = document.getElementById('protocol-chart').getContext('2d');
    protocolChart = new Chart(protocolCtx, {
        type: 'doughnut',
        data: protocolData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    displayColors: false,
                    callbacks: {
                        label: (context) => {
                            const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                            const percentage = total === 0 ? 0 : Math.round((context.raw / total) * 100);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Traffic chart
    const trafficCtx = document.getElementById('traffic-chart').getContext('2d');
    trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Traffic (bytes)',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: 'Alerts',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 0,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        boxWidth: 12,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

// Set up event listeners for UI elements
function setupEventListeners() {
    // Start button
    document.getElementById('start-btn').addEventListener('click', startMonitoring);
    
    // Stop button
    document.getElementById('stop-btn').addEventListener('click', stopMonitoring);
    
    // Train model button
    document.getElementById('train-btn').addEventListener('click', trainModel);
    
    // Save model button
    document.getElementById('save-model-btn').addEventListener('click', saveModel);
    
    // Upload dataset button
    document.getElementById('upload-dataset-btn').addEventListener('click', uploadDataset);
    
    // Clear alerts button
    document.getElementById('clear-alerts-btn').addEventListener('click', clearAlerts);
    
    // Alert search box
    document.getElementById('alert-search').addEventListener('input', searchAlerts);
    
    // Close alert details button
    document.getElementById('close-details-btn').addEventListener('click', () => {
        document.getElementById('alert-details').style.display = 'none';
    });
    
    // Block IP button
    document.getElementById('block-ip-btn').addEventListener('click', blockIP);
    
    // Ignore alert button
    document.getElementById('ignore-alert-btn').addEventListener('click', ignoreAlert);
    
    // Time selector buttons
    const timeButtons = document.querySelectorAll('.time-btn');
    timeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active class
            timeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update time window
            selectedTimeWindow = parseInt(btn.dataset.time);
            updateTrafficChart();
        });
    });
}

// Load available network interfaces
function loadNetworkInterfaces() {
    fetch('/api/interfaces')
        .then(response => response.json())
        .then(data => {
            const interfaceSelect = document.getElementById('interface-select');
            interfaceSelect.innerHTML = '';
            
            if (data.interfaces && data.interfaces.length > 0) {
                data.interfaces.forEach(iface => {
                    const option = document.createElement('option');
                    option.value = iface;
                    option.textContent = iface;
                    interfaceSelect.appendChild(option);
                });
            } else {
                const option = document.createElement('option');
                option.value = 'default';
                option.textContent = 'Default Interface';
                interfaceSelect.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Error loading interfaces:', error);
            showToast('error', 'Failed to load network interfaces');
        });
}

// Check system status on startup
function checkSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'running') {
                updateUIStatus('monitoring');
                isMonitoring = true;
                document.getElementById('start-btn').disabled = true;
                document.getElementById('stop-btn').disabled = false;
            } else {
                updateUIStatus('offline');
                isMonitoring = false;
            }
        })
        .catch(error => {
            console.error('Error checking status:', error);
            updateUIStatus('offline');
        });
    
    // Check model status
    checkModelStatus();
}

// Check if model is loaded
function checkModelStatus() {
    fetch('/api/model_status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'loaded') {
                document.getElementById('model-loaded').textContent = 'Ready';
                document.getElementById('model-loaded').className = 'badge success';
                document.getElementById('save-model-btn').disabled = false;
            } else {
                document.getElementById('model-loaded').textContent = 'Not Loaded';
                document.getElementById('model-loaded').className = 'badge error';
                document.getElementById('save-model-btn').disabled = true;
            }
        })
        .catch(error => {
            console.error('Error checking model status:', error);
            document.getElementById('model-loaded').textContent = 'Unknown';
            document.getElementById('model-loaded').className = 'badge';
        });
}

// Start network monitoring
function startMonitoring() {
    const interfaceSelect = document.getElementById('interface-select');
    const selectedInterface = interfaceSelect.value;
    
    fetch('/api/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ interface: selectedInterface })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            showToast('success', `Started monitoring on interface: ${data.interface}`);
            updateUIStatus('monitoring');
            isMonitoring = true;
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
        } else if (data.status === 'already_running') {
            showToast('info', 'Monitoring is already active');
        } else {
            showToast('error', 'Failed to start monitoring');
        }
    })
    .catch(error => {
        console.error('Error starting monitoring:', error);
        showToast('error', 'Failed to connect to server');
    });
}

// Stop network monitoring
function stopMonitoring() {
    fetch('/api/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'stopped') {
            showToast('info', 'Stopped monitoring');
            updateUIStatus('offline');
            isMonitoring = false;
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
        } else {
            showToast('error', 'Failed to stop monitoring');
        }
    })
    .catch(error => {
        console.error('Error stopping monitoring:', error);
        showToast('error', 'Failed to connect to server');
    });
}

// Train the intrusion detection model
function trainModel() {
    document.getElementById('train-btn').disabled = true;
    document.getElementById('model-loaded').textContent = 'Training...';
    document.getElementById('model-loaded').className = 'badge warning';
    
    showToast('info', 'Training model... This may take a few minutes');
    
    fetch('/api/train_model', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'training') {
            showToast('info', 'Model training started in background');
        } else if (data.status === 'error') {
            showToast('error', `Training error: ${data.message}`);
            document.getElementById('model-loaded').textContent = 'Error';
            document.getElementById('model-loaded').className = 'badge error';
        }
        document.getElementById('train-btn').disabled = false;
    })
    .catch(error => {
        console.error('Error training model:', error);
        showToast('error', 'Failed to connect to server');
        document.getElementById('train-btn').disabled = false;
        document.getElementById('model-loaded').textContent = 'Error';
        document.getElementById('model-loaded').className = 'badge error';
    });
}

// Save the trained model
function saveModel() {
    showToast('info', 'Saving model...');
    
    fetch('/api/save_model', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('success', 'Model saved successfully');
        } else {
            showToast('error', `Error saving model: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error saving model:', error);
        showToast('error', 'Failed to connect to server');
    });
}

// Upload dataset for training
function uploadDataset() {
    const datasetFile = document.getElementById('dataset-file').files[0];
    
    if (!datasetFile) {
        showToast('error', 'Please select a dataset file first');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const fileContent = e.target.result;
        
        showToast('info', 'Uploading dataset...');
        
        fetch('/api/load_dataset', {
            method: 'POST',
            body: fileContent
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast('success', 'Dataset uploaded successfully');
            } else {
                showToast('error', `Error uploading dataset: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error uploading dataset:', error);
            showToast('error', 'Failed to connect to server');
        });
    };
    
    reader.onerror = function() {
        showToast('error', 'Error reading file');
    };
    
    reader.readAsText(datasetFile);
}

// Update UI status indicators
function updateUIStatus(status) {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    switch (status) {
        case 'online':
            statusIndicator.className = 'status online';
            statusText.textContent = 'Connected';
            break;
        case 'offline':
            statusIndicator.className = 'status offline';
            statusText.textContent = 'Offline';
            break;
        case 'monitoring':
            statusIndicator.className = 'status monitoring';
            statusText.textContent = 'Monitoring';
            break;
        default:
            statusIndicator.className = 'status offline';
            statusText.textContent = 'Unknown';
    }
}

// Update stats display with new data
function updateStats(stats) {
    // Update basic statistics
    if (stats.active_connections !== undefined) {
        document.getElementById('active-connections').textContent = stats.active_connections;
    }
    
    if (stats.total_packets !== undefined) {
        document.getElementById('total-packets').textContent = stats.total_packets;
    }
    
    if (stats.total_bytes !== undefined) {
        let formattedBytes = formatBytes(stats.total_bytes);
        document.getElementById('total-bytes').textContent = formattedBytes;
    }
    
    if (stats.alerts_count !== undefined) {
        document.getElementById('alerts-count').textContent = stats.alerts_count;
    }
    
    // Update protocol chart if protocol data is available
    if (stats.protocols) {
        protocolData.datasets[0].data = [
            stats.protocols.tcp || 0,
            stats.protocols.udp || 0,
            stats.protocols.icmp || 0,
            stats.protocols.other || 0
        ];
        protocolChart.update();
    }
    
    // Add data point to traffic chart
    if (stats.timestamp && stats.total_bytes) {
        const time = moment(stats.timestamp).format('HH:mm:ss');
        const bytes = stats.total_bytes;
        const alerts = stats.alerts_count || 0;
        
        addTrafficDataPoint(time, bytes, alerts);
    }
}

// Add a data point to the traffic chart
function addTrafficDataPoint(time, bytes, alerts) {
    // Add data to our array
    trafficData.push({
        time: time,
        bytes: bytes,
        alerts: alerts
    });
    
    // Keep only last 60 data points
    if (trafficData.length > 60) {
        trafficData.shift();
    }
    
    // Update chart
    updateTrafficChart();
}

// Update traffic chart based on selected time window
function updateTrafficChart() {
    // Filter data based on time window
    const filteredData = trafficData.slice(-selectedTimeWindow * 12); // 12 data points per minute (5 sec intervals)
    
    // Update chart data
    trafficChart.data.labels = filteredData.map(d => d.time);
    trafficChart.data.datasets[0].data = filteredData.map(d => d.bytes);
    trafficChart.data.datasets[1].data = filteredData.map(d => d.alerts);
    
    // Update chart
    trafficChart.update();
}

// Add a new alert to the alerts table
function addNewAlert(alert) {
    // Store alert in our list
    alertsList.unshift(alert);
    
    // Keep max 100 alerts in memory
    if (alertsList.length > 100) {
        alertsList.pop();
    }
    
    // Play alert sound
    playAlertSound();
    
    // Show notification
    showToast('error', `New alert: ${alert.src_ip}:${alert.src_port} → ${alert.dst_ip}:${alert.dst_port}`);
    
    // Update alerts table
    updateAlertsTable();
}

// Update the alerts table with current alerts
function updateAlertsTable() {
    const alertsBody = document.getElementById('alerts-body');
    const searchTerm = document.getElementById('alert-search').value.toLowerCase();
    
    // Filter alerts if search term exists
    const filteredAlerts = searchTerm ? 
        alertsList.filter(alert => 
            alert.src_ip.toLowerCase().includes(searchTerm) || 
            alert.dst_ip.toLowerCase().includes(searchTerm) || 
            alert.protocol.toLowerCase().includes(searchTerm)
        ) : 
        alertsList;
    
    // Clear existing rows
    alertsBody.innerHTML = '';
    
    if (filteredAlerts.length === 0) {
        // Show empty message
        const emptyRow = document.createElement('tr');
        emptyRow.className = 'empty-alert';
        emptyRow.innerHTML = `<td colspan="6" class="center">No alerts detected yet</td>`;
        alertsBody.appendChild(emptyRow);
        return;
    }
    
    // Add alert rows
    filteredAlerts.forEach((alert, index) => {
        const row = document.createElement('tr');
        const riskClass = alert.probability > 0.9 ? 'high-risk' : 
                         alert.probability > 0.8 ? 'medium-risk' : '';
        
        row.className = `alert-row ${riskClass}`;
        row.innerHTML = `
            <td>${formatTimestamp(alert.timestamp)}</td>
            <td>${alert.src_ip}:${alert.src_port}</td>
            <td>${alert.dst_ip}:${alert.dst_port}</td>
            <td>${alert.protocol.toUpperCase()}</td>
            <td>${formatProbability(alert.probability)}</td>
            <td class="alert-actions-cell">
                <button class="action-btn" onclick="showAlertDetails(${index})"><i class="fas fa-info-circle"></i></button>
                <button class="action-btn danger" onclick="dismissAlert(${index})"><i class="fas fa-times"></i></button>
            </td>
        `;
        
        alertsBody.appendChild(row);
    });
}

// Play alert sound
function playAlertSound() {
    // Create audio element
    const audio = new Audio('/static/alert.mp3');
    audio.volume = 0.5;
    audio.play().catch(e => {
        console.log("Auto-play prevented. User interaction needed to play sounds.");
    });
}

// Clear all alerts
function clearAlerts() {
    alertsList = [];
    updateAlertsTable();
    showToast('info', 'All alerts cleared');
}

// Search alerts based on search term
function searchAlerts() {
    updateAlertsTable();
}

// Dismiss a single alert
function dismissAlert(index) {
    alertsList.splice(index, 1);
    updateAlertsTable();
}

// Show alert details
function showAlertDetails(index) {
    const alert = alertsList[index];
    
    // Update details panel
    document.getElementById('detail-timestamp').textContent = formatTimestamp(alert.timestamp);
    document.getElementById('detail-source').textContent = `${alert.src_ip}:${alert.src_port}`;
    document.getElementById('detail-destination').textContent = `${alert.dst_ip}:${alert.dst_port}`;
    document.getElementById('detail-protocol').textContent = alert.protocol.toUpperCase();
    document.getElementById('detail-probability').textContent = `${Math.round(alert.probability * 100)}%`;
    document.getElementById('detail-connkey').textContent = alert.connection_key || 'N/A';
    
    // Store source IP for block action
    document.getElementById('block-ip-btn').dataset.ip = alert.src_ip;
    document.getElementById('ignore-alert-btn').dataset.index = index;
    
    // Show panel
    document.getElementById('alert-details').style.display = 'block';
}

// Block IP address
function blockIP() {
    const ipAddress = document.getElementById('block-ip-btn').dataset.ip;
    
    if (!ipAddress) return;
    
    showToast('info', `Blocking IP address: ${ipAddress}`);
    
    fetch('/api/block_ip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ip: ipAddress })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('success', `IP address ${ipAddress} blocked successfully`);
            document.getElementById('alert-details').style.display = 'none';
        } else {
            showToast('error', `Failed to block IP: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error blocking IP:', error);
        showToast('error', 'Failed to connect to server');
    });
}

// Ignore similar alerts
function ignoreAlert() {
    const index = document.getElementById('ignore-alert-btn').dataset.index;
    const alert = alertsList[index];
    
    if (!alert) return;
    
    showToast('info', `Ignoring similar alerts from ${alert.src_ip}`);
    
    fetch('/api/ignore_alert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            src_ip: alert.src_ip,
            dst_ip: alert.dst_ip,
            protocol: alert.protocol
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('success', 'Will ignore similar alerts');
            document.getElementById('alert-details').style.display = 'none';
        } else {
            showToast('error', `Failed to set ignore rule: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error setting ignore rule:', error);
        showToast('error', 'Failed to connect to server');
    });
}

// Show toast notification
function showToast(type, message, duration = 3000) {
    const toastContainer = document.getElementById('toast-container');
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Set icon based on type
    let icon;
    switch (type) {
        case 'success':
            icon = 'fas fa-check-circle';
            break;
        case 'error':
            icon = 'fas fa-exclamation-circle';
            break;
        case 'warning':
            icon = 'fas fa-exclamation-triangle';
            break;
        case 'info':
        default:
            icon = 'fas fa-info-circle';
    }
    
    toast.innerHTML = `<i class="${icon}"></i><span>${message}</span>`;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Remove after duration
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 300);
    }, duration);
}

// Utility functions

// Format bytes to human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Format ISO timestamp to readable format
function formatTimestamp(timestamp) {
    return moment(timestamp).format('HH:mm:ss');
}

// Format probability as percentage
function formatProbability(probability) {
    const percent = Math.round(probability * 100);
    let color;
    
    if (percent > 90) {
        color = '#e74c3c'; // Red for high probability
    } else if (percent > 80) {
        color = '#f39c12'; // Orange for medium
    } else {
        color = '#3498db'; // Blue for low
    }
    
    return `<span style="color: ${color}; font-weight: 600;">${percent}%</span>`;
}

// Expose functions for inline event handlers
window.showAlertDetails = showAlertDetails;
window.dismissAlert = dismissAlert;