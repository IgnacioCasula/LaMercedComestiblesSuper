document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.getElementById('togglePwd');
  var pwd = document.getElementById('password');
  if (toggle && pwd) {
    toggle.addEventListener('click', function () {
      var isPassword = pwd.getAttribute('type') === 'password';
      pwd.setAttribute('type', isPassword ? 'text' : 'password');
      toggle.src = toggle.src.includes('eyeX') ? toggle.src.replace('eyeX', 'eye') : toggle.src.replace('eye', 'eyeX');
    });
  }

  // Prefill hidden email for recovery from current visible input
  var prefill = document.getElementById('prefillEmail');
  var userInput = document.querySelector('input[name="usuario_email"]');
  if (prefill && userInput) {
    var sync = function(){ prefill.value = userInput.value; };
    ['input','change','keyup','blur'].forEach(function(evt){ userInput.addEventListener(evt, sync); });
    sync();
  }

  // Inicio page behavior
  var panel = document.getElementById('greeting-panel');
  var audioShine = document.getElementById('audio-shine');
  var audioSwipe = document.getElementById('audio-swipe');
  var logoutBtn = document.getElementById('logout-btn');
  var logoutModal = document.getElementById('logout-modal');
  var logoutConfirm = document.getElementById('logout-confirm');

  if (panel) {
    if (audioShine) { try { audioShine.currentTime = 0; audioShine.play(); } catch(e){} }
    var lastIsShrunk = false;
    var ticking = false;
    var onScroll = function(){
      var y = window.scrollY || window.pageYOffset || 0;
      var shouldShrink = y > 30;
      if (shouldShrink !== lastIsShrunk) {
        panel.classList.toggle('shrunk', shouldShrink);
        if (shouldShrink) {
          if (audioSwipe) { try { audioSwipe.currentTime = 0; audioSwipe.play(); } catch(e){} }
          var handler = function(){
            panel.removeEventListener('transitionend', handler);
            panel.classList.add('shake');
            setTimeout(function(){ panel.classList.remove('shake'); }, 450);
          };
          panel.addEventListener('transitionend', handler);
        } else {
          if (audioShine) { try { audioShine.currentTime = 0; audioShine.play(); } catch(e){} }
        }
        lastIsShrunk = shouldShrink;
      }
      ticking = false;
    };
    window.addEventListener('scroll', function(){
      if (!ticking) {
        window.requestAnimationFrame(onScroll);
        ticking = true;
      }
    }, { passive:true });
  }

  if (logoutBtn) {
    var doLogout = function(){
      fetch('/logout/', { method:'POST', headers:{ 'X-Requested-With':'fetch' } })
        .then(function(){ window.location.href = '/login/'; })
        .catch(function(){ window.location.href = '/login/'; });
    };
    logoutBtn.addEventListener('click', function(){
      if (logoutModal && typeof logoutModal.showModal === 'function') {
        logoutModal.showModal();
      } else {
        if (confirm('¿Seguro que deseas cerrar sesión?')) doLogout();
      }
    });
    if (logoutConfirm) {
      logoutConfirm.addEventListener('click', function(e){ e.preventDefault(); doLogout(); });
    }
  }
});



