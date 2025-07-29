const wrapper = document.querySelector('.form-container');
const searchButton = document.querySelector('.form-button-container');
const searchResultContainer = document.querySelector('.search-result-container');
const yesBtnContainer = document.querySelector('.yes-button-container')
const noBtnContainer = document.querySelector('.no-button-container')

document.addEventListener('mousemove', (e) => {
    // Form container effect
    const rect = wrapper.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const angle = Math.atan2(y - rect.height / 2, x - rect.width / 2) * (180 / Math.PI);
    wrapper.style.background = `linear-gradient(${angle}deg, #FFFFFF, #F5F5F5)`;

    // Search button effect - only if not disabled
    if (searchButton && !searchButton.classList.contains('disabled')) {
        const buttonRect = searchButton.getBoundingClientRect();
        const buttonX = e.clientX - buttonRect.left;
        const buttonY = e.clientY - buttonRect.top;

        const buttonAngle = Math.atan2(buttonY - buttonRect.height / 2, buttonX - buttonRect.width / 2) * (180 / Math.PI);
        searchButton.style.background = `linear-gradient(${buttonAngle}deg, #0091FF, #00ffea)`;
    }

    // Search result container effect
    if (searchResultContainer) {
        const resultRect = searchResultContainer.getBoundingClientRect();
        const resultX = e.clientX - resultRect.left;
        const resultY = e.clientY - resultRect.top;

        const resultAngle = Math.atan2(resultY - resultRect.height / 2, resultX - resultRect.width / 2) * (180 / Math.PI);
        searchResultContainer.style.background = `linear-gradient(${resultAngle}deg, #F5F5F5, #0000001a)`;
    }

    if (yesBtnContainer) {
        const yesRect = yesBtnContainer.getBoundingClientRect();
        const yesX = e.clientX - yesRect.left;
        const yesY = e.clientY - yesRect.top;

        const yesAngle = Math.atan2(yesY - yesRect.height / 2, yesX - yesRect.width / 2) * (180 / Math.PI);
        yesBtnContainer.style.background = `linear-gradient(${yesAngle}deg, #0091FF, #00ffea)`;
    }

    if (noBtnContainer) {
        const noRect = noBtnContainer.getBoundingClientRect();
        const noX = e.clientX - noRect.left;
        const noY = e.clientY - noRect.top;

        const noAngle = Math.atan2(noY - noRect.height / 2, noX - noRect.width / 2) * (180 / Math.PI);
        noBtnContainer.style.background = `linear-gradient(${noAngle}deg, #F7F7F7, #0000001a)`;
    }

});

// Add this new code for the loading functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchBtn = document.getElementById('search-btn');
    const loadingGif = document.getElementById('loading-gif');
    const albumInput = document.getElementById('album');
    const artistInput = document.getElementById('artist');
    const form = document.querySelector('form');

    if (form) {
        form.addEventListener('submit', function(e) {
            // Check if both fields are empty
            if (!albumInput.value.trim() && !artistInput.value.trim()) {
                e.preventDefault();
                alert('Please enter an album or artist name to search.');
                return;
            }

            // Show loading state
            if (searchBtn) {
                searchBtn.disabled = true;
                searchBtn.classList.add('loading');
                searchBtn.textContent = 'Searching...';
                
                // Also disable the container gradient
                const buttonContainer = document.querySelector('.form-button-container');
                if (buttonContainer) {
                    buttonContainer.classList.add('disabled');
                    buttonContainer.style.background = '#A0A0A0'; // Override the gradient
                }
            }
            if (loadingGif) {
                loadingGif.classList.add('show');
            }
        });
    }

    // Reset button state when page loads
    if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.classList.remove('loading');
        searchBtn.textContent = 'Search';
    }
    if (loadingGif) {
        loadingGif.classList.remove('show');
    }
});