document.addEventListener('DOMContentLoaded', function () {
  // ===== TOGGLE DE CONTRASEÑA =====
  var toggle = document.getElementById('togglePwd');
  var pwd = document.getElementById('password');
  var eyeIcon = document.getElementById('eyeIcon');
  
  if (toggle && pwd && eyeIcon) {
    toggle.addEventListener('mouseenter', () => {
      if (window.audioSystem) window.audioSystem.play('hover');
    });
    
    toggle.addEventListener('click', function () {
      if (window.audioSystem) window.audioSystem.play('select');
      var isPassword = pwd.getAttribute('type') === 'password';
      pwd.setAttribute('type', isPassword ? 'text' : 'password');
      
      // Cambiar ícono
      if (isPassword) {
        eyeIcon.classList.remove('fa-eye');
        eyeIcon.classList.add('fa-eye-slash');
      } else {
        eyeIcon.classList.remove('fa-eye-slash');
        eyeIcon.classList.add('fa-eye');
      }
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
});