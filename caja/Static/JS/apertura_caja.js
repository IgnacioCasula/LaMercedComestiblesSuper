// apertura_caja.js
// Anima el div #notification que contiene los mensajes del servidor (messages).

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var notification = document.getElementById('notification');
    if (!notification) return;
    notification.style.opacity = 0;
    notification.style.display = 'block';
    notification.style.transition = 'opacity 400ms ease';
    setTimeout(function () { notification.style.opacity = 1; }, 50);
    setTimeout(function () { notification.style.opacity = 0; }, 3500);
  });
})();