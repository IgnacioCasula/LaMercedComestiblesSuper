document.addEventListener('DOMContentLoaded', function () {
  // ===== TOGGLE DE CONTRASEÑA =====
  var toggle = document.getElementById('togglePwd');
  var pwd = document.getElementById('password');
  if (toggle && pwd) {
    toggle.addEventListener('mouseenter', () => {
      if (window.audioSystem) window.audioSystem.play('hover');
    });
    toggle.addEventListener('click', function () {
      if (window.audioSystem) window.audioSystem.play('select');
      var isPassword = pwd.getAttribute('type') === 'password';
      pwd.setAttribute('type', isPassword ? 'text' : 'password');
      toggle.src = toggle.src.includes('eyeX') ? toggle.src.replace('eyeX', 'eye') : toggle.src.replace('eye', 'eyeX');
    });
  }

  // ===== PREFILL EMAIL PARA RECUPERACIÓN =====
  var prefill = document.getElementById('prefillEmail');
  var userInput = document.querySelector('input[name="usuario_email"]');
  if (prefill && userInput) {
    var sync = function(){ prefill.value = userInput.value; };
    ['input','change','keyup','blur'].forEach(function(evt){ userInput.addEventListener(evt, sync); });
    sync();
  }

  // ===== SONIDOS EN BOTONES =====
  var loginForm = document.querySelector('form[action*="login"]');
  if (loginForm) {
    loginForm.addEventListener('submit', function() {
      if (window.audioSystem) window.audioSystem.play('select');
    });
  }

  var recoverForm = document.querySelector('form[action*="enviar_codigo"]');
  if (recoverForm) {
    recoverForm.addEventListener('submit', function() {
      if (window.audioSystem) window.audioSystem.play('select');
    });
  }

  var reenviarForm = document.querySelector('form[action*="reenviar_codigo"]');
  if (reenviarForm) {
    reenviarForm.addEventListener('submit', function() {
      if (window.audioSystem) window.audioSystem.play('select');
    });
  }

  // ===== SONIDOS EN MENSAJES =====
  var errorMessages = document.querySelectorAll('.msgs li.error, .warn');
  if (errorMessages.length > 0) {
    setTimeout(() => {
      if (window.audioSystem) window.audioSystem.play('negative');
    }, 200);
  }

  var successMessages = document.querySelectorAll('.msgs li.success');
  if (successMessages.length > 0) {
    setTimeout(() => {
      if (window.audioSystem) window.audioSystem.play('positive');
    }, 200);
  }

  // ===== SONIDOS EN INPUTS =====
  var inputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="email"], select');
  inputs.forEach(function(input) {
    input.addEventListener('focus', function() {
      if (window.audioSystem) window.audioSystem.play('select');
    });
  });

  // ===== INICIO PAGE BEHAVIOR =====
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
    logoutBtn.addEventListener('mouseenter', () => {
      if (window.audioSystem) window.audioSystem.play('hover');
    });
    
    var doLogout = function(){
      if (window.audioSystem) window.audioSystem.play('negative');
      fetch('/logout/', { method:'POST', headers:{ 'X-Requested-With':'fetch' } })
        .then(function(){ window.location.href = '/login/'; })
        .catch(function(){ window.location.href = '/login/'; });
    };
    
    logoutBtn.addEventListener('click', function(){
      if (window.audioSystem) window.audioSystem.play('select');
      if (logoutModal && typeof logoutModal.showModal === 'function') {
        logoutModal.showModal();
      } else {
        if (confirm('¿Seguro que deseas cerrar sesión?')) doLogout();
      }
    });
    
    if (logoutConfirm) {
      logoutConfirm.addEventListener('mouseenter', () => {
        if (window.audioSystem) window.audioSystem.play('hover');
      });
      logoutConfirm.addEventListener('click', function(e){ 
        e.preventDefault(); 
        doLogout(); 
      });
    }
    
    // Botón cancelar del modal
    var logoutCancelBtn = logoutModal ? logoutModal.querySelector('button[value="cancel"]') : null;
    if (logoutCancelBtn) {
      logoutCancelBtn.addEventListener('mouseenter', () => {
        if (window.audioSystem) window.audioSystem.play('hover');
      });
      logoutCancelBtn.addEventListener('click', () => {
        if (window.audioSystem) window.audioSystem.play('select');
      });
    }
  }
});