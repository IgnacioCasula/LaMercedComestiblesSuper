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
            const producto = productosData[productoId];
            const cantidad = fila.querySelector('.qty-value').textContent;
            const productoNombre = fila.querySelector('.nombre').textContent;
            const precioUnitario = producto.precio;
            const totalLinea = parseInt(cantidad) * precioUnitario;
           
            subtotal += totalLinea;
           
            const itemDiv = document.createElement("div");
            itemDiv.className = "receipt-line";
            itemDiv.innerHTML = `
                <span>${cantidad}</span>
                <span>${productoNombre}</span>
                <span>$${totalLinea}</span>
            `;
           
            ticketItems.appendChild(itemDiv);
        });
       
        const recargo = Number(document.getElementById('recargo').value) || 0;
        const total = subtotal + recargo;
        const metodoPago = document.getElementById('metodoPago').value;
       
        document.getElementById("subtotalTicket").textContent = "$" + subtotal;
        document.getElementById("recargoTicket").textContent = "$" + recargo;
        document.getElementById("totalTicket").textContent = "$" + total;
        document.getElementById("metodoPagoTicket").textContent = metodoPago;
       
        document.getElementById("ticketModal").style.display = "flex";
        console.log('✅ Ticket mostrado');
    }
}

// ===== FUNCIONES GLOBALES =====

function cerrarTicket() {
    console.log('❌ Cerrando ticket...');
    document.getElementById("ticketModal").style.display = "none";
}

function confirmarImpresion() {
    console.log('🖨️ Abriendo modal de confirmación...');
    document.getElementById("confirmModal").style.display = "flex";
}

function cerrarConfirmacion() {
    document.getElementById("confirmModal").style.display = "none";
    console.log('❌ Confirmación cancelada');
}

function procesarVentaDesdeTicket() {
    console.log('✅ Procesando venta desde ticket...');
    // Cerrar ambos modales
    document.getElementById("confirmModal").style.display = "none";
    document.getElementById("ticketModal").style.display = "none";
   
    // Usar el GestorVenta para procesar la venta
    if (window.gestorVenta && window.gestorVenta.procesarVenta) {
        window.gestorVenta.procesarVenta();
    } else {
        console.error('❌ GestorVenta no disponible:', window.gestorVenta);
        alert('❌ Error: Sistema de ventas no disponible. Recarga la página.');
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎫 Inicializando GestorTicket...');
    window.gestorTicket = new GestorTicket();
    window.mostrarTicket = () => window.gestorTicket.mostrarTicket();
    console.log('✅ GestorTicket inicializado globalmente');
});
