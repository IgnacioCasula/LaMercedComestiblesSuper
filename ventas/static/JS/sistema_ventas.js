class SistemaVentas {
    constructor() {
        this.carrito = [];
        this.productos = productosData;
        this.init();
    }

    init() {
        this.bindEvents();
        this.actualizarResumen();
        console.log('🛒 Sistema de ventas inicializado');
    }

    bindEvents() {
        // Búsqueda
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.buscarProductos(e.target.value);
        });

        document.getElementById('btnSearch').addEventListener('click', () => {
            this.buscarProductos(document.getElementById('searchInput').value);
        });

        // Venta rápida
        document.getElementById('btnVentaRapida').addEventListener('click', () => {
            this.agregarVentaRapida();
        });

        document.getElementById('ventaRapidaMonto').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.agregarVentaRapida();
        });

        // Acciones principales
        document.getElementById('btnFinalizarVenta').addEventListener('click', () => {
            this.finalizarVenta();
        });

        document.getElementById('btnCancelarVenta').addEventListener('click', () => {
            this.cancelarVenta();
        });

        // Cambios en recargo
        document.getElementById('recargo').addEventListener('input', () => {
            this.actualizarResumen();
        });

        // Cerrar resultados de búsqueda al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.ocultarResultadosBusqueda();
            }
        });
    }

    buscarProductos(query) {
        if (query.length < 2) {
            this.ocultarResultadosBusqueda();
            return;
        }

        fetch(`${buscarProductosUrl}?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                this.mostrarResultadosBusqueda(data.resultados);
            })
            .catch(error => {
                console.error('Error en búsqueda:', error);
                this.ocultarResultadosBusqueda();
            });
    }

    mostrarResultadosBusqueda(resultados) {
        const container = document.getElementById('searchResults');
        container.innerHTML = '';

        if (resultados.length === 0) {
            container.innerHTML = '<div class="search-item text-muted">No se encontraron productos</div>';
        } else {
            resultados.forEach(producto => {
                const item = document.createElement('div');
                item.className = 'search-item';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${producto.nombre}</strong>
                            <br>
                            <small class="text-muted">${producto.marca} • ${producto.categoria}</small>
                        </div>
                        <div class="text-end">
                            <div class="fw-bold text-success">$${producto.precio.toFixed(2)}</div>
                            <small class="text-muted">Stock: ${producto.stock}</small>
                        </div>
                    </div>
                `;
                item.addEventListener('click', () => {
                    this.agregarProductoAlCarrito(producto);
                    document.getElementById('searchInput').value = '';
                    this.ocultarResultadosBusqueda();
                });
                container.appendChild(item);
            });
        }

        container.style.display = 'block';
    }

    ocultarResultadosBusqueda() {
        document.getElementById('searchResults').style.display = 'none';
    }

    agregarProductoAlCarrito(producto) {
        // Verificar si el producto ya está en el carrito
        const itemExistente = this.carrito.find(item => 
            item.id === producto.id && !item.esVentaRapida
        );

        if (itemExistente) {
            if (itemExistente.cantidad < producto.stock) {
                itemExistente.cantidad++;
            } else {
                alert(`❌ No hay suficiente stock de ${producto.nombre}`);
                return;
            }
        } else {
            if (producto.stock > 0) {
                this.carrito.push({
                    id: producto.id,
                    nombre: producto.nombre,
                    precio: producto.precio,
                    cantidad: 1,
                    stock: producto.stock,
                    esVentaRapida: false
                });
            } else {
                alert(`❌ No hay stock disponible de ${producto.nombre}`);
                return;
            }
        }

        this.actualizarInterfaz();
    }

    agregarVentaRapida() {
        const montoInput = document.getElementById('ventaRapidaMonto');
        const monto = parseFloat(montoInput.value);

        if (!monto || monto <= 0) {
            alert('❌ Ingresa un monto válido para la venta rápida');
            return;
        }

        this.carrito.push({
            id: 'venta_rapida_' + Date.now(),
            nombre: '🍎 Venta Rápida (Frutas/Verduras)',
            precio: monto,
            cantidad: 1,
            esVentaRapida: true
        });

        montoInput.value = '';
        this.actualizarInterfaz();
    }

    eliminarProducto(index) {
        this.carrito.splice(index, 1);
        this.actualizarInterfaz();
    }

    modificarCantidad(index, cambio) {
        const item = this.carrito[index];
        
        if (item.esVentaRapida) return; // No modificar venta rápida

        const nuevaCantidad = item.cantidad + cambio;

        if (nuevaCantidad < 1) {
            this.eliminarProducto(index);
        } else if (nuevaCantidad > item.stock) {
            alert(`❌ No hay suficiente stock. Máximo: ${item.stock}`);
        } else {
            item.cantidad = nuevaCantidad;
            this.actualizarInterfaz();
        }
    }

    actualizarInterfaz() {
        this.mostrarCarrito();
        this.actualizarResumen();
    }

    mostrarCarrito() {
        const container = document.getElementById('listaProductos');
        const emptyCart = document.getElementById('emptyCart');
        const contador = document.getElementById('contadorProductos');

        if (this.carrito.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-5" id="emptyCart"><i class="fas fa-shopping-cart fa-3x mb-3"></i><p>No hay productos en la venta<br>Busca y agrega productos para comenzar</p></div>';
            contador.textContent = '0';
            return;
        }

        emptyCart.style.display = 'none';
        contador.textContent = this.carrito.length;

        let html = '';
        this.carrito.forEach((item, index) => {
            const subtotal = item.cantidad * item.precio;
            
            html += `
                <div class="producto-item">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h6 class="mb-1">${item.nombre}</h6>
                            ${!item.esVentaRapida ? `<small class="text-muted">Stock: ${item.stock}</small>` : ''}
                        </div>
                        <div class="col-md-2 text-center">
                            ${!item.esVentaRapida ? `
                                <div class="cantidad-controls">
                                    <button class="btn btn-sm btn-outline-secondary btn-cantidad" onclick="sistemaVentas.modificarCantidad(${index}, -1)">
                                        <i class="fas fa-minus"></i>
                                    </button>
                                    <span class="input-cantidad">${item.cantidad}</span>
                                    <button class="btn btn-sm btn-outline-secondary btn-cantidad" onclick="sistemaVentas.modificarCantidad(${index}, 1)">
                                        <i class="fas fa-plus"></i>
                                    </button>
                                </div>
                            ` : '<span class="badge bg-warning">VENTA RÁPIDA</span>'}
                        </div>
                        <div class="col-md-2 text-end">
                            <strong>$${item.precio.toFixed(2)}</strong>
                        </div>
                        <div class="col-md-2 text-end">
                            <strong class="text-success">$${subtotal.toFixed(2)}</strong>
                            <button class="btn btn-sm btn-outline-danger ms-2" onclick="sistemaVentas.eliminarProducto(${index})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    actualizarResumen() {
        const subtotal = this.carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
        const recargo = parseFloat(document.getElementById('recargo').value) || 0;
        const total = subtotal + recargo;

        document.getElementById('subtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('total').textContent = `$${total.toFixed(2)}`;
    }

    async finalizarVenta() {
        if (this.carrito.length === 0) {
            alert('❌ No hay productos en la venta');
            return;
        }

        const metodoPago = document.getElementById('metodoPago').value;
        const recargo = parseFloat(document.getElementById('recargo').value) || 0;

        // Separar productos normales de venta rápida
        const itemsNormales = this.carrito
            .filter(item => !item.esVentaRapida)
            .map(item => ({
                producto_id: item.id,
                cantidad: item.cantidad
            }));

        const ventaRapidaTotal = this.carrito
            .filter(item => item.esVentaRapida)
            .reduce((sum, item) => sum + item.precio, 0);

        try {
            const response = await fetch(procesarVentaUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    items: itemsNormales,
                    venta_rapida_total: ventaRapidaTotal,
                    recargo: recargo,
                    metodo_pago: metodoPago
                })
            });

            const result = await response.json();

            if (result.success) {
                this.mostrarTicket(result);
                this.cancelarVenta();
            } else {
                alert(`❌ Error: ${result.error}`);
            }
        } catch (error) {
            alert(`❌ Error de conexión: ${error}`);
        }
    }

    mostrarTicket(resultado) {
        document.getElementById('numeroVenta').textContent = resultado.venta_id.toString().padStart(4, '0');
        document.getElementById('fechaTicket').textContent = `${resultado.fecha} ${resultado.hora}`;
        
        // Calcular totales para el ticket
        const subtotal = this.carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
        const recargo = parseFloat(document.getElementById('recargo').value) || 0;
        const total = subtotal + recargo;

        // Mostrar items en el ticket
        const ticketItems = document.getElementById('ticketItems');
        let itemsHTML = '';

        this.carrito.forEach(item => {
            const itemTotal = item.precio * item.cantidad;
            itemsHTML += `
                <div class="ticket-item">
                    <div>
                        <div>${item.nombre}</div>
                        ${!item.esVentaRapida ? `<small>Cant: ${item.cantidad} x $${item.precio.toFixed(2)}</small>` : ''}
                    </div>
                    <div>$${itemTotal.toFixed(2)}</div>
                </div>
            `;
        });

        ticketItems.innerHTML = itemsHTML;

        // Actualizar totales en el ticket
        document.getElementById('subtotalTicket').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('recargoTicket').textContent = `$${recargo.toFixed(2)}`;
        document.getElementById('totalTicket').textContent = `$${total.toFixed(2)}`;
        document.getElementById('metodoPagoTicket').textContent = document.getElementById('metodoPago').value;

        // Mostrar modal
        document.getElementById('ticketModal').style.display = 'flex';
    }

    cancelarVenta() {
        if (this.carrito.length === 0) return;
        
        if (confirm('¿Estás seguro de que quieres cancelar toda la venta?')) {
            this.carrito = [];
            document.getElementById('recargo').value = '0';
            document.getElementById('ventaRapidaMonto').value = '';
            this.actualizarInterfaz();
        }
    }
}

// Funciones globales para el ticket
function imprimirTicket() {
    window.print();
    setTimeout(() => {
        cerrarTicket();
    }, 1000);
}

function cerrarTicket() {
    document.getElementById('ticketModal').style.display = 'none';
}

// Inicializar el sistema cuando se cargue la página
let sistemaVentas;
document.addEventListener('DOMContentLoaded', function() {
    sistemaVentas = new SistemaVentas();
    console.log('✅ Sistema de ventas listo');
});