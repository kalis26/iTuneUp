const wrapper = document.querySelector('.form-container');
const searchButton = document.querySelector('.form-button-container');
const searchResultContainer = document.querySelector('.search-result-container');
const yesBtnContainer = document.querySelector('.yes-button-container');
const noBtnContainer = document.querySelector('.no-button-container');
const flashBtnContainer = document.querySelector('.flash-button-container');
const startSearchbtn = document.querySelector('.start-searching-btn-container');
const libraryContainer = document.getElementById('libraryContainer');

function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

function getThemeColors() {
    if (isDarkMode()) {
        return {
            wrapper: {
                start: '#2C2C2E',
                end: '#1C1C1E'
            },
            button: {
                start: '#0A84FF',
                end: '#007AFF'
            },
            searchResult: {
                start: '#2C2C2E',
                end: '#3A3A3C'
            },
            noButton: {
                start: '#3A3A3C',
                end: '#48484A'
            }
        };
    } else {
        return {
            wrapper: {
                start: '#FFFFFF',
                end: '#F5F5F5'
            },
            button: {
                start: '#0091FF',
                end: '#00ffea'
            },
            searchResult: {
                start: '#F5F5F5',
                end: '#ececec'
            },
            noButton: {
                start: '#F7F7F7',
                end: '#0000001a'
            }
        };
    }
}

document.addEventListener('mousemove', (e) => {

    colors = getThemeColors();

    if (wrapper) {
        const rect = wrapper.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const angle = Math.atan2(y - rect.height / 2, x - rect.width / 2) * (180 / Math.PI);
        wrapper.style.background = `linear-gradient(${angle}deg, ${colors.wrapper.start}, ${colors.wrapper.end})`;
    }
    
    if (searchButton && !searchButton.classList.contains('disabled')) {
        const buttonRect = searchButton.getBoundingClientRect();
        const buttonX = e.clientX - buttonRect.left;
        const buttonY = e.clientY - buttonRect.top;

        const buttonAngle = Math.atan2(buttonY - buttonRect.height / 2, buttonX - buttonRect.width / 2) * (180 / Math.PI);
        searchButton.style.background = `linear-gradient(${buttonAngle}deg, ${colors.button.start}, ${colors.button.end})`;
    }

    if (searchResultContainer) {
        const resultRect = searchResultContainer.getBoundingClientRect();
        const resultX = e.clientX - resultRect.left;
        const resultY = e.clientY - resultRect.top;

        const resultAngle = Math.atan2(resultY - resultRect.height / 2, resultX - resultRect.width / 2) * (180 / Math.PI);
        searchResultContainer.style.background = `linear-gradient(${resultAngle}deg, ${colors.searchResult.start}, ${colors.searchResult.end})`;

    }    

    if (yesBtnContainer) {
        const yesRect = yesBtnContainer.getBoundingClientRect();
        const yesX = e.clientX - yesRect.left;
        const yesY = e.clientY - yesRect.top;

        const yesAngle = Math.atan2(yesY - yesRect.height / 2, yesX - yesRect.width / 2) * (180 / Math.PI);
        yesBtnContainer.style.background = `linear-gradient(${yesAngle}deg, ${colors.button.start}, ${colors.button.end})`;
    }

    if (noBtnContainer) {
        const noRect = noBtnContainer.getBoundingClientRect();
        const noX = e.clientX - noRect.left;
        const noY = e.clientY - noRect.top;

        const noAngle = Math.atan2(noY - noRect.height / 2, noX - noRect.width / 2) * (180 / Math.PI);
        noBtnContainer.style.background = `linear-gradient(${noAngle}deg, ${colors.noButton.start}, ${colors.noButton.end})`;
    }

    if (flashBtnContainer) {
        const flashRect = flashBtnContainer.getBoundingClientRect();
        const flashX = e.clientX - flashRect.left;
        const flashY = e.clientY - flashRect.top;

        const flashAngle = Math.atan2(flashY - flashRect.height / 2, flashX - flashRect.width / 2) * (180 / Math.PI);
        flashBtnContainer.style.background = `linear-gradient(${flashAngle}deg, ${colors.button.start}, ${colors.button.end})`;
    }

    if (startSearchbtn) {
        const stsRect = startSearchbtn.getBoundingClientRect();
        const stsX = e.clientX - stsRect.left;
        const stsY = e.clientY - stsRect.top;

        const stsAngle = Math.atan2(stsY - stsRect.height / 2, stsX - stsRect.width / 2) * (180 / Math.PI);
        startSearchbtn.style.background = `linear-gradient(${stsAngle}deg, ${colors.button.start}, ${colors.button.end})`;
    }

});

document.addEventListener('themechange', function() {
    const elements = [wrapper, searchButton, searchResultContainer, yesBtnContainer, noBtnContainer, flashBtnContainer, startSearchbtn];
    elements.forEach(element => {
        if (element) {
            element.style.background = '';
        }
    });
});

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


document.addEventListener('DOMContentLoaded', function() {

    setTimeout(() => {
        document.body.classList.remove('no-transition');
    }, 100);

    const searchBtn = document.getElementById('search-btn');
    const loadingGif = document.getElementById('loading-gif');
    const form = document.querySelector('form');
    const flashOverlay = document.getElementById('flashOverlay');

    if (form && searchBtn) {
        form.addEventListener('submit', function(e) {
            
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

    if (loadingGif) {
        loadingGif.classList.remove('show');
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

});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && document.getElementById('flashOverlay')) {
        closeFlash();
    }
});