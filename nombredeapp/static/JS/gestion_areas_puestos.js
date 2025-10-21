// Variables globales (fuera del DOMContentLoaded para acceso global)
let areasData = [];
let currentFilter = 'all';
let currentAreaId = null;
let currentPuestoId = null;
let currentMode = 'crear';

// Elementos del DOM (se inicializarán en DOMContentLoaded)
let searchInput, filterBtns, areasContainer, btnCrearArea, modalArea, modalPuesto;

// ===== FUNCIONES GLOBALES (accesibles desde HTML) =====
window.editarArea = function(areaId) {
    console.log('Editando área:', areaId);
    if (window.audioSystem) window.audioSystem.play('select');
    abrirModalArea('editar', areaId);
};

window.crearPuesto = function(areaId) {
    console.log('Creando puesto para área:', areaId);
    if (window.audioSystem) window.audioSystem.play('select');
    abrirModalPuesto('crear', areaId);
};

window.editarPuesto = function(areaId, puestoId) {
    console.log('Editando puesto:', puestoId, 'del área:', areaId);
    if (window.audioSystem) window.audioSystem.play('select');
    abrirModalPuesto('editar', areaId, puestoId);
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Iniciando gestión de áreas y puestos...');
    
    // Inicializar elementos del DOM
    searchInput = document.getElementById('search-input');
    filterBtns = document.querySelectorAll('.filter-btn');
    areasContainer = document.getElementById('areas-container');
    btnCrearArea = document.getElementById('btn-crear-area');
    modalArea = document.getElementById('modal-area');
    modalPuesto = document.getElementById('modal-puesto');

    // Verificar que los elementos existen
    if (!searchInput || !areasContainer || !btnCrearArea || !modalArea || !modalPuesto) {
        console.error('Error: No se encontraron elementos necesarios en el DOM');
        return;
    }

    console.log('Elementos del DOM encontrados correctamente');
    
    init();
});

function init() {
    console.log('Inicializando...');
    setupEventListeners();
    cargarAreas();
}

function setupEventListeners() {
    // Búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            renderAreas();
            if (window.audioSystem) window.audioSystem.play('select');
        }, 300));
    }

    // Filtros
    if (filterBtns) {
        filterBtns.forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
            btn.addEventListener('click', () => {
                if (window.audioSystem) window.audioSystem.play('select');
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderAreas();
            });
        });
    }

    // Botón crear área
    if (btnCrearArea) {
        btnCrearArea.addEventListener('mouseenter', () => {
            if (window.audioSystem) window.audioSystem.play('hover');
        });
        btnCrearArea.addEventListener('click', () => {
            if (window.audioSystem) window.audioSystem.play('select');
            abrirModalArea('crear');
        });
    }

    // Modal Área
    const btnAreaCancelar = document.getElementById('btn-area-cancelar');
    const btnAreaGuardar = document.getElementById('btn-area-guardar');
    
    if (btnAreaCancelar) {
        btnAreaCancelar.addEventListener('click', () => {
            if (window.audioSystem) window.audioSystem.play('select');
            cerrarModal(modalArea);
        });
    }
    
    if (btnAreaGuardar) {
        btnAreaGuardar.addEventListener('click', guardarArea);
    }

    // Modal Puesto
    const btnPuestoCancelar = document.getElementById('btn-puesto-cancelar');
    const btnPuestoGuardar = document.getElementById('btn-puesto-guardar');
    
    if (btnPuestoCancelar) {
        btnPuestoCancelar.addEventListener('click', () => {
            if (window.audioSystem) window.audioSystem.play('select');
            cerrarModal(modalPuesto);
        });
    }
    
    if (btnPuestoGuardar) {
        btnPuestoGuardar.addEventListener('click', guardarPuesto);
    }

    // Agregar sonidos a checkboxes de permisos
    document.querySelectorAll('input[name="permiso"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            if (window.audioSystem) window.audioSystem.play('select');
        });
    });
}

// ===== CARGAR DATOS =====
async function cargarAreas() {
    console.log('Cargando áreas...');
    
    if (!areasContainer) {
        console.error('Error: areasContainer no está definido');
        return;
    }
    
    areasContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Cargando...</div>';
    
    try {
        const response = await fetch('/api/areas-puestos/');
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        areasData = await response.json();
        
        // Procesar los datos para extraer el salario de cada puesto
        areasData.forEach(area => {
            area.puestos.forEach(puesto => {
                // Si el salario no viene en el objeto, lo extraemos de la API específica
                if (!puesto.salario || puesto.salario === 0) {
                    puesto.salario = 0; // Valor por defecto
                }
            });
        });
        
        console.log('Áreas cargadas con salarios:', areasData);
        renderAreas();
    } catch (error) {
        console.error('Error al cargar áreas:', error);
        if (window.audioSystem) window.audioSystem.play('error');
        areasContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error al cargar las áreas: ${error.message}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-sync"></i> Reintentar
                </button>
            </div>
        `;
    }
}

// ===== RENDERIZAR =====
function renderAreas() {
    if (!areasContainer || !searchInput) {
        console.error('Error: Elementos necesarios no encontrados');
        return;
    }
    
    const searchTerm = searchInput.value.toLowerCase();
    
    let filtered = areasData.filter(area => {
        const matchSearch = area.nombre.toLowerCase().includes(searchTerm) ||
                           area.puestos.some(p => p.nombre.toLowerCase().includes(searchTerm));
        
        let matchFilter = true;
        if (currentFilter === 'with-positions') {
            matchFilter = area.puestos.length > 0;
        } else if (currentFilter === 'empty') {
            matchFilter = area.puestos.length === 0;
        }
        
        return matchSearch && matchFilter;
    });

    if (filtered.length === 0) {
        areasContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No se encontraron resultados</p>
            </div>
        `;
        return;
    }

    areasContainer.innerHTML = filtered.map(area => `
        <div class="area-card" data-area-id="${escapeHtml(area.id)}">
            <div class="area-header">
                <div class="area-nombre">
                    <i class="fas fa-folder"></i>
                    <span>${escapeHtml(area.nombre)}</span>
                </div>
                <div class="area-actions">
                    <button class="icon-btn" onclick="window.editarArea('${escapeHtml(area.id)}')" title="Editar área">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
            <div class="area-body">
                <div class="puestos-header">
                    <h3>
                        <i class="fas fa-users"></i>
                        Puestos
                        <span class="badge">${area.puestos.length}</span>
                    </h3>
                    <button class="btn-add-puesto" onclick="window.crearPuesto('${escapeHtml(area.id)}')">
                        <i class="fas fa-plus"></i> Añadir
                    </button>
                </div>
                <div class="puestos-list">
                    ${area.puestos.length === 0 ? `
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <p>No hay puestos en esta área</p>
                        </div>
                    ` : area.puestos.map(puesto => `
                        <div class="puesto-item">
                            <div class="puesto-info">
                                <h4>${escapeHtml(puesto.nombre)}</h4>
                                <div style="margin: 8px 0;">
                                    <strong style="color: #28a745;">
                                        <i class="fas fa-dollar-sign"></i> 
                                        Salario: $${formatNumber(puesto.salario || 0)}
                                    </strong>
                                </div>
                                <div class="puesto-permisos">
                                    ${puesto.permisos.length === 0 ? 
                                        '<small style="color: #6c757d;">Sin permisos asignados</small>' :
                                        puesto.permisos.map(p => `
                                            <span class="permiso-badge">
                                                <i class="fas ${getPermisoIcon(p)}"></i>
                                                ${getPermisoNombre(p)}
                                            </span>
                                        `).join('')
                                    }
                                </div>
                            </div>
                            <div class="puesto-actions">
                                <button class="icon-btn" onclick="window.editarPuesto('${escapeHtml(area.id)}', ${puesto.id})" title="Editar puesto">
                                    <i class="fas fa-edit"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `).join('');

    // Agregar sonidos a los botones recién creados
    document.querySelectorAll('.icon-btn, .btn-add-puesto').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            if (window.audioSystem) window.audioSystem.play('hover');
        });
    });
}

// ===== MODALES =====
function abrirModalArea(modo, areaId = null) {
    currentMode = modo;
    currentAreaId = areaId;
    
    const titulo = document.querySelector('#modal-area-titulo span');
    const input = document.getElementById('area-nombre');
    const errorMsg = document.getElementById('area-error-msg');
    
    if (!titulo || !input || !errorMsg) {
        console.error('Error: Elementos del modal de área no encontrados');
        return;
    }
    
    if (modo === 'crear') {
        titulo.textContent = 'Nueva Área';
        input.value = '';
    } else {
        titulo.textContent = 'Editar Área';
        const area = areasData.find(a => a.id === areaId);
        if (area) input.value = area.nombre;
    }
    
    errorMsg.textContent = '';
    modalArea.classList.add('show');
    if (window.audioSystem) window.audioSystem.play('positive');
}

function abrirModalPuesto(modo, areaId, puestoId = null) {
    currentMode = modo;
    currentAreaId = areaId;
    currentPuestoId = puestoId;
    
    const titulo = document.querySelector('#modal-puesto-titulo span');
    const inputNombre = document.getElementById('puesto-nombre');
    const inputSalario = document.getElementById('puesto-salario');
    const errorMsg = document.getElementById('puesto-error-msg');
    const checkboxes = document.querySelectorAll('input[name="permiso"]');
    
    if (!titulo || !inputNombre || !inputSalario || !errorMsg) {
        console.error('Error: Elementos del modal de puesto no encontrados');
        return;
    }
    
    if (modo === 'crear') {
        titulo.textContent = 'Nuevo Puesto';
        inputNombre.value = '';
        inputSalario.value = '';
        checkboxes.forEach(cb => cb.checked = false);
    } else {
        titulo.textContent = 'Editar Puesto';
        const area = areasData.find(a => a.id === areaId);
        const puesto = area?.puestos.find(p => p.id === puestoId);
        if (puesto) {
            inputNombre.value = puesto.nombre;
            inputSalario.value = puesto.salario || 0;
            checkboxes.forEach(cb => {
                cb.checked = puesto.permisos.includes(cb.value);
            });
        }
    }
    
    errorMsg.textContent = '';
    modalPuesto.classList.add('show');
    if (window.audioSystem) window.audioSystem.play('positive');
}

function cerrarModal(modal) {
    if (modal) {
        modal.classList.remove('show');
    }
}

// ===== GUARDAR =====
async function guardarArea() {
    if (window.audioSystem) window.audioSystem.play('select');
    
    const input = document.getElementById('area-nombre');
    const errorMsg = document.getElementById('area-error-msg');
    
    if (!input || !errorMsg) return;
    
    const nombre = input.value.trim();
    
    if (!nombre) {
        errorMsg.textContent = 'El nombre del área es obligatorio';
        if (window.audioSystem) window.audioSystem.play('error');
        return;
    }

    const btnGuardar = document.getElementById('btn-area-guardar');
    if (btnGuardar) {
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    }

    try {
        const url = currentMode === 'crear' 
            ? '/api/areas-puestos/crear-area/' 
            : `/api/areas-puestos/editar-area/${encodeURIComponent(currentAreaId)}/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ nombre })
        });

        const data = await response.json();
        
        if (response.ok) {
            if (window.audioSystem) window.audioSystem.play('positive');
            cerrarModal(modalArea);
            await cargarAreas();
        } else {
            errorMsg.textContent = data.error || 'Error al guardar el área';
            if (window.audioSystem) window.audioSystem.play('error');
        }
    } catch (error) {
        console.error('Error:', error);
        errorMsg.textContent = 'Error de red. Inténtalo de nuevo.';
        if (window.audioSystem) window.audioSystem.play('error');
    } finally {
        if (btnGuardar) {
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = '<i class="fas fa-check"></i> Guardar';
        }
    }
}

async function guardarPuesto() {
    if (window.audioSystem) window.audioSystem.play('select');
    
    const inputNombre = document.getElementById('puesto-nombre');
    const inputSalario = document.getElementById('puesto-salario');
    const errorMsg = document.getElementById('puesto-error-msg');
    
    if (!inputNombre || !inputSalario || !errorMsg) return;
    
    const nombre = inputNombre.value.trim();
    const salario = inputSalario.value.trim();
    const permisos = Array.from(document.querySelectorAll('input[name="permiso"]:checked')).map(cb => cb.value);
    
    if (!nombre) {
        errorMsg.textContent = 'El nombre del puesto es obligatorio';
        if (window.audioSystem) window.audioSystem.play('error');
        return;
    }

    if (!salario || parseFloat(salario) < 0) {
        errorMsg.textContent = 'Debes ingresar un salario válido';
        if (window.audioSystem) window.audioSystem.play('error');
        return;
    }

    const btnGuardar = document.getElementById('btn-puesto-guardar');
    if (btnGuardar) {
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    }

    try {
        const url = currentMode === 'crear' 
            ? '/api/areas-puestos/crear-puesto/' 
            : `/api/areas-puestos/editar-puesto/${currentPuestoId}/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ 
                nombre, 
                area_id: currentAreaId,
                permisos,
                salario: parseFloat(salario)
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            if (window.audioSystem) window.audioSystem.play('positive');
            cerrarModal(modalPuesto);
            await cargarAreas();
            
            if (currentMode === 'editar' && data.empleados_actualizados > 0) {
                alert(`Puesto actualizado correctamente.\n${data.empleados_actualizados} empleado(s) han recibido el nuevo salario automáticamente.`);
            }
        } else {
            errorMsg.textContent = data.error || 'Error al guardar el puesto';
            if (window.audioSystem) window.audioSystem.play('error');
        }
    } catch (error) {
        console.error('Error:', error);
        errorMsg.textContent = 'Error de red. Inténtalo de nuevo.';
        if (window.audioSystem) window.audioSystem.play('error');
    } finally {
        if (btnGuardar) {
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = '<i class="fas fa-check"></i> Guardar';
        }
    }
}

// ===== UTILIDADES =====
function getPermisoIcon(permiso) {
    const iconos = {
        'caja': 'fa-cash-register',
        'stock': 'fa-boxes',
        'crear_empleado': 'fa-user-plus',
        'asistencias': 'fa-clock',
        'registrar_venta': 'fa-receipt'
    };
    return iconos[permiso] || 'fa-check';
}

function getPermisoNombre(permiso) {
    const nombres = {
        'caja': 'Caja',
        'stock': 'Stock',
        'crear_empleado': 'Crear Empleados',
        'asistencias': 'Asistencias',
        'registrar_venta': 'Registrar Venta'
    };
    return nombres[permiso] || permiso;
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

function formatNumber(num) {
    return new Intl.NumberFormat('es-AR').format(num);
}

console.log('Gestión de áreas y puestos inicializada correctamente');