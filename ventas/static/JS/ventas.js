class GestorVenta {
    constructor() {
        this.catalogo = productosData;
        this.initEventListeners();
        console.log('✅ GestorVenta creado con', Object.keys(this.catalogo).length, 'productos');
    }

    initEventListeners() {
        console.log('🔧 Configurando event listeners...');
       
        document.getElementById('btnAgregarProducto').addEventListener('click', () => this.agregarProducto());
       
        document.getElementById('productoInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.agregarProducto();
        });
       
        document.getElementById('productoInput').addEventListener('input', () => this.buscarProductos());
       
        document.getElementById('btnEmitirTicket').addEventListener('click', () => this.emitirTicket());
        
        // ELIMINADO: btnProcesarVenta
        document.getElementById('btnCancelarTodo').addEventListener('click', () => this.cancelarTodo());
       
        document.getElementById('recargo').addEventListener('input', () => this.calcularTotales());
       
        console.log('✅ Event listeners configurados');
    }

    buscarProductos() {
        const query = document.getElementById('productoInput').value.toLowerCase();
        const datalist = document.getElementById('productosLista');
        datalist.innerHTML = '';
       
        if (query.length < 2) return;
       
        const resultados = Object.entries(this.catalogo).filter(([id, producto]) =>
            producto.nombre.toLowerCase().includes(query) ||
            (producto.codigo_barras && producto.codigo_barras.toString().includes(query)) ||
            (producto.marca && producto.marca.toLowerCase().includes(query))
        ).slice(0, 10);
       
        resultados.forEach(([id, producto]) => {
            const option = document.createElement('option');
            option.value = `${producto.nombre} - $${producto.precio}`;
            option.setAttribute('data-id', id);
            option.setAttribute('data-precio', producto.precio);
               datalist.appendChild(option);
        });
    }

    agregarProducto() {
        const nombre = document.getElementById("productoInput").value.trim();
        if (!nombre) return;

        const productoEntry = Object.entries(this.catalogo).find(([id, producto]) =>
            producto.nombre.toLowerCase() === nombre.toLowerCase()
        );

        if (!productoEntry) {
            alert("❌ El producto no existe o no tiene stock.");
            return;
        }

        const [productoId, producto] = productoEntry;
        const tablaBody = document.getElementById("tablaBody");

        let filaExistente = Array.from(tablaBody.querySelectorAll("tr")).find(r =>
            r.getAttribute('data-producto-id') === productoId
        );

        if (filaExistente) {
            this.incrementarCantidad(filaExistente, producto);
        } else {
            this.crearFilaProducto(tablaBody, productoId, producto);
        }

        document.getElementById("productoInput").value = "";
        this.calcularTotales();
    }

    incrementarCantidad(fila, producto) {
        let qtyCell = fila.querySelector(".qty-value");
        let qty = Number(qtyCell.textContent);
       
        if (qty >= producto.stock) {
            alert("❌ No hay suficiente stock disponible.");
            return;
        }
       
        qty++;
        qtyCell.textContent = qty;
    }

    crearFilaProducto(tablaBody, productoId, producto) {
        const nuevaFila = document.createElement("tr");
        nuevaFila.setAttribute('data-producto-id', productoId);
        nuevaFila.innerHTML = `
            <td>
                <div class="qty-buttons">
                    <button class="qty-btn" type="button">-</button>
                    <span class="qty-value">1</span>
                    <button class="qty-btn" type="button">+</button>
                    <button class="btn-eliminar-producto" onclick="gestorVenta.eliminarProducto(this)">X</button>
                </div>
            </td>
            <td class="nombre">${producto.nombre}</td>
            <td class="price">$${producto.precio.toFixed(2)}</td>
            <td class="line-total">$${producto.precio.toFixed(2)}</td>
        `;
       
        const botones = nuevaFila.querySelectorAll('.qty-btn');
        botones[0].addEventListener('click', () => this.modificarCantidad(nuevaFila, -1));
        botones[1].addEventListener('click', () => this.modificarCantidad(nuevaFila, 1));
       
        tablaBody.appendChild(nuevaFila);
    }

    eliminarProducto(boton) {
        const fila = boton.closest('tr');
        fila.remove();
        this.calcularTotales();
    }

    modificarCantidad(fila, cambio) {
        const productoId = fila.getAttribute('data-producto-id');
        const producto = this.catalogo[productoId];
        const qtyElement = fila.querySelector('.qty-value');
        let cantidad = parseInt(qtyElement.textContent);
       
        cantidad += cambio;
       
        if (cantidad < 1) {
            fila.remove();
        } else {
            if (cantidad > producto.stock) {
                alert("❌ No hay suficiente stock disponible.");
                return;
            }
            qtyElement.textContent = cantidad;
        }
       
        this.calcularTotales();
    }

    calcularTotales() {
        const rows = document.querySelectorAll('#tablaBody tr');
        let subtotal = 0;
       
        rows.forEach(r => {
            const productoId = r.getAttribute('data-producto-id');
            const producto = this.catalogo[productoId];
            const qty = Number(r.querySelector('.qty-value').textContent.trim()) || 0;
            const price = producto.precio || 0;
            const line = qty * price;
            subtotal += line;
            r.querySelector('.line-total').textContent = "$" + line.toFixed(2);
        });
       
        const recargo = Number(document.getElementById('recargo').value) || 0;
        const total = subtotal + recargo;
       
        document.getElementById('subtotal').value = "$" + subtotal.toFixed(2);
        document.getElementById('total').value = "$" + total.toFixed(2);
    }

    cancelarTodo() {
        document.getElementById("tablaBody").innerHTML = "";
        this.calcularTotales();
    }

    

    async procesarVenta() {
        console.log('💾 Procesando venta...');
        const filas = document.querySelectorAll('#tablaBody tr');
       
        if (filas.length === 0) {
            alert("❌ No hay productos en la venta.");
            return;
        }
       
        const items = Array.from(filas).map(fila => {
            const productoId = fila.getAttribute('data-producto-id');
            const cantidad = parseInt(fila.querySelector('.qty-value').textContent);
            return {
                producto_id: parseInt(productoId),
                cantidad: cantidad
            };
        });
       
        const recargo = Number(document.getElementById('recargo').value) || 0;
        const metodo_pago = document.getElementById('metodoPago').value;
       
        try {
            const response = await fetch(procesarVentaUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    items: items,
                    recargo: recargo,
                    metodo_pago: metodo_pago
                })
            });
           
            const result = await response.json();
           
            if (result.success) {
                alert(`✅ Venta registrada exitosamente\nN° Venta: ${result.venta_id}\nTotal: $${result.total.toFixed(2)}`);
                this.cancelarTodo();
                document.getElementById('numeroVenta').textContent = result.venta_id.toString().padStart(4, '0');
                document.getElementById('recargo').value = '0';
                if (typeof window.mostrarTicket === 'function') {
                    window.mostrarTicket();
                }
            } else {
                alert('❌ Error al procesar la venta: ' + result.error);
            }
        } catch (error) {
            alert('❌ Error de conexión: ' + error);
        }
    }

    emitirTicket() {
        if (typeof window.mostrarTicket === 'function') {
            window.mostrarTicket();
        }
    }
}

// Inicializar GestorVenta globalmente
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando GestorVenta...');
    window.gestorVenta = new GestorVenta();
    console.log('✅ GestorVenta inicializado globalmente');
});
