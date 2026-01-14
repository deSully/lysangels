/**
 * LysAngels - Micro-interactions & Animations
 * Système de toasts, scroll reveals, counters et animations avancées
 */

// ============================================
// TOAST NOTIFICATION SYSTEM
// ============================================

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    init() {
        // Créer le conteneur de toasts s'il n'existe pas
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }
    }

    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = 4000,
            dismissible = true
        } = options;

        // Créer l'élément toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const id = Date.now();
        toast.dataset.toastId = id;

        // Icône selon le type
        const icons = {
            success: `<svg class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`,
            error: `<svg class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`,
            warning: `<svg class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>`,
            info: `<svg class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>`
        };

        toast.innerHTML = `
            ${icons[type]}
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                ${message ? `<div class="toast-message">${message}</div>` : ''}
            </div>
            ${dismissible ? `
                <button class="toast-close" onclick="toastManager.dismiss(${id})">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            ` : ''}
            ${duration > 0 ? '<div class="toast-progress"></div>' : ''}
        `;

        this.container.appendChild(toast);
        this.toasts.push({ id, element: toast });

        // Auto-dismiss après la durée spécifiée
        if (duration > 0) {
            setTimeout(() => this.dismiss(id), duration);
        }

        return id;
    }

    dismiss(id) {
        const toast = this.toasts.find(t => t.id === id);
        if (!toast) return;

        toast.element.classList.add('toast-exit');

        setTimeout(() => {
            toast.element.remove();
            this.toasts = this.toasts.filter(t => t.id !== id);
        }, 300);
    }

    success(title, message, duration) {
        return this.show({ type: 'success', title, message, duration });
    }

    error(title, message, duration) {
        return this.show({ type: 'error', title, message, duration });
    }

    warning(title, message, duration) {
        return this.show({ type: 'warning', title, message, duration });
    }

    info(title, message, duration) {
        return this.show({ type: 'info', title, message, duration });
    }
}

// Instance globale
const toastManager = new ToastManager();


// ============================================
// BUTTON LOADING & SUCCESS STATES
// ============================================

function setButtonLoading(button, loading = true) {
    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.classList.add('btn-loading');
        button.disabled = true;
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    }
}

function setButtonSuccess(button, duration = 2000) {
    const originalText = button.innerHTML;
    button.classList.remove('btn-loading');
    button.classList.add('btn-success-check');
    button.style.backgroundColor = 'var(--color-success)';

    setTimeout(() => {
        button.classList.remove('btn-success-check');
        button.style.backgroundColor = '';
        button.innerHTML = originalText;
        button.disabled = false;
    }, duration);
}


// ============================================
// SCROLL REVEAL ANIMATIONS
// ============================================

class ScrollReveal {
    constructor() {
        this.elements = [];
        this.init();
    }

    init() {
        // Observer les éléments avec les classes scroll-reveal
        const revealElements = document.querySelectorAll('.scroll-reveal, .scroll-reveal-left, .scroll-reveal-right');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    // Optionnel: arrêter d'observer après révélation
                    // observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        revealElements.forEach(el => {
            observer.observe(el);
            this.elements.push(el);
        });
    }
}


// ============================================
// ANIMATED COUNTERS
// ============================================

function animateCounter(element, start, end, duration = 2000) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current).toLocaleString('fr-FR');
    }, 16);
}

// Observer pour détecter quand les compteurs entrent dans le viewport
function initCounters() {
    const counters = document.querySelectorAll('.counter');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.dataset.animated) {
                entry.target.dataset.animated = 'true';
                const end = parseInt(entry.target.dataset.count || entry.target.textContent.replace(/\s/g, ''));
                const duration = parseInt(entry.target.dataset.duration || 2000);
                animateCounter(entry.target, 0, end, duration);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}


// ============================================
// CARD ENTRANCE ANIMATIONS
// ============================================

function initCardAnimations() {
    const cards = document.querySelectorAll('.card-base, .card-image, .card-featured');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting && !entry.target.classList.contains('card-animate-enter')) {
                entry.target.classList.add('card-animate-enter');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    });

    cards.forEach(card => observer.observe(card));
}


// ============================================
// FORM ENHANCEMENTS
// ============================================

function initFormEnhancements() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });

    // Show password toggle
    const passwordToggles = document.querySelectorAll('[data-password-toggle]');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.dataset.passwordToggle;
            const input = document.getElementById(targetId);

            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>
                    </svg>
                `;
            } else {
                input.type = 'password';
                this.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                    </svg>
                `;
            }
        });
    });

    // Character counter for textareas with maxlength
    const textareasWithMax = document.querySelectorAll('textarea[maxlength]');
    textareasWithMax.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        const counter = document.createElement('div');
        counter.className = 'text-sm text-gray-500 mt-1 text-right';
        counter.textContent = `0 / ${maxLength}`;
        textarea.parentNode.appendChild(counter);

        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength} / ${maxLength}`;

            if (currentLength > maxLength * 0.9) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
        });
    });
}


// ============================================
// RIPPLE EFFECT ON BUTTONS
// ============================================

function createRipple(event) {
    const button = event.currentTarget;

    // Ne pas créer de ripple si le bouton est disabled ou en loading
    if (button.disabled || button.classList.contains('btn-loading')) {
        return;
    }

    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    const rect = button.getBoundingClientRect();
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - rect.left - radius}px`;
    circle.style.top = `${event.clientY - rect.top - radius}px`;
    circle.classList.add('ripple');

    const ripple = button.getElementsByClassName('ripple')[0];
    if (ripple) {
        ripple.remove();
    }

    button.appendChild(circle);
}

function initRippleEffect() {
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary, .btn-accent');
    buttons.forEach(button => {
        if (!button.classList.contains('btn-ripple')) {
            button.classList.add('btn-ripple');
        }
        button.addEventListener('click', createRipple);
    });
}


// ============================================
// SMOOTH SCROLL TO ANCHOR
// ============================================

function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            // Ignorer si c'est juste "#"
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}


// ============================================
// IMAGE LAZY LOADING AVEC BLUR EFFECT
// ============================================

function initLazyImages() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('fade-in');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}


// ============================================
// COPY TO CLIPBOARD
// ============================================

async function copyToClipboard(text, button) {
    try {
        await navigator.clipboard.writeText(text);

        // Animation de succès
        const originalContent = button.innerHTML;
        button.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
        `;
        button.classList.add('btn-success-check');

        setTimeout(() => {
            button.innerHTML = originalContent;
            button.classList.remove('btn-success-check');
        }, 2000);

        toastManager.success('Copié !', 'Le texte a été copié dans le presse-papier', 2000);
    } catch (err) {
        toastManager.error('Erreur', 'Impossible de copier le texte', 3000);
    }
}


// ============================================
// BACK TO TOP BUTTON
// ============================================

function initBackToTop() {
    const button = document.createElement('button');
    button.className = 'fixed bottom-8 right-8 w-12 h-12 bg-lily-purple text-white rounded-full shadow-lg hover:bg-purple-dark transition-all duration-300 opacity-0 pointer-events-none z-50';
    button.innerHTML = `
        <svg class="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
        </svg>
    `;
    button.setAttribute('aria-label', 'Retour en haut');

    document.body.appendChild(button);

    // Afficher/masquer selon le scroll
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            button.style.opacity = '1';
            button.style.pointerEvents = 'auto';
        } else {
            button.style.opacity = '0';
            button.style.pointerEvents = 'none';
        }
    });

    // Scroll to top au clic
    button.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}


// ============================================
// ACCESSIBILITY ENHANCEMENTS
// ============================================

function initAccessibility() {
    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-lily-purple focus:text-white focus:rounded-lg';
    skipLink.textContent = 'Aller au contenu principal';
    document.body.insertBefore(skipLink, document.body.firstChild);

    // Focus trap for modals
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const closeBtn = modal.querySelector('[data-modal-close]');
                if (closeBtn) closeBtn.click();
            }
        });
    });

    // Announce dynamic content changes to screen readers
    const ariaLive = document.createElement('div');
    ariaLive.setAttribute('aria-live', 'polite');
    ariaLive.setAttribute('aria-atomic', 'true');
    ariaLive.className = 'sr-only';
    ariaLive.id = 'aria-live-region';
    document.body.appendChild(ariaLive);

    // Add keyboard navigation hints
    document.querySelectorAll('[data-keyboard-hint]').forEach(el => {
        el.setAttribute('aria-label', el.dataset.keyboardHint);
    });
}

// Announce to screen readers
function announceToScreenReader(message) {
    const liveRegion = document.getElementById('aria-live-region');
    if (liveRegion) {
        liveRegion.textContent = message;
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
}


// ============================================
// PERFORMANCE OPTIMIZATIONS
// ============================================

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for scroll events
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Preload critical images
function preloadImages() {
    const criticalImages = document.querySelectorAll('[data-preload]');
    criticalImages.forEach(img => {
        const image = new Image();
        image.src = img.dataset.src || img.src;
    });
}

// Lazy load non-critical resources
function lazyLoadResources() {
    // Defer non-critical CSS
    const deferredStyles = document.querySelectorAll('link[data-defer]');
    deferredStyles.forEach(link => {
        link.rel = 'stylesheet';
    });

    // Defer non-critical scripts
    const deferredScripts = document.querySelectorAll('script[data-defer]');
    deferredScripts.forEach(script => {
        const newScript = document.createElement('script');
        newScript.src = script.dataset.src;
        newScript.defer = true;
        document.body.appendChild(newScript);
    });
}

// Connection-aware loading
function checkConnection() {
    if ('connection' in navigator) {
        // @ts-ignore - Connection API types
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

        if (connection && connection.effectiveType) {
            const effectiveType = connection.effectiveType;

            // Reduce animations on slow connections
            if (effectiveType === 'slow-2g' || effectiveType === '2g') {
                document.body.classList.add('reduce-animations');
            }
        }
    }
}


// ============================================
// OFFLINE SUPPORT
// ============================================

function initOfflineSupport() {
    window.addEventListener('online', () => {
        toastManager.success('Connexion rétablie', 'Vous êtes de nouveau en ligne', 3000);
        announceToScreenReader('Connexion Internet rétablie');
    });

    window.addEventListener('offline', () => {
        toastManager.warning('Hors ligne', 'Vérifiez votre connexion Internet', 5000);
        announceToScreenReader('Connexion Internet perdue');
    });
}


// ============================================
// ERROR TRACKING
// ============================================

function initErrorTracking() {
    // Global error handler
    window.addEventListener('error', (event) => {
        console.error('Error caught:', event.error);

        // User-friendly error message
        if (!navigator.onLine) {
            toastManager.error('Erreur', 'Vérifiez votre connexion Internet', 5000);
        } else {
            toastManager.error('Erreur', 'Une erreur est survenue. Veuillez réessayer.', 5000);
        }
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
    });
}


// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Performance optimizations
    preloadImages();
    checkConnection();

    // Initialize all systems
    new ScrollReveal();
    initCounters();
    initCardAnimations();
    initFormEnhancements();
    initRippleEffect();
    initSmoothScroll();
    initLazyImages();
    initBackToTop();
    initAccessibility();
    initOfflineSupport();
    initErrorTracking();

    // Lazy load non-critical resources after initial load
    setTimeout(() => {
        lazyLoadResources();
    }, 2000);

    console.log('✨ LysAngels initialized with performance & accessibility enhancements');
});


// ============================================
// EXPORT POUR UTILISATION GLOBALE
// ============================================

window.LysAngels = {
    toast: toastManager,
    setButtonLoading,
    setButtonSuccess,
    animateCounter,
    copyToClipboard
};
