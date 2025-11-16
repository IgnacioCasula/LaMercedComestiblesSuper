document.addEventListener('DOMContentLoaded', function() {
    
  // ==================== TOGGLE CONTRASEÑA ====================
  const togglePasswordBtn = document.getElementById('togglePassword');
  const passwordInput = document.getElementById('password');
  
  if (togglePasswordBtn && passwordInput) {
      // Hover sound
      togglePasswordBtn.addEventListener('mouseenter', function() {
          if (window.audioSystem) {
              window.audioSystem.play('hover');
          }
      });
      
      // Toggle visibilidad
      togglePasswordBtn.addEventListener('click', function() {
          if (window.audioSystem) {
              window.audioSystem.play('select');
          }
          
          const type = passwordInput.getAttribute('type');
          const icon = this.querySelector('i');
          
          if (type === 'password') {
              passwordInput.setAttribute('type', 'text');
              icon.classList.remove('fa-eye');
              icon.classList.add('fa-eye-slash');
          } else {
              passwordInput.setAttribute('type', 'password');
              icon.classList.remove('fa-eye-slash');
              icon.classList.add('fa-eye');
          }
      });
  }
  
  // ==================== PREFILL EMAIL RECUPERACIÓN ====================
  const prefillInput = document.getElementById('prefillEmail');
  const usuarioEmailInput = document.getElementById('usuario_email');
  
  if (prefillInput && usuarioEmailInput) {
      function syncEmail() {
          prefillInput.value = usuarioEmailInput.value;
      }
      
      // Sincronizar en múltiples eventos
      ['input', 'change', 'keyup', 'blur'].forEach(function(event) {
          usuarioEmailInput.addEventListener(event, syncEmail);
      });
      
      // Sincronización inicial
      syncEmail();
  }
  
  // ==================== SONIDOS EN FORMULARIOS ====================
  const loginForm = document.querySelector('.login-form');
  if (loginForm) {
      loginForm.addEventListener('submit', function() {
          if (window.audioSystem) {
              window.audioSystem.play('select');
          }
      });
  }
  
  const recoveryForm = document.querySelector('.recovery-section form');
  if (recoveryForm) {
      recoveryForm.addEventListener('submit', function() {
          if (window.audioSystem) {
              window.audioSystem.play('select');
          }
      });
  }
  
  // ==================== SONIDOS EN INPUTS ====================
  const allInputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="email"]');
  allInputs.forEach(function(input) {
      input.addEventListener('focus', function() {
          if (window.audioSystem) {
              window.audioSystem.play('select');
          }
      });
  });
  
  // ==================== SONIDOS PARA MENSAJES ====================
  const errorMessages = document.querySelectorAll('.message.error, .blocked-message');
  if (errorMessages.length > 0) {
      setTimeout(function() {
          if (window.audioSystem) {
              window.audioSystem.play('negative');
          }
      }, 200);
  }
  
  const successMessages = document.querySelectorAll('.message.success');
  if (successMessages.length > 0) {
      setTimeout(function() {
          if (window.audioSystem) {
              window.audioSystem.play('positive');
          }
      }, 200);
  }
  
  // ==================== ANIMACIONES HOVER BOTONES ====================
  const buttons = document.querySelectorAll('.btn-login, .btn-recovery');
  buttons.forEach(function(button) {
      button.addEventListener('mouseenter', function() {
          if (window.audioSystem) {
              window.audioSystem.play('hover');
          }
      });
  });
  
  console.log('Login script cargado correctamente');
});