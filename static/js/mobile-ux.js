// Mobile UX Enhancements for LysAngels PWA

// ============================================
// 1. SMOOTH SCROLLING
// ============================================
document.documentElement.style.scrollBehavior = 'smooth';

// Smooth scroll pour tous les liens d'ancre
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ============================================
// 2. PULL TO REFRESH
// ============================================
let startY = 0;
let currentY = 0;
let isPulling = false;
const refreshThreshold = 80;

document.addEventListener('touchstart', (e) => {
    if (window.scrollY === 0) {
        startY = e.touches[0].pageY;
        isPulling = true;
    }
}, { passive: true });

document.addEventListener('touchmove', (e) => {
    if (!isPulling) return;
    currentY = e.touches[0].pageY;
    const pullDistance = currentY - startY;
    
    if (pullDistance > 0 && pullDistance < refreshThreshold * 2) {
        // Afficher indicateur de pull-to-refresh
        const indicator = document.getElementById('pull-refresh-indicator');
        if (indicator) {
            indicator.style.opacity = Math.min(pullDistance / refreshThreshold, 1);
            indicator.style.transform = `translateY(${Math.min(pullDistance / 2, refreshThreshold)}px)`;
        }
    }
}, { passive: true });

document.addEventListener('touchend', () => {
    if (!isPulling) return;
    const pullDistance = currentY - startY;
    
    if (pullDistance > refreshThreshold) {
        // Déclencher le rafraîchissement
        window.location.reload();
    } else {
        // Réinitialiser l'indicateur
        const indicator = document.getElementById('pull-refresh-indicator');
        if (indicator) {
            indicator.style.opacity = 0;
            indicator.style.transform = 'translateY(0)';
        }
    }
    
    isPulling = false;
    startY = 0;
    currentY = 0;
});

// ============================================
// 3. LOADING STATES
// ============================================
function showLoadingSpinner(container) {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
        <div class="flex items-center justify-center p-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-lily-purple"></div>
        </div>
    `;
    container.appendChild(spinner);
    return spinner;
}

function hideLoadingSpinner(spinner) {
    if (spinner && spinner.parentNode) {
        spinner.parentNode.removeChild(spinner);
    }
}

// Ajouter un spinner aux formulaires lors de la soumission
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const submitButton = this.querySelector('button[type="submit"]');
        if (submitButton && !submitButton.disabled) {
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <span class="inline-flex items-center">
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Envoi en cours...
                </span>
            `;
        }
    });
});

// ============================================
// 4. TOUCH FEEDBACK
// ============================================
function addTouchFeedback(element) {
    element.addEventListener('touchstart', function() {
        this.style.transform = 'scale(0.98)';
        this.style.opacity = '0.8';
    }, { passive: true });
    
    element.addEventListener('touchend', function() {
        this.style.transform = 'scale(1)';
        this.style.opacity = '1';
    }, { passive: true });
}

// Appliquer le feedback tactile aux boutons et liens
document.querySelectorAll('button, a.btn, .card').forEach(element => {
    element.style.transition = 'transform 0.1s ease, opacity 0.1s ease';
    addTouchFeedback(element);
});

// ============================================
// 5. SKELETON SCREENS
// ============================================
function createSkeletonCard() {
    return `
        <div class="skeleton-card animate-pulse bg-gray-200 rounded-xl p-6">
            <div class="h-48 bg-gray-300 rounded-lg mb-4"></div>
            <div class="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
            <div class="h-4 bg-gray-300 rounded w-1/2"></div>
        </div>
    `;
}

function showSkeletons(container, count = 3) {
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
        container.innerHTML += createSkeletonCard();
    }
}

// ============================================
// 6. LAZY LOADING IMAGES
// ============================================
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            const src = img.dataset.src || img.dataset.lazySrc;
            
            if (src) {
                img.src = src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        }
    });
}, {
    rootMargin: '50px 0px',
    threshold: 0.01
});

// Observer toutes les images avec data-src
document.querySelectorAll('img[data-src], img[data-lazy-src]').forEach(img => {
    imageObserver.observe(img);
});

// ============================================
// 7. ONLINE/OFFLINE STATUS
// ============================================
function updateOnlineStatus() {
    const statusIndicator = document.getElementById('online-status');
    
    if (navigator.onLine) {
        if (statusIndicator) {
            statusIndicator.className = 'hidden';
        }
    } else {
        if (statusIndicator) {
            statusIndicator.className = 'fixed bottom-4 left-4 right-4 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 text-center font-medium';
            statusIndicator.textContent = '⚠️ Vous êtes hors ligne';
        } else {
            // Créer l'indicateur s'il n'existe pas
            const indicator = document.createElement('div');
            indicator.id = 'online-status';
            indicator.className = 'fixed bottom-4 left-4 right-4 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 text-center font-medium';
            indicator.textContent = '⚠️ Vous êtes hors ligne';
            document.body.appendChild(indicator);
        }
    }
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

// Vérifier le statut au chargement
updateOnlineStatus();

// ============================================
// 8. SWIPE GESTURES
// ============================================
class SwipeDetector {
    constructor(element, onSwipeLeft, onSwipeRight) {
        this.element = element;
        this.onSwipeLeft = onSwipeLeft;
        this.onSwipeRight = onSwipeRight;
        this.startX = 0;
        this.startY = 0;
        this.distX = 0;
        this.distY = 0;
        this.threshold = 50;
        this.restraint = 100;
        this.allowedTime = 300;
        this.startTime = 0;
        
        this.element.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        this.element.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: true });
        this.element.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
    }
    
    handleTouchStart(e) {
        const touch = e.touches[0];
        this.startX = touch.pageX;
        this.startY = touch.pageY;
        this.startTime = new Date().getTime();
    }
    
    handleTouchMove(e) {
        const touch = e.touches[0];
        this.distX = touch.pageX - this.startX;
        this.distY = touch.pageY - this.startY;
    }
    
    handleTouchEnd(e) {
        const elapsedTime = new Date().getTime() - this.startTime;
        
        if (elapsedTime <= this.allowedTime) {
            if (Math.abs(this.distX) >= this.threshold && Math.abs(this.distY) <= this.restraint) {
                if (this.distX > 0 && this.onSwipeRight) {
                    this.onSwipeRight();
                } else if (this.distX < 0 && this.onSwipeLeft) {
                    this.onSwipeLeft();
                }
            }
        }
    }
}

// ============================================
// 9. HAPTIC FEEDBACK (si disponible)
// ============================================
function triggerHapticFeedback(type = 'light') {
    if ('vibrate' in navigator) {
        const patterns = {
            light: [10],
            medium: [30],
            heavy: [50],
            success: [10, 30, 10],
            error: [30, 10, 30, 10, 30]
        };
        navigator.vibrate(patterns[type] || patterns.light);
    }
}

// Ajouter haptic aux boutons importants
document.querySelectorAll('button[type="submit"], .btn-primary').forEach(button => {
    button.addEventListener('click', () => triggerHapticFeedback('light'), { passive: true });
});

// ============================================
// 10. PREVENT ZOOM ON DOUBLE TAP (optionnel)
// ============================================
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, { passive: false });

console.log('✨ Mobile UX enhancements loaded');
