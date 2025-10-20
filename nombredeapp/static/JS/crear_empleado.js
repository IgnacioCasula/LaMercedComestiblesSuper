document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let selectedArea = null;
    let selectedPuesto = null;
    let scheduleData = {};
    let dayColorMap = {};
    let weekIdCounter = 1;

    const daysOfWeek = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'];
    const availableColors = ["#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9"];
    let activeColors = [availableColors[0]];
    let selectedColor = activeColors[0];

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

        if (emailInput) {
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
                alert('Primero debes seleccionar un área');
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
                console.error("Error al cargar áreas:", error);
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
                    resultsList.innerHTML = '<li>No hay puestos en esta área</li>';
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