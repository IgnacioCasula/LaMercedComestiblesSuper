/**
 * Sistema de Audio Global
 * Maneja todos los efectos de sonido de la aplicación
 */

class AudioSystem {
    constructor() {
        this.sounds = {
            hover: null,        // al-pasar.mp3
            positive: null,     // aviso-positivo.mp3
            negative: null,     // aviso-selec-effect.mp3
            error: null,        // error-desconocido.mp3
            select: null        // selec-effect.mp3
        };
        
        this.initialized = false;
        this.volume = 0.5;
        this.enabled = true;
        
        this.initializeSounds();
        this.setupUnlockListeners();
    }
    
    initializeSounds() {
        // Cargar todos los sonidos
        this.sounds.hover = new Audio('/static/effects/al-pasar.mp3');
        this.sounds.positive = new Audio('/static/effects/aviso-positivo.mp3');
        this.sounds.negative = new Audio('/static/effects/aviso-selec-effect.mp3');
        this.sounds.error = new Audio('/static/effects/error-desconocido.mp3');
        this.sounds.select = new Audio('/static/effects/selec-effect.mp3');
        
        // Configurar volumen inicial
        Object.values(this.sounds).forEach(sound => {
            if (sound) {
                sound.volume = this.volume;
                sound.preload = 'auto';
            }
        });
    }
    
    setupUnlockListeners() {
        // Desbloquear audio en la primera interacción del usuario
        const unlockAudio = () => {
            if (!this.initialized) {
                Object.values(this.sounds).forEach(sound => {
                    if (sound) {
                        sound.play().then(() => sound.pause()).catch(() => {});
                        sound.currentTime = 0;
                    }
                });
                this.initialized = true;
                
                // Remover listeners después de inicializar
                window.removeEventListener('click', unlockAudio);
                window.removeEventListener('touchstart', unlockAudio);
                window.removeEventListener('keydown', unlockAudio);
            }
        };
        
        window.addEventListener('click', unlockAudio);
        window.addEventListener('touchstart', unlockAudio);
        window.addEventListener('keydown', unlockAudio);
    }
    
    play(soundName) {
        if (!this.enabled || !this.sounds[soundName]) return;
        
        try {
            const sound = this.sounds[soundName];
            sound.currentTime = 0;
            sound.play().catch(error => {
                console.log(`Error reproduciendo ${soundName}:`, error);
            });
        } catch (error) {
            console.log(`Error en play(${soundName}):`, error);
        }
    }
    
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        Object.values(this.sounds).forEach(sound => {
            if (sound) sound.volume = this.volume;
        });
    }
    
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }
    
    enable() {
        this.enabled = true;
    }
    
    disable() {
        this.enabled = false;
    }
}

// Crear instancia global
window.audioSystem = new AudioSystem();

/**
 * Función auxiliar para agregar efectos de hover a botones
 * @param {string} selector - Selector CSS para los elementos
 */
function addHoverSounds(selector = 'button, .btn, a.action-btn, .tool-button, .modal-btn') {
    document.querySelectorAll(selector).forEach(element => {
        if (!element.dataset.audioInitialized) {
            element.addEventListener('mouseenter', () => {
                window.audioSystem.play('hover');
            });
            element.dataset.audioInitialized = 'true';
        }
    });
}

/**
 * Función auxiliar para agregar efectos de click a botones
 * @param {string} selector - Selector CSS para los elementos
 */
function addClickSounds(selector = 'button, .btn, a.action-btn, .tool-button, .modal-btn') {
    document.querySelectorAll(selector).forEach(element => {
        if (!element.dataset.audioClickInitialized) {
            element.addEventListener('click', () => {
                window.audioSystem.play('select');
            });
            element.dataset.audioClickInitialized = 'true';
        }
    });
}

/**
 * Inicializar sonidos en elementos dinámicos
 */
function initializeDynamicSounds() {
    addHoverSounds();
    addClickSounds();
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDynamicSounds);
} else {
    initializeDynamicSounds();
}

// Observer para elementos dinámicos
const observer = new MutationObserver(() => {
    initializeDynamicSounds();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});