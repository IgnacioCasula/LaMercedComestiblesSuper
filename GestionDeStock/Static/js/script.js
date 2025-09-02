// JavaScript para la gestión de stock del supermercado

// Función para realizar pedidos de productos
function orderProduct(productId) {
    const quantity = prompt('¿Cuántas unidades desea pedir?');
    
    if (quantity && !isNaN(quantity) && quantity > 0) {
        // Aquí iría la llamada AJAX para realizar el pedido
        fetch(`/api/order-product/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ quantity: quantity })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Pedido realizado con éxito');
                // Recargar la página para actualizar los datos
                location.reload();
            } else {
                alert('Error al realizar el pedido: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al realizar el pedido');
        });
    } else if (quantity !== null) {
        alert('Por favor, introduzca una cantidad válida');
    }
}

// Función para obtener el valor de una cookie
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

// Función para buscar productos
function searchProducts() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#productsTable tbody tr');
    
    rows.forEach(row => {
        const productName = row.cells[0].textContent.toLowerCase();
        const category = row.cells[1].textContent.toLowerCase();
        
        if (productName.includes(searchTerm) || category.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Función para ordenar la tabla
function sortTable(columnIndex) {
    const table = document.getElementById('productsTable');
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const header = table.querySelectorAll('thead th')[columnIndex];
    const isAscending = header.getAttribute('data-sort') === 'asc';
    
    // Alternar dirección de ordenamiento
    header.setAttribute('data-sort', isAscending ? 'desc' : 'asc');
    
    // Quitar indicadores de ordenamiento de otras columnas
    table.querySelectorAll('thead th').forEach(th => {
        if (th !== header) {
            th.removeAttribute('data-sort');
        }
    });
    
    // Ordenar las filas
    rows.sort((a, b) => {
        let aValue = a.cells[columnIndex].textContent;
        let bValue = b.cells[columnIndex].textContent;
        
        // Si es numérico, convertir a número
        if (!isNaN(aValue) && !isNaN(bValue)) {
            aValue = Number(aValue);
            bValue = Number(bValue);
        } else {
            aValue = aValue.toLowerCase();
            bValue = bValue.toLowerCase();
        }
        
        if (aValue < bValue) return isAscending ? -1 : 1;
        if (aValue > bValue) return isAscending ? 1 : -1;
        return 0;
    });
    
    // Reinsertar filas ordenadas
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Inicializar tooltips de Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Actualizar hora actual cada minuto
    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
        const dateStr = now.toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        
        const clockElement = document.getElementById('current-time');
        if (clockElement) {
            clockElement.innerHTML = `<i class="fas fa-clock"></i> ${timeStr} - ${dateStr}`;
        }
    }
    
    updateClock();
    setInterval(updateClock, 60000);
});

// Función para exportar datos a CSV
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    
    // Obtener headers
    const headers = [];
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent);
    });
    csv.push(headers.join(','));
    
    // Obtener datos de las filas
    table.querySelectorAll('tbody tr').forEach(row => {
        const rowData = [];
        row.querySelectorAll('td').forEach(cell => {
            rowData.push(cell.textContent);
        });
        csv.push(rowData.join(','));
    });
    
    // Crear y descargar archivo
    const csvContent = "data:text/csv;charset=utf-8," + csv.join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}