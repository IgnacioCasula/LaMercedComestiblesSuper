// ignaciocasula/lamercedcomestiblessuper/LaMercedComestiblesSuper-9e4cb265129870267e8e016db0b510984c444d8d/nombredeapp/static/JS/password_visibility.js
document.addEventListener('DOMContentLoaded', function () {
    const togglePasswordIcons = document.querySelectorAll('.toggle-password');

    togglePasswordIcons.forEach(icon => {
        icon.addEventListener('click', function () {
            // Obtenemos el input de la contraseña a través del atributo data-target
            const targetInputId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetInputId);

            // Cambiamos el tipo de input entre 'password' y 'text'
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Cambiamos la imagen del ojo dependiendo de si la contraseña es visible o no
            if (type === 'text') {
                // La contraseña es visible, mostramos el ojo abierto
                this.src = this.dataset.openEye;
            } else {
                // La contraseña está oculta, mostramos el ojo cerrado
                this.src = this.dataset.closedEye;
            }
        });
    });
});