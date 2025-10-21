document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let areasData = [];
    let currentFilter = 'all';
    let currentAreaId = null;
    let currentPuestoId = null;
    let currentMode = 'crear'; // 'crear' o 'editar'
    let deleteCallback = null;

    // Elementos del DOM
    const searchInput = document.getElementById('search-input');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const areasContainer = document.getElementById('areas-container');
    const btnCrearArea = document.getElementById('btn-crear-area');

    // Modales
    const modalArea = document.getElementById('modal-area');
    const modalPuesto = document.getElementById('modal-puesto');
    const modalConfirmar = document.getElementById('modal-confirmar');

    // Inicializar
    init();

    function init() {
        cargarAreas();
        setupEventListeners();
    }

    function setupEventListeners() {
        // Búsqueda
        searchInput.addEventListener('input', debounce(() => {
            renderAreas();
            window.audioSystem.play('select');
        }, 300));

        // Filtros
        filterBtns.forEach(btn => {
            btn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
            btn.addEventListener('click', () => {
                window.audioSystem.play('select');
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderAreas();
            });
        });

        // Botón crear área
        btnCrearArea.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
        btnCrearArea.addEventListener('click', () => {
            window.audioSystem.play('select');
            abrirModalArea('crear');
        });

        // Modal Área
        document.getElementById('btn-area-cancelar').addEventListener('click', () => {
            window.audioSystem.play('select');
            cerrarModal(modalArea);
        });
        document.getElementById('btn-area-guardar').addEventListener('click', guardarArea);

        // Modal Puesto
        document.getElementById('btn-puesto-cancelar').addEventListener('click', () => {
            window.audioSystem.play('select');
            cerrarModal(modalPuesto);
        });
        document.getElementById('btn-puesto-guardar').addEventListener('click', guardarPuesto);

        // Modal Confirmar
        document.getElementById('btn-confirmar-cancelar').addEventListener('click', () => {
            window.audioSystem.play('select');
            cerrarModal(modalConfirmar);
        });
        document.getElementById('btn-confirmar-eliminar').addEventListener('click', confirmarEliminacion);

        // Agregar sonidos a checkboxes de permisos
        document.querySelectorAll('input[name="permiso"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => window.audioSystem.play('select'));
        });
    }

    // ===== CARGAR DATOS =====
    async function cargarAreas() {
        try {
            const response = await fetch('/api/areas-puestos/');
            if (!response.ok) throw new Error('Error al cargar áreas');
            areasData = await response.json();
            renderAreas();
        } catch (error) {
            console.error('Error:', error);
            window.audioSystem.play('error');
            areasContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar las áreas. Por favor, recarga la página.</p>
                </div>
            `;
        }
    }

    // ===== RENDERIZAR =====
    function renderAreas() {
        const searchTerm = searchInput.value.toLowerCase();
        
        // Filtrar áreas
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
            <div class="area-card" data-area-id="${area.id}">
                <div class="area-header">
                    <div class="area-nombre">
                        <i class="fas fa-folder"></i>
                        <span>${area.nombre}</span>
                    </div>
                    <div class="area-actions">
                        <button class="icon-btn" onclick="editarArea(${area.id})" title="Editar área">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="icon-btn" onclick="eliminarArea(${area.id}, '${area.nombre}')" title="Eliminar área">
                            <i class="fas fa-trash"></i>
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
                        <button class="btn-add-puesto" onclick="crearPuesto(${area.id})">
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
                                    <h4>${puesto.nombre}</h4>
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
                                    <button class="icon-btn" onclick="editarPuesto(${area.id}, ${puesto.id})" title="Editar puesto">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="icon-btn" onclick="eliminarPuesto(${area.id}, ${puesto.id}, '${puesto.nombre}')" title="Eliminar puesto">
                                        <i class="fas fa-trash"></i>
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
            btn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
        });
    }

    // ===== MODALES =====
    function abrirModalArea(modo, areaId = null) {
        currentMode = modo;
        currentAreaId = areaId;
        
        const titulo = document.querySelector('#modal-area-titulo span');
        const input = document.getElementById('area-nombre');
        const errorMsg = document.getElementById('area-error-msg');
        
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
        window.audioSystem.play('positive');
    }

    function abrirModalPuesto(modo, areaId, puestoId = null) {
        currentMode = modo;
        currentAreaId = areaId;
        currentPuestoId = puestoId;
        
        const titulo = document.querySelector('#modal-puesto-titulo span');
        const input = document.getElementById('puesto-nombre');
        const errorMsg = document.getElementById('puesto-error-msg');
        const checkboxes = document.querySelectorAll('input[name="permiso"]');
        
        if (modo === 'crear') {
            titulo.textContent = 'Nuevo Puesto';
            input.value = '';
            checkboxes.forEach(cb => cb.checked = false);
        } else {
            titulo.textContent = 'Editar Puesto';
            const area = areasData.find(a => a.id === areaId);
            const puesto = area?.puestos.find(p => p.id === puestoId);
            if (puesto) {
                input.value = puesto.nombre;
                checkboxes.forEach(cb => {
                    cb.checked = puesto.permisos.includes(cb.value);
                });
            }
        }
        
        errorMsg.textContent = '';
        modalPuesto.classList.add('show');
        window.audioSystem.play('positive');
    }

    function cerrarModal(modal) {
        modal.classList.remove('show');
    }

    // ===== GUARDAR =====
    async function guardarArea() {
        window.audioSystem.play('select');
        const nombre = document.getElementById('area-nombre').value.trim();
        const errorMsg = document.getElementById('area-error-msg');
        
        if (!nombre) {
            errorMsg.textContent = 'El nombre del área es obligatorio';
            window.audioSystem.play('error');
            return;
        }

        const btnGuardar = document.getElementById('btn-area-guardar');
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

        try {
            const url = currentMode === 'crear' ? '/api/areas-puestos/crear-area/' : `/api/areas-puestos/editar-area/${currentAreaId}/`;
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
                window.audioSystem.play('positive');
                cerrarModal(modalArea);
                await cargarAreas();
            } else {
                errorMsg.textContent = data.error || 'Error al guardar el área';
                window.audioSystem.play('error');
            }
        } catch (error) {
            console.error('Error:', error);
            errorMsg.textContent = 'Error de red. Inténtalo de nuevo.';
            window.audioSystem.play('error');
        } finally {
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = '<i class="fas fa-check"></i> Guardar';
        }
    }

    async function guardarPuesto() {
        window.audioSystem.play('select');
        const nombre = document.getElementById('puesto-nombre').value.trim();
        const permisos = Array.from(document.querySelectorAll('input[name="permiso"]:checked')).map(cb => cb.value);
        const errorMsg = document.getElementById('puesto-error-msg');
        
        if (!nombre) {
            errorMsg.textContent = 'El nombre del puesto es obligatorio';
            window.audioSystem.play('error');
            return;
        }

        const btnGuardar = document.getElementById('btn-puesto-guardar');
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

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
                    permisos 
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                window.audioSystem.play('positive');
                cerrarModal(modalPuesto);
                await cargarAreas();
            } else {
                errorMsg.textContent = data.error || 'Error al guardar el puesto';
                window.audioSystem.play('error');
            }
        } catch (error) {
            console.error('Error:', error);
            errorMsg.textContent = 'Error de red. Inténtalo de nuevo.';
            window.audioSystem.play('error');
        } finally {
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = '<i class="fas fa-check"></i> Guardar';
        }
    }

    // ===== ELIMINAR =====
    function mostrarModalConfirmar(mensaje, callback) {
        document.getElementById('confirmar-mensaje').textContent = mensaje;
        deleteCallback = callback;
        modalConfirmar.classList.add('show');
        window.audioSystem.play('negative');
    }

    async function confirmarEliminacion() {
        window.audioSystem.play('select');
        if (deleteCallback) {
            await deleteCallback();
            deleteCallback = null;
        }
        cerrarModal(modalConfirmar);
    }

    // ===== FUNCIONES GLOBALES (llamadas desde onclick) =====
    window.editarArea = function(areaId) {
        window.audioSystem.play('select');
        abrirModalArea('editar', areaId);
    };

    window.eliminarArea = function(areaId, nombre) {
        window.audioSystem.play('select');
        const area = areasData.find(a => a.id === areaId);
        if (area && area.puestos.length > 0) {
            window.audioSystem.play('error');
            alert('No puedes eliminar un área que tiene puestos asignados. Elimina primero los puestos.');
            return;
        }
        
        mostrarModalConfirmar(
            `¿Estás seguro de que deseas eliminar el área "${nombre}"? Esta acción no se puede deshacer.`,
            async () => {
                try {
                    const response = await fetch(`/api/areas-puestos/eliminar-area/${areaId}/`, {
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': getCookie('csrftoken') }
                    });
                    
                    if (response.ok) {
                        window.audioSystem.play('positive');
                        await cargarAreas();
                    } else {
                        const data = await response.json();
                        window.audioSystem.play('error');
                        alert(data.error || 'Error al eliminar el área');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    window.audioSystem.play('error');
                    alert('Error de red. Inténtalo de nuevo.');
                }
            }
        );
    };

    window.crearPuesto = function(areaId) {
        window.audioSystem.play('select');
        abrirModalPuesto('crear', areaId);
    };

    window.editarPuesto = function(areaId, puestoId) {
        window.audioSystem.play('select');
        abrirModalPuesto('editar', areaId, puestoId);
    };

    window.eliminarPuesto = function(areaId, puestoId, nombre) {
        window.audioSystem.play('select');
        mostrarModalConfirmar(
            `¿Estás seguro de que deseas eliminar el puesto "${nombre}"? Los empleados con este puesto perderán sus permisos asociados.`,
            async () => {
                try {
                    const response = await fetch(`/api/areas-puestos/eliminar-puesto/${puestoId}/`, {
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': getCookie('csrftoken') }
                    });
                    
                    if (response.ok) {
                        window.audioSystem.play('positive');
                        await cargarAreas();
                    } else {
                        const data = await response.json();
                        window.audioSystem.play('error');
                        alert(data.error || 'Error al eliminar el puesto');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    window.audioSystem.play('error');
                    alert('Error de red. Inténtalo de nuevo.');
                }
            }
        );
    };

    // ===== UTILIDADES =====
    function getPermisoIcon(permiso) {
        const iconos = {
            'caja': 'fa-cash-register',
            'stock': 'fa-boxes',
            'crear_empleado': 'fa-user-plus',
            'asistencias': 'fa-clock'
        };
        return iconos[permiso] || 'fa-check';
    }

    function getPermisoNombre(permiso) {
        const nombres = {
            'caja': 'Caja',
            'stock': 'Stock',
            'crear_empleado': 'Crear Empleados',
            'asistencias': 'Asistencias'
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
});