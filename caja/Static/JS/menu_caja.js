// menu_caja.js
// Maneja clicks en el menú: bloquea acciones si no hay apertura y muestra notificaciones animadas.

(function () {
  function showMenuNotification(text, type) {
    var container = document.getElementById('menu-notification');
    if (!container) return;
    container.innerHTML = '';
    var div = document.createElement('div');
    div.className = 'alert alert-' + (type || 'info') + ' shadow';
    div.style.opacity = 0;
    div.style.transition = 'opacity 300ms ease';
    div.innerText = text;
    container.appendChild(div);
    container.style.display = 'block';
    setTimeout(function () { div.style.opacity = 1; }, 50);
    setTimeout(function () {
      div.style.opacity = 0;
      setTimeout(function () { container.style.display = 'none'; container.innerHTML = ''; }, 400);
    }, 3500);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var btnApertura = document.getElementById('boton-apertura');
    var btnCierre  = document.getElementById('boton-cierre');
    var btnVenta   = document.getElementById('boton-venta');

    function handleButton(el) {
      if (!el) return;
      el.addEventListener('click', function (e) {
        var allowed = el.getAttribute('data-allowed');
        var msg = el.getAttribute('data-message');
        var notImpl = el.getAttribute('data-impl');

        if (allowed === 'false') {
          e.preventDefault();
          showMenuNotification(msg || 'Acción no permitida hasta realizar apertura.', 'warning');
          return;
        }

        if (notImpl === 'not-implemented') {
          e.preventDefault();
          showMenuNotification('Funcionalidad pendiente. Pronto estará disponible.', 'info');
          return;
        }
      });
    }

    handleButton(btnApertura);
    handleButton(btnCierre);
    handleButton(btnVenta);

    // pequeño efecto hover
    [btnApertura, btnCierre, btnVenta].forEach(function (el) {
      if (!el) return;
      el.addEventListener('mouseenter', function () {
        el.style.transition = 'transform 0.15s ease';
        el.style.transform = 'scale(1.03)';
      });
      el.addEventListener('mouseleave', function () {
        el.style.transform = 'scale(1)';
      });
    });
  });
})();