class GestorTicket {
    constructor() {
        this.initEventListeners();
    }

    initEventListeners() {
        document.getElementById('btnCerrarTicket').addEventListener('click', () => this.cerrarTicket());
    }

    mostrarTicket() {
        const filas = document.querySelectorAll("#tablaBody tr");
        const ticketItems = document.getElementById("ticketItems");
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
    }

    cerrarTicket() {
        document.getElementById("ticketModal").style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.gestorTicket = new GestorTicket();
    window.mostrarTicket = () => window.gestorTicket.mostrarTicket();
});