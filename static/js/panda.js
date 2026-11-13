// ==========================================================
// Dali_Gastos - Controlador Interactivo de Mascota Panda
// ==========================================================

document.addEventListener('DOMContentLoaded', function() {
  const pandaWrapper = document.getElementById('pandaWrapper');
  const userInput = document.getElementById('username');
  const passInput = document.getElementById('password');
  const togglePassBtn = document.getElementById('togglePassword');
  const eyePupils = document.querySelectorAll('.panda-pupil');
  const pandaHead = document.querySelector('.panda-head');

  if (!pandaWrapper || !userInput || !passInput) return;

  let isPasswordVisible = false;

  // 1. EVENTOS EN CAMPO USUARIO (Mirar y seguir la escritura)
  userInput.addEventListener('focus', function() {
    pandaWrapper.classList.remove('covering-eyes', 'peeking');
    updatePupils(this.value.length);
  });

  userInput.addEventListener('input', function() {
    updatePupils(this.value.length);
  });

  userInput.addEventListener('blur', function() {
    resetPupils();
  });

  function updatePupils(length) {
    // Rango de seguimiento suave de -4px a +4px
    const maxChars = 20;
    const clamped = Math.min(Math.max(length, 0), maxChars);
    const offsetX = ((clamped / maxChars) * 8) - 4; // de -4 a +4
    const offsetY = 2; // mira ligeramente hacia abajo al campo

    eyePupils.forEach(pupil => {
      pupil.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
    });

    if (pandaHead) {
      const tilt = (offsetX / 4) * 2; // inclinación de -2deg a +2deg
      pandaHead.style.transform = `rotate(${tilt}deg)`;
    }
  }

  function resetPupils() {
    eyePupils.forEach(pupil => {
      pupil.style.transform = 'translate(0, 0)';
    });
    if (pandaHead) {
      pandaHead.style.transform = 'rotate(0deg)';
    }
  }

  // 2. EVENTOS EN CAMPO CONTRASEÑA (Taparse los ojos)
  passInput.addEventListener('focus', function() {
    resetPupils();
    if (isPasswordVisible) {
      pandaWrapper.classList.remove('covering-eyes');
      pandaWrapper.classList.add('peeking');
    } else {
      pandaWrapper.classList.remove('peeking');
      pandaWrapper.classList.add('covering-eyes');
    }
  });

  passInput.addEventListener('blur', function() {
    // Si el usuario hace clic en el botón de alternar visibilidad, no quitar de golpe
    setTimeout(() => {
      if (document.activeElement !== passInput && document.activeElement !== togglePassBtn) {
        pandaWrapper.classList.remove('covering-eyes', 'peeking');
        resetPupils();
      }
    }, 120);
  });

  // 3. BOTÓN MOSTRAR/OCULTAR CONTRASEÑA (Espiar)
  if (togglePassBtn) {
    togglePassBtn.addEventListener('click', function(e) {
      e.preventDefault();
      isPasswordVisible = !isPasswordVisible;

      if (isPasswordVisible) {
        passInput.type = 'text';
        togglePassBtn.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
          </svg>
        `;
        togglePassBtn.setAttribute('aria-label', 'Ocultar contraseña');

        // Panda espía
        pandaWrapper.classList.remove('covering-eyes');
        pandaWrapper.classList.add('peeking');
      } else {
        passInput.type = 'password';
        togglePassBtn.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        `;
        togglePassBtn.setAttribute('aria-label', 'Mostrar contraseña');

        // Panda vuelve a taparse si el campo sigue enfocado
        if (document.activeElement === passInput) {
          pandaWrapper.classList.remove('peeking');
          pandaWrapper.classList.add('covering-eyes');
        } else {
          pandaWrapper.classList.remove('peeking', 'covering-eyes');
        }
      }
      passInput.focus();
    });
  }
});
