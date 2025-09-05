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
    
    autoScanToggle.addEventListener('change', function() {
        localStorage.setItem('autoScan', this.checked);
        console.log('Auto-scan:', this.checked);
    });
});

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