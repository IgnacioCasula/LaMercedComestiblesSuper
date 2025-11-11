document.addEventListener('DOMContentLoaded', function() {
    // ===== VARIABLES GLOBALES =====
    let logsData = [];
    let currentPage = 1;
    let totalPages = 1;
    let autoUpdateInterval = null;
    let currentFilters = {
        search: '',
        tipo: 'all',
        nivel: 'all',
        fecha_inicio: '',
        fecha_fin: '',
        page: 1
    };

    // Gráficos
    let chartHora = null;
    let chartVentas = null;
    let chartCaja = null;
    let chartPuntualidad = null;
    let chartTendencia = null;
    let chartErrores = null;

    // ===== ELEMENTOS DEL DOM =====
    const searchInput = document.getElementById('search-input');
    const clearSearchBtn = document.getElementById('clear-search');
    const filterTipo = document.getElementById('filter-tipo');
    const filterNivel = document.getElementById('filter-nivel');
    const filterFechaInicio = document.getElementById('filter-fecha-inicio');
    const filterFechaFin = document.getElementById('filter-fecha-fin');
    const resetFiltersBtn = document.getElementById('reset-filters');
    const exportLogsBtn = document.getElementById('export-logs');
    const logsContainer = document.getElementById('logs-container');
    const paginationContainer = document.getElementById('pagination-container');
    const currentPageSpan = document.getElementById('current-page');
    const totalPagesSpan = document.getElementById('total-pages');
    const totalLogsSpan = document.getElementById('total-logs');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const modalDetalle = document.getElementById('modal-detalle');
    const closeDetalleBtn = document.getElementById('close-detalle');

    // ===== INICIALIZACIÓN =====
    init();

    function init() {
        setupEventListeners();
        setupTabs();
        cargarLogs();
        iniciarActualizacionAutomatica();
    }

    // ===== TABS =====
    function setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });

            btn.addEventListener('click', () => {
                if (window.audioSystem) window.audioSystem.play('select');

                const targetTab = btn.dataset.tab;

                // Actualizar tabs
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Mostrar contenido
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `tab-${targetTab}`) {
                        content.classList.add('active');
                    }
                });

                // Cargar estadísticas si es necesario
                if (targetTab === 'estadisticas') {
                    cargarEstadisticas();
                }
            });
        });
    }

    // ===== EVENT LISTENERS =====
    function setupEventListeners() {
        // Búsqueda con debounce
        searchInput.addEventListener('input', debounce(() => {
            currentFilters.search = searchInput.value.trim();
            currentFilters.page = 1;
            cargarLogs();
            
            if (searchInput.value.trim()) {
                clearSearchBtn.style.display = 'block';
            } else {
                clearSearchBtn.style.display = 'none';
            }
            
            if (window.audioSystem) window.audioSystem.play('select');
        }, 500));

        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            currentFilters.search = '';
            currentFilters.page = 1;
            cargarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        // Filtros
        filterTipo.addEventListener('change', () => {
            currentFilters.tipo = filterTipo.value;
            currentFilters.page = 1;
            cargarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        filterNivel.addEventListener('change', () => {
            currentFilters.nivel = filterNivel.value;
            currentFilters.page = 1;
            cargarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        filterFechaInicio.addEventListener('change', () => {
            currentFilters.fecha_inicio = filterFechaInicio.value;
            currentFilters.page = 1;
            cargarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        filterFechaFin.addEventListener('change', () => {
            currentFilters.fecha_fin = filterFechaFin.value;
            currentFilters.page = 1;
            cargarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        resetFiltersBtn.addEventListener('mouseenter', () => {
            if (window.audioSystem) window.audioSystem.play('hover');
        });

        resetFiltersBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            filterTipo.value = 'all';
            filterNivel.value = 'all';
            filterFechaInicio.value = '';
            filterFechaFin.value = '';
            
            currentFilters = {
                search: '',
                tipo: 'all',
                nivel: 'all',
                fecha_inicio: '',
                fecha_fin: '',
                page: 1
            };
            
            cargarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        exportLogsBtn.addEventListener('mouseenter', () => {
            if (window.audioSystem) window.audioSystem.play('hover');
        });

        exportLogsBtn.addEventListener('click', () => {
            exportarLogs();
            if (window.audioSystem) window.audioSystem.play('select');
        });

        // Paginación
        prevPageBtn.addEventListener('click', () => {
            if (currentFilters.page > 1) {
                currentFilters.page--;
                cargarLogs();
                if (window.audioSystem) window.audioSystem.play('select');
            }
        });

        nextPageBtn.addEventListener('click', () => {
            if (currentFilters.page < totalPages) {
                currentFilters.page++;
                cargarLogs();
                if (window.audioSystem) window.audioSystem.play('select');
            }
        });

        // Modal
        closeDetalleBtn.addEventListener('click', () => {
            cerrarModal(modalDetalle);
        });

        modalDetalle.addEventListener('click', (e) => {
            if (e.target === modalDetalle) {
                cerrarModal(modalDetalle);
            }
        });
    }

    // ===== CARGAR LOGS =====
    async function cargarLogs() {
        logsContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Cargando logs...</div>';

        try {
            const params = new URLSearchParams();
            params.append('page', currentFilters.page);
            
            if (currentFilters.search) params.append('search', currentFilters.search);
            if (currentFilters.tipo !== 'all') params.append('tipo', currentFilters.tipo);
            if (currentFilters.nivel !== 'all') params.append('nivel', currentFilters.nivel);
            if (currentFilters.fecha_inicio) params.append('fecha_inicio', currentFilters.fecha_inicio);
            if (currentFilters.fecha_fin) params.append('fecha_fin', currentFilters.fecha_fin);

            const response = await fetch(`/api/logs-actividad/?${params.toString()}`);
            
            if (!response.ok) throw new Error('Error al cargar logs');

            const data = await response.json();
            logsData = data.logs;
            totalPages = data.total_pages;
            currentPage = data.page;

            renderLogs(logsData);
            actualizarPaginacion(data);

        } catch (error) {
            console.error('Error:', error);
            if (window.audioSystem) window.audioSystem.play('error');
            logsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar los logs</p>
                </div>
            `;
        }
    }

    // ===== RENDERIZAR LOGS (SIMPLIFICADO - SIN USER AGENT) =====
    function renderLogs(logs) {
        if (logs.length === 0) {
            logsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No se encontraron registros con los filtros seleccionados</p>
                </div>
            `;
            return;
        }
    
        logsContainer.innerHTML = logs.map(log => `
            <div class="log-item" data-timestamp="${log.timestamp}" style="cursor: pointer;">
                <div class="log-header">
                    <div class="log-info">
                        <div class="log-tipo">
                            <i class="${getTipoIcon(log.tipo_actividad)}"></i>
                            ${log.tipo_actividad_display}
                        </div>
                        <div class="log-usuario">
                            <i class="fas fa-user"></i>
                            <strong>${log.nombre_usuario}</strong>
                            ${log.area && log.area !== 'N/A' ? `<span>• ${log.area}</span>` : ''}
                        </div>
                    </div>
                    <div class="log-meta">
                        <div class="log-fecha">
                            <i class="far fa-calendar"></i>
                            ${log.fecha} ${log.hora}
                        </div>
                        <span class="nivel-badge ${log.nivel.toLowerCase()}">
                            <i class="fas ${getNivelIcon(log.nivel)}"></i>
                            ${log.nivel_display}
                        </span>
                    </div>
                </div>
                <div class="log-body">
                    <div class="log-descripcion">${log.descripcion}</div>
                    ${log.detalles ? `
                        <div class="log-details-preview">
                            ${renderDetallesPreview(log.detalles)}
                        </div>
                    ` : ''}
                </div>
                <div class="log-footer">
                    <div class="log-ip">
                        <i class="fas fa-network-wired"></i>
                        IP: ${log.ip_address || 'N/A'}
                    </div>
                    <button class="btn-ver-mas" onclick="event.stopPropagation();">
                        Ver más <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        `).join('');

        // Agregar eventos de click a los items
        document.querySelectorAll('.log-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                if (window.audioSystem) window.audioSystem.play('hover');
            });
            
            item.addEventListener('click', () => {
                const timestamp = item.dataset.timestamp;
                verDetalle(timestamp);
            });
        });
    }

    function renderDetallesPreview(detalles) {
        if (!detalles || typeof detalles !== 'object') return '';

        const keys = Object.keys(detalles).slice(0, 3);
        return keys.map(key => `
            <div class="detail-chip">
                <i class="fas fa-info-circle"></i>
                <strong>${formatKey(key)}:</strong> ${formatValue(detalles[key])}
            </div>
        `).join('');
    }

    // ===== VER DETALLE =====
    async function verDetalle(logTimestamp) {
        if (window.audioSystem) window.audioSystem.play('select');
    
        try {
            const response = await fetch(`/api/logs-actividad/${encodeURIComponent(logTimestamp)}/`);
            if (!response.ok) throw new Error('Error al cargar detalle');
    
            const log = await response.json();
    
            document.getElementById('detalle-content').innerHTML = `
                <div class="detalle-section">
                    <h3><i class="fas fa-info-circle"></i> Información General</h3>
                    <div class="detalle-row">
                        <span class="detalle-label">Fecha y Hora:</span>
                        <span class="detalle-value">${log.fecha} ${log.hora}</span>
                    </div>
                    <div class="detalle-row">
                        <span class="detalle-label">Tipo de Actividad:</span>
                        <span class="detalle-value">${log.tipo_actividad_display}</span>
                    </div>
                    <div class="detalle-row">
                        <span class="detalle-label">Nivel:</span>
                        <span class="detalle-value">
                            <span class="nivel-badge ${log.nivel.toLowerCase()}">
                                ${log.nivel_display}
                            </span>
                        </span>
                    </div>
                    <div class="detalle-row">
                        <span class="detalle-label">Descripción:</span>
                        <span class="detalle-value">${log.descripcion}</span>
                    </div>
                </div>
    
                <div class="detalle-section">
                    <h3><i class="fas fa-user"></i> Usuario</h3>
                    <div class="detalle-row">
                        <span class="detalle-label">Nombre:</span>
                        <span class="detalle-value">${log.nombre_usuario}</span>
                    </div>
                    ${log.area ? `
                        <div class="detalle-row">
                            <span class="detalle-label">Área:</span>
                            <span class="detalle-value">${log.area}</span>
                        </div>
                    ` : ''}
                    ${log.puesto ? `
                        <div class="detalle-row">
                            <span class="detalle-label">Puesto:</span>
                            <span class="detalle-value">${log.puesto}</span>
                        </div>
                    ` : ''}
                </div>
    
                <div class="detalle-section">
                    <h3><i class="fas fa-network-wired"></i> Información Técnica</h3>
                    <div class="detalle-row">
                        <span class="detalle-label">Dirección IP:</span>
                        <span class="detalle-value">${log.ip_address || 'N/A'}</span>
                    </div>
                </div>
    
                ${log.detalles ? `
                    <div class="detalle-section">
                        <h3><i class="fas fa-file-code"></i> Detalles Adicionales</h3>
                        <div class="detalle-json"><pre>${JSON.stringify(log.detalles, null, 2)}</pre></div>
                    </div>
                ` : ''}
            `;
    
            abrirModal(modalDetalle);
    
        } catch (error) {
            console.error('Error:', error);
            if (window.audioSystem) window.audioSystem.play('error');
            alert('Error al cargar los detalles del log');
        }
    }

    window.verDetalle = verDetalle;

    // ===== PAGINACIÓN =====
    function actualizarPaginacion(data) {
        currentPageSpan.textContent = data.page;
        totalPagesSpan.textContent = data.total_pages;
        totalLogsSpan.textContent = data.total;

        prevPageBtn.disabled = !data.has_previous;
        nextPageBtn.disabled = !data.has_next;

        paginationContainer.style.display = data.total_pages > 1 ? 'flex' : 'none';
    }

    // ===== ACTUALIZACIÓN AUTOMÁTICA =====
    function iniciarActualizacionAutomatica() {
        autoUpdateInterval = setInterval(() => {
            const tabLogs = document.getElementById('tab-logs');
            if (tabLogs && tabLogs.classList.contains('active')) {
                cargarLogs();
            }
        }, 30000);
    }

    // ===== ESTADÍSTICAS OPTIMIZADAS =====
    async function cargarEstadisticas() {
        try {
            const response = await fetch('/api/estadisticas-logs/');
            if (!response.ok) throw new Error('Error al cargar estadísticas');

            const data = await response.json();

            // Renderizar gráficos útiles
            renderGraficoActividadPorHora(data.actividad_por_hora);
            renderGraficoVentasPorUsuario(data.ventas_por_usuario);
            renderGraficoProblemasCaja(data.problemas_caja);
            renderGraficoPuntualidad(data.puntualidad_empleados);
            renderGraficoTendencia(data.actividad_diaria);
            renderGraficoErrores(data.errores_por_tipo);

            // Mostrar resumen
            mostrarResumen(data.resumen);

        } catch (error) {
            console.error('Error:', error);
            if (window.audioSystem) window.audioSystem.play('error');
        }
    }

    // 📊 GRÁFICO 1: Actividad por hora del día
    function renderGraficoActividadPorHora(data) {
        const ctx = document.getElementById('chart-hora');
        if (!ctx || data.length === 0) return;

        if (chartHora) chartHora.destroy();

        const labels = data.map(d => d.hora_label);
        const valores = data.map(d => d.total);

        chartHora = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Actividades por Hora',
                    data: valores,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '📊 ¿A qué horas hay más actividad?',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // 📊 GRÁFICO 2: Rendimiento de ventas por usuario
    function renderGraficoVentasPorUsuario(data) {
        const ctx = document.getElementById('chart-ventas');
        if (!ctx || data.length === 0) return;

        if (chartVentas) chartVentas.destroy();

        const labels = data.map(d => d.usuario);
        const valores = data.map(d => d.total_vendido);

        chartVentas = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Total Vendido ($)',
                    data: valores,
                    backgroundColor: 'rgba(39, 174, 96, 0.8)',
                    borderColor: 'rgba(39, 174, 96, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '💰 ¿Quién vende más?',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    // 📊 GRÁFICO 3: Problemas de caja
    function renderGraficoProblemasCaja(data) {
        const ctx = document.getElementById('chart-caja');
        if (!ctx || data.length === 0) return;

        if (chartCaja) chartCaja.destroy();

        const labels = data.map(d => d.usuario);
        const valores = data.map(d => Math.abs(d.diferencia_promedio));
        const colores = data.map(d => d.diferencia_promedio < 0 ? 'rgba(52, 152, 219, 0.8)' : 'rgba(231, 76, 60, 0.8)');

        chartCaja = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Diferencia Promedio (valor absoluto)',
                    data: valores,
                    backgroundColor: colores,
                    borderColor: colores.map(c => c.replace('0.8', '1')),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '⚠️ ¿Qué cajas tienen más diferencias?',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }

    // 📊 GRÁFICO 4: Puntualidad de empleados
    function renderGraficoPuntualidad(data) {
        const ctx = document.getElementById('chart-puntualidad');
        if (!ctx || data.length === 0) return;

        if (chartPuntualidad) chartPuntualidad.destroy();

        const labels = data.map(d => d.usuario);
        const valores = data.map(d => d.porcentaje_tardanzas);

        chartPuntualidad = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '% de Tardanzas',
                    data: valores,
                    backgroundColor: 'rgba(230, 126, 34, 0.8)',
                    borderColor: 'rgba(230, 126, 34, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    title: {
                        display: true,
                        text: '⏰ ¿Quiénes llegan tarde más seguido?',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // 📊 GRÁFICO 5: Tendencia de actividad
    function renderGraficoTendencia(data) {
        const ctx = document.getElementById('chart-tendencia');
        if (!ctx || data.length === 0) return;

        if (chartTendencia) chartTendencia.destroy();

        const labels = data.map(d => d.fecha_str);
        const valores = data.map(d => d.total);

        chartTendencia = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Actividades por Día',
                    data: valores,
                    borderColor: 'rgba(155, 89, 182, 1)',
                    backgroundColor: 'rgba(155, 89, 182, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '📈 ¿La actividad está aumentando o disminuyendo?',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 10 }
                    }
                }
            }
        });
    }

    // 📊 GRÁFICO 6: Errores por tipo
    function renderGraficoErrores(data) {
        const ctx = document.getElementById('chart-errores');
        if (!ctx || data.length === 0) return;

        if (chartErrores) chartErrores.destroy();

        const labels = data.map(d => d.tipo_actividad);
        const valores = data.map(d => d.total);

        chartErrores = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: valores,
                    backgroundColor: [
                        'rgba(231, 76, 60, 0.8)',
                        'rgba(230, 126, 34, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(155, 89, 182, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '🚨 ¿Qué tipo de errores estamos teniendo?',
                        font: { size: 16, weight: 'bold' }
                    }
                }
            }
        });
    }

    function mostrarResumen(resumen) {
        // Aquí puedes agregar cards de resumen si quieres
        console.log('Resumen:', resumen);
    }

    // ===== EXPORTAR LOGS =====
    function exportarLogs() {
        const headers = ['Fecha', 'Hora', 'Usuario', 'Área', 'Tipo', 'Nivel', 'Descripción', 'IP'];
        const rows = logsData.map(log => [
            log.fecha,
            log.hora,
            log.nombre_usuario,
            log.area || 'N/A',
            log.tipo_actividad_display,
            log.nivel_display,
            `"${log.descripcion}"`,
            log.ip_address || 'N/A'
        ]);

        let csvContent = headers.join(',') + '\n';
        rows.forEach(row => {
            csvContent += row.join(',') + '\n';
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `logs_actividad_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        if (window.audioSystem) window.audioSystem.play('positive');
    }

    // ===== UTILIDADES =====
    function getTipoIcon(tipo) {
        const iconos = {
            'LOGIN': 'fas fa-sign-in-alt',
            'LOGOUT': 'fas fa-sign-out-alt',
            'ENTRADA': 'fas fa-clock',
            'SALIDA': 'fas fa-clock',
            'APERTURA_CAJA': 'fas fa-cash-register',
            'CIERRE_CAJA': 'fas fa-cash-register',
            'VENTA': 'fas fa-shopping-cart',
            'CREAR_EMPLEADO': 'fas fa-user-plus',
            'EDITAR_EMPLEADO': 'fas fa-user-edit'
        };
        return iconos[tipo] || 'fas fa-info-circle';
    }

    function getNivelIcon(nivel) {
        const iconos = {
            'INFO': 'fa-info-circle',
            'WARNING': 'fa-exclamation-triangle',
            'ERROR': 'fa-times-circle',
            'CRITICAL': 'fa-bomb'
        };
        return iconos[nivel] || 'fa-info-circle';
    }

    function formatKey(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    function formatValue(value) {
        if (typeof value === 'object') {
            return JSON.stringify(value);
        }
        if (typeof value === 'number') {
            return value.toLocaleString('es-AR');
        }
        return String(value);
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

    function abrirModal(modal) {
        modal.classList.add('show');
        if (window.audioSystem) window.audioSystem.play('positive');
    }

    function cerrarModal(modal) {
        modal.classList.remove('show');
        if (window.audioSystem) window.audioSystem.play('select');
    }

    // Limpiar interval al cerrar página
    window.addEventListener('beforeunload', () => {
        if (autoUpdateInterval) {
            clearInterval(autoUpdateInterval);
        }
    });
});