document.addEventListener('DOMContentLoaded', function() {
    // --- LÓGICA DE FOTO Y DATOS PERSONALES ---
    // ... (esta parte se mantiene igual que la versión anterior) ...
    const photoUploader = document.getElementById('photo-uploader');
    const photoInput = document.getElementById('photo-input');
    const photoButton = document.getElementById('photo-button');
    photoUploader.addEventListener('click', () => photoInput.click());
    photoInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                photoUploader.style.backgroundImage = `url('${e.target.result}')`;
                photoButton.textContent = 'Cambiar Foto';
            };
            reader.readAsDataURL(file);
        }
    });

    const fechaNacimientoInput = document.getElementById('fecha_nacimiento');
    fechaNacimientoInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        let formattedValue = '';
        if (value.length > 0) formattedValue = value.substring(0, 2);
        if (value.length > 2) formattedValue += '/' + value.substring(2, 4);
        if (value.length > 4) formattedValue += '/' + value.substring(4, 8);
        e.target.value = formattedValue;
    });

    document.getElementById('btn-cancel').addEventListener('click', () => {
        if (confirm('¿Está seguro de que desea cancelar? Se perderán todos los datos ingresados.')) {
            window.location.href = document.body.dataset.inicioUrl;
        }
    });

    const nombreInput = document.getElementById('nombre');
    const apellidoInput = document.getElementById('apellido');
    const dniInput = document.getElementById('dni');
    const telefonoInput = document.getElementById('telefono');
    const emailInput = document.getElementById('email');
    const codPaisInput = document.getElementById('cod_pais');

    function allowOnlyLetters(event) { event.target.value = event.target.value.replace(/[^a-zA-Z\sñÑáéíóúÁÉÍÓÚ]/g, ''); }
    nombreInput.addEventListener('input', allowOnlyLetters);
    apellidoInput.addEventListener('input', allowOnlyLetters);

    function allowOnlyNumbers(event) { event.target.value = event.target.value.replace(/\D/g, ''); }
    dniInput.addEventListener('input', allowOnlyNumbers);
    telefonoInput.addEventListener('input', allowOnlyNumbers);

    codPaisInput.addEventListener('input', (event) => {
        let value = event.target.value;
        let numbers = value.replace(/\D/g, '');
        event.target.value = '+' + numbers;
    });
    codPaisInput.addEventListener('blur', (event) => {
        if (event.target.value === '' || event.target.value === '+') { event.target.value = '+'; }
    });
    codPaisInput.value = '+';
    
    emailInput.addEventListener('blur', (event) => {
        let emailValue = event.target.value.trim();
        if (emailValue && !emailValue.includes('@')) {
            event.target.value = emailValue + '@gmail.com';
        }
    });

    const btnAddLaboral = document.getElementById('btn-add-laboral');
    const laboralDataSection = document.getElementById('laboral-data');
    btnAddLaboral.addEventListener('click', () => {
        laboralDataSection.style.display = 'block';
        btnAddLaboral.style.display = 'none';
    });
    
    // --- LÓGICA DEL HORARIO ---
    const colorPaletteContainer = document.getElementById('color-palette');
    const addColorBtn = document.getElementById('add-color');
    const scheduleContainer = document.getElementById('schedule-container'); // Cambiado de weeksContainer
    const dailyScheduleContainer = document.getElementById('daily-schedule-container');

    const daysOfWeek = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do'];
    const availableColors = ["#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9"];
    let activeColors = [availableColors[0]];
    let selectedColor = activeColors[0];
    
    let scheduleData = {};
    let dayColorMap = {};

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
            
            colorDiv.addEventListener('click', () => {
                selectedColor = color;
                renderPalette();
            });

            const removeTrigger = document.createElement('div');
            removeTrigger.className = 'remove-color-trigger';
            removeTrigger.onclick = (e) => { e.stopPropagation(); removeColor(color); };
            colorDiv.appendChild(removeTrigger);

            if (activeColors.length <= 1) { colorDiv.classList.add('is-last'); }
            colorPaletteContainer.appendChild(colorDiv);
        });
    }

    function removeColor(colorToRemove) {
        if (activeColors.length <= 1) return;
        document.querySelectorAll(`.day-btn[data-color="${colorToRemove}"]`).forEach(btn => {
            const dayKey = btn.dataset.day; // Simplificado
            delete dayColorMap[dayKey];
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
        if (nextColor) { activeColors.push(nextColor); renderPalette(); }
    });
    
    // --- FUNCIÓN SIMPLIFICADA PARA CREAR LA FILA DE DÍAS ---
    function createDayRow() {
        scheduleContainer.innerHTML = ''; // Limpiamos el contenedor
        const weekDiv = document.createElement('div');
        weekDiv.className = 'schedule-week'; // Reutilizamos la clase
        
        daysOfWeek.forEach(day => {
            const dayBtn = document.createElement('button');
            dayBtn.className = 'day-btn';
            dayBtn.textContent = day;
            dayBtn.dataset.day = day;
            dayBtn.addEventListener('click', () => toggleDayColor(dayBtn));
            weekDiv.appendChild(dayBtn);
        });
        scheduleContainer.appendChild(weekDiv);
    }
    
    function toggleDayColor(dayBtn) {
        const dayKey = dayBtn.dataset.day; // Ya no necesitamos la semana
        if (dayColorMap[dayKey] === selectedColor) {
            delete dayColorMap[dayKey];
            delete dayBtn.dataset.color;
            dayBtn.style.backgroundColor = '';
            dayBtn.classList.remove('text-light', 'text-dark');
        } else {
            dayColorMap[dayKey] = selectedColor;
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
        for(const dayKey in dayColorMap) {
            const color = dayColorMap[dayKey];
            if (!groupedDaysByColor[color]) { groupedDaysByColor[color] = []; }
            groupedDaysByColor[color].push(dayKey);
        }
        if (Object.keys(groupedDaysByColor).length === 0) { dailyScheduleContainer.style.display = 'none'; return; }
        dailyScheduleContainer.style.display = 'block';
        for (const color in groupedDaysByColor) {
            if (!scheduleData[color]) { scheduleData[color] = [{ start: '', end: '' }]; }
            const scheduleRow = document.createElement('div');
            scheduleRow.className = 'schedule-day-row';
            scheduleRow.style.borderColor = color;
            const contrastClass = getContrastColor(color);
            scheduleRow.classList.add(contrastClass);
            const title = document.createElement('h4');
            const titleParts = groupedDaysByColor[color]
                .sort((a,b) => daysOfWeek.indexOf(a) - daysOfWeek.indexOf(b));
            title.textContent = titleParts.join(', ');
            title.style.backgroundColor = color;
            scheduleRow.appendChild(title);
            const timeSlotsContainer = document.createElement('div');
            timeSlotsContainer.className = 'time-slots-container';
            scheduleData[color].forEach((slot, index) => {
                const timeSlotDiv = document.createElement('div');
                timeSlotDiv.className = 'time-slot';
                const startTimeInput = document.createElement('input');
                startTimeInput.type = 'time';
                startTimeInput.value = slot.start;
                startTimeInput.onchange = (e) => scheduleData[color][index].start = e.target.value;
                const endTimeInput = document.createElement('input');
                endTimeInput.type = 'time';
                endTimeInput.value = slot.end;
                endTimeInput.onchange = (e) => scheduleData[color][index].end = e.target.value;
                const addTimeSlotBtn = document.createElement('button');
                addTimeSlotBtn.className = 'add-btn';
                addTimeSlotBtn.innerHTML = `<img src="${document.body.dataset.addIconUrl}" alt="Añadir horario">`;
                addTimeSlotBtn.onclick = () => { scheduleData[color].push({ start: '', end: '' }); renderDailySchedules(); };
                const removeTimeSlotBtn = document.createElement('button');
                removeTimeSlotBtn.className = 'remove-btn';
                removeTimeSlotBtn.innerHTML = `<img src="${document.body.dataset.removeIconUrl}" alt="Eliminar horario">`;
                removeTimeSlotBtn.onclick = () => { if (scheduleData[color].length > 1) { scheduleData[color].splice(index, 1); renderDailySchedules(); } };
                timeSlotDiv.appendChild(startTimeInput);
                timeSlotDiv.appendChild(document.createElement('span')).textContent = 'a';
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
    createDayRow(); // Llamamos a la nueva función simplificada
    renderDailySchedules();

    // --- SCRIPT PARA ÁREA Y PUESTO ---
    // ... (esta parte se mantiene igual que la versión anterior) ...
    let selectedArea = null;
    let selectedPuesto = null;
    const btnArea = document.getElementById('btn-area');
    const btnPuesto = document.getElementById('btn-puesto');
    const btnOpcionCargar = document.getElementById('btn-opcion-cargar');
    const btnOpcionCrear = document.getElementById('btn-opcion-crear');
    const btnCargarVolver = document.getElementById('btn-cargar-volver');
    const btnCrearVolver = document.getElementById('btn-crear-volver');
    const btnCrearConfirmar = document.getElementById('btn-crear-confirmar');
    const opcionesTitulo = document.getElementById('opciones-titulo');
    const cargarTitulo = document.getElementById('cargar-titulo');
    const crearTitulo = document.getElementById('crear-titulo');
    const crearLabel = document.getElementById('crear-label');
    const searchInput = document.getElementById('searchInput');
    const resultsList = document.getElementById('resultsList');
    const newItemInput = document.getElementById('new-item-name');
    const crearErrorMsg = document.getElementById('crear-error-msg');
    let currentSelectionMode = null;

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
    const csrftoken = getCookie('csrftoken');

    window.abrirModal = (id) => document.getElementById(id).style.display = 'flex';
    window.cerrarModal = (id) => document.getElementById(id).style.display = 'none';

    btnArea.addEventListener('click', () => { currentSelectionMode = 'area'; opcionesTitulo.textContent = 'Seleccionar Área'; abrirModal('modal-opciones'); });
    btnPuesto.addEventListener('click', () => { currentSelectionMode = 'puesto'; opcionesTitulo.textContent = 'Seleccionar Puesto'; abrirModal('modal-opciones'); });

    btnOpcionCargar.addEventListener('click', () => {
        cerrarModal('modal-opciones');
        if (currentSelectionMode === 'area') {
            cargarTitulo.textContent = 'Cargar Área';
            cargarResultados('area');
        } else {
            cargarTitulo.textContent = 'Cargar Puesto';
            cargarResultados('puesto');
        }
        abrirModal('modal-cargar');
    });

    btnOpcionCrear.addEventListener('click', () => {
        cerrarModal('modal-opciones');
        newItemInput.value = '';
        crearErrorMsg.textContent = '';
        if (currentSelectionMode === 'area') {
            crearTitulo.textContent = 'Crear Nueva Área';
            crearLabel.textContent = 'Nombre del Área:';
        } else {
            crearTitulo.textContent = 'Crear Nuevo Puesto';
            crearLabel.textContent = 'Nombre del Puesto:';
        }
        abrirModal('modal-crear');
    });
    
    btnCargarVolver.addEventListener('click', () => { cerrarModal('modal-cargar'); abrirModal('modal-opciones'); });
    btnCrearVolver.addEventListener('click', () => { cerrarModal('modal-crear'); abrirModal('modal-opciones'); });

    async function cargarResultados(tipo, query = '') {
        let url = '';
        if (tipo === 'area') {
            url = `${document.body.dataset.apiAreasUrl}?q=${query}`;
        } else if (tipo === 'puesto' && selectedArea) {
            url = `/api/puestos/${selectedArea.id}/`;
        } else {
            resultsList.innerHTML = '<li>Selecciona un área primero</li>';
            return;
        }
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            resultsList.innerHTML = '';
            if (data.length === 0) {
                resultsList.innerHTML = '<li>No hay resultados</li>';
            }
            data.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item.nombre;
                li.dataset.id = item.id;
                li.addEventListener('click', () => seleccionarItem(item));
                resultsList.appendChild(li);
            });
        } catch (error) {
            console.error("Error al cargar resultados:", error);
            resultsList.innerHTML = '<li>Error al cargar datos</li>';
        }
    }

    searchInput.addEventListener('input', () => {
        if (currentSelectionMode === 'area') {
            cargarResultados('area', searchInput.value);
        }
    });

    function seleccionarItem(item) {
        if (currentSelectionMode === 'area') {
            selectedArea = item;
            btnArea.textContent = item.nombre;
            btnArea.classList.add('selected');
            selectedPuesto = null;
            btnPuesto.textContent = 'Selecciona un puesto';
            btnPuesto.classList.remove('selected');
            btnPuesto.disabled = false;
        } else if (currentSelectionMode === 'puesto') {
            selectedPuesto = item;
            btnPuesto.textContent = item.nombre;
            btnPuesto.classList.add('selected');
        }
        cerrarModal('modal-cargar');
    }

    btnCrearConfirmar.addEventListener('click', async () => {
        const nombre = newItemInput.value.trim();
        if (!nombre) {
            crearErrorMsg.textContent = 'El nombre no puede estar vacío.';
            return;
        }
        
        let url = '';
        let body = {};
        if (currentSelectionMode === 'area') {
            url = document.body.dataset.apiCrearAreaUrl;
            body = { nombre: nombre };
        } else {
            url = document.body.dataset.apiCrearPuestoUrl;
            body = { nombre: nombre, area_id: selectedArea.id };
        }
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify(body)
            });
            const data = await response.json();
            if (response.ok) {
                seleccionarItem(data);
                cerrarModal('modal-crear');
            } else {
                crearErrorMsg.textContent = data.error || 'Ocurrió un error.';
            }
        } catch(error) {
            console.error("Error al crear:", error);
            crearErrorMsg.textContent = "Error de red al intentar crear.";
        }
    });

    // --- LÓGICA PARA EL BOTÓN "LISTO" (CON GUARDADO DE FOTO) ---
    const btnListo = document.querySelector('.btn-success');

    const toBase64 = file => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });

    btnListo.addEventListener('click', async () => {
        let fotoBase64 = null;
        const fotoInput = document.getElementById('photo-input');
        if (fotoInput.files[0]) {
            fotoBase64 = await toBase64(fotoInput.files[0]);
        }

        const data = {
            personal: {
                nombre: document.getElementById('nombre').value,
                apellido: document.getElementById('apellido').value,
                dni: document.getElementById('dni').value,
                telefono: document.getElementById('telefono').value,
                email: document.getElementById('email').value,
                codigo_telefonico: document.getElementById('cod_pais').value,
                direccion: document.getElementById('direccion').value,
                fecha_nacimiento: document.getElementById('fecha_nacimiento').value,
                foto: fotoBase64
            },
            area: selectedArea,
            puesto: selectedPuesto,
            horario: { scheduleData: scheduleData, dayColorMap: dayColorMap },
            permisos: Array.from(document.querySelectorAll('input[name="permisos"]:checked')).map(el => el.value)
        };

        if (!data.personal.nombre || !data.personal.apellido || !data.personal.email || !data.personal.dni) {
            alert('Por favor, completa los campos obligatorios: Nombre, Apellido, DNI y Email.');
            return;
        }
        if (!data.area || !data.puesto) {
            alert('Por favor, selecciona un Área y un Puesto para el empleado.');
            return;
        }
        
        btnListo.disabled = true;
        btnListo.textContent = 'Guardando...';

        try {
            const response = await fetch(document.body.dataset.apiRegistrarEmpleadoUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                alert(result.message);
                window.location.href = document.body.dataset.inicioUrl;
            } else {
                alert(`Error: ${result.error}`);
            }
        } catch (error) {
            console.error('Error al enviar el formulario:', error);
            alert('Ocurrió un error de red. Inténtalo de nuevo.');
        } finally {
            btnListo.disabled = false;
            btnListo.textContent = 'Listo';
        }
    });
});