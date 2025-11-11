document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let selectedArea = null;
    let selectedPuesto = null;
    let scheduleData = {};
    let dayColorMap = {};
    let weekIdCounter = 1;
    let modoOperacion = null; // 'crear' o 'asignar'
    let empleadoSeleccionado = null;

    const daysOfWeek = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'];
    const availableColors = ["#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9"];
    let activeColors = [availableColors[0]];
    let selectedColor = activeColors[0];

    // ===== MODAL INICIAL: ELEGIR TIPO DE OPERACIÓN =====
    setupModalTipoOperacion();

    // ===== FOTO DE PERFIL =====
    const photoUploader = document.getElementById('photo-uploader');
    const photoInput = document.getElementById('photo-input');
    const photoButton = document.getElementById('photo-button');
    
    if (photoUploader && photoInput && photoButton) {
        photoUploader.addEventListener('click', () => {
            window.audioSystem.play('select');
            photoInput.click();
        });
        
        photoInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                window.audioSystem.play('positive');
                const reader = new FileReader();
                reader.onload = (e) => {
                    photoUploader.style.backgroundImage = `url('${e.target.result}')`;
                    photoButton.textContent = 'Cambiar Foto';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // ===== VALIDACIONES DE CAMPOS =====
    setupFieldValidations();
    
    // ===== BOTONES DE ACCIÓN =====
    const btnCancel = document.getElementById('btn-cancel');
    if (btnCancel) {
        btnCancel.addEventListener('click', () => {
            window.audioSystem.play('select');
            if (confirm('¿Está seguro de que desea cancelar? Se perderán todos los datos ingresados.')) {
                window.audioSystem.play('negative');
                window.location.href = document.body.dataset.inicioUrl;
            }
        });
    }

    const btnAddLaboral = document.getElementById('btn-add-laboral');
    const laboralDataSection = document.getElementById('laboral-data');
    
    if (btnAddLaboral && laboralDataSection) {
        btnAddLaboral.addEventListener('click', () => {
            window.audioSystem.play('select');
            laboralDataSection.style.display = 'block';
            btnAddLaboral.style.display = 'none';
        });
    }

    // ===== LÓGICA DE ÁREA Y PUESTO =====
    setupAreaPuestoLogic();
    
    // ===== LÓGICA DEL HORARIO =====
    setupScheduleLogic();
    
    // ===== ENVÍO FINAL =====
    setupFinalSubmit();

    // ========== FUNCIONES AUXILIARES ==========
    
    function setupModalTipoOperacion() {
        const modalTipoOperacion = document.getElementById('modal-tipo-operacion');
        const btnCrearNuevo = document.getElementById('btn-crear-nuevo');
        const btnAsignarRol = document.getElementById('btn-asignar-rol');
        const mainFormContainer = document.getElementById('main-form-container');

        if (!modalTipoOperacion || !btnCrearNuevo || !btnAsignarRol) return;

        btnCrearNuevo.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
        btnAsignarRol.addEventListener('mouseenter', () => window.audioSystem.play('hover'));

        btnCrearNuevo.addEventListener('click', () => {
            window.audioSystem.play('positive');
            modoOperacion = 'crear';
            modalTipoOperacion.classList.remove('show');
            setTimeout(() => {
                modalTipoOperacion.style.display = 'none';
                mainFormContainer.style.display = 'block';
                configurarModoCrear();
            }, 300);
        });

        btnAsignarRol.addEventListener('click', () => {
            window.audioSystem.play('positive');
            modoOperacion = 'asignar';
            modalTipoOperacion.classList.remove('show');
            setTimeout(() => {
                modalTipoOperacion.style.display = 'none';
                abrirModalBuscarEmpleado();
            }, 300);
        });
    }

    function configurarModoCrear() {
        const tituloPrincipal = document.getElementById('titulo-principal');
        const seccionDatosPersonales = document.getElementById('seccion-datos-personales');
        const empleadoBanner = document.getElementById('empleado-seleccionado-banner');
        const textoBtnListo = document.getElementById('texto-btn-listo');
        const tituloSeccionLaboral = document.getElementById('titulo-seccion-laboral');

        if (tituloPrincipal) tituloPrincipal.textContent = 'Añadir Nuevo Empleado';
        if (seccionDatosPersonales) seccionDatosPersonales.style.display = 'block';
        if (empleadoBanner) empleadoBanner.style.display = 'none';
        if (textoBtnListo) textoBtnListo.textContent = 'Listo';
        if (tituloSeccionLaboral) tituloSeccionLaboral.textContent = 'Datos Laborales';
    }

    function abrirModalBuscarEmpleado() {
        const modalBuscar = document.getElementById('modal-buscar-empleado');
        const searchInput = document.getElementById('search-empleado-input');
        const empleadosEncontrados = document.getElementById('empleados-encontrados');
        const btnCancelarBusqueda = document.getElementById('btn-cancelar-busqueda');

        if (!modalBuscar) return;

        modalBuscar.style.display = 'flex';
        searchInput.value = '';
        empleadosEncontrados.innerHTML = '<p style="text-align:center; color:#666;">Escribe para buscar empleados...</p>';

        searchInput.focus();

        searchInput.addEventListener('input', debounce(async () => {
            const query = searchInput.value.trim();
            if (query.length < 2) {
                empleadosEncontrados.innerHTML = '<p style="text-align:center; color:#666;">Escribe al menos 2 caracteres...</p>';
                return;
            }
            await buscarEmpleados(query);
        }, 300));

        btnCancelarBusqueda.addEventListener('click', () => {
            window.audioSystem.play('select');
            modalBuscar.style.display = 'none';
            // Volver al modal inicial
            const modalTipoOperacion = document.getElementById('modal-tipo-operacion');
            if (modalTipoOperacion) {
                modalTipoOperacion.style.display = 'flex';
                setTimeout(() => modalTipoOperacion.classList.add('show'), 10);
            }
        });
    }

    async function buscarEmpleados(query) {
        const empleadosEncontrados = document.getElementById('empleados-encontrados');
        try {
            const url = `${document.body.dataset.apiBuscarEmpleadosUrl}?q=${encodeURIComponent(query)}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.length === 0) {
                empleadosEncontrados.innerHTML = '<p style="text-align:center; color:#666;">No se encontraron empleados.</p>';
                return;
            }

            empleadosEncontrados.innerHTML = '';
            data.forEach(emp => {
                const div = document.createElement('div');
                div.className = 'empleado-item';
                
                // Construir roles actuales
                const rolesHTML = emp.roles_actuales && emp.roles_actuales.length > 0
                    ? emp.roles_actuales.map(r => `<span class="rol-badge">${r.nombrearea} - ${r.nombrerol}</span>`).join('')
                    : '<span class="rol-badge">Sin roles</span>';
                
                div.innerHTML = `
                    <div class="empleado-item-foto">
                        <img src="${emp.imagen || '/static/iconos/default-avatar.png'}" alt="Foto">
                    </div>
                    <div class="empleado-item-info">
                        <h4>${emp.nombre} ${emp.apellido}</h4>
                        <p><strong>DNI:</strong> ${emp.dni}</p>
                        <p><strong>Email:</strong> ${emp.email}</p>
                        <div class="empleado-item-roles">
                            ${rolesHTML}
                        </div>
                    </div>
                `;
                div.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                div.addEventListener('click', () => {
                    window.audioSystem.play('positive');
                    seleccionarEmpleado(emp);
                });
                empleadosEncontrados.appendChild(div);
            });
        } catch (error) {
            console.error('Error al buscar empleados:', error);
            window.audioSystem.play('error');
            empleadosEncontrados.innerHTML = '<p style="text-align:center; color:red;">Error al buscar.</p>';
        }
    }

    function seleccionarEmpleado(emp) {
        empleadoSeleccionado = emp;
        const modalBuscar = document.getElementById('modal-buscar-empleado');
        const mainFormContainer = document.getElementById('main-form-container');
        
        modalBuscar.style.display = 'none';
        mainFormContainer.style.display = 'block';

        configurarModoAsignar(emp);
    }

    function configurarModoAsignar(emp) {
        const tituloPrincipal = document.getElementById('titulo-principal');
        const seccionDatosPersonales = document.getElementById('seccion-datos-personales');
        const empleadoBanner = document.getElementById('empleado-seleccionado-banner');
        const bannerFoto = document.getElementById('banner-foto');
        const bannerNombre = document.getElementById('banner-nombre');
        const bannerDni = document.getElementById('banner-dni');
        const bannerEmail = document.getElementById('banner-email');
        const bannerRolesList = document.getElementById('banner-roles-list');
        const textoBtnListo = document.getElementById('texto-btn-listo');
        const tituloSeccionLaboral = document.getElementById('titulo-seccion-laboral');
        const laboralDataSection = document.getElementById('laboral-data');

        if (tituloPrincipal) tituloPrincipal.textContent = 'Asignar Nuevo Rol';
        if (seccionDatosPersonales) seccionDatosPersonales.style.display = 'none';
        if (empleadoBanner) empleadoBanner.style.display = 'block';
        if (textoBtnListo) textoBtnListo.textContent = 'Asignar Rol';
        if (tituloSeccionLaboral) tituloSeccionLaboral.textContent = 'Nuevo Rol Laboral';
        if (laboralDataSection) laboralDataSection.style.display = 'block';

        if (bannerFoto) bannerFoto.src = emp.imagen || '/static/iconos/default-avatar.png';
        if (bannerNombre) bannerNombre.textContent = `${emp.nombre} ${emp.apellido}`;
        if (bannerDni) bannerDni.innerHTML = `<i class="fas fa-id-card"></i> DNI: ${emp.dni}`;
        if (bannerEmail) bannerEmail.innerHTML = `<i class="fas fa-envelope"></i> ${emp.email}`;
        
        if (bannerRolesList && emp.roles_actuales) {
            bannerRolesList.innerHTML = emp.roles_actuales.map(r => 
                `<div class="rol-actual-badge">
                    <i class="fas fa-briefcase"></i> ${r.nombrearea} - ${r.nombrerol}
                </div>`
            ).join('');
        }
    }

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function setupFieldValidations() {
        const nombreInput = document.getElementById('nombre');
        const apellidoInput = document.getElementById('apellido');
        const dniInput = document.getElementById('dni');
        const telefonoInput = document.getElementById('telefono');
        const emailInput = document.getElementById('email');
        const codPaisInput = document.getElementById('cod_pais');
        const fechaNacimientoInput = document.getElementById('fecha_nacimiento');
    
        function allowOnlyLetters(event) {
            const oldValue = event.target.value;
            event.target.value = event.target.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
            if (oldValue !== event.target.value) window.audioSystem.play('negative');
        }
        
        if (nombreInput) nombreInput.addEventListener('input', allowOnlyLetters);
        if (apellidoInput) apellidoInput.addEventListener('input', allowOnlyLetters);
    
        function allowOnlyNumbers(event) {
            const oldValue = event.target.value;
            event.target.value = event.target.value.replace(/\D/g, '');
            if (oldValue !== event.target.value) window.audioSystem.play('negative');
        }
        
        if (dniInput) dniInput.addEventListener('input', allowOnlyNumbers);
        if (telefonoInput) telefonoInput.addEventListener('input', allowOnlyNumbers);
    
        if (codPaisInput) {
            codPaisInput.addEventListener('input', (event) => {
                let value = event.target.value;
                if (!value.startsWith('+')) {
                    value = '+' + value.replace(/\D/g, '');
                } else {
                    value = '+' + value.substring(1).replace(/\D/g, '');
                }
                event.target.value = value;
            });
            codPaisInput.value = '+54';
        }
        
        if (fechaNacimientoInput) {
            fechaNacimientoInput.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                let formattedValue = '';
                
                if (value.length > 0) {
                    let day = value.substring(0, 2);
                    if (parseInt(day) > 31) day = '31';
                    formattedValue = day;
                }
                if (value.length > 2) {
                    let month = value.substring(2, 4);
                    if (parseInt(month) > 12) month = '12';
                    formattedValue += '/' + month;
                }
                if (value.length > 4) {
                    formattedValue += '/' + value.substring(4, 8);
                }
                
                e.target.value = formattedValue;
            });
            
            fechaNacimientoInput.addEventListener('blur', (e) => {
                const value = e.target.value;
                if (value && value.length === 10) {
                    const parts = value.split('/');
                    const day = parseInt(parts[0]);
                    const month = parseInt(parts[1]);
                    const year = parseInt(parts[2]);
                    
                    const date = new Date(year, month - 1, day);
                    if (date.getDate() !== day || date.getMonth() !== month - 1 || date.getFullYear() !== year) {
                        window.audioSystem.play('error');
                        alert('Fecha inválida. Por favor ingrese una fecha válida.');
                        e.target.value = '';
                    }
                }
            });
        }
    
        // ===== AUTOCOMPLETADO DE @GMAIL.COM =====
        if (emailInput) {
            emailInput.addEventListener('keydown', (event) => {
                const value = event.target.value;
                
                if (event.key === '@' && !value.includes('@')) {
                    event.preventDefault();
                    event.target.value = value + '@gmail.com';
                    const cursorPos = value.length;
                    event.target.setSelectionRange(cursorPos, cursorPos);
                    window.audioSystem.play('positive');
                }
            });
            
            emailInput.addEventListener('input', (event) => {
                let value = event.target.value;
                
                if (value.includes('@') && !value.includes('@gmail.com')) {
                    const atIndex = value.indexOf('@');
                    const beforeAt = value.substring(0, atIndex);
                    const afterAt = value.substring(atIndex + 1);
                    
                    if (afterAt === '' || 'gmail.com'.startsWith(afterAt.toLowerCase())) {
                        event.target.value = beforeAt + '@gmail.com';
                        event.target.setSelectionRange(beforeAt.length, beforeAt.length);
                        window.audioSystem.play('positive');
                    }
                }
            });
    
            emailInput.addEventListener('blur', (event) => {
                let emailValue = event.target.value.trim();
                if (emailValue && !emailValue.includes('@')) {
                    event.target.value = emailValue + '@gmail.com';
                    window.audioSystem.play('positive');
                }
            });
        }
    }
    
    function setupAreaPuestoLogic() {
        const btnArea = document.getElementById('btn-area');
        const btnPuesto = document.getElementById('btn-puesto');
        const searchInput = document.getElementById('searchInput');
        const resultsList = document.getElementById('resultsList');
        const btnSeleccionarVolver = document.getElementById('btn-seleccionar-volver');
        const modalSeleccionar = document.getElementById('modal-seleccionar');
        const seleccionarTitulo = document.getElementById('seleccionar-titulo');
        let currentMode = null;

        if (!btnArea || !btnPuesto || !modalSeleccionar) return;

        btnArea.addEventListener('click', () => {
            window.audioSystem.play('select');
            currentMode = 'area';
            seleccionarTitulo.textContent = 'Seleccionar Área';
            searchInput.value = '';
            cargarAreas();
            modalSeleccionar.style.display = 'flex';
        });
        
        btnPuesto.addEventListener('click', () => {
            if (!selectedArea) {
                window.audioSystem.play('error');
                alert('Primero debes seleccionar un Área');
                return;
            }
            window.audioSystem.play('select');
            currentMode = 'puesto';
            seleccionarTitulo.textContent = 'Seleccionar Puesto';
            searchInput.value = '';
            cargarPuestos(selectedArea.id);
            modalSeleccionar.style.display = 'flex';
        });

        if (btnSeleccionarVolver) {
            btnSeleccionarVolver.addEventListener('click', () => {
                window.audioSystem.play('select');
                modalSeleccionar.style.display = 'none';
            });
        }

        if (searchInput) {
            searchInput.addEventListener('input', () => {
                if (currentMode === 'area') {
                    cargarAreas(searchInput.value);
                } else if (currentMode === 'puesto' && selectedArea) {
                    cargarPuestos(selectedArea.id, searchInput.value);
                }
            });
        }

        async function cargarAreas(query = '') {
            try {
                const url = `${document.body.dataset.apiAreasUrl}?q=${encodeURIComponent(query)}`;
                const response = await fetch(url);
                const data = await response.json();
                
                resultsList.innerHTML = '';
                if (data.length === 0) {
                    resultsList.innerHTML = '<li>No hay resultados</li>';
                    return;
                }
                
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = item.nombre;
                    li.dataset.id = item.id;
                    li.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                    li.addEventListener('click', () => {
                        window.audioSystem.play('select');
                        selectedArea = item;
                        btnArea.textContent = item.nombre;
                        btnArea.classList.add('selected');
                        selectedPuesto = null;
                        btnPuesto.textContent = 'Selecciona un puesto';
                        btnPuesto.classList.remove('selected');
                        btnPuesto.disabled = false;
                        document.getElementById('permisos-info').style.display = 'none';
                        modalSeleccionar.style.display = 'none';
                    });
                    resultsList.appendChild(li);
                });
            } catch (error) {
                console.error("Error al cargar Áreas:", error);
                window.audioSystem.play('error');
                resultsList.innerHTML = '<li>Error al cargar datos</li>';
            }
        }

        async function cargarPuestos(areaId, query = '') {
            try {
                const url = `${document.body.dataset.apiPuestosPorAreaUrl}${encodeURIComponent(areaId)}/`;
                const response = await fetch(url);
                const data = await response.json();
                
                const filtered = query ? data.filter(p => p.nombre.toLowerCase().includes(query.toLowerCase())) : data;
                
                resultsList.innerHTML = '';
                if (filtered.length === 0) {
                    resultsList.innerHTML = '<li>No hay puestos en esta Área</li>';
                    return;
                }
                
                filtered.forEach(item => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <strong>${item.nombre}</strong>
                        ${item.permisos && item.permisos.length > 0 ? `<br><small>Permisos: ${item.permisos.join(', ')}</small>` : ''}
                    `;
                    li.dataset.id = item.id;
                    li.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                    li.addEventListener('click', () => {
                        window.audioSystem.play('positive');
                        selectedPuesto = item;
                        btnPuesto.textContent = item.nombre;
                        btnPuesto.classList.add('selected');
                        mostrarPermisosPuesto(item.permisos || []);
                        modalSeleccionar.style.display = 'none';
                    });
                    resultsList.appendChild(li);
                });
            } catch (error) {
                console.error("Error al cargar puestos:", error);
                window.audioSystem.play('error');
                resultsList.innerHTML = '<li>Error al cargar datos</li>';
            }
        }

        function mostrarPermisosPuesto(permisos) {
            const permisosInfo = document.getElementById('permisos-info');
            const permisosDisplay = document.getElementById('permisos-display');
            
            if (!permisosInfo || !permisosDisplay) return;
            
            if (permisos.length === 0) {
                permisosInfo.style.display = 'none';
                return;
            }
            
            const iconos = {
                'caja': 'fa-cash-register',
                'stock': 'fa-boxes',
                'crear_empleado': 'fa-user-plus',
                'asistencias': 'fa-clock'
            };
            
            permisosDisplay.innerHTML = permisos.map(p => `
                <div class="permiso-badge">
                    <i class="fas ${iconos[p] || 'fa-check'}"></i> ${p}
                </div>
            `).join('');
            
            permisosInfo.style.display = 'block';
        }
    }

    function setupScheduleLogic() {
        const colorPaletteContainer = document.getElementById('color-palette');
        const addColorBtn = document.getElementById('add-color');
        const scheduleContainer = document.getElementById('schedule-container');
        const dailyScheduleContainer = document.getElementById('daily-schedule-container');

        if (!colorPaletteContainer || !addColorBtn || !scheduleContainer || !dailyScheduleContainer) return;

        function getContrastColor(hexcolor){
            if (hexcolor.startsWith('#')) hexcolor = hexcolor.slice(1);
            const r = parseInt(hexcolor.substr(0,2),16);
            const g = parseInt(hexcolor.substr(2,2),16);
            const b = parseInt(hexcolor.substr(4,2),16);
            const yiq = ((r*299)+(g*587)+(b*114))/1000;
            return (yiq >= 149) ? 'text-dark' : 'text-light';
        }

        function renderPalette() {
            colorPaletteContainer.innerHTML = '';
            activeColors.forEach(color => {
                const colorDiv = document.createElement('div');
                colorDiv.className = 'color-box';
                colorDiv.style.backgroundColor = color;
                if (color === selectedColor) colorDiv.classList.add('selected');
                
                colorDiv.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                colorDiv.addEventListener('click', () => {
                    window.audioSystem.play('select');
                    selectedColor = color;
                    renderPalette();
                });

                const removeTrigger = document.createElement('div');
                removeTrigger.className = 'remove-color-trigger';
                removeTrigger.textContent = '-';
                removeTrigger.onclick = (e) => { 
                    e.stopPropagation(); 
                    window.audioSystem.play('negative');
                    removeColor(color); 
                };
                colorDiv.appendChild(removeTrigger);

                if (activeColors.length <= 1) { colorDiv.classList.add('is-last'); }
                colorPaletteContainer.appendChild(colorDiv);
            });
        }

        function removeColor(colorToRemove) {
            if (activeColors.length <= 1) return;
            document.querySelectorAll(`.day-btn[data-color="${colorToRemove}"]`).forEach(btn => {
                const dayKey = btn.dataset.day;
                const weekElement = btn.closest('.schedule-week');
                if (weekElement) {
                    const weekId = weekElement.dataset.weekId;
                    const compositeKey = `w${weekId}-${dayKey}`;
                    delete dayColorMap[compositeKey];
                }
                delete btn.dataset.color;
                btn.style.backgroundColor = '';
                btn.classList.remove('text-light', 'text-dark');
            });
            delete scheduleData[colorToRemove];
            activeColors = activeColors.filter(c => c !== colorToRemove);
            if (selectedColor === colorToRemove) { selectedColor = activeColors[0]; }
            renderPalette();
            renderDailySchedules();
        }

        addColorBtn.addEventListener('click', () => {
            const nextColor = availableColors.find(c => !activeColors.includes(c));
            if (nextColor) { 
                window.audioSystem.play('positive');
                activeColors.push(nextColor); 
                renderPalette(); 
            } else {
                window.audioSystem.play('negative');
            }
        });

        function addWeek(event) {
            const allWeeks = scheduleContainer.querySelectorAll('.schedule-week');
            if (allWeeks.length >= 4) {
                window.audioSystem.play('negative');
                return;
            }
            window.audioSystem.play('positive');
            if (event && event.target) {
                const addBtn = event.target.closest('.add-btn');
                if (addBtn) addBtn.style.display = 'none';
            }
            createAndAppendWeek();
            updateWeeksUI();
        }

        function removeWeek(event) {
            window.audioSystem.play('negative');
            const weekToRemove = event.target.closest('.schedule-week');
            if (!weekToRemove) return;
            
            const weekId = weekToRemove.dataset.weekId;
            for (const key in dayColorMap) {
                if (key.startsWith(`w${weekId}-`)) {
                    delete dayColorMap[key];
                }
            }
            weekToRemove.remove();
            updateWeeksUI();
            renderDailySchedules();
        }

        function updateWeeksUI() {
            const allWeeks = scheduleContainer.querySelectorAll('.schedule-week');
            allWeeks.forEach((week, index) => {
                const weekLabel = week.querySelector('.week-label');
                if (weekLabel) weekLabel.textContent = `Semana ${index + 1}:`;
                
                const addBtn = week.querySelector('.add-btn');
                const removeBtn = week.querySelector('.remove-btn');
                if (removeBtn) removeBtn.style.display = (index > 0) ? 'flex' : 'none';
                if (addBtn) addBtn.style.display = (index === allWeeks.length - 1 && allWeeks.length < 4) ? 'flex' : 'none';
            });
        }

        function createAndAppendWeek() {
            const weekId = weekIdCounter++;
            const weekDiv = document.createElement('div');
            weekDiv.className = 'schedule-week';
            weekDiv.dataset.weekId = weekId;

            const weekLabel = document.createElement('span');
            weekLabel.className = 'week-label';
            weekDiv.appendChild(weekLabel);
            
            daysOfWeek.forEach(day => {
                const dayBtn = document.createElement('button');
                dayBtn.className = 'day-btn';
                dayBtn.textContent = day;
                dayBtn.type = 'button';
                dayBtn.dataset.day = day;
                dayBtn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                dayBtn.addEventListener('click', () => {
                    window.audioSystem.play('select');
                    toggleDayColor(dayBtn);
                });
                weekDiv.appendChild(dayBtn);
            });

            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'week-actions-individual';
            
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = `<img src="${document.body.dataset.removeIconUrl}" alt="Quitar Semana">`;
            removeBtn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
            removeBtn.addEventListener('click', removeWeek);
            actionsDiv.appendChild(removeBtn);

            const addBtn = document.createElement('button');
            addBtn.type = 'button';
            addBtn.className = 'add-btn';
            addBtn.innerHTML = `<img src="${document.body.dataset.addIconUrl}" alt="Añadir Semana">`;
            addBtn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
            addBtn.addEventListener('click', addWeek);
            actionsDiv.appendChild(addBtn);

            weekDiv.appendChild(actionsDiv);
            scheduleContainer.appendChild(weekDiv);
        }

        function toggleDayColor(dayBtn) {
            const dayKey = dayBtn.dataset.day;
            const weekElement = dayBtn.closest('.schedule-week');
            if (!weekElement) return;
            
            const weekId = weekElement.dataset.weekId;
            const compositeKey = `w${weekId}-${dayKey}`;

            if (dayColorMap[compositeKey] === selectedColor) {
                delete dayColorMap[compositeKey];
                delete dayBtn.dataset.color;
                dayBtn.style.backgroundColor = '';
                dayBtn.classList.remove('text-light', 'text-dark');
            } else {
                dayColorMap[compositeKey] = selectedColor;
                dayBtn.dataset.color = selectedColor;
                dayBtn.style.backgroundColor = selectedColor;
                dayBtn.classList.remove('text-light', 'text-dark');
                dayBtn.classList.add(getContrastColor(selectedColor));
            }
            renderDailySchedules();
        }

        function renderDailySchedules() {
            dailyScheduleContainer.innerHTML = '';
            const groupedDaysByColor = {};
            for (const compositeKey in dayColorMap) {
                const color = dayColorMap[compositeKey];
                if (!groupedDaysByColor[color]) { groupedDaysByColor[color] = []; }
                groupedDaysByColor[color].push(compositeKey);
            }

            if (Object.keys(groupedDaysByColor).length === 0) {
                dailyScheduleContainer.style.display = 'none';
                return;
            }
            dailyScheduleContainer.style.display = 'block';

            const weekIndexMap = {};
            scheduleContainer.querySelectorAll('.schedule-week').forEach((week, index) => {
                weekIndexMap[week.dataset.weekId] = index + 1;
            });

            for (const color in groupedDaysByColor) {
                if (!scheduleData[color]) {
                    scheduleData[color] = [{ start: '', end: '' }];
                }
                const scheduleRow = document.createElement('div');
                scheduleRow.className = 'schedule-day-row';
                scheduleRow.style.borderColor = color;
                const contrastClass = getContrastColor(color);
                scheduleRow.classList.add(contrastClass);
                
                const title = document.createElement('h4');
                const titleParts = groupedDaysByColor[color].map(key => {
                    const parts = key.split('-');
                    if (parts.length >= 2) {
                        const weekId = parts[0].substring(1);
                        const day = parts[1];
                        const weekNum = weekIndexMap[weekId] || '?';
                        return `S${weekNum}-${day}`;
                    }
                    return key;
                });
                title.textContent = titleParts.sort((a, b) => {
                    const [aWeek, aDay] = a.substring(1).split('-');
                    const [bWeek, bDay] = b.substring(1).split('-');
                    if (aWeek !== bWeek) return parseInt(aWeek) - parseInt(bWeek);
                    return daysOfWeek.indexOf(aDay) - daysOfWeek.indexOf(bDay);
                }).join(', ');
                title.style.backgroundColor = color;
                scheduleRow.appendChild(title);

                const timeSlotsContainer = document.createElement('div');
                timeSlotsContainer.className = 'time-slots-container';
                scheduleData[color].forEach((slot, index) => {
                    const timeSlotDiv = document.createElement('div');
                    timeSlotDiv.className = 'time-slot';
                    
                    const startTimeInput = document.createElement('input');
                    startTimeInput.type = 'time';
                    startTimeInput.value = slot.start || '';
                    startTimeInput.onchange = (e) => {
                        window.audioSystem.play('select');
                        scheduleData[color][index].start = e.target.value;
                    };
                    
                    const spanText = document.createElement('span');
                    spanText.textContent = 'a';
                    
                    const endTimeInput = document.createElement('input');
                    endTimeInput.type = 'time';
                    endTimeInput.value = slot.end || '';
                    endTimeInput.onchange = (e) => {
                        window.audioSystem.play('select');
                        scheduleData[color][index].end = e.target.value;
                    };
                    
                    const addTimeSlotBtn = document.createElement('button');
                    addTimeSlotBtn.type = 'button';
                    addTimeSlotBtn.className = 'add-btn';
                    addTimeSlotBtn.innerHTML = `<img src="${document.body.dataset.addIconUrl}" alt="Añadir horario">`;
                    addTimeSlotBtn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                    addTimeSlotBtn.onclick = () => { 
                        window.audioSystem.play('positive');
                        scheduleData[color].push({ start: '', end: '' }); 
                        renderDailySchedules(); 
                    };
                    
                    const removeTimeSlotBtn = document.createElement('button');
                    removeTimeSlotBtn.type = 'button';
                    removeTimeSlotBtn.className = 'remove-btn';
                    removeTimeSlotBtn.innerHTML = `<img src="${document.body.dataset.removeIconUrl}" alt="Eliminar horario">`;
                    removeTimeSlotBtn.addEventListener('mouseenter', () => window.audioSystem.play('hover'));
                    removeTimeSlotBtn.onclick = () => { 
                        if (scheduleData[color].length > 1) { 
                            window.audioSystem.play('negative');
                            scheduleData[color].splice(index, 1); 
                            renderDailySchedules(); 
                        } 
                    };
                    
                    timeSlotDiv.appendChild(startTimeInput);
                    timeSlotDiv.appendChild(spanText);
                    timeSlotDiv.appendChild(endTimeInput);
                    timeSlotDiv.appendChild(addTimeSlotBtn);
                    if (scheduleData[color].length > 1) { timeSlotDiv.appendChild(removeTimeSlotBtn); }
                    timeSlotsContainer.appendChild(timeSlotDiv);
                });
                scheduleRow.appendChild(timeSlotsContainer);
                dailyScheduleContainer.appendChild(scheduleRow);
            }
        }

        renderPalette();
        createAndAppendWeek();
        updateWeeksUI();
        renderDailySchedules();
    }

    function setupFinalSubmit() {
        const btnListo = document.getElementById('btn-listo');
        if (!btnListo) return;
    
        const toBase64 = file => new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    
        btnListo.addEventListener('click', async () => {
            window.audioSystem.play('select');
            
            // Si estamos en modo "asignar", usar endpoint diferente
            if (modoOperacion === 'asignar') {
                await procesarAsignarRol();
                return;
            }

            // Modo "crear" - continuar con lógica original
            let fotoBase64 = null;
            const fotoInput = document.getElementById('photo-input');
            if (fotoInput && fotoInput.files[0]) {
                try {
                    fotoBase64 = await toBase64(fotoInput.files[0]);
                } catch (error) {
                    console.error('Error al procesar foto:', error);
                }
            }
    
            const data = {
                personal: {
                    nombre: document.getElementById('nombre')?.value.trim() || '',
                    apellido: document.getElementById('apellido')?.value.trim() || '',
                    dni: document.getElementById('dni')?.value.trim() || '',
                    telefono: document.getElementById('telefono')?.value.trim() || '',
                    email: document.getElementById('email')?.value.trim() || '',
                    codigo_telefonico: document.getElementById('cod_pais')?.value.trim() || '+54',
                    direccion: document.getElementById('direccion')?.value.trim() || '',
                    fecha_nacimiento: document.getElementById('fecha_nacimiento')?.value.trim() || '',
                    foto: fotoBase64
                },
                area: selectedArea,
                puesto: selectedPuesto,
                horario: { scheduleData: scheduleData, dayColorMap: dayColorMap }
            };
    
            // Validaciones básicas
            if (!data.personal.nombre || !data.personal.apellido || !data.personal.email || !data.personal.dni) {
                window.audioSystem.play('error');
                alert('Por favor, completa los campos obligatorios: Nombre, Apellido, DNI y Email.');
                return;
            }
            if (!data.area || !data.puesto) {
                window.audioSystem.play('error');
                alert('Por favor, selecciona un Área y un Puesto para el empleado.');
                return;
            }
            
            // Validación de horario
            if (Object.keys(dayColorMap).length === 0) {
                window.audioSystem.play('error');
                alert('Por favor, asigna al menos un día de trabajo para el empleado.');
                return;
            }
            
            let horarioIncompleto = false;
            for (const color in scheduleData) {
                const tramos = scheduleData[color];
                for (const tramo of tramos) {
                    if (!tramo.start || !tramo.end) {
                        horarioIncompleto = true;
                        break;
                    }
                }
                if (horarioIncompleto) break;
            }
            
            if (horarioIncompleto) {
                window.audioSystem.play('error');
                alert('Por favor, completa todos los horarios de entrada y salida para los días asignados.');
                return;
            }
            
            // Modal de confirmación
            const confirmar = await mostrarModalConfirmacion(data);
            
            if (!confirmar) {
                window.audioSystem.play('select');
                return;
            }
            
            btnListo.disabled = true;
            btnListo.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    
            try {
                const response = await fetch(document.body.dataset.apiRegistrarEmpleadoUrl, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json', 
                        'X-CSRFToken': getCookie('csrftoken') 
                    },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (response.ok) {
                    window.audioSystem.play('positive');
                    alert(result.message + '\n\nUsuario: ' + result.username);
                    window.location.href = document.body.dataset.inicioUrl;
                } else {
                    window.audioSystem.play('error');
                    alert(`Error: ${result.error}`);
                    btnListo.disabled = false;
                    btnListo.innerHTML = '<i class="fas fa-check"></i> Listo';
                }
            } catch (error) {
                console.error('Error al enviar el formulario:', error);
                window.audioSystem.play('error');
                alert('Ocurrió un error de red. Inténtalo de nuevo.');
                btnListo.disabled = false;
                btnListo.innerHTML = '<i class="fas fa-check"></i> Listo';
            }
        });
    }

    async function procesarAsignarRol() {
        const btnListo = document.getElementById('btn-listo');

        if (!selectedArea || !selectedPuesto) {
            window.audioSystem.play('error');
            alert('Por favor, selecciona un Área y un Puesto para el nuevo rol.');
            return;
        }
        
        // Validación de horario
        if (Object.keys(dayColorMap).length === 0) {
            window.audioSystem.play('error');
            alert('Por favor, asigna al menos un día de trabajo para el nuevo rol.');
            return;
        }
        
        let horarioIncompleto = false;
        for (const color in scheduleData) {
            const tramos = scheduleData[color];
            for (const tramo of tramos) {
                if (!tramo.start || !tramo.end) {
                    horarioIncompleto = true;
                    break;
                }
            }
            if (horarioIncompleto) break;
        }
        
        if (horarioIncompleto) {
            window.audioSystem.play('error');
            alert('Por favor, completa todos los horarios de entrada y salida para los días asignados.');
            return;
        }

        const data = {
            empleado_id: empleadoSeleccionado.id,
            puesto_id: selectedPuesto.id,
            horario: { scheduleData: scheduleData, dayColorMap: dayColorMap }
        };

        const confirmar = await mostrarModalConfirmacionAsignar(data);
        
        if (!confirmar) {
            window.audioSystem.play('select');
            return;
        }

        btnListo.disabled = true;
        btnListo.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Asignando...';

        try {
            const response = await fetch(document.body.dataset.apiAsignarRolUrl, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-CSRFToken': getCookie('csrftoken') 
                },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                window.audioSystem.play('positive');
                alert(result.message);
                window.location.href = document.body.dataset.inicioUrl;
            } else {
                window.audioSystem.play('error');
                alert(`Error: ${result.error}`);
                btnListo.disabled = false;
                btnListo.innerHTML = '<i class="fas fa-check"></i> Asignar Rol';
            }
        } catch (error) {
            console.error('Error al asignar rol:', error);
            window.audioSystem.play('error');
            alert('Ocurrió un error de red. Inténtalo de nuevo.');
            btnListo.disabled = false;
            btnListo.innerHTML = '<i class="fas fa-check"></i> Asignar Rol';
        }
    }
    
    function mostrarModalConfirmacion(data) {
        return new Promise((resolve) => {
            const totalDias = Object.keys(dayColorMap).length;
            
            const modalHTML = `
                <div id="modal-confirmacion-empleado" class="modal-confirmacion-overlay">
                    <div class="modal-confirmacion-content">
                        <div class="modal-confirmacion-header">
                            <i class="fas fa-user-check"></i>
                            <h2>Confirmar Creación de Empleado</h2>
                        </div>
                        <div class="modal-confirmacion-body">
                            <p class="modal-confirmacion-pregunta">
                                ¿Estás seguro de que deseas crear este empleado con los siguientes datos?
                            </p>
                            <div class="modal-confirmacion-datos">
                                <div class="dato-item">
                                    <i class="fas fa-user"></i>
                                    <span><strong>Nombre:</strong> ${data.personal.nombre} ${data.personal.apellido}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-id-card"></i>
                                    <span><strong>DNI:</strong> ${data.personal.dni}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-envelope"></i>
                                    <span><strong>Email:</strong> ${data.personal.email}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-briefcase"></i>
                                    <span><strong>Área:</strong> ${data.area?.nombre || 'N/A'}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-user-tag"></i>
                                    <span><strong>Puesto:</strong> ${data.puesto?.nombre || 'N/A'}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-calendar-check"></i>
                                    <span><strong>Días laborales:</strong> ${totalDias} día(s) asignado(s)</span>
                                </div>
                            </div>
                            <p class="modal-confirmacion-nota">
                                <i class="fas fa-info-circle"></i>
                                Se enviará un correo con las credenciales de acceso al email proporcionado.
                            </p>
                        </div>
                        <div class="modal-confirmacion-actions">
                            <button class="btn-modal-confirmacion btn-cancelar" id="btn-confirmar-cancelar">
                                <i class="fas fa-times"></i> Cancelar
                            </button>
                            <button class="btn-modal-confirmacion btn-confirmar" id="btn-confirmar-si">
                                <i class="fas fa-check"></i> Sí, estoy seguro
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            const modal = document.getElementById('modal-confirmacion-empleado');
            const btnCancelar = document.getElementById('btn-confirmar-cancelar');
            const btnConfirmar = document.getElementById('btn-confirmar-si');
            
            if (window.audioSystem) window.audioSystem.play('positive');
            
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
            
            btnCancelar.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
            
            btnConfirmar.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
            
            btnCancelar.addEventListener('click', () => {
                if (window.audioSystem) window.audioSystem.play('negative');
                cerrarModal(modal, false, resolve);
            });
            
            btnConfirmar.addEventListener('click', () => {
                if (window.audioSystem) window.audioSystem.play('positive');
                cerrarModal(modal, true, resolve);
            });
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    if (window.audioSystem) window.audioSystem.play('select');
                    cerrarModal(modal, false, resolve);
                }
            });
        });
    }

    function mostrarModalConfirmacionAsignar(data) {
        return new Promise((resolve) => {
            const totalDias = Object.keys(dayColorMap).length;
            
            const modalHTML = `
                <div id="modal-confirmacion-empleado" class="modal-confirmacion-overlay">
                    <div class="modal-confirmacion-content">
                        <div class="modal-confirmacion-header">
                            <i class="fas fa-user-tag"></i>
                            <h2>Confirmar Asignación de Rol</h2>
                        </div>
                        <div class="modal-confirmacion-body">
                            <p class="modal-confirmacion-pregunta">
                                ¿Estás seguro de que deseas asignar este nuevo rol?
                            </p>
                            <div class="modal-confirmacion-datos">
                                <div class="dato-item">
                                    <i class="fas fa-user"></i>
                                    <span><strong>Empleado:</strong> ${empleadoSeleccionado.nombre} ${empleadoSeleccionado.apellido}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-briefcase"></i>
                                    <span><strong>Nueva Área:</strong> ${selectedArea?.nombre || 'N/A'}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-user-tag"></i>
                                    <span><strong>Nuevo Puesto:</strong> ${selectedPuesto?.nombre || 'N/A'}</span>
                                </div>
                                <div class="dato-item">
                                    <i class="fas fa-calendar-check"></i>
                                    <span><strong>Días laborales:</strong> ${totalDias} día(s) asignado(s)</span>
                                </div>
                            </div>
                            <p class="modal-confirmacion-nota">
                                <i class="fas fa-info-circle"></i>
                                El empleado podrá acceder con sus credenciales actuales y tendrá los permisos del nuevo rol.
                            </p>
                        </div>
                        <div class="modal-confirmacion-actions">
                            <button class="btn-modal-confirmacion btn-cancelar" id="btn-confirmar-cancelar">
                                <i class="fas fa-times"></i> Cancelar
                            </button>
                            <button class="btn-modal-confirmacion btn-confirmar" id="btn-confirmar-si">
                                <i class="fas fa-check"></i> Sí, asignar rol
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            const modal = document.getElementById('modal-confirmacion-empleado');
            const btnCancelar = document.getElementById('btn-confirmar-cancelar');
            const btnConfirmar = document.getElementById('btn-confirmar-si');
            
            if (window.audioSystem) window.audioSystem.play('positive');
            
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
            
            btnCancelar.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
            
            btnConfirmar.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
            
            btnCancelar.addEventListener('click', () => {
                if (window.audioSystem) window.audioSystem.play('negative');
                cerrarModal(modal, false, resolve);
            });
            
            btnConfirmar.addEventListener('click', () => {
                if (window.audioSystem) window.audioSystem.play('positive');
                cerrarModal(modal, true, resolve);
            });
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    if (window.audioSystem) window.audioSystem.play('select');
                    cerrarModal(modal, false, resolve);
                }
            });
        });
    }
    
    function cerrarModal(modal, resultado, resolve) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
            resolve(resultado);
        }, 300);
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