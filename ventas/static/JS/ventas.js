    class GestorVenta {
        constructor() {
            // ✅ USAR PRODUCTOS DE LA BASE DE DATOS (pasados desde Django)
            // productosData viene del template como: { "1": {...}, "2": {...} }
            if (typeof productosData !== 'undefined' && productosData) {
                this.catalogo = productosData;
                console.log('✅ GestorVenta creado con', Object.keys(this.catalogo).length, 'productos desde BD');
            } else {
                // Fallback si no hay datos (no debería pasar)
                this.catalogo = {};
                console.warn('⚠️ No se encontraron productos desde la BD. Usando catálogo vacío.');
            }
            this.initEventListeners();
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
            let inputValue = input.value.trim();
            
            if (!inputValue) return;

            console.log('🔍 Buscando producto con input:', inputValue);
            console.log('📦 Catálogo disponible:', Object.keys(this.catalogo).length, 'productos');

            // ✅ Limpiar nombre - el datalist viene como "Nombre - $Precio"
            let nombreBuscado = inputValue;
            
            // Si viene del datalist con formato "Nombre - $Precio"
            const matchDatalist = inputValue.match(/^(.+?)\s*-\s*\$/);
            if (matchDatalist) {
                nombreBuscado = matchDatalist[1].trim();
                console.log('📝 Nombre extraído del datalist:', nombreBuscado);
            } else if (inputValue.includes('$')) {
                // Si solo tiene $, remover todo después del $
                nombreBuscado = inputValue.split('$')[0].trim();
                console.log('📝 Nombre limpiado (tiene $):', nombreBuscado);
            }

            // Buscar producto por nombre exacto primero
            let productoEntry = Object.entries(this.catalogo).find(([id, producto]) =>
                producto.nombre.toLowerCase() === nombreBuscado.toLowerCase()
            );

            // Si no se encuentra, buscar por coincidencia parcial
            if (!productoEntry) {
                console.log('⚠️ No se encontró por nombre exacto, buscando por coincidencia parcial...');
                productoEntry = Object.entries(this.catalogo).find(([id, producto]) =>
                    producto.nombre.toLowerCase().includes(nombreBuscado.toLowerCase()) ||
                    nombreBuscado.toLowerCase().includes(producto.nombre.toLowerCase())
                );
            }

            // También verificar si hay una opción seleccionada del datalist con data-id
            if (!productoEntry) {
                const selectedOption = document.querySelector(`#productosLista option[value="${inputValue}"]`);
                if (selectedOption) {
                    const dataId = selectedOption.getAttribute('data-id');
                    if (dataId && this.catalogo[dataId]) {
                        productoEntry = [dataId, this.catalogo[dataId]];
                        console.log('✅ Producto encontrado por data-id del datalist:', dataId);
                    }
                }
            }

            if (!productoEntry) {
                console.error('❌ Producto no encontrado. Input original:', inputValue);
                console.error('❌ Nombre buscado:', nombreBuscado);
                console.error('❌ Productos en catálogo:', Object.keys(this.catalogo).map(id => this.catalogo[id].nombre));
                alert("❌ El producto no existe o no tiene stock.");
                return;
            }

            const [productoId, producto] = productoEntry;
            
            // ✅ DEBUG: Verificar que el producto tenga todas las propiedades
            console.log('🔍 Producto encontrado:', {
                id: productoId,
                nombre: producto.nombre,
                precio: producto.precio,
                codigo_barras: producto.codigo_barras,
                stock: producto.stock,
                marca: producto.marca,
                producto_completo: producto
            });
            
            // ✅ Validar que el producto tenga las propiedades necesarias
            if (!producto.nombre || !producto.precio) {
                console.error('❌ Producto incompleto:', producto);
                alert("❌ Error: El producto no tiene todos los datos necesarios.");
                return;
            }
            
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
            
            // Validar que el producto tenga las propiedades necesarias
            if (!producto) {
                console.error('❌ Producto no definido en mostrarVistaPrevia');
                vistaPrevia.innerHTML = `
                    <div class="text-center text-muted">
                        <i>Seleccione un producto para ver detalles</i>
                    </div>
                `;
                return;
            }
            
            // Obtener valores con fallbacks para evitar undefined
            const codigoBarras = producto.codigo_barras || producto.codigobarraproducto || 'N/A';
            const stock = producto.stock !== undefined ? producto.stock : 'N/A';
            const marca = producto.marca || producto.marcaproducto || 'N/A';
            const nombre = producto.nombre || producto.nombreproductos || 'Producto sin nombre';
            const precio = producto.precio || producto.precioproducto || 0;
            
            // Ruta de la imagen (basada en código de barras)
            const rutaImagen = codigoBarras !== 'N/A' ? `/static/productos/img/${codigoBarras}.jpg` : '';
            
            vistaPrevia.innerHTML = `
                <div class="vista-previa-card">
                    ${rutaImagen ? `
                    <div class="text-center mb-3">
                        <img src="${rutaImagen}"
                            alt="${nombre}"
                            class="img-producto-preview"
                            onerror="this.style.display='none'">
                    </div>
                    ` : ''}
                    <h6 class="text-center mb-2">${nombre}</h6>
                    <div class="text-center mb-2">
                        <strong class="text-success">$${precio.toFixed(2)}</strong>
                    </div>
                    <div class="small">
                        <div><strong>Código:</strong> ${codigoBarras}</div>
                        <div><strong>Stock:</strong> ${stock} ${stock !== 'N/A' ? 'unidades' : ''}</div>
                        <div><strong>Marca:</strong> ${marca}</div>
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
                    // ✅ GUARDAR DATOS DE LA VENTA ANTES DE LIMPIAR
                    const datosVenta = this.obtenerDatosVenta(filas, recargo, metodo_pago);
                    
                    alert(`✅ Venta registrada exitosamente\nN° Venta: ${result.venta_id}\nTotal: $${result.total.toFixed(2)}`);
                    
                    // Actualizar número de venta en el ticket
                    const numeroVentaElement = document.getElementById('numeroVenta');
                    if (numeroVentaElement) {
                        numeroVentaElement.textContent = result.venta_id.toString().padStart(4, '0');
                    }
                    
                    // Actualizar ticket con los datos guardados
                    this.actualizarTicketConDatos(datosVenta, result);
                    
                    // Limpiar después de actualizar el ticket
                    this.cancelarTodo();
                    document.getElementById('recargo').value = '0';
                    
                    // ✅ GENERAR PDF AUTOMÁTICAMENTE (con un pequeño delay para asegurar renderizado)
                    setTimeout(() => {
                        this.generarPDF(result);
                    }, 200);
                    
                } else {
                    alert('❌ Error al procesar la venta: ' + result.error);
                }
            } catch (error) {
                alert('❌ Error de conexión: ' + error);
            }
        }

        // ✅ OBTENER DATOS DE LA VENTA ANTES DE LIMPIAR
        obtenerDatosVenta(filas, recargo, metodo_pago) {
            const items = [];
            let subtotal = 0;
            
            filas.forEach(fila => {
                try {
                    const productoId = fila.getAttribute('data-producto-id');
                    if (!productoId) {
                        console.warn('⚠️ Fila sin data-producto-id, saltando...');
                        return;
                    }
                    
                    // Obtener cantidad
                    const qtyElement = fila.querySelector('.qty-value');
                    if (!qtyElement) {
                        console.error('❌ No se encontró .qty-value en la fila');
                        return;
                    }
                    const cantidad = parseInt(qtyElement.textContent) || 0;
                    
                    // Obtener nombre (el td.nombre contiene el texto, pero puede tener botones)
                    const nombreElement = fila.querySelector('.nombre');
                    if (!nombreElement) {
                        console.error('❌ No se encontró .nombre en la fila');
                        return;
                    }
                    // Obtener solo el texto, excluyendo botones
                    const productoNombre = nombreElement.cloneNode(true);
                    const botones = productoNombre.querySelectorAll('button');
                    botones.forEach(btn => btn.remove());
                    const nombreTexto = productoNombre.textContent.trim();
                    
                    // Obtener precio (la clase es "price", no "precio")
                    const priceElement = fila.querySelector('.price');
                    if (!priceElement) {
                        console.error('❌ No se encontró .price en la fila');
                        return;
                    }
                    const precioUnitario = parseFloat(priceElement.textContent.replace('$', '').replace(',', '').trim()) || 0;
                    
                    const totalLinea = cantidad * precioUnitario;
                    
                    items.push({
                        productoId: productoId,
                        nombre: nombreTexto,
                        cantidad: cantidad,
                        precioUnitario: precioUnitario,
                        totalLinea: totalLinea
                    });
                    
                    subtotal += totalLinea;
                } catch (error) {
                    console.error('❌ Error al procesar fila:', error);
                }
            });
            
            return {
                items: items,
                subtotal: subtotal,
                recargo: recargo,
                total: subtotal + recargo,
                metodo_pago: metodo_pago
            };
        }

        // ✅ ACTUALIZAR TICKET CON DATOS GUARDADOS
        actualizarTicketConDatos(datosVenta, resultadoVenta) {
            const ticketItems = document.getElementById("ticketItems");
            if (!ticketItems) {
                console.error('❌ ticketItems no encontrado');
                return;
            }
            
            ticketItems.innerHTML = "";
            
            // Agregar cada item al ticket
            datosVenta.items.forEach(item => {
                const itemDiv = document.createElement("div");
                itemDiv.className = "receipt-line";
                itemDiv.innerHTML = `
                    <span>${item.cantidad}</span>
                    <span>${item.nombre}</span>
                    <span>$${item.totalLinea.toFixed(2)}</span>
                `;
                ticketItems.appendChild(itemDiv);
            });
            
            // Actualizar totales (verificar que los elementos existan)
            const subtotalTicket = document.getElementById("subtotalTicket");
            const recargoTicket = document.getElementById("recargoTicket");
            const totalTicket = document.getElementById("totalTicket");
            const metodoPagoTicket = document.getElementById("metodoPagoTicket");
            
            if (subtotalTicket) {
                subtotalTicket.textContent = "$" + datosVenta.subtotal.toFixed(2);
            }
            if (recargoTicket) {
                recargoTicket.textContent = "$" + datosVenta.recargo.toFixed(2);
            }
            if (totalTicket) {
                totalTicket.textContent = "$" + datosVenta.total.toFixed(2);
            }
            if (metodoPagoTicket) {
                metodoPagoTicket.textContent = datosVenta.metodo_pago;
            }
            
            // Actualizar fecha si está disponible
            if (resultadoVenta.fecha) {
                const fechaElement = document.getElementById('fechaTicket');
                if (fechaElement) {
                    fechaElement.textContent = resultadoVenta.fecha;
                }
            }
        }

        // ✅ FUNCIÓN GENERAR PDF AUTOMÁTICO
        generarPDF(resultadoVenta) {
            console.log('📄 Generando PDF...');
            
            // Verificar que las librerías estén cargadas
            if (typeof window.jspdf === 'undefined' || typeof window.html2canvas === 'undefined') {
                console.error('❌ Librerías PDF no disponibles');
                console.log('jspdf disponible:', typeof window.jspdf !== 'undefined');
                console.log('html2canvas disponible:', typeof window.html2canvas !== 'undefined');
                return;
            }

            const { jsPDF } = window.jspdf;
            
            // Asegurar que el modal del ticket esté visible y tenga los datos
            const ticketElement = document.getElementById('ticketModal');
            if (!ticketElement) {
                console.error('❌ No se encontró el elemento ticketModal');
                return;
            }
            
            // Verificar que el ticket tenga contenido
            const ticketItems = document.getElementById('ticketItems');
            if (!ticketItems || ticketItems.children.length === 0) {
                console.error('❌ El ticket no tiene items. Asegúrate de actualizar el ticket antes de generar el PDF.');
                return;
            }
            
            // Guardar estado original del modal
            const originalDisplay = ticketElement.style.display;
            const originalVisibility = ticketElement.style.visibility;
            const originalPosition = ticketElement.style.position;
            const originalLeft = ticketElement.style.left;
            const originalTop = ticketElement.style.top;
            const originalZIndex = ticketElement.style.zIndex;
            
            // Asegurar que el modal esté visible y posicionado correctamente para html2canvas
            ticketElement.style.display = 'block';
            ticketElement.style.visibility = 'visible';
            ticketElement.style.position = 'absolute';
            ticketElement.style.left = '-9999px'; // Mover fuera de la vista pero visible para html2canvas
            ticketElement.style.top = '0';
            ticketElement.style.zIndex = '9999';
            
            // Esperar un momento para que se renderice completamente
            setTimeout(() => {
                this.generarPDFDesdeModal(resultadoVenta, jsPDF, ticketElement, {
                    display: originalDisplay,
                    visibility: originalVisibility,
                    position: originalPosition,
                    left: originalLeft,
                    top: originalTop,
                    zIndex: originalZIndex
                });
            }, 300);
        }

        generarPDFDesdeModal(resultadoVenta, jsPDF, ticketElement, originalStyles) {
            window.html2canvas(ticketElement, {
                scale: 2,
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff',
                allowTaint: true,
                removeContainer: false,
                imageTimeout: 15000,
                onclone: (clonedDoc) => {
                    // Asegurar que el clon también esté visible
                    const clonedElement = clonedDoc.getElementById('ticketModal');
                    if (clonedElement) {
                        clonedElement.style.display = 'block';
                        clonedElement.style.visibility = 'visible';
                    }
                }
            }).then(canvas => {
                try {
                    // Verificar que el canvas sea válido
                    if (!canvas || canvas.width === 0 || canvas.height === 0) {
                        throw new Error('Canvas inválido o vacío');
                    }
                    
                    const imgData = canvas.toDataURL('image/png', 1.0);
                    
                    // Verificar que la imagen sea válida
                    if (!imgData || imgData === 'data:,') {
                        throw new Error('No se pudo generar la imagen del canvas');
                    }
                    
                    const pdf = new jsPDF('p', 'mm', 'a4');
                    const imgWidth = 190;
                    const pageHeight = 280;
                    const imgHeight = (canvas.height * imgWidth) / canvas.width;
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
                } catch (error) {
                    console.error('❌ Error al procesar el canvas:', error);
                    throw error;
                } finally {
                    // Restaurar estilos originales del modal
                    ticketElement.style.display = originalStyles.display || 'none';
                    ticketElement.style.visibility = originalStyles.visibility || '';
                    ticketElement.style.position = originalStyles.position || '';
                    ticketElement.style.left = originalStyles.left || '';
                    ticketElement.style.top = originalStyles.top || '';
                    ticketElement.style.zIndex = originalStyles.zIndex || '';
                }
            }).catch(error => {
                console.error('❌ Error al generar PDF:', error);
                console.error('Detalles del error:', error.message, error.stack);
                
                // Restaurar estilos originales del modal
                ticketElement.style.display = originalStyles.display || 'none';
                ticketElement.style.visibility = originalStyles.visibility || '';
                ticketElement.style.position = originalStyles.position || '';
                ticketElement.style.left = originalStyles.left || '';
                ticketElement.style.top = originalStyles.top || '';
                ticketElement.style.zIndex = originalStyles.zIndex || '';
                
                alert('❌ Error al generar el PDF: ' + error.message + '\nVer consola para más detalles.');
            });
        }

        emitirTicket() {
                
                const gestorTicket = new GestorTicket();
                const mostrarTicket = () => gestorTicket.mostrarTicket();
                mostrarTicket();
            
        }
    }

    // Inicializar GestorVenta globalmente
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Inicializando GestorVenta...');
        window.gestorVenta = new GestorVenta();
        console.log('✅ GestorVenta inicializado globalmente');
    });