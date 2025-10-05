
/* ==========================================================================
   Salon Booking System - Ultra Modern JavaScript
   Advanced animations, micro-interactions, and modern UX
   ========================================================================== */

// Check if running as PWA and redirect to client booking link
(function checkPWARedirect() {
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                        window.navigator.standalone === true;
    
    if (isStandalone) {
        const savedToken = localStorage.getItem('client_booking_token');
        const currentPath = window.location.pathname;
        
        // Validar se o token existe, não está vazio e parece um UUID válido
        const isValidToken = savedToken && 
                            savedToken.trim() !== '' && 
                            savedToken.length > 20 && 
                            savedToken.includes('-');
        
        // Se tem token válido e não está na página de agendamento, redirecionar
        if (isValidToken && !currentPath.includes('/appointments/booking/')) {
            console.log('🔄 PWA detectado - Redirecionando para link do cliente');
            window.location.href = `/appointments/booking/${savedToken}/`;
        }
    }
})();

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Salon Booking System - Ultra Modern Frontend Initialized');
    
    // Initialize all modern components
    initializeThemeToggle();
    initializeFormEnhancements();
    initializeAdvancedAnimations();
    initializeHTMXExtensions();
    initializePWA();
    initializePerformanceOptimizations();
    initializeMicroInteractions();
    initializeParticleEffects();
});

/* ==========================================================================
   Theme Management with Modern Transitions
   ========================================================================== */

function initializeThemeToggle() {
    // Forçar modo escuro permanente
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
    
    console.log('🌙 Theme system initialized:', 'dark');
}

// Função simplificada - sempre modo escuro
function setTheme(theme = 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    console.log('✨ Theme changed to:', 'dark');
}

/* ==========================================================================
   Advanced Form Enhancements
   ========================================================================== */

function initializeFormEnhancements() {
    // Enhanced password toggle with animation
    window.togglePassword = function(fieldId = 'id_password', iconId = 'togglePasswordIcon') {
        const passwordField = document.getElementById(fieldId);
        const toggleIcon = document.getElementById(iconId);
        const button = toggleIcon?.parentElement;
        
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            toggleIcon.classList.remove('fa-eye');
            toggleIcon.classList.add('fa-eye-slash');
            button?.classList.add('pulse-glow');
        } else {
            passwordField.type = 'password';
            toggleIcon.classList.remove('fa-eye-slash');
            toggleIcon.classList.add('fa-eye');
            button?.classList.remove('pulse-glow');
        }
        
        // Add bounce animation
        toggleIcon?.style.setProperty('animation', 'bounce 0.6s ease-in-out');
        setTimeout(() => {
            toggleIcon?.style.removeProperty('animation');
        }, 600);
    };
    
    // Real-time validation with modern UI
    initializeRealTimeValidation();
    
    // Form submission with loading states
    enhanceFormSubmissions();
    
    // Add floating labels enhancement
    enhanceFloatingLabels();
    
    console.log('📝 Modern form enhancements initialized');
}

function initializeRealTimeValidation() {
    const forms = document.querySelectorAll('form[data-validate="true"]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', debounce((e) => validateField(e.target), 300));
            input.addEventListener('blur', (e) => validateField(e.target));
            input.addEventListener('focus', (e) => addFocusGlow(e.target));
            
            if (!input.nextElementSibling?.classList.contains('field-validation')) {
                const feedback = document.createElement('div');
                feedback.className = 'field-validation';
                input.parentNode.insertBefore(feedback, input.nextSibling);
            }
        });
    });
}

function addFocusGlow(field) {
    field.style.boxShadow = '0 0 30px rgba(102, 126, 234, 0.3)';
    field.style.transform = 'translateY(-2px)';
}

function validateField(field) {
    try {
        const feedback = field.nextElementSibling;
        if (!feedback?.classList.contains('field-validation')) return;
        
        const value = field.value.trim();
        const fieldType = field.type;
        const isRequired = field.hasAttribute('required');
        
        field.classList.remove('is-valid', 'is-invalid');
        feedback.className = 'field-validation checking';
        
        let isValid = true;
        let message = '';
        
        if (isRequired && !value) {
            isValid = false;
            message = 'Este campo é obrigatório';
        } else if (value) {
            switch (fieldType) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        isValid = false;
                        message = '✗ Digite um email válido';
                    } else {
                        message = '✓ Email válido';
                    }
                    break;
                    
                case 'password':
                    if (value.length < 8) {
                        isValid = false;
                        message = '✗ Mínimo 8 caracteres';
                    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
                        isValid = false;
                        message = '✗ Precisa de maiúscula, minúscula e número';
                    } else {
                        message = '✓ Senha forte';
                    }
                    break;
                    
                case 'tel':
                    const phoneRegex = /^[\d\s\-\(\)\+]+$/;
                    if (!phoneRegex.test(value) || value.length < 10) {
                        isValid = false;
                        message = '✗ Telefone inválido';
                    } else {
                        message = '✓ Telefone válido';
                    }
                    break;
                    
                default:
                    if (value.length < 2) {
                        isValid = false;
                        message = '✗ Muito curto';
                    } else {
                        message = '✓ Válido';
                    }
            }
        }
        
        setTimeout(() => {
            try {
                field.classList.add(isValid ? 'is-valid' : 'is-invalid');
                feedback.className = `field-validation ${isValid ? 'valid' : 'invalid'}`;
                feedback.innerHTML = `
                    <span class="validation-icon">
                        <i class="fas fa-${isValid ? 'check-circle' : 'exclamation-circle'}"></i>
                    </span>
                    <span>${message}</span>
                `;
                
                // Add animation to feedback
                feedback.style.animation = 'slideInUp 0.3s ease-out';
            } catch (error) {
                console.warn('Validation display error:', error);
            }
        }, 100);
    } catch (error) {
        console.warn('Field validation error:', error);
    }
}

function enhanceFloatingLabels() {
    const floatingInputs = document.querySelectorAll('.form-floating input, .form-floating textarea');
    
    floatingInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
}

function enhanceFormSubmissions() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                
                // Modern loading animation
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    Processando...
                `;
                submitBtn.classList.add('loading-btn');
                
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                    submitBtn.classList.remove('loading-btn');
                }, 3000);
            }
        });
    });
}

/* ==========================================================================
   Advanced Animations and Micro-interactions
   ========================================================================== */

function initializeAdvancedAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Add staggered animation for multiple elements
                const index = Array.from(entry.target.parentNode.children).indexOf(entry.target);
                entry.target.style.animationDelay = `${index * 0.1}s`;
            }
        });
    }, observerOptions);
    
    // Observe cards and other elements
    const animatedElements = document.querySelectorAll('.card, .feature-card, .btn, .alert');
    animatedElements.forEach(el => {
        el.classList.add('animate-on-scroll');
        observer.observe(el);
    });
    
    // Add floating animation to certain elements
    const floatingElements = document.querySelectorAll('.card-header i, .feature-card .display-4 i');
    floatingElements.forEach(el => {
        el.classList.add('floating');
    });
    
    console.log('🎭 Advanced animations initialized');
}

function initializeMicroInteractions() {
    // Ripple effect for buttons
    const buttons = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            createRippleEffect(this, e);
        });
    });
    
    // Hover effects for cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
            this.style.boxShadow = '0 25px 80px rgba(0,0,0,0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
    
    // Magnetic effect for important buttons
    const magneticButtons = document.querySelectorAll('.btn-primary, .btn-success');
    magneticButtons.forEach(button => {
        button.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            this.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px) scale(1.05)`;
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    console.log('🎯 Micro-interactions initialized');
}

function createRippleEffect(element, event) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = (event?.clientX || rect.width / 2) - rect.left - size / 2;
    const y = (event?.clientY || rect.height / 2) - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
        z-index: 1000;
    `;
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

/* ==========================================================================
   Particle Effects
   ========================================================================== */

function initializeParticleEffects() {
    // Create particle container
    const particleContainer = document.createElement('div');
    particleContainer.id = 'particle-container';
    particleContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    `;
    document.body.appendChild(particleContainer);
    
    // Create floating particles
    createFloatingParticles();
    
    console.log('✨ Particle effects initialized');
}

function createFloatingParticles() {
    try {
        const container = document.getElementById('particle-container');
        if (!container) return;
        
        const particleCount = window.innerWidth > 768 ? 30 : 15;
        
        // Criar partículas em lote para evitar layout shifts
        const fragment = document.createDocumentFragment();
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'floating-particle';
            particle.style.cssText = `
                position: absolute;
                width: ${Math.random() * 3 + 1}px;
                height: ${Math.random() * 3 + 1}px;
                background: rgba(102, 126, 234, ${Math.random() * 0.2 + 0.05});
                border-radius: 50%;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: floatParticle ${Math.random() * 25 + 15}s linear infinite;
                animation-delay: ${Math.random() * 25}s;
                will-change: transform;
            `;
            fragment.appendChild(particle);
        }
        
        container.appendChild(fragment);
    } catch (error) {
        console.warn('Particle creation error:', error);
    }
}

function triggerThemeChangeParticles() {
    const container = document.getElementById('particle-container');
    if (!container) return;
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: absolute;
            width: 6px;
            height: 6px;
            background: #667eea;
            border-radius: 50%;
            left: 50%;
            top: 50%;
            animation: explodeParticle 1s ease-out forwards;
            animation-delay: ${i * 0.05}s;
            transform: rotate(${i * 18}deg);
        `;
        container.appendChild(particle);
        
        setTimeout(() => particle.remove(), 1000);
    }
}

/* ==========================================================================
   HTMX Extensions with Modern UX
   ========================================================================== */

function initializeHTMXExtensions() {
    if (typeof htmx !== 'undefined') {
        // Modern loading states
        document.body.addEventListener('htmx:beforeRequest', function(event) {
            const element = event.target;
            element.classList.add('loading');
            
            // Add modern spinner
            if (element.tagName === 'BUTTON') {
                const originalText = element.innerHTML;
                element.dataset.originalText = originalText;
                element.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    Carregando...
                `;
            }
            
            // Add loading overlay for forms
            if (element.tagName === 'FORM') {
                const overlay = document.createElement('div');
                overlay.className = 'loading-overlay';
                overlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.8);
                    backdrop-filter: blur(5px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    border-radius: inherit;
                `;
                overlay.innerHTML = `
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                `;
                element.style.position = 'relative';
                element.appendChild(overlay);
            }
        });
        
        document.body.addEventListener('htmx:afterRequest', function(event) {
            const element = event.target;
            element.classList.remove('loading');
            
            // Restore button text
            if (element.tagName === 'BUTTON' && element.dataset.originalText) {
                element.innerHTML = element.dataset.originalText;
                delete element.dataset.originalText;
            }
            
            // Remove loading overlay
            const overlay = element.querySelector('.loading-overlay');
            if (overlay) {
                overlay.remove();
            }
            
            // Add success animation
            element.style.animation = 'pulse 0.3s ease-in-out';
            setTimeout(() => {
                element.style.animation = '';
            }, 300);
        });
        
        // Handle errors with modern notifications
        document.body.addEventListener('htmx:responseError', function(event) {
            console.error('HTMX Error:', event.detail);
            showModernNotification('Ops! Algo deu errado. Tente novamente.', 'error');
        });
        
        console.log('🔄 Modern HTMX extensions initialized');
    }
}

/* ==========================================================================
   PWA Enhancements
   ========================================================================== */

function initializePWA() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js')
                .then((registration) => {
                    console.log('🔧 SW registered: ', registration);
                })
                .catch((registrationError) => {
                    console.log('❌ SW registration failed: ', registrationError);
                });
        });
    }
    
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        showModernInstallPromotion();
    });
    
    window.installPWA = function() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('✅ User accepted PWA install');
                    hideInstallPromotion();
                    showModernNotification('App instalado com sucesso! 🎉', 'success');
                }
                deferredPrompt = null;
            });
        }
    };
}

function showModernInstallPromotion() {
    const installBanner = document.createElement('div');
    installBanner.id = 'pwa-install-banner';
    installBanner.className = 'position-fixed top-0 start-0 end-0 p-3';
    installBanner.style.cssText = `
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        backdrop-filter: blur(20px);
        z-index: 9999;
        transform: translateY(-100%);
        animation: slideDown 0.5s ease-out forwards;
    `;
    installBanner.innerHTML = `
        <div class="container-fluid d-flex justify-content-between align-items-center text-white">
            <div class="d-flex align-items-center">
                <i class="fas fa-mobile-alt me-3 fa-2x"></i>
                <div>
                    <strong>Instalar App</strong>
                    <br><small>Acesso rápido e experiência nativa!</small>
                </div>
            </div>
            <div>
                <button class="btn btn-light btn-sm me-2" onclick="installPWA()">
                    <i class="fas fa-download me-1"></i>Instalar
                </button>
                <button class="btn btn-outline-light btn-sm" onclick="hideInstallPromotion()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    document.body.prepend(installBanner);
    setTimeout(hideInstallPromotion, 10000);
}

function hideInstallPromotion() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.style.animation = 'slideUp 0.5s ease-out forwards';
        setTimeout(() => banner.remove(), 500);
    }
}

/* ==========================================================================
   Modern Notifications
   ========================================================================== */

function showModernNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `modern-notification notification-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const colors = {
        success: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        error: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
        warning: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        info: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        backdrop-filter: blur(20px);
        z-index: 10000;
        transform: translateX(400px);
        animation: slideInRight 0.5s ease-out forwards;
        min-width: 300px;
        max-width: 400px;
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${icons[type]} me-3 fa-lg"></i>
            <div class="flex-grow-1">${message}</div>
            <button class="btn btn-sm text-white ms-2" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.5s ease-out forwards';
            setTimeout(() => notification.remove(), 500);
        }
    }, duration);
}

/* ==========================================================================
   Performance Optimizations
   ========================================================================== */

function initializePerformanceOptimizations() {
    initializeLazyLoading();
    preloadCriticalResources();
    monitorPerformance();
    optimizeAnimations();
    
    console.log('⚡ Performance optimizations initialized');
}

function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => imageObserver.observe(img));
    }
}

function preloadCriticalResources() {
    const criticalPages = ['/accounts/dashboard/', '/accounts/login/'];
    
    criticalPages.forEach(page => {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = page;
        document.head.appendChild(link);
    });
}

function optimizeAnimations() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--transition-fast', '0.01ms');
        document.documentElement.style.setProperty('--transition-base', '0.01ms');
        document.documentElement.style.setProperty('--transition-slow', '0.01ms');
    }
    
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
        document.documentElement.classList.add('reduced-animations');
    }
}

function monitorPerformance() {
    if ('performance' in window) {
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            const lastEntry = entries[entries.length - 1];
            console.log('📊 LCP:', lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
        
        new PerformanceObserver((entryList) => {
            const firstInput = entryList.getEntries()[0];
            console.log('⚡ FID:', firstInput.processingStart - firstInput.startTime);
        }).observe({ entryTypes: ['first-input'] });
        
        let clsValue = 0;
        new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            }
            console.log('📐 CLS:', clsValue);
        }).observe({ entryTypes: ['layout-shift'] });
        
        window.addEventListener('load', function() {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                console.log('🚀 Page Load Time:', loadTime + 'ms');
                
                if (loadTime < 1000) {
                    console.log('🟢 Performance: Excellent');
                } else if (loadTime < 2500) {
                    console.log('🟡 Performance: Good');
                } else {
                    console.log('🔴 Performance: Needs Improvement');
                }
            }, 0);
        });
    }
}

/* ==========================================================================
   Utility Functions
   ========================================================================== */

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

/* ==========================================================================
   Global Error Handling
   ========================================================================== */

window.addEventListener('error', function(event) {
    // Evitar notificação para erros conhecidos ou menores
    if (event.error && event.error.message && 
        (event.error.message.includes('ResizeObserver') || 
         event.error.message.includes('Non-Error promise rejection'))) {
        console.warn('Minor error suppressed:', event.error.message);
        return;
    }
    
    console.error('❌ JavaScript Error:', event.error);
    
    // Só mostrar notificação para erros críticos
    if (event.error && event.filename && !event.filename.includes('extension')) {
        showModernNotification('Erro detectado. Atualize se necessário.', 'warning', 3000);
    }
});

window.addEventListener('unhandledrejection', function(event) {
    console.warn('❌ Promise rejection:', event.reason);
    // Prevenir que apareça no console como erro não tratado
    event.preventDefault();
});

/* ==========================================================================
   CSS Animations (injected via JavaScript)
   ========================================================================== */

// Inject additional CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { transform: translateX(400px); }
        to { transform: translateX(0); }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); }
        to { transform: translateX(400px); }
    }
    
    @keyframes slideDown {
        from { transform: translateY(-100%); }
        to { transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { transform: translateY(0); }
        to { transform: translateY(-100%); }
    }
    
    @keyframes ripple {
        to { transform: scale(4); opacity: 0; }
    }
    
    @keyframes bounce {
        0%, 20%, 60%, 100% { transform: translateY(0); }
        40% { transform: translateY(-20px); }
        80% { transform: translateY(-10px); }
    }
    
    @keyframes floatParticle {
        0% { transform: translateY(100vh) translateX(0); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translateY(-100px) translateX(100px); opacity: 0; }
    }
    
    @keyframes explodeParticle {
        to { transform: rotate(var(--rotation, 0deg)) translateY(-100px); opacity: 0; }
    }
    
    .animate-on-scroll {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.6s ease-out;
    }
    
    .animate-in {
        opacity: 1;
        transform: translateY(0);
    }
    
    .theme-transitioning {
        transition: all 0.5s ease-in-out;
    }
    
    .loading-btn {
        pointer-events: none;
        opacity: 0.8;
    }
`;
document.head.appendChild(style);

console.log('🎨 Ultra Modern Salon Booking System Ready! ✨');
