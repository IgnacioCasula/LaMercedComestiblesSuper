class GestorTicket {
    constructor() {
        console.log('🎫 Inicializando GestorTicket...');
    }

    mostrarTicket() {
        console.log('🔄 Mostrando ticket...');
        const filas = document.querySelectorAll("#tablaBody tr");
        const ticketItems = document.getElementById("ticketItems");
       
        if (!ticketItems) {
            console.log('❌ ticketItems no encontrado');
            return;
        }
       
        ticketItems.innerHTML = "";
       
        let subtotal = 0;
       
        filas.forEach((fila) => {
            const productoId = fila.getAttribute('data-producto-id');
            const esVentaRapida = fila.getAttribute('data-venta-rapida') === 'true';
            const cantidad = fila.querySelector('.qty-value').textContent;
            const productoNombre = fila.querySelector('.nombre').textContent;
            
            let precioUnitario, totalLinea;
            
            if (esVentaRapida) {
                // Venta rápida
                precioUnitario = parseFloat(fila.querySelector('.price').textContent.replace('$', ''));
                totalLinea = precioUnitario;
            } else {
                // Producto normal
                const producto = productosData[productoId];
                precioUnitario = producto.precio;
                totalLinea = parseInt(cantidad) * precioUnitario;
            }
           
            subtotal += totalLinea;
           
            const itemDiv = document.createElement("div");
            itemDiv.className = "receipt-line";
            itemDiv.innerHTML = `
                <span>${cantidad}</span>
                <span>${productoNombre}</span>
                <span>$${totalLinea.toFixed(2)}</span>
            `;
           
            ticketItems.appendChild(itemDiv);
        });
       
        const recargo = Number(document.getElementById('recargo').value) || 0;
        const total = subtotal + recargo;
        const metodoPago = document.getElementById('metodoPago').value;
       
        document.getElementById("subtotalTicket").textContent = "$" + subtotal.toFixed(2);
        document.getElementById("recargoTicket").textContent = "$" + recargo.toFixed(2);
        document.getElementById("totalTicket").textContent = "$" + total.toFixed(2);
        document.getElementById("metodoPagoTicket").textContent = metodoPago;
       
        document.getElementById("ticketModal").style.display = "flex";
        console.log('✅ Ticket mostrado');
    }
}

// ===== FUNCIONES GLOBALES =====

function imprimirYNuevaVenta() {
    console.log('🖨️ Imprimiendo y creando nueva venta...');
    
    // Aquí puedes agregar lógica de impresión real si es necesario
    window.print();
    
    // Cerrar modal después de un breve delay
    setTimeout(() => {
        document.getElementById("ticketModal").style.display = "none";
        
        // Limpiar para nueva venta
        if (window.gestorVenta) {
            window.gestorVenta.cancelarTodo();
        }
        
        console.log('✅ Listo para nueva venta');
    }, 500);
}

function cerrarTicket() {
    console.log('❌ Cerrando ticket...');
    document.getElementById("ticketModal").style.display = "none";
}

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎫 Inicializando GestorTicket...');
    window.gestorTicket = new GestorTicket();
    window.mostrarTicket = () => window.gestorTicket.mostrarTicket();
    console.log('✅ GestorTicket inicializado globalmente');
});