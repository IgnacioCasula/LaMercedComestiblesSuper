// Variables globales
let empleadosData = [];
let filteredData = [];
let currentEmpleadoId = null;
let fechaInicio = null;
let fechaFin = null;

// Elementos DOM
let searchInput, filterEstado, filterArea, filterPeriodo;
let empleadosContainer, modalDetalle;

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Iniciando gestión de nóminas...');
    
    initElements();
    setupEventListeners();
    cargarAreas();
    setPeriodoActual();
    cargarDatos();
});

function initElements() {
    searchInput = document.getElementById('search-input');
    filterEstado = document.getElementById('filter-estado');
    filterArea = document.getElementById('filter-area');
    filterPeriodo = document.getElementById('filter-periodo');
    empleadosContainer = document.getElementById('empleados-container');
    modalDetalle = document.getElementById('modal-detalle');
}

function setupEventListeners() {
    // Búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            aplicarFiltros();
            if (window.audioSystem) window.audioSystem.play('select');
        }, 300));
    }

    // Filtros
    [filterEstado, filterArea, filterPeriodo].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', () => {
                if (filter === filterPeriodo && filter.value === 'personalizado') {
                    document.getElementById('fecha-personalizada').style.display = 'flex';
                } else if (filter === filterPeriodo) {
                    document.getElementById('fecha-personalizada').style.display = 'none';
                    setPeriodoActual();
                    cargarDatos();
                }
                aplicarFiltros();
                if (window.audioSystem) window.audioSystem.play('select');
            });
        }
    });

    // Botón aplicar fechas personalizadas
    const btnAplicarFechas = document.getElementById('btn-aplicar-fechas');
    if (btnAplicarFechas) {
        btnAplicarFechas.addEventListener('click', () => {
            fechaInicio = document.getElementById('fecha-inicio').value;
            fechaFin = document.getElementById('fecha-fin').value;
            if (fechaInicio && fechaFin) {
                cargarDatos();
            }
        });
    }

    // Modal detalle
    const btnDetalleCerrar = document.getElementById('btn-detalle-cerrar');
    if (btnDetalleCerrar) {
        btnDetalleCerrar.addEventListener('click', () => {
            cerrarModal(modalDetalle);
        });
    }
}

function setPeriodoActual() {
    const hoy = new Date();
    const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    const ultimoDia = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0);
    
    fechaInicio = formatDate(primerDia);
    fechaFin = formatDate(ultimoDia);
}

// ===== CARGAR DATOS =====
async function cargarAreas() {
    try {
        const response = await fetch('/api/areas-simple/');
        const areas = await response.json();
        
        const filterArea = document.getElementById('filter-area');
        areas.forEach(area => {
            const option = document.createElement('option');
            option.value = area.id;
            option.textContent = area.nombre;
            filterArea.appendChild(option);
        });
    } catch (error) {
        console.error('Error al cargar áreas:', error);
    }
}

async function cargarDatos() {
    if (!empleadosContainer) return;
    
    empleadosContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Cargando datos...</div>';
    
    try {
        const url = `/api/nominas/lista/?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        empleadosData = data.empleados || [];
        
        console.log('Datos de nómina cargados:', empleadosData);
        
        actualizarEstadisticas(data.estadisticas || {});
        aplicarFiltros();
        
    } catch (error) {
        console.error('Error al cargar datos:', error);
        if (window.audioSystem) window.audioSystem.play('error');
        empleadosContainer.innerHTML = `
            <div class="empty-state">
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
    document.getElementById('stat-horas').textContent = (stats.total_horas || 0).toFixed(1) + 'h';
    document.getElementById('stat-salarios').textContent = '$' + formatNumber(stats.total_salarios || 0);
    document.getElementById('stat-pendiente').textContent = '$' + formatNumber(stats.total_pendiente || 0);
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
        if (estado === 'pendiente') {
            matchEstado = emp.saldo_pendiente > 0;
        } else if (estado === 'pagado') {
            matchEstado = emp.saldo_pendiente === 0;
        } else if (estado === 'adelanto') {
            matchEstado = emp.saldo_pendiente < 0;
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
    
    empleadosContainer.innerHTML = filteredData.map(emp => `
        <div class="empleado-row" data-empleado-id="${emp.id}" onclick="verDetalle(${emp.id})" style="cursor: pointer;">
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
                ${emp.puestos.map(p => `<span class="puesto-badge">${escapeHtml(p)}</span>`).join('')}
            </div>
            <div class="empleado-horas">${emp.horas_trabajadas.toFixed(1)}h</div>
            <div class="empleado-devengado">$${formatNumber(emp.total_devengado)}</div>
            <div class="empleado-saldo ${emp.saldo_pendiente > 0 ? 'saldo-positivo' : emp.saldo_pendiente < 0 ? 'saldo-negativo' : 'saldo-cero'}">
                $${formatNumber(emp.saldo_pendiente)}
            </div>
        </div>
    `).join('');
}

// ===== FUNCIONES GLOBALES =====
window.verDetalle = async function(empleadoId) {
    if (window.audioSystem) window.audioSystem.play('select');
    currentEmpleadoId = empleadoId;
    
    try {
        const url = `/api/nominas/detalle/${empleadoId}/?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
        const response = await fetch(url);
        const data = await response.json();
        
        // Llenar información personal
        document.getElementById('detalle-nombre').textContent = `${data.nombre} ${data.apellido}`;
        document.getElementById('detalle-dni').textContent = data.dni;
        
        const puestosHtml = data.puestos.map(p => `<span class="puesto-badge">${p}</span>`).join('');
        document.getElementById('detalle-puestos').innerHTML = puestosHtml;
        
        // Resumen financiero
        document.getElementById('detalle-horas').textContent = data.horas_trabajadas.toFixed(1) + 'h';
        document.getElementById('detalle-devengado').textContent = '$' + formatNumber(data.total_devengado);
        document.getElementById('detalle-pendiente').textContent = '$' + formatNumber(data.saldo_pendiente);
        
        // Historial de asistencias
        const asistenciasHtml = data.asistencias.map(a => `
            <div class="historial-item">
                <div>
                    <strong>${a.fecha}</strong> - ${a.puesto}
                    <br>
                    <small>${a.entrada} - ${a.salida || 'En turno'}</small>
                </div>
                <div><strong>${a.horas.toFixed(1)}h</strong></div>
            </div>
        `).join('');
        document.getElementById('historial-asistencias').innerHTML = asistenciasHtml || '<p style="text-align:center;color:#6c757d;">Sin registros</p>';
        
        modalDetalle.classList.add('show');
        if (window.audioSystem) window.audioSystem.play('positive');
        
    } catch (error) {
        console.error('Error al cargar detalle:', error);
        if (window.audioSystem) window.audioSystem.play('error');
        alert('Error al cargar el detalle del empleado');
    }
};

function cerrarModal(modal) {
    if (modal) {
        modal.classList.remove('show');
    }
}

// ===== UTILIDADES =====
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatNumber(num) {
    return new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
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

console.log('Gestión de nóminas inicializada correctamente');