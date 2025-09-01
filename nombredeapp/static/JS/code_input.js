// ignaciocasula/lamercedcomestiblessuper/LaMercedComestiblesSuper-9e4cb265129870267e8e016db0b510984c444d8d/nombredeapp/static/JS/code_input.js
document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.code-inputs input');

    inputs.forEach((input, index) => {
        input.addEventListener('keyup', (e) => {
            // Si es un número, pasa al siguiente input
            if (e.key >= 0 && e.key <= 9) {
                if (index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            } else if (e.key === 'Backspace') {
                // Si es backspace, vuelve al input anterior
                if (index > 0) {
                    inputs[index - 1].focus();
                }
            }
        });
    });
});