document.addEventListener('DOMContentLoaded', function() {
    // ===== VARIABLES GLOBALES =====
    let empleadosData = [];
    let filteredData = [];
    let currentPage = 1;
    const itemsPerPage = 12;
    let currentEditId = null;
    let horariosEdit = [];
    let rolesEmpleado = []; // ✅ NUEVO: Almacenar todos los roles del empleado
    let rolSeleccionadoEdicion = null; // ✅ NUEVO: Rol que se está editando

    // ===== ELEMENTOS DEL DOM =====
    const searchInput = document.getElementById('search-input');
    const clearSearchBtn = document.getElementById('clear-search');
    const filterEstado = document.getElementById('filter-estado');
    const filterArea = document.getElementById('filter-area');
    const sortSelect = document.getElementById('sort-select');
    const resetFiltersBtn = document.getElementById('reset-filters');
    const empleadosContainer = document.getElementById('empleados-container');
    const paginationContainer = document.getElementById('pagination-container');
    const totalEmpleadosSpan = document.getElementById('total-empleados');
    const currentPageSpan = document.getElementById('current-page');
    const totalPagesSpan = document.getElementById('total-pages');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');

    // Modales
    const modalDetalles = document.getElementById('modal-detalles');
    const modalEditar = document.getElementById('modal-editar');
    const closeDetallesBtn = document.getElementById('close-detalles');
    const closeEditarBtn = document.getElementById('close-editar');
    const cancelEditarBtn = document.getElementById('cancel-editar');
    const formEditarEmpleado = document.getElementById('form-editar-empleado');

    // ===== INICIALIZACIÓN =====
    init();

    function init() {
        cargarEmpleados();
        setupEventListeners();
    }

    function setupEventListeners() {
        // Búsqueda con debounce
        searchInput.addEventListener('input', debounce(() => {
            applyFilters();
            if (searchInput.value.trim()) {
                clearSearchBtn.style.display = 'block';
            } else {
                clearSearchBtn.style.display = 'none';
            }
            if (window.audioSystem) window.audioSystem.play('select');
        }, 300));

        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            applyFilters();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        // Filtros
        filterEstado.addEventListener('change', () => {
            applyFilters();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        filterArea.addEventListener('change', () => {
            applyFilters();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        sortSelect.addEventListener('change', () => {
            applyFilters();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        resetFiltersBtn.addEventListener('mouseenter', () => {
            if (window.audioSystem) window.audioSystem.play('hover');
        });

        resetFiltersBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            filterEstado.value = 'Trabajando';
            filterArea.value = 'all';
            sortSelect.value = 'fecha_desc';
            applyFilters();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        // Paginación
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderEmpleados();
                if (window.audioSystem) window.audioSystem.play('select');
            }
        });

        nextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredData.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderEmpleados();
                if (window.audioSystem) window.audioSystem.play('select');
            }
        });

        // Modales
        closeDetallesBtn.addEventListener('click', () => {
            cerrarModal(modalDetalles);
        });

        closeEditarBtn.addEventListener('click', () => {
            cerrarModal(modalEditar);
        });

        cancelEditarBtn.addEventListener('click', () => {
            cerrarModal(modalEditar);
        });

        formEditarEmpleado.addEventListener('submit', guardarEdicionEmpleado);

        // Botón agregar semana en horarios
        document.getElementById('btn-add-semana').addEventListener('click', () => {
            agregarSemanaEdit();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        // Cerrar modal al hacer click fuera
        [modalDetalles, modalEditar].forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    cerrarModal(modal);
                }
            });
        });
    }

    // ===== CARGAR DATOS =====
    async function cargarEmpleados() {
        try {
            const response = await fetch('/api/empleados/lista/');
            if (!response.ok) throw new Error('Error al cargar empleados');
            
            const data = await response.json();
            empleadosData = data.empleados;
            
            // ✅ CORREGIDO: Cargar TODAS las áreas únicas
            const areasUnicas = [...new Set(empleadosData
                .map(e => e.area)
                .filter(a => a && a !== 'Sin área')  // ✅ Excluir "Sin área"
            )].sort();
            
            filterArea.innerHTML = '<option value="all">Todas las áreas</option>';
            areasUnicas.forEach(area => {
                const option = document.createElement('option');
                option.value = area;
                option.textContent = area;
                filterArea.appendChild(option);
            });
    
            applyFilters();
        } catch (error) {
            console.error('Error:', error);
            if (window.audioSystem) window.audioSystem.play('error');
            empleadosContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar los empleados. Por favor, recarga la página.</p>
                </div>
            `;
        }
    }

    // ===== APLICAR FILTROS =====
    function applyFilters() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const estadoFilter = filterEstado.value;
        const areaFilter = filterArea.value;
        const sortType = sortSelect.value;

        // Filtrar
        filteredData = empleadosData.filter(empleado => {
            // Búsqueda
            const matchSearch = !searchTerm || 
                empleado.nombre.toLowerCase().includes(searchTerm) ||
                empleado.apellido.toLowerCase().includes(searchTerm) ||
                empleado.dni.toString().includes(searchTerm) ||
                empleado.email.toLowerCase().includes(searchTerm) ||
                empleado.puesto.toLowerCase().includes(searchTerm);

            // Estado
            const matchEstado = estadoFilter === 'all' || empleado.estado === estadoFilter;

            // Área
            const matchArea = areaFilter === 'all' || empleado.area === areaFilter;

            return matchSearch && matchEstado && matchArea;
        });

        // Ordenar
        filteredData.sort((a, b) => {
            switch(sortType) {
                case 'nombre_asc':
                    return a.nombre.localeCompare(b.nombre);
                case 'nombre_desc':
                    return b.nombre.localeCompare(a.nombre);
                case 'fecha_asc':
                    return new Date(a.fecha_contratado) - new Date(b.fecha_contratado);
                case 'fecha_desc':
                    return new Date(b.fecha_contratado) - new Date(a.fecha_contratado);
                default:
                    return 0;
            }
        });

        // Actualizar contador
        totalEmpleadosSpan.textContent = filteredData.length;

        // Reset página
        currentPage = 1;
        renderEmpleados();
    }

    // ===== RENDERIZAR EMPLEADOS =====
    function renderEmpleados() {
        if (filteredData.length === 0) {
            empleadosContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No se encontraron empleados con los criterios seleccionados</p>
                </div>
            `;
            paginationContainer.style.display = 'none';
            return;
        }

        // Calcular paginación
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const empleadosPage = filteredData.slice(startIndex, endIndex);
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);

        // Renderizar empleados
        empleadosContainer.innerHTML = empleadosPage.map(empleado => `
            <div class="empleado-card" data-id="${empleado.id}">
                <div class="empleado-header">
                    <div class="empleado-avatar" ${empleado.imagen ? `style="background-image: url('${empleado.imagen}')"` : ''}>
                        ${!empleado.imagen ? getInitials(empleado.nombre, empleado.apellido) : ''}
                    </div>
                    <div class="empleado-info-header">
                        <h3 class="empleado-nombre">${empleado.nombre} ${empleado.apellido}</h3>
                        <p class="empleado-puesto">${empleado.puesto}</p>
                    </div>
                </div>
                <div class="empleado-body">
                    <div class="empleado-details">
                        <div class="detail-item">
                            <i class="fas fa-id-card"></i>
                            <span class="detail-label">DNI:</span>
                            <span class="detail-value">${empleado.dni}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-envelope"></i>
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">${empleado.email}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-briefcase"></i>
                            <span class="detail-label">Área:</span>
                            <span class="detail-value">${empleado.area || 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-circle"></i>
                            <span class="detail-label">Estado:</span>
                            <span class="estado-badge ${empleado.estado.toLowerCase()}">
                                ${empleado.estado}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="empleado-footer">
                    <button class="btn btn-primary" onclick="verDetalles(${empleado.id})">
                        <i class="fas fa-eye"></i> Ver Detalles
                    </button>
                    <button class="btn btn-secondary" onclick="editarEmpleado(${empleado.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                </div>
            </div>
        `).join('');

        // Actualizar paginación
        currentPageSpan.textContent = currentPage;
        totalPagesSpan.textContent = totalPages;
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
        paginationContainer.style.display = totalPages > 1 ? 'flex' : 'none';

        // Agregar sonidos a botones
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
        });
    }

    // ===== VER DETALLES =====
    window.verDetalles = async function(empleadoId) {
        if (window.audioSystem) window.audioSystem.play('select');
        
        try {
            const response = await fetch(`/api/empleados/${empleadoId}/`);
            if (!response.ok) throw new Error('Error al cargar detalles');
            
            const empleado = await response.json();
            
            document.getElementById('detalles-content').innerHTML = `
                <div class="detalles-grid">
                    <div class="detalle-section">
                        <h3><i class="fas fa-user"></i> Información Personal</h3>
                        <div class="detalle-info">
                            <div class="info-row">
                                <span class="info-label">Nombre completo</span>
                                <span class="info-value">${empleado.nombre} ${empleado.apellido}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">DNI</span>
                                <span class="info-value">${empleado.dni}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Email</span>
                                <span class="info-value">${empleado.email}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Teléfono</span>
                                <span class="info-value">${empleado.telefono || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    <div class="detalle-section">
                        <h3><i class="fas fa-briefcase"></i> Información Laboral</h3>
                        <div class="detalle-info">
                            <div class="info-row">
                                <span class="info-label">Área</span>
                                <span class="info-value">${empleado.area || 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Puesto</span>
                                <span class="info-value">${empleado.puesto}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Salario</span>
                                <span class="info-value">$${empleado.salario.toLocaleString()}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Fecha de Contratación</span>
                                <span class="info-value">${formatDate(empleado.fecha_contratado)}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Estado</span>
                                <span class="info-value">
                                    <span class="estado-badge ${empleado.estado.toLowerCase()}">
                                        ${empleado.estado}
                                    </span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="detalle-section">
                        <h3><i class="fas fa-key"></i> Acceso al Sistema</h3>
                        <div class="detalle-info">
                            <div class="info-row">
                                <span class="info-label">Usuario</span>
                                <span class="info-value">${empleado.usuario}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Fecha de Registro</span>
                                <span class="info-value">${formatDate(empleado.fecha_registro)}</span>
                            </div>
                        </div>
                    </div>

                    ${empleado.horarios && empleado.horarios.length > 0 ? `
                    <div class="detalle-section horarios-section" style="grid-column: 1 / -1;">
                        <h3><i class="fas fa-calendar-week"></i> Horarios Semanales</h3>
                        <div class="horarios-grid">
                            ${generarVistaHorarios(empleado.horarios)}
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
            
            abrirModal(modalDetalles);
        } catch (error) {
            console.error('Error:', error);
            if (window.audioSystem) window.audioSystem.play('error');
            alert('Error al cargar los detalles del empleado');
        }
    };

    // ===== EDITAR EMPLEADO (RENOVADO) =====
    window.editarEmpleado = async function(empleadoId) {
        if (window.audioSystem) window.audioSystem.play('select');
        currentEditId = empleadoId;
        
        try {
            const response = await fetch(`/api/empleados/${empleadoId}/`);
            if (!response.ok) throw new Error('Error al cargar datos');
            
            const empleado = await response.json();
            
            // ✅ Llenar campos personales (NUEVO: más campos)
            document.getElementById('edit-nombre').value = empleado.nombre;
            document.getElementById('edit-apellido').value = empleado.apellido;
            document.getElementById('edit-dni').value = empleado.dni;
            document.getElementById('edit-email').value = empleado.email;
            document.getElementById('edit-telefono').value = empleado.telefono || '';
            document.getElementById('edit-direccion').value = empleado.direccion || '';
            document.getElementById('edit-fecha-nacimiento').value = empleado.fecha_nacimiento || '';
            document.getElementById('edit-cod-pais').value = empleado.codigo_telefonico || '+54';
            document.getElementById('edit-salario').value = empleado.salario;
            document.getElementById('edit-estado').value = empleado.estado;
            
            // ✅ NUEVO: Mostrar foto actual
            const photoPreview = document.getElementById('edit-photo-preview');
            if (empleado.imagen) {
                photoPreview.style.backgroundImage = `url('${empleado.imagen}')`;
                photoPreview.innerHTML = '';
            } else {
                photoPreview.style.backgroundImage = '';
                photoPreview.innerHTML = `<i class="fas fa-user"></i>`;
            }
            
            // ✅ NUEVO: Cargar todos los roles del empleado
            await cargarRolesEmpleado(empleado);
            
            // Abrir modal
            abrirModal(modalEditar);
        } catch (error) {
            console.error('Error:', error);
            if (window.audioSystem) window.audioSystem.play('error');
            alert('Error al cargar los datos del empleado');
        }
    };

    async function cargarRolesEmpleado(empleado) {
        try {
            const response = await fetch(`/api/empleados/${empleado.id}/roles/`);
            const data = await response.json();
            rolesEmpleado = data.roles || [];
            
            // ✅ Renderizar selector de roles SIN toggle
            const rolesSelector = document.getElementById('roles-selector');
            rolesSelector.innerHTML = `
                <label><i class="fas fa-briefcase"></i> Selecciona el rol a editar:</label>
                <div class="roles-list">
                    ${rolesEmpleado.map((rol, index) => `
                        <div class="rol-item ${index === 0 ? 'active' : ''}" data-rol-id="${rol.idroles}">
                            <div class="rol-info">
                                <strong>${rol.nombrearea}</strong>
                                <span>${rol.nombrerol}</span>
                            </div>
                            <i class="fas fa-chevron-right"></i>
                        </div>
                    `).join('')}
                </div>
            `;
            
            // Seleccionar el primer rol por defecto
            if (rolesEmpleado.length > 0) {
                rolSeleccionadoEdicion = rolesEmpleado[0].idroles;
                await cargarHorariosDelRol(empleado.id, rolSeleccionadoEdicion);
            }
            
            // Event listeners para cambiar de rol
            document.querySelectorAll('.rol-item').forEach(item => {
                item.addEventListener('click', async function() {
                    const rolId = this.dataset.rolId;
                    rolSeleccionadoEdicion = parseInt(rolId);
                    
                    // Actualizar UI
                    document.querySelectorAll('.rol-item').forEach(r => r.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Cargar horarios de este rol
                    await cargarHorariosDelRol(empleado.id, rolId);
                });
            });
            
        } catch (error) {
            console.error('Error cargando roles:', error);
        }
    }

    // ✅ NUEVO: Cargar horarios específicos de un rol
    async function cargarHorariosDelRol(empleadoId, rolId) {
        try {
            const response = await fetch(`/api/empleados/${empleadoId}/`);
            const empleado = await response.json();
            
            // Filtrar horarios del rol seleccionado
            horariosEdit = empleado.horarios.filter(h => h.rol_id === parseInt(rolId)) || [];
            renderHorariosEdit();
        } catch (error) {
            console.error('Error cargando horarios del rol:', error);
        }
    }

    // ✅ NUEVO: Event listener para cambio de foto
    document.getElementById('edit-photo-input').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const preview = document.getElementById('edit-photo-preview');
                preview.style.backgroundImage = `url('${event.target.result}')`;
                preview.innerHTML = '';
            };
            reader.readAsDataURL(file);
        }
    });

    // ===== GESTIÓN DE HORARIOS EN EDICIÓN =====
    function renderHorariosEdit() {
        const container = document.getElementById('semanas-edit-container');
        
        // Organizar horarios por semana
        const semanas = {};
        horariosEdit.forEach(h => {
            if (!semanas[h.semana_del_mes]) {
                semanas[h.semana_del_mes] = [];
            }
            semanas[h.semana_del_mes].push(h);
        });

        container.innerHTML = '';
        
        const numSemanas = Object.keys(semanas).length;
        if (numSemanas === 0) {
            container.innerHTML = '<p class="no-horarios-edit">No hay horarios asignados para este rol. Agrega una semana para comenzar.</p>';
            return;
        }

        for (let semana in semanas) {
            const semanaDiv = crearSemanaEditHTML(parseInt(semana), semanas[semana]);
            container.insertAdjacentHTML('beforeend', semanaDiv);
        }

        // Agregar eventos a los botones
        container.querySelectorAll('.btn-eliminar-semana').forEach(btn => {
            btn.addEventListener('click', function() {
                const semana = parseInt(this.dataset.semana);
                eliminarSemanaEdit(semana);
            });
        });

        container.querySelectorAll('.btn-toggle-dia').forEach(btn => {
            btn.addEventListener('click', function() {
                const semana = parseInt(this.dataset.semana);
                const dia = parseInt(this.dataset.dia);
                toggleDiaEdit(semana, dia);
            });
        });

        container.querySelectorAll('.btn-add-turno-small').forEach(btn => {
            btn.addEventListener('click', function() {
                const semana = parseInt(this.dataset.semana);
                const dia = parseInt(this.dataset.dia);
                agregarTurnoEdit(semana, dia);
            });
        });

        container.querySelectorAll('.btn-eliminar-turno').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.dataset.index);
                eliminarTurnoEdit(index);
            });
        });

        container.querySelectorAll('.turno-input').forEach(input => {
            input.addEventListener('change', function() {
                const index = parseInt(this.dataset.index);
                const field = this.dataset.field;
                if (horariosEdit[index]) {
                    if (field === 'inicio') {
                        horariosEdit[index].hora_inicio = this.value;
                    } else {
                        horariosEdit[index].hora_fin = this.value;
                    }
                }
            });
        });
    }

    function crearSemanaEditHTML(numSemana, horariosSemanales) {
        const dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
        
        // Organizar horarios por día
        const horariosPorDia = {};
        horariosSemanales.forEach((h, idx) => {
            if (!horariosPorDia[h.dia_semana]) {
                horariosPorDia[h.dia_semana] = [];
            }
            const globalIndex = horariosEdit.findIndex(he => 
                he.semana_del_mes === numSemana && 
                he.dia_semana === h.dia_semana && 
                he.hora_inicio === h.hora_inicio &&
                he.hora_fin === h.hora_fin
            );
            horariosPorDia[h.dia_semana].push({...h, index: globalIndex});
        });

        let html = `
            <div class="semana-edit-card">
                <div class="semana-edit-header">
                    <h4><i class="fas fa-calendar-alt"></i> Semana ${numSemana}</h4>
                    <button type="button" class="btn-icon btn-eliminar-semana" data-semana="${numSemana}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="dias-edit-grid">
        `;

        for (let dia = 0; dia < 7; dia++) {
            const turnos = horariosPorDia[dia] || [];
            const activo = turnos.length > 0;
            
            html += `
                <div class="dia-edit-card ${activo ? 'activo' : ''}">
                    <div class="dia-edit-header">
                        <span>${dias[dia]}</span>
                        <button type="button" class="btn-toggle-dia" data-semana="${numSemana}" data-dia="${dia}">
                            <i class="fas fa-${activo ? 'toggle-on' : 'toggle-off'}"></i>
                        </button>
                    </div>
                    ${activo ? `
                        <div class="turnos-edit-list">
                            ${turnos.map(t => `
                                <div class="turno-edit-item">
                                    <input type="time" class="turno-input" 
                                           value="${t.hora_inicio}" 
                                           data-index="${t.index}" 
                                           data-field="inicio">
                                    <span>-</span>
                                    <input type="time" class="turno-input" 
                                           value="${t.hora_fin}" 
                                           data-index="${t.index}" 
                                           data-field="fin">
                                    <button type="button" class="btn-icon-small btn-eliminar-turno" data-index="${t.index}">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            `).join('')}
                            <button type="button" class="btn-add-turno-small" data-semana="${numSemana}" data-dia="${dia}">
                                <i class="fas fa-plus"></i> Agregar turno
                            </button>
                        </div>
                    ` : `
                        <p class="dia-libre">Día libre</p>
                    `}
                </div>
            `;
        }

        html += `
                </div>
            </div>
        `;

        return html;
    }

    function agregarSemanaEdit() {
        const semanas = [...new Set(horariosEdit.map(h => h.semana_del_mes))];
        const nuevaSemana = semanas.length > 0 ? Math.max(...semanas) + 1 : 1;
        
        if (nuevaSemana > 4) {
            alert('Solo se pueden tener hasta 4 semanas recurrentes');
            if (window.audioSystem) window.audioSystem.play('error');
            return;
        }

        // Agregar un día por defecto (Lunes) con un turno vacío
        horariosEdit.push({
            semana_del_mes: nuevaSemana,
            dia_semana: 0,
            hora_inicio: '09:00',
            hora_fin: '18:00',
            rol_id: rolSeleccionadoEdicion
        });

        renderHorariosEdit();
        if (window.audioSystem) window.audioSystem.play('positive');
    }

    function eliminarSemanaEdit(semana) {
        if (confirm(`¿Eliminar todos los horarios de la Semana ${semana}?`)) {
            horariosEdit = horariosEdit.filter(h => h.semana_del_mes !== semana);
            renderHorariosEdit();
            if (window.audioSystem) window.audioSystem.play('negative');
        }
    }

    function toggleDiaEdit(semana, dia) {
        const turnosDelDia = horariosEdit.filter(h => 
            h.semana_del_mes === semana && h.dia_semana === dia
        );

        if (turnosDelDia.length > 0) {
            // Eliminar todos los turnos del día
            horariosEdit = horariosEdit.filter(h => 
                !(h.semana_del_mes === semana && h.dia_semana === dia)
            );
        } else {
            // Agregar un turno por defecto
            horariosEdit.push({
                semana_del_mes: semana,
                dia_semana: dia,
                hora_inicio: '09:00',
                hora_fin: '18:00',
                rol_id: rolSeleccionadoEdicion
            });
        }

        renderHorariosEdit();
        if (window.audioSystem) window.audioSystem.play('select');
    }

    function agregarTurnoEdit(semana, dia) {
        horariosEdit.push({
            semana_del_mes: semana,
            dia_semana: dia,
            hora_inicio: '09:00',
            hora_fin: '18:00',
            rol_id: rolSeleccionadoEdicion
        });
        renderHorariosEdit();
        if (window.audioSystem) window.audioSystem.play('positive');
    }

    function eliminarTurnoEdit(index) {
        if (index >= 0 && index < horariosEdit.length) {
            horariosEdit.splice(index, 1);
            renderHorariosEdit();
            if (window.audioSystem) window.audioSystem.play('negative');
        }
    }

    async function guardarEdicionEmpleado(e) {
        e.preventDefault();
        if (window.audioSystem) window.audioSystem.play('select');
        
        const errorMsg = document.getElementById('edit-error-msg');
        errorMsg.classList.remove('show');
        
        const saveBtn = document.getElementById('save-editar');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        
        // ✅ Recopilar TODOS los datos (incluyendo nuevos campos)
        const data = {
            nombre: document.getElementById('edit-nombre').value.trim(),
            apellido: document.getElementById('edit-apellido').value.trim(),
            dni: document.getElementById('edit-dni').value.trim(),
            email: document.getElementById('edit-email').value.trim(),
            telefono: document.getElementById('edit-telefono').value.trim(),
            direccion: document.getElementById('edit-direccion').value.trim(),
            fecha_nacimiento: document.getElementById('edit-fecha-nacimiento').value.trim(),
            codigo_telefonico: document.getElementById('edit-cod-pais').value.trim(),
            salario: parseFloat(document.getElementById('edit-salario').value) || 0,
            estado: document.getElementById('edit-estado').value,
            rol_editado: rolSeleccionadoEdicion,
            horarios: horariosEdit,
            roles_activos: [] // IDs de roles que están activos
        };
        
        // ✅ Recopilar estados de roles
        document.querySelectorAll('.btn-toggle-rol').forEach(btn => {
            const icon = btn.querySelector('i');
            const isActive = icon.classList.contains('fa-toggle-on');
            const rolId = parseInt(btn.dataset.rolId);
            if (isActive) {
                data.roles_activos.push(rolId);
            }
        });
        
        // ✅ Foto
        const photoInput = document.getElementById('edit-photo-input');
        if (photoInput.files[0]) {
            const reader = new FileReader();
            reader.onload = async function(e) {
                data.foto = e.target.result;
                await enviarDatosEdicion(data, errorMsg, saveBtn);
            };
            reader.readAsDataURL(photoInput.files[0]);
        } else {
            await enviarDatosEdicion(data, errorMsg, saveBtn);
        }
    }
    
    async function enviarDatosEdicion(data, errorMsg, saveBtn) {
        try {
            const response = await fetch(`/api/empleados/${currentEditId}/editar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                if (window.audioSystem) window.audioSystem.play('positive');
                cerrarModal(modalEditar);
                await cargarEmpleados();
            } else {
                errorMsg.textContent = result.error || 'Error al guardar los cambios';
                errorMsg.classList.add('show');
                if (window.audioSystem) window.audioSystem.play('error');
            }
        } catch (error) {
            console.error('Error:', error);
            errorMsg.textContent = 'Error de red. Inténtalo de nuevo.';
            errorMsg.classList.add('show');
            if (window.audioSystem) window.audioSystem.play('error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
        }
    }

    // ===== UTILIDADES =====
    function abrirModal(modal) {
        modal.classList.add('show');
        if (window.audioSystem) window.audioSystem.play('positive');
    }

    function cerrarModal(modal) {
        modal.classList.remove('show');
        if (window.audioSystem) window.audioSystem.play('select');
    }

    function getInitials(nombre, apellido) {
        return (nombre.charAt(0) + apellido.charAt(0)).toUpperCase();
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-AR');
    }

    function getDiaNombre(dia) {
        const dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
        return dias[dia] || 'N/A';
    }

    function generarVistaHorarios(horarios) {
        // Organizar horarios por semana
        const semanas = {};
        horarios.forEach(h => {
            if (!semanas[h.semana_del_mes]) {
                semanas[h.semana_del_mes] = {};
            }
            if (!semanas[h.semana_del_mes][h.dia_semana]) {
                semanas[h.semana_del_mes][h.dia_semana] = [];
            }
            semanas[h.semana_del_mes][h.dia_semana].push({
                inicio: h.hora_inicio,
                fin: h.hora_fin
            });
        });

        let html = '';
        const numSemanas = Object.keys(semanas).length;

        for (let semana in semanas) {
            html += `
                <div class="semana-horario">
                    <div class="semana-header">Semana ${semana}</div>
                    <div class="dias-horario">
            `;
            
            for (let dia = 0; dia < 7; dia++) {
                const nombreDia = getDiaNombre(dia);
                const turnosDia = semanas[semana][dia] || [];
                
                html += `
                    <div class="dia-horario ${turnosDia.length > 0 ? 'tiene-turno' : 'sin-turno'}">
                        <div class="dia-nombre">${nombreDia.substring(0, 3)}</div>
                        <div class="dia-turnos">
                            ${turnosDia.length > 0 
                                ? turnosDia.map(t => `
                                    <div class="turno">
                                        <i class="fas fa-clock"></i>
                                        <span>${t.inicio.substring(0,5)} - ${t.fin.substring(0,5)}</span>
                                    </div>
                                `).join('')
                                : '<span class="sin-turno-text">Libre</span>'
                            }
                        </div>
                    </div>
                `;
            }
            
            html += `
                    </div>
                </div>
            `;
        }

        return html || '<p class="no-horarios">No hay horarios asignados</p>';
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
});