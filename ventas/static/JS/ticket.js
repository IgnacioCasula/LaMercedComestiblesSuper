class GestorTicket {
    
    constructor() {
        console.log('🎫 Inicializando GestorTicket...');
    }

    mostrarTicket() {
        const productosData = [
      
        {"nombre": "Leche Entera La Serenísima (1L)", "precio": 1450, "marca": "La Serenísima", "codigo_barra": 7790080080004, "categoria": "Lácteos"},
        {"nombre": "Yogur Bebible Sancor Frutilla (900g)", "precio": 2300, "marca": "Sancor", "codigo_barra": 7790070014022, "categoria": "Lácteos"},
        {"nombre": "Queso Cremoso Ilolay (250g)", "precio": 4800, "marca": "Ilolay", "codigo_barra": 7791850100251, "categoria": "Lácteos"},
       
     
        {"nombre": "Aceite de Girasol Cocinero (900ml)", "precio": 2800, "marca": "Cocinero", "codigo_barra": 7790750275000, "categoria": "Almacén"},
        {"nombre": "Fideos Spaghetti Lucchetti (500g)", "precio": 1300, "marca": "Lucchetti", "codigo_barra": 7790382000030, "categoria": "Almacén"},
        {"nombre": "Arroz Largo Fino Gallo (1kg)", "precio": 1950, "marca": "Gallo", "codigo_barra": 7790070502018, "categoria": "Almacén"},
        {"nombre": "Azúcar Ledesma (1kg)", "precio": 1200, "marca": "Ledesma", "codigo_barra": 7790150000010, "categoria": "Almacén"},
       

        {"nombre": "Gaseosa Coca-Cola (1.5L)", "precio": 3100, "marca": "Coca-Cola", "codigo_barra": 7790070773663, "categoria": "Bebidas"},
        {"nombre": "Cerveza Quilmes Clásica (Lata 473ml)", "precio": 1800, "marca": "Quilmes", "codigo_barra": 7790400012146, "categoria": "Bebidas"},
       
  
        {"nombre": "Jabón en Polvo Ala (800g)", "precio": 3900, "marca": "Ala", "codigo_barra": 7791290022306, "categoria": "Limpieza"},
        {"nombre": "Papel Higiénico Higienol (4 rollos)", "precio": 2700, "marca": "Higienol", "codigo_barra": 7790510000520, "categoria": "Limpieza"},
    ]
    
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
            debugger;
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