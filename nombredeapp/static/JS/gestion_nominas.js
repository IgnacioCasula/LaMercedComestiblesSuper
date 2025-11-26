// ===== GESTIÃ"N DE NÃ"MINAS V2 - COMPLETO =====

// Variables globales
let empleadosData = [];
let filteredData = [];
let currentEmpleadoId = null;
let currentRolId = null;
let periodoActual = null;

// Elementos DOM
let searchInput, filterEstado, filterArea, filterPeriodo;
let empleadosContainer, modalDetalle, modalPago;

// ===== INICIALIZACIÃ"N =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando Gestión de Nóminas V2...');
    
    initElements();
    setupEventListeners();
    cargarAreas();
    cargarDatos();
});

function initElements() {
    searchInput = document.getElementById('search-input');
    filterEstado = document.getElementById('filter-estado');
    filterArea = document.getElementById('filter-area');
    empleadosContainer = document.getElementById('empleados-container');
    modalDetalle = document.getElementById('modal-detalle');
    modalPago = document.getElementById('modal-pago');
}

function setupEventListeners() {
    // Búsqueda en tiempo real
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            aplicarFiltros();
            if (window.audioSystem) window.audioSystem.play('select');
        }, 300));
    }

    // Filtros
    [filterEstado, filterArea].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', () => {
                aplicarFiltros();
                if (window.audioSystem) window.audioSystem.play('select');
            });
        }
    });

    // Modal detalle - cerrar
    const btnDetalleCerrar = document.getElementById('btn-detalle-cerrar');
    if (btnDetalleCerrar) {
        btnDetalleCerrar.addEventListener('click', () => {
            cerrarModal(modalDetalle);
        });
    }

    // Modal pago - cerrar
    const btnPagoCancelar = document.getElementById('btn-pago-cancelar');
    if (btnPagoCancelar) {
        btnPagoCancelar.addEventListener('click', () => {
            cerrarModal(modalPago);
        });
    }

    // Modal pago - confirmar
    const btnPagoConfirmar = document.getElementById('btn-pago-confirmar');
    if (btnPagoConfirmar) {
        btnPagoConfirmar.addEventListener('click', confirmarPago);
    }
}

// ===== CARGAR DATOS =====
async function cargarAreas() {
    try {
        const response = await fetch('/api/areas-simple/');
        const areas = await response.json();
        
        const filterArea = document.getElementById('filter-area');
        filterArea.innerHTML = '<option value="all">Todas las áreas</option>';
        
        areas.forEach(area => {
            const option = document.createElement('option');
            option.value = area.id;
            option.textContent = area.nombre;
            filterArea.appendChild(option);
        });
    } catch (error) {
        console.error('❌ Error al cargar áreas:', error);
    }
}

async function cargarDatos() {
    if (!empleadosContainer) return;
    
    empleadosContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Cargando datos de nómina...</div>';
    
    try {
        const response = await fetch('/api/nominas/lista-v2/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        empleadosData = data.empleados || [];
        periodoActual = data.periodo_actual;
        
        console.log('✅ Datos cargados:', empleadosData.length, 'empleados');
        console.log('📅 Período actual:', periodoActual);
        
        actualizarEstadisticas(data.estadisticas || {});
        actualizarInfoPeriodo();
        aplicarFiltros();
        
    } catch (error) {
        console.error('❌ Error al cargar datos:', error);
        if (window.audioSystem) window.audioSystem.play('error');
        empleadosContainer.innerHTML = `
            <div class="empty-state error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error al cargar los datos: ${error.message}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-sync"></i> Reintentar
                </button>
            </div>
        `;
    }
}

function actualizarEstadisticas(stats) {
    document.getElementById('stat-empleados').textContent = stats.total_empleados || 0;
    document.getElementById('stat-horas').textContent = (stats.total_horas_semana || 0).toFixed(1) + 'h';
    document.getElementById('stat-deuda').textContent = '$' + formatNumber(stats.total_deuda || 0);
}

function actualizarInfoPeriodo() {
    if (!periodoActual) return;
    
    const infoPeriodo = document.getElementById('info-periodo');
    if (infoPeriodo) {
        infoPeriodo.innerHTML = `
            <i class="fas fa-calendar-week"></i>
            <strong>Semana actual:</strong> ${formatFecha(periodoActual.inicio)} - ${formatFecha(periodoActual.fin)}
        `;
    }
}

// ===== FILTROS Y RENDERIZADO =====
function aplicarFiltros() {
    if (!searchInput || !filterEstado || !filterArea) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const estado = filterEstado.value;
    const area = filterArea.value;
    
    filteredData = empleadosData.filter(emp => {
        // Filtro de búsqueda
        const matchSearch = 
            emp.nombre.toLowerCase().includes(searchTerm) ||
            emp.apellido.toLowerCase().includes(searchTerm) ||
            emp.dni.includes(searchTerm);
        
        // Filtro de estado
        let matchEstado = true;
        if (estado !== 'all') {
            matchEstado = emp.estado === estado;
        }
        
        // Filtro de área
        let matchArea = true;
        if (area !== 'all') {
            matchArea = emp.areas.includes(area);
        }
        
        return matchSearch && matchEstado && matchArea;
    });
    
    renderEmpleados();
}

function renderEmpleados() {
    if (!empleadosContainer) return;
    
    if (filteredData.length === 0) {
        empleadosContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No se encontraron empleados con los filtros aplicados</p>
            </div>
        `;
        return;
    }
    
    empleadosContainer.innerHTML = filteredData.map(emp => {
        const estadoClass = getEstadoClass(emp.estado);
        const estadoIcon = getEstadoIcon(emp.estado);
        const estadoText = getEstadoText(emp.estado);
        
        return `
            <div class="empleado-row ${estadoClass}" data-empleado-id="${emp.id}" onclick="verDetalle(${emp.id})">
                <div class="empleado-info">
                    ${emp.imagen ? 
                        `<img src="${emp.imagen}" class="empleado-avatar" alt="${emp.nombre}">` :
                        `<div class="empleado-avatar-placeholder">${emp.nombre.charAt(0)}</div>`
                    }
                    <div class="empleado-datos">
                        <h4>${escapeHtml(emp.nombre)} ${escapeHtml(emp.apellido)}</h4>
                        <p>DNI: ${escapeHtml(emp.dni)}</p>
                    </div>
                </div>
                <div class="empleado-puestos">
                    ${emp.puestos.map(p => `<span class="puesto-badge">${escapeHtml(p.nombre)}</span>`).join('')}
                </div>
                <div class="empleado-horas">
                    <div class="valor-principal">${emp.horas_semana_actual.toFixed(1)}h</div>
                    <div class="texto-secundario">Esta semana</div>
                </div>
                <div class="empleado-devengado">
                    <div class="valor-principal">$${formatNumber(emp.devengado_semana_actual)}</div>
                    <div class="texto-secundario">Devengado</div>
                </div>
                <div class="empleado-deuda">
                    <div class="valor-principal ${emp.deuda_acumulada > 0 ? 'texto-warning' : ''}">
                        $${formatNumber(emp.deuda_acumulada)}
                    </div>
                    <div class="texto-secundario">Deuda anterior</div>
                </div>
                <div class="empleado-total">
                    <div class="valor-principal texto-bold">$${formatNumber(emp.total_adeudado)}</div>
                    <div class="texto-secundario">Total a pagar</div>
                </div>
                <div class="empleado-estado">
                    <span class="estado-badge estado-${emp.estado}">
                        <i class="${estadoIcon}"></i> ${estadoText}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

// ===== DETALLE DE EMPLEADO =====
window.verDetalle = async function(empleadoId) {
    if (window.audioSystem) window.audioSystem.play('select');
    currentEmpleadoId = empleadoId;
    currentRolId = null;
    
    try {
        const response = await fetch(`/api/nominas/detalle-v2/${empleadoId}/`);
        const data = await response.json();
        
        // Información personal
        document.getElementById('detalle-nombre').textContent = `${data.nombre} ${data.apellido}`;
        document.getElementById('detalle-dni').textContent = data.dni;
        
        // Período actual
        document.getElementById('detalle-periodo').textContent = 
            `${data.periodo_actual.inicio} - ${data.periodo_actual.fin}`;
        
        // Semana actual
        document.getElementById('detalle-horas-semana').textContent = data.semana_actual.horas_total.toFixed(1) + 'h';
        document.getElementById('detalle-devengado-semana').textContent = '$' + formatNumber(data.semana_actual.devengado_total);
        
        // Deuda acumulada
        document.getElementById('detalle-deuda-acumulada').textContent = '$' + formatNumber(data.deuda_acumulada);
        
        // Total a pagar
        const totalAdeudado = data.total_adeudado;
        document.getElementById('detalle-total-pagar').textContent = '$' + formatNumber(totalAdeudado);
        
        // Habilitar/deshabilitar botón de pago
        const btnPagar = document.getElementById('btn-detalle-pagar');
        if (btnPagar) {
            if (totalAdeudado > 0) {
                btnPagar.disabled = false;
                btnPagar.onclick = () => mostrarModalPago(empleadoId, totalAdeudado);
            } else {
                btnPagar.disabled = true;
            }
        }
        
        // Renderizar roles
        renderRoles(data.roles);
        
        // Renderizar historial semanal
        renderHistorialSemanal(data.historial_semanal);
        
        // Renderizar pagos recientes
        renderPagosRecientes(data.pagos_recientes);
        
        // Mostrar asistencias de todos los roles por defecto
        renderAsistencias(data.roles);
        
        modalDetalle.classList.add('show');
        if (window.audioSystem) window.audioSystem.play('positive');
        
    } catch (error) {
        console.error('❌ Error al cargar detalle:', error);
        if (window.audioSystem) window.audioSystem.play('error');
        alert('Error al cargar el detalle del empleado');
    }
};

function renderRoles(roles) {
    const rolesContainer = document.getElementById('detalle-roles');
    if (!rolesContainer) return;
    
    rolesContainer.innerHTML = roles.map(rol => `
        <div class="rol-card ${currentRolId === rol.id ? 'active' : ''}" onclick="filtrarPorRol(${rol.id})">
            <div class="rol-header">
                <h4>${escapeHtml(rol.nombre)}</h4>
                <span class="rol-area">${escapeHtml(rol.area)}</span>
            </div>
            <div class="rol-stats">
                <div class="rol-stat">
                    <i class="fas fa-clock"></i>
                    <span>${rol.horas_semana.toFixed(1)}h</span>
                </div>
                <div class="rol-stat">
                    <i class="fas fa-dollar-sign"></i>
                    <span>$${formatNumber(rol.devengado_semana)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

window.filtrarPorRol = async function(rolId) {
    if (window.audioSystem) window.audioSystem.play('select');
    currentRolId = rolId;
    
    try {
        const response = await fetch(`/api/nominas/detalle-v2/${currentEmpleadoId}/`);
        const data = await response.json();
        
        if (rolId === null) {
            // Mostrar todos los roles
            renderAsistencias(data.roles);
        } else {
            // Filtrar por rol específico
            const rolData = data.roles.find(r => r.id === rolId);
            if (rolData) {
                renderAsistencias([rolData]);
            }
        }
        
        // Actualizar UI de roles
        renderRoles(data.roles);
        
    } catch (error) {
        console.error('❌ Error al filtrar por rol:', error);
    }
};

function renderAsistencias(roles) {
    const asistenciasContainer = document.getElementById('historial-asistencias');
    if (!asistenciasContainer) return;
    
    let todasAsistencias = [];
    roles.forEach(rol => {
        rol.asistencias.forEach(asistencia => {
            todasAsistencias.push({
                ...asistencia,
                rol: rol.nombre
            });
        });
    });
    
    if (todasAsistencias.length === 0) {
        asistenciasContainer.innerHTML = '<p class="empty-message">Sin registros en esta semana</p>';
        return;
    }
    
    asistenciasContainer.innerHTML = todasAsistencias.map(a => `
        <div class="historial-item">
            <div class="asistencia-info">
                <strong>${a.fecha}</strong>
                <span class="asistencia-rol">${escapeHtml(a.rol)}</span>
                <br>
                <small>${a.entrada} - ${a.salida}</small>
            </div>
            <div class="asistencia-horas">
                <strong>${a.horas.toFixed(1)}h</strong>
            </div>
        </div>
    `).join('');
}

function renderHistorialSemanal(historial) {
    const historialContainer = document.getElementById('historial-semanal');
    if (!historialContainer) return;
    
    if (historial.length === 0) {
        historialContainer.innerHTML = '<p class="empty-message">Sin historial previo</p>';
        return;
    }
    
    historialContainer.innerHTML = historial.map(h => `
        <div class="historial-semanal-item">
            <div class="semana-info">
                <strong>${h.periodo}</strong>
                <span class="semana-rol">${escapeHtml(h.rol)}</span>
            </div>
            <div class="semana-stats">
                <span>${h.horas.toFixed(1)}h</span>
                <span class="semana-monto">$${formatNumber(h.monto)}</span>
            </div>
        </div>
    `).join('');
}

function renderPagosRecientes(pagos) {
    const pagosContainer = document.getElementById('pagos-recientes');
    if (!pagosContainer) return;
    
    if (pagos.length === 0) {
        pagosContainer.innerHTML = '<p class="empty-message">Sin pagos registrados</p>';
        return;
    }
    
    pagosContainer.innerHTML = pagos.map(p => `
        <div class="pago-item">
            <div class="pago-info">
                <strong>$${formatNumber(p.monto)}</strong>
                <span class="pago-metodo">${p.metodo}</span>
                <br>
                <small>${p.fecha} - ${escapeHtml(p.usuario)}</small>
                ${p.observacion ? `<br><small class="pago-obs">${escapeHtml(p.observacion)}</small>` : ''}
            </div>
        </div>
    `).join('');
}

// ===== MODAL DE PAGO =====
function mostrarModalPago(empleadoId, totalAdeudado) {
    if (window.audioSystem) window.audioSystem.play('select');
    
    currentEmpleadoId = empleadoId;
    
    document.getElementById('pago-monto-max').textContent = formatNumber(totalAdeudado);
    document.getElementById('pago-monto').value = totalAdeudado.toFixed(2);
    document.getElementById('pago-monto').max = totalAdeudado.toFixed(2);
    document.getElementById('pago-metodo').value = 'Efectivo';
    document.getElementById('pago-observacion').value = '';
    document.getElementById('pago-comprobante').value = '';
    
    modalPago.classList.add('show');
}

async function confirmarPago() {
    const monto = parseFloat(document.getElementById('pago-monto').value);
    const metodo = document.getElementById('pago-metodo').value;
    const observacion = document.getElementById('pago-observacion').value;
    const comprobante = document.getElementById('pago-comprobante').value;
    
    if (!monto || monto <= 0) {
        alert('Ingrese un monto válido');
        return;
    }
    
    if (window.audioSystem) window.audioSystem.play('processing');
    
    try {
        const response = await fetch('/api/nominas/registrar-pago-v2/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                empleado_id: currentEmpleadoId,
                monto: monto,
                metodo: metodo,
                observacion: observacion,
                comprobante: comprobante
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (window.audioSystem) window.audioSystem.play('success');
            alert(`Pago registrado correctamente.\nNuevo saldo: $${formatNumber(data.nuevo_saldo)}`);
            cerrarModal(modalPago);
            cerrarModal(modalDetalle);
            cargarDatos();
        } else {
            throw new Error(data.error || 'Error al registrar el pago');
        }
        
    } catch (error) {
        console.error('❌ Error al registrar pago:', error);
        if (window.audioSystem) window.audioSystem.play('error');
        alert('Error: ' + error.message);
    }
}

// ===== UTILIDADES =====
function getEstadoClass(estado) {
    const classes = {
        'pagado': 'estado-pagado',
        'pendiente': 'estado-pendiente',
        'alerta': 'estado-alerta',
        'critico': 'estado-critico'
    };
    return classes[estado] || '';
}

function getEstadoIcon(estado) {
    const icons = {
        'pagado': 'fas fa-check-circle',
        'pendiente': 'fas fa-clock',
        'alerta': 'fas fa-exclamation-triangle',
        'critico': 'fas fa-exclamation-circle'
    };
    return icons[estado] || 'fas fa-question-circle';
}

function getEstadoText(estado) {
    const texts = {
        'pagado': 'Al día',
        'pendiente': 'Pendiente',
        'alerta': 'Alerta',
        'critico': 'Crítico'
    };
    return texts[estado] || 'Desconocido';
}

function cerrarModal(modal) {
    if (modal) {
        modal.classList.remove('show');
    }
}

function formatNumber(num) {
    return new Intl.NumberFormat('es-AR', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    }).format(num);
}

function formatFecha(fechaStr) {
    const [year, month, day] = fechaStr.split('-');
    return `${day}/${month}/${year}`;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

console.log('✅ Gestión de Nóminas V2 inicializada correctamente');