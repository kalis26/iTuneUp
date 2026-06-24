class StorageManager {
    constructor() {
        this.isLocalStorageAvailable = this.testLocalStorage();
        this.fallbackStorage = {};
        console.log('Storage available:', this.isLocalStorageAvailable);
    }
    
    testLocalStorage() {
        try {
            const test = 'storage_test';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch(e) {
            return false;
        }
    }
    
    setItem(key, value) {
        if (this.isLocalStorageAvailable) {
            try {
                localStorage.setItem(key, value);
                return true;
            } catch(e) {
                console.warn('LocalStorage setItem failed, using fallback');
                this.isLocalStorageAvailable = false;
            }
        }
        
        this.fallbackStorage[key] = value;
        
        this.saveToServer(key, value);
        return false;
    }
    
    getItem(key) {
        if (this.isLocalStorageAvailable) {
            try {
                return localStorage.getItem(key);
            } catch(e) {
                console.warn('LocalStorage getItem failed, using fallback');
                this.isLocalStorageAvailable = false;
            }
        }
        
        return this.fallbackStorage[key] || null;
    }

    saveToServer(key, value) {
        // Save settings to Flask backend
        fetch('/api/save_setting', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ key: key, value: value })
        }).catch(error => {
            console.log('Server save failed:', error);
        });
    }
    
    loadFromServer() {
        // Load settings from Flask backend
        return fetch('/api/load_settings')
            .then(response => response.json())
            .then(data => {
                if (data.settings) {
                    Object.assign(this.fallbackStorage, data.settings);
                }
                return data.settings;
            })
            .catch(error => {
                console.log('Server load failed:', error);
                return {};
            });
    }
}

const storage = new StorageManager();

const libraryContainer = document.getElementById('libraryContainer');

function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const isDark = currentTheme === 'dark';
    const newTheme = isDark ? '' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    storage.setItem('darkMode', (!isDark).toString());

    document.dispatchEvent(new Event('themechange'));
    
    console.log('Theme changed to:', newTheme || 'light');
}

function closeFlash() {

    const overlay = document.getElementById('flashOverlay');
    if (!overlay) return;

    const bubble = overlay.querySelector('.flash-bubble');
    const body = document.body;
    
    overlay.classList.add('fade-out');
    bubble.classList.add('fade-out');

    body.classList.remove('flash-active');
    
    setTimeout(() => {
        if (overlay && overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
        }
    }, 200);
}

function showNoLoading() {
    const noButton = document.getElementById('no-button');
    const noContainer = document.getElementById('no-button-container');
    const noLoadingGif = document.getElementById('no-loading-gif');
    
    if (noButton && noContainer && noLoadingGif) {
        noButton.classList.add('loading');
        noButton.disabled = true;
        noContainer.classList.add('disabled');
        noLoadingGif.classList.add('show');
    }
}

function dismissDeezerPrompt() {
    const modal = document.getElementById('deezerConnectModal');
    if (modal) modal.style.display = 'none';
    sessionStorage.setItem('deezerConnectPromptShown', 'true');
}

function openDeezerSettings() {
    window.location.href = '/settings';
}

async function promptForDeezerConnection() {
    const modal = document.getElementById('deezerConnectModal');
    if (!modal || sessionStorage.getItem('deezerConnectPromptShown') === 'true') return;
    try {
        const response = await fetch('/api/deezer/status');
        const status = await response.json();
        if (!status.connected) modal.style.display = 'flex';
    } catch (_) {
        // Do not block app startup when connection status cannot be checked.
    }
}

document.addEventListener('DOMContentLoaded', function() {

    promptForDeezerConnection();

    if (!storage.isLocalStorageAvailable) {
        storage.loadFromServer().then(settings => {
            if (settings.darkMode === 'true') {
                document.documentElement.setAttribute('data-theme', 'dark');
                document.dispatchEvent(new Event('themechange'));
            }
        });
    } else {
        const savedTheme = storage.getItem('darkMode');
        if (savedTheme === 'true') {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }

    setTimeout(() => {
        document.body.classList.remove('no-transition');
    }, 100);

    const searchBtn = document.getElementById('search-btn');
    const loadingGif = document.getElementById('loading-gif');
    const searchForm = document.getElementById('home-search-form');
    const urlForm = document.getElementById('home-url-form');
    const urlDownloadBtn = document.getElementById('url-download-btn');
    const urlLoadingGif = document.getElementById('url-loading-gif');
    const flashOverlay = document.getElementById('flashOverlay');
    const confirmForm = document.getElementById('confirm-form');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const tabButtons = document.querySelectorAll('.home-tab-button');
    const tabPanels = {
        search: document.getElementById('search-tab-panel'),
        url: document.getElementById('url-tab-panel')
    };

    function setActiveTab(tabName) {
        tabButtons.forEach(button => {
            button.classList.toggle('active', button.dataset.tabTarget === tabName);
        });

        Object.keys(tabPanels).forEach(key => {
            if (tabPanels[key]) {
                tabPanels[key].classList.toggle('active', key === tabName);
            }
        });
    }

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.dataset.tabTarget;
            if (targetTab) {
                setActiveTab(targetTab);
            }
        });
    });

    const initiallyActiveButton = document.querySelector('.home-tab-button.active');
    if (initiallyActiveButton && initiallyActiveButton.dataset.tabTarget) {
        setActiveTab(initiallyActiveButton.dataset.tabTarget);
    } else {
        setActiveTab('search');
    }
    
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', toggleDarkMode);
        darkModeToggle.checked = isDarkMode();
    }

    if (confirmForm) {
        confirmForm.addEventListener('submit', function(e) {
            const submitter = e.submitter;
            
            if (submitter && submitter.name === 'no') {
                showNoLoading();
            }
        });
    }

    if (searchForm && searchBtn) {
        searchForm.addEventListener('submit', function(e) {
            
            const submitButton = e.submitter;
            if (submitButton && submitButton.id == 'search-btn') {

                if (searchBtn) {
                    searchBtn.disabled = true;
                    searchBtn.classList.add('loading');
                    searchBtn.textContent = 'Searching...';
                    
                    const buttonContainer = document.querySelector('.form-button-container');
                    if (buttonContainer) {
                        buttonContainer.classList.add('disabled');
                        buttonContainer.style.background = '#A0A0A0';
                    }
                }

                if (loadingGif) {
                loadingGif.classList.add('show');
            }
            }
        });

        searchBtn.disabled = false;
        searchBtn.classList.remove('loading');
        searchBtn.textContent = 'Search';
    }

    if (urlForm && urlDownloadBtn) {
        urlForm.addEventListener('submit', function(e) {
            const submitButton = e.submitter;
            if (submitButton && submitButton.id === 'url-download-btn') {
                urlDownloadBtn.disabled = true;
                urlDownloadBtn.classList.add('loading');
                urlDownloadBtn.textContent = 'Starting...';

                const urlButtonContainer = document.getElementById('url-button-container');
                if (urlButtonContainer) {
                    urlButtonContainer.classList.add('disabled');
                    urlButtonContainer.style.background = '#A0A0A0';
                }

                if (urlLoadingGif) {
                    urlLoadingGif.classList.add('show');
                }
            }
        });

        urlDownloadBtn.disabled = false;
        urlDownloadBtn.classList.remove('loading');
        urlDownloadBtn.textContent = 'Download From URL';
    }

    if (loadingGif) {
        loadingGif.classList.remove('show');
    }

    if (urlLoadingGif) {
        urlLoadingGif.classList.remove('show');
    }


    if (flashOverlay) { 
        document.body.classList.add('flash-active');
    }

    if (libraryContainer && libraryContainer.dataset.albums) {
        try {
            const albumsScript = document.getElementById('albums-data');
            if (albumsScript) {
                albums = JSON.parse(albumsScript.textContent);
                console.log('Albums loaded:', albums.length);
                
                if (albums.length > 0) {
                    totalPages = Math.ceil(albums.length / albumsPerPage);
                    console.log('Total pages:', totalPages);
                    generatePageDots();
                    updatePagination();
                } else {
                    console.log('No albums found');
                }
            } else {
                console.log('Albums script element not found');
            }
        } catch (error) {
            console.error('Error parsing albums data:', error);
            console.log('Script content:', document.getElementById('albums-data')?.textContent);
        }
    }

    console.log('=== Storage Debug ===');
    console.log('localStorage available:', storage.isLocalStorageAvailable);
    console.log('Storage test - setting theme preference...');
    storage.setItem('test_setting', 'test_value');
    console.log('Storage test - reading back:', storage.getItem('test_setting'));
    console.log('===================');
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && document.getElementById('flashOverlay')) {
        closeFlash();
    }
});

function openLibraryFolder() {
    fetch('/open-library-folder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to open library folder:', data.error);
        }
    })
    .catch(error => {
        console.error('Error opening library folder:', error);
    });
}
