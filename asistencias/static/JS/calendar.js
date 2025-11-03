// calendar.js - Sistema de calendario de asistencias

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema de calendario...');
    
    var calendarEl = document.getElementById('calendar');
    
    if (!calendarEl) {
        console.error('❌ Elemento #calendar no encontrado en el DOM');
        return;
    }
    
    console.log('✓ Elemento calendar encontrado');
    console.log('✓ URL de eventos:', calendarEl.dataset.eventsUrl);
    
    // Verificar que FullCalendar esté disponible
    if (typeof FullCalendar === 'undefined') {
        console.error('❌ FullCalendar no está cargado');
        calendarEl.innerHTML = '<div style="padding: 40px; text-align: center; color: #e74c3c;"><i class="fas fa-exclamation-triangle" style="font-size: 3em; margin-bottom: 15px;"></i><p>Error: FullCalendar no se cargó correctamente</p></div>';
        return;
    }
    
    console.log('✓ FullCalendar disponible');
    
    try {
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            height: 'auto',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            buttonText: {
                today: 'Hoy',
                month: 'Mes',
                week: 'Semana',
                day: 'Día'
            },
            
            loading: function(isLoading) {
                if (isLoading) {
                    console.log('⏳ Cargando eventos...');
                } else {
                    console.log('✓ Eventos cargados');
                }
            },
            
            events: function(fetchInfo, successCallback, failureCallback) {
                const params = new URLSearchParams({
                    start: fetchInfo.startStr,
                    end: fetchInfo.endStr
                });

                const url = `${calendarEl.dataset.eventsUrl}?${params.toString()}`;
                console.log('📅 Solicitando eventos desde:', url);
                console.log('📅 Rango:', fetchInfo.startStr, 'a', fetchInfo.endStr);

                fetch(url)
                    .then(response => {
                        console.log('📡 Respuesta recibida:', response.status, response.statusText);
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log(`✅ ${data.length} evento(s) recibido(s):`, data);
                        
                        if (data.length === 0) {
                            console.warn('⚠️ No hay eventos para mostrar en este período');
                        } else {
                            console.log('Primer evento:', data[0]);
                        }
                        
                        successCallback(data);
                    })
                    .catch(error => {
                        console.error('❌ Error cargando eventos:', error);
                        failureCallback(error);
                        
                        // Mostrar mensaje de error en el calendario
                        alert(`Error al cargar asistencias: ${error.message}\n\nRevisa la consola (F12) para más detalles.`);
                    });
            },

            eventContent: function(arg) {
                const props = arg.event.extendedProps;
                let iconHtml = '';

                // Iconos según el estado
                switch(props.estado) {
                    case 'Justo': 
                        iconHtml = '<i class="fa-solid fa-circle-check"></i>'; 
                        break;
                    case 'Temprano': 
                        iconHtml = '<i class="fa-solid fa-hourglass-start"></i>'; 
                        break;
                    case 'Tarde': 
                        iconHtml = '<i class="fa-solid fa-clock"></i>'; 
                        break;
                    case 'Ausente': 
                        iconHtml = '<i class="fa-solid fa-circle-xmark"></i>'; 
                        break;
                    case 'Programado': 
                        iconHtml = '<i class="fa-solid fa-calendar-days"></i>'; 
                        break;
                    case 'Fuera de Turno': 
                        iconHtml = '<i class="fa-solid fa-triangle-exclamation"></i>'; 
                        break;
                    default:
                        iconHtml = '<i class="fa-solid fa-question"></i>';
                }
                
                // Formatear horarios
                const formatOptions = { hour: '2-digit', minute: '2-digit' };
                let startTime = arg.event.start ? arg.event.start.toLocaleTimeString('es-ES', formatOptions) : '';
                let endTime = arg.event.end ? arg.event.end.toLocaleTimeString('es-ES', formatOptions) : '';
                let timeText = endTime ? `${startTime} - ${endTime}` : startTime;

                return {
                    html: `
                        <div style="padding: 4px; line-height: 1.4;">
                            <div style="font-weight: 700; margin-bottom: 3px; font-size: 0.95em;">${timeText}</div>
                            <div style="font-size: 0.9em; margin-bottom: 2px;">${arg.event.title}</div>
                            <div style="font-size: 0.85em; opacity: 0.95; display: flex; align-items: center; gap: 4px;">
                                ${iconHtml} <span>${props.estado}</span>
                            </div>
                        </div>
                    `
                };
            },

            eventDidMount: function(info) {
                const props = info.event.extendedProps;
                
                // Verificar si Tippy está disponible
                if (typeof tippy === 'undefined') {
                    console.warn('⚠️ Tippy.js no está disponible, tooltips deshabilitados');
                    return;
                }
                
                // Crear tooltip con Tippy.js
                tippy(info.el, {
                    content: `
                        <div class="tooltip-content">
                            <div><strong>Puesto:</strong> ${info.event.title}</div>
                            <div><strong>Área:</strong> ${props.area || 'N/A'}</div>
                            <hr class="tooltip-divider">
                            <div><strong>Estado:</strong> ${props.estado}</div>
                            <div><strong>Hora de entrada:</strong> ${props.entrada_registrada || 'N/A'}</div>
                        </div>
                    `,
                    allowHTML: true,
                    animation: 'scale-subtle',
                    theme: 'asistencia',
                    delay: [200, 50],
                    arrow: true,
                    placement: 'top',
                });
            },
            
            eventTimeFormat: {
                hour: '2-digit',
                minute: '2-digit',
                meridiem: false
            },

            datesSet: function(dateInfo) {
                console.log('📆 Vista actualizada:', dateInfo.view.type);
                console.log('📆 Mostrando desde', dateInfo.startStr, 'hasta', dateInfo.endStr);
            },
            
            eventClassNames: function(arg) {
                // Asignar clases según el estado
                const estado = arg.event.extendedProps.estado;
                const classMap = {
                    'Programado': 'event-programado',
                    'Temprano': 'event-temprano',
                    'Justo': 'event-justo',
                    'Tarde': 'event-tarde',
                    'Ausente': 'event-ausente',
                    'Fuera de Turno': 'event-fuera-de-turno'
                };
                return classMap[estado] || '';
            }
        });
        
        console.log('🎨 Renderizando calendario...');
        calendar.render();
        console.log('✅ Calendario renderizado exitosamente');

        // ===== SISTEMA DE SONIDOS =====
        if (window.audioSystem) {
            console.log('🔊 Sistema de audio disponible');
            
            // Sonidos en botones del calendario (usar delegación de eventos)
            document.addEventListener('click', function(e) {
                if (e.target.closest('.fc-button')) {
                    window.audioSystem.play('select');
                }
            });
            
            document.addEventListener('mouseenter', function(e) {
                if (e.target.closest('.fc-button')) {
                    window.audioSystem.play('hover');
                }
            }, true);

            // Sonido en botón volver
            const backBtn = document.querySelector('.back-btn');
            if (backBtn) {
                backBtn.addEventListener('mouseenter', () => {
                    window.audioSystem.play('hover');
                });
                backBtn.addEventListener('click', () => {
                    window.audioSystem.play('select');
                });
            }
        } else {
            console.warn('⚠️ Sistema de audio no disponible');
        }

    } catch (error) {
        console.error('❌ Error fatal al inicializar calendario:', error);
        calendarEl.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #e74c3c;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3em; margin-bottom: 15px;"></i>
                <h3>Error al cargar el calendario</h3>
                <p style="margin-top: 10px;">${error.message}</p>
                <p style="margin-top: 15px; font-size: 0.9em; color: #6c757d;">Revisa la consola (F12) para más detalles</p>
            </div>
        `;
    }

    console.log('✅ Sistema de calendario inicializado');
});