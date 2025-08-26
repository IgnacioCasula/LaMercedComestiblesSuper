document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.code-inputs input');

    inputs.forEach((input, index) => {
        input.addEventListener('keyup', (e) => {
            if (e.key >= 0 && e.key <= 9) {
                if (index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            } else if (e.key === 'Backspace') {
                if (index > 0) {
                    inputs[index - 1].focus();
                }
            }
        });
    });
});
