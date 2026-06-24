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
    const message = document.getElementById('deezer-message');
    const connect = document.getElementById('deezer-connect');
    connect.disabled = true;
    message.textContent = 'Opening Deezer sign-in…';
    const response = await fetch('/api/deezer/connect', {method: 'POST'});
    const data = await response.json();
    if (!response.ok) {
        message.textContent = data.message || 'Could not start Deezer sign-in.';
        connect.disabled = false;
        return;
    }
    const poll = setInterval(async () => {
        const statusResponse = await fetch(`/api/deezer/connect/${data.connection_id}`);
        const status = await statusResponse.json();
        message.textContent = status.message || 'Waiting for Deezer sign-in…';
        if (status.state === 'connected' || status.state === 'failed') {
            clearInterval(poll);
            connect.disabled = false;
            loadDeezerStatus();
        }
    }, 1000);
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
