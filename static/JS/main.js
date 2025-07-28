const wrapper = document.querySelector('.form-container');
const searchButton = document.querySelector('.form-button-container');

document.addEventListener('mousemove', (e) => {
    // Form container effect
    const rect = wrapper.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const angle = Math.atan2(y - rect.height / 2, x - rect.width / 2) * (180 / Math.PI);
    wrapper.style.background = `linear-gradient(${angle}deg, #FFFFFF, #F5F5F5)`;

    // Search button effect
    if (searchButton) {
        const buttonRect = searchButton.getBoundingClientRect();
        const buttonX = e.clientX - buttonRect.left;
        const buttonY = e.clientY - buttonRect.top;

        const buttonAngle = Math.atan2(buttonY - buttonRect.height / 2, buttonX - buttonRect.width / 2) * (180 / Math.PI);
        searchButton.style.background = `linear-gradient(${buttonAngle}deg, #0091FF, #00ffc3)`;
    }
});