/* ===== VARIABLES GLOBALES ===== */
let productos = [];
let proveedores = [];
let categorias = [];
let movimientos = [];
let ventas = [];
let categoriesChart, stockChart;

/* ===== UTILIDADES ===== */
function byId(id) {
  return document.getElementById(id);
}

function showNotification(message, type = 'success') {
  const container = byId('notification-container');
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  
  const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
  
  notification.innerHTML = `
    <i class="material-icons">${icon}</i>
    <span class="notification-message">${message}</span>
    <button class="notification-close" onclick="this.parentElement.remove()">
      <i class="material-icons">close</i>
    </button>
  `;
  
  container.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.4s ease-out';
    setTimeout(() => notification.remove(), 400);
  }, 5000);
}

function fmtMoney(n) {
  return new Intl.NumberFormat('es-AR', { 
    style: 'currency', 
    currency: 'ARS' 
  }).format(Number(n) || 0);
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

/* ===== NAVEGACIÓN ===== */
const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.section');

navItems.forEach(item => {
  item.addEventListener('click', () => {
    const sectionId = item.getAttribute('data-section');
    
    navItems.forEach(n => n.classList.remove('active'));
    item.classList.add('active');
    
    sections.forEach(s => s.classList.remove('active'));
    document.getElementById(`${sectionId}-section`).classList.add('active');
    
    if (sectionId === 'productos') cargarProductos();
    if (sectionId === 'proveedores') cargarProveedores();
    if (sectionId === 'categorias') cargarCategorias();
    if (sectionId === 'stock-bajo') cargarStockBajo();
    if (sectionId === 'dashboard') {
      cargarProductos();
      actualizarDashboard();
    }
  });
});

/* ===== BÚSQUEDA ===== */
function setupSearch(inputId, tableId) {
  const input = byId(inputId);
  if (!input) return;
  
  input.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const table = byId(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    for (let row of rows) {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(searchTerm) ? '' : 'none';
    }
  });
}

setupSearch('search-productos', 'productos-table');
setupSearch('search-proveedores', 'proveedores-table');
setupSearch('search-categorias', 'categorias-table');
setupSearch('search-stock-bajo', 'stock-bajo-table');

/* ===== CARGAR DATOS ===== */
async function cargarProductos() {
  try {
    const response = await fetch(`/stock/api/productos/?sucursal_id=${SUCURSAL_ID}`);
    if (!response.ok) throw new Error('Error al cargar productos');
    
    productos = await response.json();
    renderProductos();
    cargarStockBajo();
    actualizarDashboard();
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error al cargar productos', 'error');
  }
}

async function cargarProveedores() {
  try {
    const response = await fetch('/stock/api/proveedores/');
    if (!response.ok) throw new Error('Error al cargar proveedores');
    
    proveedores = await response.json();
    renderProveedores();
    llenarSelectProveedores();
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error al cargar proveedores', 'error');
  }
}

async function cargarCategorias() {
  try {
    const response = await fetch('/stock/api/categorias/');
    if (!response.ok) throw new Error('Error al cargar categorías');
    
    categorias = await response.json();
    renderCategorias();
    llenarSelectCategorias();
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error al cargar categorías', 'error');
  }
}

/* ===== RENDERIZAR TABLAS ===== */
function renderProductos() {
  const tbody = byId('productos-body');
  if (!tbody) return;
  
  if (productos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align: center; padding: 40px; color: #6c757d;">
          <i class="material-icons" style="font-size: 3rem; display: block; margin-bottom: 10px;">inventory_2</i>
          No hay productos registrados
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = productos.map(p => `
    <tr>
      <td>PRD${String(p.id).padStart(3, '0')}</td>
      <td>
        <img src="${p.imagen || 'https://via.placeholder.com/50'}" 
             class="product-image" 
             alt="${p.nombre}"
             onerror="this.src='https://via.placeholder.com/50'">
      </td>
      <td>${p.nombre}</td>
      <td>${fmtMoney(p.precio)}</td>
      <td>${p.marca}</td>
      <td>${p.codigo}</td>
      <td>${p.categoria}</td>
      <td>${p.proveedor}</td>
      <td class="${p.stock < p.stockMinimo ? 'stock-bajo' : ''}">${p.stock}</td>
      <td>
        <button class="btn-icon" onclick="editarProducto(${p.id})" title="Editar">
          <i class="material-icons">edit</i>
        </button>
        <button class="btn-icon delete" onclick="eliminarProducto(${p.id})" title="Eliminar">
          <i class="material-icons">delete</i>
        </button>
      </td>
    </tr>
  `).join('');
}

function renderProveedores() {
  const tbody = byId('proveedores-body');
  if (!tbody) return;
  
  if (proveedores.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 40px; color: #6c757d;">
          <i class="material-icons" style="font-size: 3rem; display: block; margin-bottom: 10px;">local_shipping</i>
          No hay proveedores registrados
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = proveedores.map(pr => `
    <tr>
      <td>PROV${String(pr.id).padStart(3, '0')}</td>
      <td>${pr.nombre}</td>
      <td>${pr.telefono}</td>
      <td>${pr.email}</td>
      <td>${pr.cuit}</td>
      <td>
        <button class="btn-icon" onclick="editarProveedor(${pr.id})" title="Editar">
          <i class="material-icons">edit</i>
        </button>
        <button class="btn-icon delete" onclick="eliminarProveedor(${pr.id})" title="Eliminar">
          <i class="material-icons">delete</i>
        </button>
      </td>
    </tr>
  `).join('');
}

function renderCategorias() {
  const tbody = byId('categorias-body');
  if (!tbody) return;
  
  if (categorias.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; padding: 40px; color: #6c757d;">
          <i class="material-icons" style="font-size: 3rem; display: block; margin-bottom: 10px;">category</i>
          No hay categorías registradas
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = categorias.map(c => {
    const count = productos.filter(p => p.categoria_id === c.id).length;
    return `
      <tr>
        <td>CAT${String(c.id).padStart(3, '0')}</td>
        <td>${c.nombre}</td>
        <td>${c.descripcion || '—'}</td>
        <td>${count}</td>
        <td>
          <button class="btn-icon" onclick="editarCategoria(${c.id})" title="Editar">
            <i class="material-icons">edit</i>
          </button>
          <button class="btn-icon delete" onclick="eliminarCategoria(${c.id})" title="Eliminar">
            <i class="material-icons">delete</i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function cargarStockBajo() {
  const tbody = byId('stock-bajo-body');
  if (!tbody) return;
  
  const low = productos.filter(p => p.stock < p.stockMinimo);
  byId('badge-stock-bajo').textContent = `${low.length} productos`;
  
  if (low.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="11" style="text-align: center; padding: 40px; color: #28a745;">
          <i class="material-icons" style="font-size: 3rem; display: block; margin-bottom: 10px;">check_circle</i>
          ¡Excelente! No hay productos con stock bajo
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = low.map(p => `
    <tr>
      <td>PRD${String(p.id).padStart(3, '0')}</td>
      <td>
        <img src="${p.imagen || 'https://via.placeholder.com/50'}" 
             class="product-image" 
             alt="${p.nombre}"
             onerror="this.src='https://via.placeholder.com/50'">
      </td>
      <td>${p.nombre}</td>
      <td>${fmtMoney(p.precio)}</td>
      <td>${p.marca}</td>
      <td>${p.codigo}</td>
      <td>${p.categoria}</td>
      <td>${p.proveedor}</td>
      <td class="stock-bajo">${p.stock}</td>
      <td>${p.stockMinimo}</td>
      <td>
        <button class="btn-icon" onclick="editarProducto(${p.id})" title="Editar">
          <i class="material-icons">edit</i>
        </button>
      </td>
    </tr>
  `).join('');
}

/* ===== DASHBOARD ===== */
function actualizarDashboard() {
  byId('total-productos').textContent = productos.length;
  byId('total-proveedores').textContent = proveedores.length;
  byId('total-categorias').textContent = categorias.length;
  
  const stockBajo = productos.filter(p => p.stock < p.stockMinimo).length;
  byId('total-stock-bajo').textContent = stockBajo;
  
  updateCharts();
}

function initCharts() {
  const ctx1 = document.getElementById('categoriesChart');
  const ctx2 = document.getElementById('stockChart');
  
  if (!ctx1 || !ctx2) return;
  
  categoriesChart = new Chart(ctx1.getContext('2d'), {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: 'Productos por Categoría',
        data: [],
        backgroundColor: 'rgba(102, 126, 234, 0.8)',
        borderColor: 'rgba(102, 126, 234, 1)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } }
      }
    }
  });
  
  stockChart = new Chart(ctx2.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Stock Bajo', 'Stock Normal'],
      datasets: [{
        data: [0, 0],
        backgroundColor: [
          'rgba(220, 53, 69, 0.8)',
          'rgba(40, 167, 69, 0.8)'
        ],
        borderColor: ['#dc3545', '#28a745'],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function updateCharts() {
  if (!categoriesChart || !stockChart) return;
  
  // Productos por categoría
  const catCount = {};
  productos.forEach(p => {
    catCount[p.categoria] = (catCount[p.categoria] || 0) + 1;
  });
  
  const sortedCats = Object.entries(catCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  
  categoriesChart.data.labels = sortedCats.map(c => c[0]);
  categoriesChart.data.datasets[0].data = sortedCats.map(c => c[1]);
  categoriesChart.update();
  
  // Estado del inventario
  const stockBajo = productos.filter(p => p.stock < p.stockMinimo).length;
  const stockNormal = productos.length - stockBajo;
  
  stockChart.data.datasets[0].data = [stockBajo, stockNormal];
  stockChart.update();
}

/* ===== MODALES ===== */
function openModal(type) {
  const modal = byId(`modal-${type}`);
  if (!modal) return;
  
  modal.classList.add('show');
  
  if (type === 'producto') {
    if (!byId('producto-id').value) {
      byId('modal-producto-title').innerHTML = '<i class="fas fa-box"></i> Nuevo Producto';
      byId('form-producto').reset();
      byId('image-preview').innerHTML = '<span>Vista previa</span>';
    }
    llenarSelectCategorias();
    llenarSelectProveedores();
  }
  
  if (type === 'proveedor') {
    if (!byId('proveedor-id').value) {
      byId('modal-proveedor-title').innerHTML = '<i class="fas fa-truck"></i> Nuevo Proveedor';
      byId('form-proveedor').reset();
    }
  }
  
  if (type === 'categoria') {
    if (!byId('categoria-id').value) {
      byId('modal-categoria-title').innerHTML = '<i class="fas fa-tags"></i> Nueva Categoría';
      byId('form-categoria').reset();
    }
  }
}

function closeModal(type) {
  const modal = byId(`modal-${type}`);
  if (!modal) return;
  
  modal.classList.remove('show');
  
  // Limpiar campos ID
  const idField = byId(`${type}-id`);
  if (idField) idField.value = '';
}

// Cerrar modal al hacer clic fuera
window.onclick = function(e) {
  document.querySelectorAll('.modal').forEach(m => {
    if (e.target === m) {
      m.classList.remove('show');
      // Limpiar IDs
      ['producto', 'proveedor', 'categoria'].forEach(type => {
        const idField = byId(`${type}-id`);
        if (idField) idField.value = '';
      });
    }
  });
};

/* ===== LLENAR SELECTS ===== */
function llenarSelectCategorias() {
  const select = byId('producto-categoria');
  if (!select) return;
  
  select.innerHTML = '<option value="">Seleccionar categoría</option>';
  
  categorias.forEach(c => {
    const option = document.createElement('option');
    option.value = c.id;
    option.textContent = c.nombre;
    select.appendChild(option);
  });
}

function llenarSelectProveedores() {
  const select = byId('producto-proveedor');
  if (!select) return;
  
  select.innerHTML = '<option value="">Seleccionar proveedor</option>';
  
  proveedores.forEach(p => {
    const option = document.createElement('option');
    option.value = p.id;
    option.textContent = p.nombre;
    select.appendChild(option);
  });
}

/* ===== PREVIEW IMAGEN ===== */
const imagenInput = byId('producto-imagen');
if (imagenInput) {
  imagenInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const preview = byId('image-preview');
      preview.innerHTML = `<img src="${event.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
  });
}

/* ===== CRUD PRODUCTOS ===== */
async function guardarProducto(e) {
  e.preventDefault();
  
  const id = byId('producto-id').value;
  const imagen = byId('image-preview').querySelector('img')?.src || null;
  
  const data = {
    nombre: byId('producto-nombre').value.trim(),
    precio: parseFloat(byId('producto-precio').value),
    marca: byId('producto-marca').value.trim(),
    codigo: byId('producto-codigo').value.trim(),
    categoria_id: parseInt(byId('producto-categoria').value),
    proveedor_id: byId('producto-proveedor').value ? parseInt(byId('producto-proveedor').value) : null,
    stock: parseInt(byId('producto-stock').value),
    stockMinimo: parseInt(byId('producto-stock-min').value),
    sucursal_id: SUCURSAL_ID,
    imagen: imagen
  };
  
  try {
    const url = id ? `/stock/api/productos/${id}/editar/` : '/stock/api/productos/crear/';
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(result.message || 'Producto guardado correctamente', 'success');
      closeModal('producto');
      await cargarProductos();
    } else {
      showNotification(result.error || 'Error al guardar producto', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  }
}

function editarProducto(id) {
  const p = productos.find(x => x.id === id);
  if (!p) return;
  
  byId('producto-id').value = p.id;
  byId('producto-nombre').value = p.nombre;
  byId('producto-precio').value = p.precio;
  byId('producto-marca').value = p.marca;
  byId('producto-codigo').value = p.codigo;
  byId('producto-categoria').value = p.categoria_id || '';
  byId('producto-proveedor').value = p.proveedor_id || '';
  byId('producto-stock').value = p.stock;
  byId('producto-stock-min').value = p.stockMinimo;
  
  if (p.imagen) {
    byId('image-preview').innerHTML = `<img src="${p.imagen}" alt="Preview">`;
  }
  
  byId('modal-producto-title').innerHTML = '<i class="fas fa-box"></i> Editar Producto';
  openModal('producto');
}

async function eliminarProducto(id) {
  if (!confirm('¿Eliminar este producto?')) return;
  
  try {
    const response = await fetch(`/stock/api/productos/${id}/eliminar/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(result.message || 'Producto eliminado', 'success');
      await cargarProductos();
    } else {
      showNotification(result.error || 'Error al eliminar', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  }
}

/* ===== CRUD PROVEEDORES ===== */
async function guardarProveedor(e) {
  e.preventDefault();
  
  const id = byId('proveedor-id').value;
  const data = {
    nombre: byId('proveedor-nombre').value.trim(),
    telefono: byId('proveedor-telefono').value.trim(),
    email: byId('proveedor-email').value.trim(),
    cuit: byId('proveedor-cuit').value.trim()
  };
  
  try {
    const url = id ? `/stock/api/proveedores/${id}/editar/` : '/stock/api/proveedores/crear/';
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(result.message || 'Proveedor guardado correctamente', 'success');
      closeModal('proveedor');
      await cargarProveedores();
    } else {
      showNotification(result.error || 'Error al guardar proveedor', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  }
}

function editarProveedor(id) {
  const p = proveedores.find(x => x.id === id);
  if (!p) return;
  
  byId('proveedor-id').value = p.id;
  byId('proveedor-nombre').value = p.nombre;
  byId('proveedor-telefono').value = p.telefono;
  byId('proveedor-email').value = p.email;
  byId('proveedor-cuit').value = p.cuit;
  
  byId('modal-proveedor-title').innerHTML = '<i class="fas fa-truck"></i> Editar Proveedor';
  openModal('proveedor');
}

async function eliminarProveedor(id) {
  if (!confirm('¿Eliminar este proveedor?')) return;
  
  try {
    const response = await fetch(`/stock/api/proveedores/${id}/eliminar/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(result.message || 'Proveedor eliminado', 'success');
      await cargarProveedores();
    } else {
      showNotification(result.error || 'Error al eliminar', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  }
}

/* ===== CRUD CATEGORÍAS ===== */
async function guardarCategoria(e) {
  e.preventDefault();
  
  const id = byId('categoria-id').value;
  const data = {
    nombre: byId('categoria-nombre').value.trim(),
    descripcion: byId('categoria-descripcion').value.trim()
  };
  
  try {
    const url = id ? `/stock/api/categorias/${id}/editar/` : '/stock/api/categorias/crear/';
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(result.message || 'Categoría guardada correctamente', 'success');
      closeModal('categoria');
      await cargarCategorias();
    } else {
      showNotification(result.error || 'Error al guardar categoría', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  }
}

function editarCategoria(id) {
  const c = categorias.find(x => x.id === id);
  if (!c) return;
  
  byId('categoria-id').value = c.id;
  byId('categoria-nombre').value = c.nombre;
  byId('categoria-descripcion').value = c.descripcion || '';
  
  byId('modal-categoria-title').innerHTML = '<i class="fas fa-tags"></i> Editar Categoría';
  openModal('categoria');
}

async function eliminarCategoria(id) {
  if (!confirm('¿Eliminar esta categoría?')) return;
  
  try {
    const response = await fetch(`/stock/api/categorias/${id}/eliminar/`, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(result.message || 'Categoría eliminada', 'success');
      await cargarCategorias();
    } else {
      showNotification(result.error || 'Error al eliminar', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  }
}

/* ===== INICIALIZACIÓN ===== */
document.addEventListener('DOMContentLoaded', async () => {
  // Event listeners para formularios
  const fProd = byId('form-producto');
  if (fProd) fProd.addEventListener('submit', guardarProducto);
  
  const fProv = byId('form-proveedor');
  if (fProv) fProv.addEventListener('submit', guardarProveedor);
  
  const fCat = byId('form-categoria');
  if (fCat) fCat.addEventListener('submit', guardarCategoria);
  
  // Inicializar gráficos
  initCharts();
  
  // Cargar datos iniciales
  await cargarCategorias();
  await cargarProveedores();
  await cargarProductos();
  
  console.log('✅ Sistema de Gestión de Stock inicializado');
});