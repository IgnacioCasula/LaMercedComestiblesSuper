// movimientos_caja.js

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes
    inicializarFiltros();
    inicializarBotonesImpresion();
    inicializarFormularios();
});

function inicializarFiltros() {
    const filtros = document.querySelectorAll('.filtro-grupo select, .filtro-grupo input');
    filtros.forEach(filtro => {
        filtro.addEventListener('change', function() {
            // Opcional: auto-aplicar filtros después de un delay
            // setTimeout(() => {
            //     this.closest('form').submit();
            // }, 1000);
        });
    });
}

function inicializarBotonesImpresion() {
    const btnImprimir = document.getElementById('btn-imprimir');
    if (btnImprimir) {
        btnImprimir.addEventListener('click', function() {
            mostrarModalImpresion();
        });
    }
}

function inicializarFormularios() {
    const formularioMovimiento = document.querySelector('.formulario-movimiento');
    if (formularioMovimiento) {
        formularioMovimiento.addEventListener('submit', function(e) {
            const valor = document.getElementById('valor').value;
            const tipo = document.getElementById('tipo').value;
            const concepto = document.getElementById('concepto').value;
            
            // Validaciones
            if (!valor || parseFloat(valor) <= 0) {
                e.preventDefault();
                mostrarAlerta('❌ Por favor ingrese un valor válido mayor a 0', 'error');
                document.getElementById('valor').focus();
                return false;
            }
            
            if (!tipo || !concepto) {
                e.preventDefault();
                mostrarAlerta('❌ Por favor complete todos los campos obligatorios', 'error');
                return false;
            }
            
            // Mostrar loading
            const btnSubmit = this.querySelector('button[type="submit"]');
            const originalText = btnSubmit.innerHTML;
            btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            btnSubmit.disabled = true;
            
            // Restaurar botón después de 5 segundos (por si hay error)
            setTimeout(() => {
                btnSubmit.innerHTML = originalText;
                btnSubmit.disabled = false;
            }, 5000);
        });
    }
}

// Funciones de impresión
function mostrarModalImpresion() {
    document.getElementById('modalImpresion').style.display = 'flex';
}

function cerrarModalImpresion() {
    document.getElementById('modalImpresion').style.display = 'none';
}

function imprimirMovimientos() {
    // Obtener parámetros actuales de filtros
    const params = new URLSearchParams(window.location.search);
    
    // Redirigir a la API de impresión
    const url = `/caja/movimientos-caja/api/?${params.toString()}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            generarPDF(data);
        })
        .catch(error => {
            console.error('Error al obtener datos para imprimir:', error);
            mostrarAlerta('❌ Error al generar el reporte', 'error');
        });
    
    cerrarModalImpresion();
}

function generarPDF(data) {
    // Crear ventana de impresión
    const ventanaImpresion = window.open('', '_blank');
    
    let contenidoHTML = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Movimientos de Caja - La Merced</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px;
                    color: #333;
                }
                .header { 
                    text-align: center; 
                    margin-bottom: 30px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                }
                .header h1 { 
                    color: #2c3e50; 
                    margin: 0;
                }
                .header .fecha {
                    color: #7f8c8d;
                    margin-top: 5px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                }
                th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                .ingreso { color: #28a745; }
                .egreso { color: #dc3545; }
                .total {
                    font-weight: bold;
                    background-color: #e9ecef;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }
                .badge {
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.8em;
                    font-weight: bold;
                }
                .badge-apertura { background: #fff3cd; color: #856404; }
                .badge-ingreso { background: #d4edda; color: #155724; }
                .badge-egreso { background: #f8d7da; color: #721c24; }
                .badge-cierre { background: #d1ecf1; color: #0c5460; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>SuperMercado La Merced</h1>
                <h2>Movimientos de Caja</h2>
                <div class="fecha">Generado el: ${new Date().toLocaleDateString('es-ES')}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Hora</th>
                        <th>Usuario</th>
                        <th>Caja</th>
                        <th>Tipo</th>
                        <th>Concepto</th>
                        <th>Valor</th>
                        <th>Saldo</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Agregar filas de datos
    data.forEach(mov => {
        const claseTipo = mov.tipo.toLowerCase();
        const badgeClass = `badge-${claseTipo}`;
        
        contenidoHTML += `
            <tr>
                <td>${mov.fecha}</td>
                <td>${mov.hora}</td>
                <td>${mov.usuario}</td>
                <td>${mov.caja}</td>
                <td><span class="badge ${badgeClass}">${mov.tipo}</span></td>
                <td>${mov.concepto}</td>
                <td class="${claseTipo === 'ingreso' ? 'ingreso' : 'egreso'}">${mov.valor}</td>
                <td>${mov.saldo}</td>
            </tr>
        `;
    });
    
    contenidoHTML += `
                </tbody>
            </table>
            
            <div class="footer">
                <p>Total de movimientos: ${data.length}</p>
                <p>SuperMercado La Merced - Sistema de Gestión</p>
            </div>
        </body>
        </html>
    `;
    
    ventanaImpresion.document.write(contenidoHTML);
    ventanaImpresion.document.close();
    
    // Esperar a que cargue el contenido y luego imprimir
    setTimeout(() => {
        ventanaImpresion.print();
        // ventanaImpresion.close(); // Opcional: cerrar después de imprimir
    }, 500);
}

// Funciones de utilidad
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(amount);
}

function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
    button.disabled = true;
    return originalText;
}

function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

function mostrarAlerta(mensaje, tipo = 'info') {
    // Crear elemento de alerta
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo === 'error' ? 'danger' : tipo}`;
    alerta.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${mensaje}</span>
        </div>
    `;
    
    // Agregar al contenedor de mensajes o crear uno
    let mensajesContainer = document.querySelector('.mensajes-container');
    if (!mensajesContainer) {
        mensajesContainer = document.createElement('div');
        mensajesContainer.className = 'mensajes-container';
        document.querySelector('.container-movimientos').appendChild(mensajesContainer);
    }
    
    mensajesContainer.appendChild(alerta);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        alerta.remove();
    }, 5000);
}

// Manejo de errores
window.addEventListener('error', function(e) {
    console.error('Error en movimientos de caja:', e.error);
});

// Exportar funciones para uso global
window.mostrarModalImpresion = mostrarModalImpresion;
window.cerrarModalImpresion = cerrarModalImpresion;
window.imprimirMovimientos = imprimirMovimientos;
window.mostrarAlerta = mostrarAlerta;