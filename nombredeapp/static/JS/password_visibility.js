document.addEventListener('DOMContentLoaded', function () {
    const togglePasswordIcons = document.querySelectorAll('.toggle-password');

    togglePasswordIcons.forEach(icon => {
        icon.addEventListener('click', function () {
            const targetInputId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetInputId);
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            if (type === 'text') {
                this.src = this.dataset.openEye;
            } else {
                this.src = this.dataset.closedEye;
            }
        });
    });
});