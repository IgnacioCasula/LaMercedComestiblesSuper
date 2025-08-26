document.addEventListener('DOMContentLoaded', function () {
    const togglePasswordIcons = document.querySelectorAll('.toggle-password');

    togglePasswordIcons.forEach(icon => {
        icon.addEventListener('click', function () {
            const targetInputId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetInputId);
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            if (this.src.includes('eyeX.png')) {
                this.src = this.src.replace('eyeX.png', 'eye.png');
            } else {
                this.src = this.src.replace('eye.png', 'eyeX.png');
            }
        });
    });
});
