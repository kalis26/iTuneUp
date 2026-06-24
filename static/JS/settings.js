document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const autoScanToggle = document.getElementById('autoScanToggle');
    
    loadSettings();
    
    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            enableDarkMode();
        } else {
            disableDarkMode();
        }
        
        localStorage.setItem('darkMode', this.checked);
    });
    
    if (autoScanToggle) autoScanToggle.addEventListener('change', function() {
        localStorage.setItem('autoScan', this.checked);
        console.log('Auto-scan:', this.checked);
    });

    const connect = document.getElementById('deezer-connect');
    const disconnect = document.getElementById('deezer-disconnect');
    if (connect) connect.addEventListener('click', connectDeezer);
    if (disconnect) disconnect.addEventListener('click', disconnectDeezer);
    loadDeezerStatus();
});

async function loadDeezerStatus() {
    const status = document.getElementById('deezer-status');
    try {
        const response = await fetch('/api/deezer/status');
        const data = await response.json();
        status.textContent = data.connected ? 'Deezer account connected' : 'No Deezer account connected';
    } catch (_) {
        status.textContent = 'Could not check Deezer connection';
    }
}

async function connectDeezer() {
    const input = document.getElementById('deezer-arl');
    const message = document.getElementById('deezer-message');
    message.textContent = 'Validating Deezer account…';
    const response = await fetch('/api/deezer/session', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({arl: input.value})});
    const data = await response.json();
    input.value = '';
    message.textContent = data.message || (data.success ? 'Deezer account connected.' : 'Could not connect Deezer account.');
    loadDeezerStatus();
}

async function disconnectDeezer() {
    const message = document.getElementById('deezer-message');
    const response = await fetch('/api/deezer/session', {method: 'DELETE'});
    const data = await response.json();
    message.textContent = data.success ? 'Deezer account disconnected.' : (data.message || 'Could not disconnect Deezer account.');
    loadDeezerStatus();
}

function loadSettings() {

    const darkMode = localStorage.getItem('darkMode') === 'true';
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    if (darkMode) {
        enableDarkMode();
        darkModeToggle.checked = true;
    }
    
    const autoScan = localStorage.getItem('autoScan') === 'true';
    const autoScanToggle = document.getElementById('autoScanToggle');
    if (autoScanToggle) {
        autoScanToggle.checked = autoScan;
    }
}

function enableDarkMode() {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.dispatchEvent(new CustomEvent('themechange', { detail: 'dark' }));
}

function disableDarkMode() {
    document.documentElement.removeAttribute('data-theme');
    document.dispatchEvent(new CustomEvent('themechange', { detail: 'light' }));
}

window.enableDarkMode = enableDarkMode;
window.disableDarkMode = disableDarkMode;
window.loadSettings = loadSettings;
