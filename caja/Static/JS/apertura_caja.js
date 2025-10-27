// Estado dinámico de la caja - Versión simplificada
document.addEventListener('DOMContentLoaded', function() {
    // Los datos reales ya vienen del servidor, no necesitamos cargarlos aquí
    
    // Solo nos encargamos de la validación del formulario
    const form = document.querySelector('form');
    const montoInput = document.getElementById('id_montoinicialcaja');
    
    if (form && montoInput) {
        form.addEventListener('submit', function(e) {
            const monto = parseFloat(montoInput.value);
            if (monto < 0) {
                e.preventDefault();
                alert('El monto inicial no puede ser negativo');
                montoInput.focus();
                return false;
            }
            
            // Validación adicional: monto no vacío
            if (!montoInput.value.trim()) {
                e.preventDefault();
                alert('El monto inicial es obligatorio');
                montoInput.focus();
                return false;
            }
        });
    }
});