const wrapper = document.querySelector('.form-container');
const searchButton = document.querySelector('.form-button-container');
const searchResultContainer = document.querySelector('.search-result-container');
const yesBtnContainer = document.querySelector('.yes-button-container')
const noBtnContainer = document.querySelector('.no-button-container')
const flashBtnContainer = document.querySelector('.flash-button-container')
let progressInterval;

document.addEventListener('mousemove', (e) => {

    const rect = wrapper.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const angle = Math.atan2(y - rect.height / 2, x - rect.width / 2) * (180 / Math.PI);
    wrapper.style.background = `linear-gradient(${angle}deg, #FFFFFF, #F5F5F5)`;

    if (searchButton && !searchButton.classList.contains('disabled')) {
        const buttonRect = searchButton.getBoundingClientRect();
        const buttonX = e.clientX - buttonRect.left;
        const buttonY = e.clientY - buttonRect.top;

        const buttonAngle = Math.atan2(buttonY - buttonRect.height / 2, buttonX - buttonRect.width / 2) * (180 / Math.PI);
        searchButton.style.background = `linear-gradient(${buttonAngle}deg, #0091FF, #00ffea)`;
    }

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

    if (flashBtnContainer) {
        const flashRect = flashBtnContainer.getBoundingClientRect();
        const flashX = e.clientX - flashRect.left;
        const flashY = e.clientY - flashRect.top;

        const flashAngle = Math.atan2(flashY - flashRect.height / 2, flashX - flashRect.width / 2) * (180 / Math.PI);
        flashBtnContainer.style.background = `linear-gradient(${flashAngle}deg, #0091FF, #00ffea)`;
    }

});

function closeFlash() {

    const overlay = document.getElementById('flashOverlay');
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

    const searchBtn = document.getElementById('search-btn');
    const loadingGif = document.getElementById('loading-gif');
    const albumInput = document.getElementById('album');
    const artistInput = document.getElementById('artist');
    const form = document.querySelector('form');
    const flashOverlay = document.getElementById('flashOverlay');

    if (form) {
        form.addEventListener('submit', function(e) {
            
            if (!albumInput.value.trim() && !artistInput.value.trim()) {
                e.preventDefault();
                alert('Please enter an album or artist name to search.');
                return;
            }

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
        });
    }

    if (searchBtn) {
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

});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && document.getElementById('flashOverlay')) {
        closeFlash();
    }
});

function updateProgress() {

    fetch(`/progress/${taskID}`)
        .then(response => response.json())
        .then(data => {
            const percentage = data.percentage;
            const message = data.message;

            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressText').textContent = percentage + '%';
            document.getElementById('progressMessage').textContent = message;
            
            if (percentage >= 100) {
                clearInterval(progressInterval);

                setTimeout(() => {
                    window.location.href = '/?download=success';
                }, 2000);
            } else if (percentage < 0) {
                clearInterval(progressInterval);
                document.getElementById('progressMessage').textContent = 'Download failed: ' + message;
                document.getElementById('progressFill').style.backgroundColor = '#ff3b30';
            }     
        })
        .catch(error => {
            console.error('Error fetching progress:', error);
        });

}

progressInterval = setInterval(updateProgress, 1000);
updateProgress();