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
        document.getElementById('btnCancelarTodo').addEventListener('click', () => this.cancelarTodo());
        
        document.getElementById('recargo').addEventListener('input', () => this.calcularTotales());
        
        // Event listener para recargo automático por crédito
        document.getElementById('metodoPago').addEventListener('change', () => this.aplicarRecargoCredito());
        
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
            // ✅ SOLO el nombre, sin precio
            option.value = producto.nombre;
            option.setAttribute('data-id', id);
            datalist.appendChild(option);
        });
    }

    agregarProducto() {
        const input = document.getElementById("productoInput");
        let nombre = input.value.trim();
        
        // ✅ Limpiar nombre - remover cualquier precio que pueda venir
        if (nombre.includes('$')) {
            nombre = nombre.split('$')[0].trim();
        }
        
        if (!nombre) return;

        // Buscar producto por nombre exacto
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

        input.value = "";
        this.calcularTotales();
        
        // Mostrar vista previa del producto
        this.mostrarVistaPrevia(productoId, producto);
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
                </div>
            </td>
            <td class="nombre">
                ${producto.nombre} <!-- ✅ SOLO NOMBRE, sin precio -->
                <button class="btn-eliminar-producto" onclick="gestorVenta.eliminarProducto(this)">X</button>
            </td>
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

    // ✅ RECARGO AUTOMÁTICO POR CRÉDITO - CORREGIDO
    aplicarRecargoCredito() {
        const metodoPago = document.getElementById('metodoPago').value;
        const recargoInput = document.getElementById('recargo');
        
        if (metodoPago === 'TARJETA CREDITO') {
            // Calcular 20% del subtotal
            const subtotal = this.obtenerSubtotal();
            const recargo = subtotal * 0.20;
            recargoInput.value = recargo.toFixed(2);
        } else {
            // Limpiar recargo si no es crédito
            recargoInput.value = '0';
        }
        this.calcularTotales();
    }

    // Función auxiliar para obtener subtotal
    obtenerSubtotal() {
        const subtotalInput = document.getElementById('subtotal');
        const subtotalText = subtotalInput.value.replace('$', '').trim();
        return parseFloat(subtotalText) || 0;
    }

    // ✅ VISTA PREVIA DE PRODUCTOS
    mostrarVistaPrevia(productoId, producto) {
        const vistaPrevia = document.getElementById('vistaPreviaProducto');
        if (!vistaPrevia) return;
        
        // Ruta de la imagen (basada en código de barras)
        const rutaImagen = `/static/productos/img/${producto.codigo_barras}.jpg`;
        
        vistaPrevia.innerHTML = `
            <div class="vista-previa-card">
                <div class="text-center mb-3">
                    <img src="${rutaImagen}"
                         alt="${producto.nombre}"
                         class="img-producto-preview"
                         onerror="this.style.display='none'">
                </div>
                <h6 class="text-center mb-2">${producto.nombre}</h6>
                <div class="text-center mb-2">
                    <strong class="text-success">$${producto.precio.toFixed(2)}</strong>
                </div>
                <div class="small">
                    <div><strong>Código:</strong> ${producto.codigo_barras}</div>
                    <div><strong>Stock:</strong> ${producto.stock} unidades</div>
                    <div><strong>Marca:</strong> ${producto.marca || 'N/A'}</div>
                </div>
            </div>
        `;
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
                
                // ✅ GENERAR PDF AUTOMÁTICAMENTE
                this.generarPDF(result);
                
            } else {
                alert('❌ Error al procesar la venta: ' + result.error);
            }
        } catch (error) {
            alert('❌ Error de conexión: ' + error);
        }
    }

    // ✅ FUNCIÓN GENERAR PDF AUTOMÁTICO
    generarPDF(resultadoVenta) {
        console.log('📄 Generando PDF...');
        
        // Verificar que las librerías estén cargadas
        if (typeof jspdf === 'undefined' || typeof html2canvas === 'undefined') {
            console.error('❌ Librerías PDF no disponibles');
            return;
        }

        const { jsPDF } = window.jspdf;
        
        // Capturar el contenido del ticket
        const ticketElement = document.getElementById('ticketModal');
        
        html2canvas(ticketElement, {
            scale: 2,
            useCORS: true,
            logging: false
        }).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const imgWidth = 190;
            const pageHeight = 280;
            const imgHeight = canvas.height * imgWidth / canvas.width;
            let heightLeft = imgHeight;
            let position = 10;

            pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;

            while (heightLeft >= 0) {
                position = heightLeft - imgHeight + 10;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }

            // Descargar automáticamente
            pdf.save(`ticket_venta_${resultadoVenta.venta_id}.pdf`);
            
            console.log('✅ PDF generado y descargado automáticamente');
        });
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