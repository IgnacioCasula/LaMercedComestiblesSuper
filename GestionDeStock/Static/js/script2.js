/* =========================
   ESTADO (arrays vacíos)
========================= */
let productos = [];     // {id, nombre, precio, marca, codigo, categoria, proveedor, stock, stockMinimo, imagen}
let proveedores = [];   // {id, nombre, telefono, email, cuit}
let categorias = [];    // {id, nombre, descripcion}
let movimientos = [];   // {id, fechaISO, productoId, tipo, cantidad, stockResultante, notas}
let ventas = [];        // SOLO LECTURA AQUÍ  {id, fechaISO, hora, productoId, cantidad, precio_unit, total, metodo, estado}

/* =========================
   NAV / SECCIONES
========================= */
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
    if (sectionId === 'movimientos') cargarMovimientos();
    if (sectionId === 'ventas') cargarVentas();
  });
});

/* =========================
   UTILIDADES
========================= */
function uid(list) {
  return (Math.max(0, ...list.map(x => x.id || 0)) + 1);
}
function byId(id){ return document.getElementById(id); }
function filterTable(tableId, txt) {
  const rows = byId(tableId).getElementsByTagName('tr');
  const t = (txt || '').toLowerCase();
  for (let i = 1; i < rows.length; i++) {
    rows[i].style.display = rows[i].textContent.toLowerCase().includes(t) ? '' : 'none';
  }
}
function fmtMoney(n){ return (Number(n)||0).toLocaleString('es-AR',{style:'currency',currency:'ARS'}); }
function todayISO(){ return new Date().toISOString().slice(0,10); }

/* =========================
   DASHBOARD + CHARTS
========================= */
let salesChart, productsChart;

function initCharts() {
  const salesCtx = document.getElementById('salesChart').getContext('2d');
  const productsCtx = document.getElementById('productsChart').getContext('2d');

  salesChart = new Chart(salesCtx, {
    type: 'line',
    data: { labels: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
      datasets: [{ label:'Ventas Mensuales ($)', data: Array(12).fill(0), borderWidth:2, tension:0.3 }]},
    options: { responsive:true, maintainAspectRatio:false, scales:{ y:{ beginAtZero:true } } }
  });

  productsChart = new Chart(productsCtx, {
    type: 'bar',
    data: { labels: [], datasets: [{ label:'Unidades Vendidas', data: [] }]},
    options: { responsive:true, maintainAspectRatio:false, scales:{ y:{ beginAtZero:true } } }
  });

  updateChartsFromVentas();
}

function updateChartsFromVentas() {
  // 1) Ventas por mes (monto)
  const byMonth = Array(12).fill(0);
  ventas.forEach(v => {
    if (!v?.fechaISO) return;
    const m = new Date(v.fechaISO).getMonth(); // 0..11
    byMonth[m] += Number(v.total)||0;
  });
  salesChart.data.datasets[0].data = byMonth;
  salesChart.update();

  // 2) Productos más vendidos (unidades)
  const qtyByProd = new Map(); // nombre -> cantidad
  ventas.forEach(v => {
    const prod = productos.find(p => p.id === v.productoId);
    const name = prod ? prod.nombre : `Prod ${v.productoId}`;
    qtyByProd.set(name, (qtyByProd.get(name)||0) + (Number(v.cantidad)||0));
  });

  const labels = Array.from(qtyByProd.keys()).slice(0,10);
  const data = labels.map(k => qtyByProd.get(k));
  productsChart.data.labels = labels;
  productsChart.data.datasets[0].data = data;
  productsChart.update();

  // Dashboard cards
  actualizarDashboard();
}

function actualizarDashboard() {
  byId('total-productos').textContent = productos.length;
  byId('total-proveedores').textContent = proveedores.length;

  const stockBajo = productos.filter(p => p.stock < p.stockMinimo).length;
  byId('total-stock-bajo').textContent = stockBajo;

  // ventas hoy (solo suma de ventas del día)
  const hoy = todayISO();
  const totalHoy = ventas
    .filter(v => v.fechaISO === hoy)
    .reduce((acc,v)=> acc + (Number(v.total)||0), 0);
  const ventasHoyEl = byId('ventas-hoy');
  if (ventasHoyEl) ventasHoyEl.textContent = fmtMoney(totalHoy);
}

/* =========================
   LISTADOS
========================= */
function cargarProductos() {
  const tb = byId('productos-body'); tb.innerHTML = '';
  productos.forEach(p => {
    const cat = categorias.find(c=>c.id===p.categoria)?.nombre || '—';
    const prov = proveedores.find(pr=>pr.id===p.proveedor)?.nombre || '—';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>PRD${String(p.id).padStart(3,'0')}</td>
      <td><img src="${p.imagen||'https://via.placeholder.com/50'}" class="product-image" alt="${p.nombre}"></td>
      <td>${p.nombre}</td>
      <td>${fmtMoney(p.precio)}</td>
      <td>${p.marca}</td>
      <td>${p.codigo}</td>
      <td>${cat}</td>
      <td>${prov}</td>
      <td class="${p.stock < p.stockMinimo ? 'stock-bajo':''}">${p.stock}</td>
      <td>
        <button class="btn-icon" onclick="editarProducto(${p.id})"><i class="material-icons">edit</i></button>
        <button class="btn-icon delete" onclick="eliminarProducto(${p.id})"><i class="material-icons">delete</i></button>
      </td>`;
    tb.appendChild(tr);
  });
}
function cargarStockBajo() {
  const tb = byId('stock-bajo-body'); tb.innerHTML = '';
  const low = productos.filter(p => p.stock < p.stockMinimo);
  byId('badge-stock-bajo').textContent = `${low.length} productos`;
  low.forEach(p => {
    const cat = categorias.find(c=>c.id===p.categoria)?.nombre || '—';
    const prov = proveedores.find(pr=>pr.id===p.proveedor)?.nombre || '—';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>PRD${String(p.id).padStart(3,'0')}</td>
      <td><img src="${p.imagen||'https://via.placeholder.com/50'}" class="product-image" alt="${p.nombre}"></td>
      <td>${p.nombre}</td>
      <td>${fmtMoney(p.precio)}</td>
      <td>${p.marca}</td>
      <td>${p.codigo}</td>
      <td>${cat}</td>
      <td>${prov}</td>
      <td class="stock-bajo">${p.stock}</td>
      <td>${p.stockMinimo}</td>
      <td>
        <button class="btn-icon" onclick="solicitarProducto(${p.id})"><i class="material-icons">local_shipping</i></button>
        <button class="btn-icon" onclick="editarProducto(${p.id})"><i class="material-icons">edit</i></button>
      </td>`;
    tb.appendChild(tr);
  });
}
function cargarProveedores() {
  const tb = byId('proveedores-body'); tb.innerHTML = '';
  proveedores.forEach(pr => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>PROV${String(pr.id).padStart(3,'0')}</td>
      <td>${pr.nombre}</td>
      <td>${pr.telefono}</td>
      <td>${pr.email}</td>
      <td>${pr.cuit}</td>
      <td>
        <button class="btn-icon" onclick="editarProveedor(${pr.id})"><i class="material-icons">edit</i></button>
        <button class="btn-icon delete" onclick="eliminarProveedor(${pr.id})"><i class="material-icons">delete</i></button>
      </td>`;
    tb.appendChild(tr);
  });
}
function cargarCategorias() {
  const tb = byId('categorias-body'); tb.innerHTML = '';
  categorias.forEach(c => {
    const count = productos.filter(p => p.categoria === c.id).length;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>CAT${String(c.id).padStart(3,'0')}</td>
      <td>${c.nombre}</td>
      <td>${c.descripcion||'—'}</td>
      <td>${count}</td>
      <td>
        <button class="btn-icon" onclick="editarCategoria(${c.id})"><i class="material-icons">edit</i></button>
        <button class="btn-icon delete" onclick="eliminarCategoria(${c.id})"><i class="material-icons">delete</i></button>
      </td>`;
    tb.appendChild(tr);
  });
}
function cargarMovimientos() {
  const tb = byId('movimientos-body'); tb.innerHTML = '';
  movimientos
    .slice()
    .sort((a,b)=> new Date(b.fechaISO) - new Date(a.fechaISO))
    .forEach(m => {
      const prod = productos.find(p=>p.id===m.productoId);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>MV${String(m.id).padStart(4,'0')}</td>
        <td>${m.fechaISO}</td>
        <td>${prod ? prod.nombre : ('ID '+m.productoId)}</td>
        <td>${m.tipo}</td>
        <td>${m.cantidad}</td>
        <td>${m.stockResultante}</td>
        <td>${m.notas || '—'}</td>`;
      tb.appendChild(tr);
    });
}
function cargarVentas() {
  const tb = byId('ventas-body'); tb.innerHTML = '';
  ventas
    .slice()
    .sort((a,b)=> new Date(b.fechaISO) - new Date(a.fechaISO))
    .forEach(v => {
      const prod = productos.find(p=>p.id===v.productoId);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>V${String(v.id).padStart(5,'0')}</td>
        <td>${v.fechaISO || '—'}</td>
        <td>${v.hora || '—'}</td>
        <td>${prod ? prod.nombre : ('ID '+v.productoId)}</td>
        <td>${v.cantidad}</td>
        <td>${fmtMoney(v.precio_unit)}</td>
        <td>${fmtMoney(v.total)}</td>
        <td>${v.metodo || '—'}</td>
        <td>${v.estado || '—'}</td>`;
      tb.appendChild(tr);
    });
}

/* =========================
   SELECTS DEPENDIENTES
========================= */
function llenarSelectsProducto() {
  const selCat = byId('producto-categoria');
  const selProv = byId('producto-proveedor');
  selCat.innerHTML = '<option value="">Seleccionar categoría</option>';
  selProv.innerHTML = '<option value="">Seleccionar proveedor</option>';
  categorias.forEach(c => {
    const o = document.createElement('option'); o.value = c.id; o.textContent = c.nombre; selCat.appendChild(o);
  });
  proveedores.forEach(p => {
    const o = document.createElement('option'); o.value = p.id; o.textContent = p.nombre; selProv.appendChild(o);
  });
}
function llenarSelectMovimiento() {
  const sel = byId('mov-producto');
  sel.innerHTML = '<option value="">Seleccionar producto</option>';
  productos.forEach(p => {
    const o = document.createElement('option');
    o.value = p.id; o.textContent = `${p.nombre} (Stock: ${p.stock})`;
    sel.appendChild(o);
  });
}

/* =========================
   CRUD – PRODUCTOS
========================= */
function editarProducto(id) {
  const p = productos.find(x=>x.id===id); if(!p) return;
  byId('producto-id').value = p.id;
  byId('producto-nombre').value = p.nombre;
  byId('producto-precio').value = p.precio;
  byId('producto-marca').value = p.marca;
  byId('producto-codigo').value = p.codigo;
  byId('producto-categoria').value = p.categoria || '';
  byId('producto-proveedor').value = p.proveedor || '';
  byId('producto-stock').value = p.stock;
  byId('producto-stock-min').value = p.stockMinimo;
  byId('modal-producto-title').textContent = 'Editar Producto';
  openModal('producto');
}
function eliminarProducto(id) {
  if (!confirm('¿Eliminar producto?')) return;
  productos = productos.filter(p=>p.id!==id);
  cargarProductos(); cargarStockBajo(); llenarSelectMovimiento(); actualizarDashboard();
  updateChartsFromVentas();
}
function guardarProducto() {
  const id = byId('producto-id').value;
  const obj = {
    nombre: byId('producto-nombre').value.trim(),
    precio: parseFloat(byId('producto-precio').value || 0),
    marca: byId('producto-marca').value.trim(),
    codigo: byId('producto-codigo').value.trim(),
    categoria: parseInt(byId('producto-categoria').value || 0),
    proveedor: parseInt(byId('producto-proveedor').value || 0),
    stock: parseInt(byId('producto-stock').value || 0),
    stockMinimo: parseInt(byId('producto-stock-min').value || 0),
    imagen: null
  };
  if (id) {
    const i = productos.findIndex(p=>p.id==id);
    if (i>-1) productos[i] = { ...productos[i], ...obj };
    alert('Producto actualizado');
  } else {
    obj.id = uid(productos);
    productos.push(obj);
    alert('Producto creado');
  }
  closeModal('producto');
  cargarProductos(); cargarStockBajo(); llenarSelectMovimiento(); actualizarDashboard();
}

/* =========================
   CRUD – PROVEEDORES / CATEGORÍAS
========================= */
function editarProveedor(id){
  const p = proveedores.find(x=>x.id===id); if(!p) return;
  byId('proveedor-id').value=p.id;
  byId('proveedor-nombre').value=p.nombre;
  byId('proveedor-telefono').value=p.telefono;
  byId('proveedor-email').value=p.email;
  byId('proveedor-cuit').value=p.cuit;
  byId('modal-proveedor-title').textContent='Editar Proveedor';
  openModal('proveedor');
}
function eliminarProveedor(id){
  if (productos.some(p=>p.proveedor===id)) return alert('No se puede eliminar: tiene productos asociados.');
  if (!confirm('¿Eliminar proveedor?')) return;
  proveedores = proveedores.filter(p=>p.id!==id);
  cargarProveedores(); llenarSelectsProducto(); actualizarDashboard();
}
function guardarProveedor(){
  const id = byId('proveedor-id').value;
  const obj = {
    nombre: byId('proveedor-nombre').value.trim(),
    telefono: byId('proveedor-telefono').value.trim(),
    email: byId('proveedor-email').value.trim(),
    cuit: byId('proveedor-cuit').value.trim(),
  };
  if (id){
    const i = proveedores.findIndex(p=>p.id==id);
    if(i>-1) proveedores[i] = { ...proveedores[i], ...obj };
    alert('Proveedor actualizado');
  } else {
    obj.id = uid(proveedores);
    proveedores.push(obj);
    alert('Proveedor creado');
  }
  closeModal('proveedor'); cargarProveedores(); llenarSelectsProducto(); actualizarDashboard();
}

function editarCategoria(id){
  const c = categorias.find(x=>x.id===id); if(!c) return;
  byId('categoria-id').value=c.id;
  byId('categoria-nombre').value=c.nombre;
  byId('categoria-descripcion').value=c.descripcion||'';
  byId('modal-categoria-title').textContent='Editar Categoría';
  openModal('categoria');
}
function eliminarCategoria(id){
  if (productos.some(p=>p.categoria===id)) return alert('No se puede eliminar: tiene productos asociados.');
  if (!confirm('¿Eliminar categoría?')) return;
  categorias = categorias.filter(c=>c.id!==id);
  cargarCategorias(); llenarSelectsProducto();
}
function guardarCategoria(){
  const id = byId('categoria-id').value;
  const obj = {
    nombre: byId('categoria-nombre').value.trim(),
    descripcion: byId('categoria-descripcion').value.trim()
  };
  if (id){
    const i = categorias.findIndex(c=>c.id==id);
    if(i>-1) categorias[i] = { ...categorias[i], ...obj };
    alert('Categoría actualizada');
  } else {
    obj.id = uid(categorias);
    categorias.push(obj);
    alert('Categoría creada');
  }
  closeModal('categoria'); cargarCategorias(); llenarSelectsProducto();
}

/* =========================
   MOVIMIENTOS – Alta y efecto en stock
========================= */
function guardarMovimiento(){
  const prodId = parseInt(byId('mov-producto').value || 0);
  const tipo = byId('mov-tipo').value;
  const cant = parseInt(byId('mov-cantidad').value || 0);
  const fecha = byId('mov-fecha').value || todayISO();
  const notas = byId('mov-notas').value.trim();

  if (!prodId || !tipo || cant<=0) return alert('Completa producto, tipo y cantidad.');
  const p = productos.find(x=>x.id===prodId); if(!p) return alert('Producto no encontrado');

  let nuevoStock = p.stock;
  if (tipo === 'Entrada') nuevoStock += cant;
  if (tipo === 'Salida') {
    if (cant > p.stock) return alert('No hay stock suficiente');
    nuevoStock -= cant;
  }
  p.stock = nuevoStock;

  const reg = {
    id: uid(movimientos),
    fechaISO: fecha,
    productoId: prodId,
    tipo, cantidad: cant,
    stockResultante: nuevoStock,
    notas
  };
  movimientos.push(reg);

  closeModal('movimiento');
  cargarMovimientos(); cargarProductos(); cargarStockBajo(); llenarSelectMovimiento(); actualizarDashboard();
}

/* =========================
   VENTAS – SOLO LECTURA
========================= */
function setVentas(dataArray){
  // ÚSALO cuando traigas ventas desde tu backend con fetch/AJAX
  ventas = Array.isArray(dataArray) ? dataArray : [];
  cargarVentas();
  updateChartsFromVentas();
}

/* =========================
   MODALES / OTROS
========================= */
function openModal(type){
  byId(`modal-${type}`).style.display = 'block';
  if (type==='producto') { byId('modal-producto-title').textContent='Nuevo Producto'; byId('producto-id').value=''; }
  if (type==='proveedor') { byId('modal-proveedor-title').textContent='Nuevo Proveedor'; byId('proveedor-id').value=''; }
  if (type==='categoria') { byId('modal-categoria-title').textContent='Nueva Categoría'; byId('categoria-id').value=''; }
  if (type==='movimiento') {
    byId('modal-movimiento-title').textContent='Nuevo Movimiento';
    byId('form-movimiento').reset();
    byId('mov-fecha').value = todayISO();
    llenarSelectMovimiento();
  }
}
function closeModal(type){
  byId(`modal-${type}`).style.display = 'none';
}
window.onclick = function(e){
  document.querySelectorAll('.modal').forEach(m=>{
    if (e.target === m) m.style.display='none';
  });
};

/* =========================
   INIT
========================= */
document.addEventListener('DOMContentLoaded', () => {
  // Listeners de formularios
  const fProd = byId('form-producto'); if (fProd) fProd.addEventListener('submit', e=>{e.preventDefault(); guardarProducto();});
  const fProv = byId('form-proveedor'); if (fProv) fProv.addEventListener('submit', e=>{e.preventDefault(); guardarProveedor();});
  const fCat  = byId('form-categoria'); if (fCat) fCat.addEventListener('submit', e=>{e.preventDefault(); guardarCategoria();});
  const fMov  = byId('form-movimiento'); if (fMov) fMov.addEventListener('submit', e=>{e.preventDefault(); guardarMovimiento();});

  initCharts();
  actualizarDashboard();
  llenarSelectsProducto();

  // TIP: cuando tengas ventas reales, llama:
  // setVentas([...]);
});

/* Extras */
function solicitarProducto(id){ alert('Solicitud de reposición enviada para el producto ID: '+id); }
