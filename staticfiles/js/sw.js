/* ==========================================================================
   Service Worker for Offline Functionality
   Modern PWA implementation with caching strategies
   ========================================================================== */

const CACHE_NAME = 'agende-sua-beleza-v1.0.1';
const OFFLINE_URL = '/offline/';

// Assets to cache on install - only public and static content
const CACHE_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/js/charts.js',
    '/offline/',
    // Only cache public pages, NOT authenticated routes
    '/accounts/login/',
    // Static icons
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    // Bootstrap and other CDN resources
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/htmx.org@2.0.7/dist/htmx.min.js',
    'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js'
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching critical assets');
                return cache.addAll(CACHE_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle network requests with caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip cross-origin requests (except for CDN resources)
    if (url.origin !== location.origin && !isCdnResource(url)) {
        return;
    }
    
    // Handle different types of requests
    if (request.method === 'GET') {
        // Security: Never cache authenticated routes
        if (isAuthenticatedRoute(url)) {
            return; // Let browser handle normally, no caching
        }
        
        if (isApiRequest(url)) {
            // API requests - network first, cache fallback
            event.respondWith(networkFirstStrategy(request));
        } else if (isStaticAsset(url)) {
            // Static assets - cache first
            event.respondWith(cacheFirstStrategy(request));
        } else if (isPageRequest(url)) {
            // HTML pages - network first with offline fallback
            event.respondWith(pageStrategy(request));
        }
    }
});

// Caching Strategies

async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network request failed, trying cache:', request.url);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response for API requests
        return new Response(JSON.stringify({
            error: 'Offline',
            message: 'Esta funcionalidade não está disponível offline'
        }), {
            headers: { 'Content-Type': 'application/json' },
            status: 503
        });
    }
}

async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Failed to fetch resource:', request.url, error);
        throw error;
    }
}

async function pageStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Page request failed, trying cache:', request.url);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page
        const offlineResponse = await caches.match(OFFLINE_URL);
        if (offlineResponse) {
            return offlineResponse;
        }
        
        // Fallback offline page
        return new Response(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Offline - Agende sua Beleza</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .offline-container { max-width: 500px; margin: 0 auto; }
                    .icon { font-size: 4rem; color: #666; margin-bottom: 1rem; }
                    h1 { color: #333; }
                    p { color: #666; line-height: 1.6; }
                    .btn { display: inline-block; padding: 12px 24px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="offline-container">
                    <div class="icon">📱</div>
                    <h1>Você está offline</h1>
                    <p>Esta página não está disponível offline. Verifique sua conexão com a internet e tente novamente.</p>
                    <a href="/" class="btn" onclick="window.location.reload()">Tentar Novamente</a>
                </div>
            </body>
            </html>
        `, {
            headers: { 'Content-Type': 'text/html' },
            status: 503
        });
    }
}

// Helper functions

function isApiRequest(url) {
    return url.pathname.startsWith('/api/') || 
           url.pathname.includes('/ajax/') ||
           url.searchParams.has('hx-request');
}

function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') ||
           url.pathname.startsWith('/media/') ||
           url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/);
}

function isPageRequest(url) {
    return url.pathname.match(/\/$/) || 
           !url.pathname.includes('.') ||
           url.pathname.match(/\.(html|php)$/);
}

function isCdnResource(url) {
    const cdnDomains = [
        'cdn.jsdelivr.net',
        'cdnjs.cloudflare.com',
        'fonts.googleapis.com',
        'fonts.gstatic.com'
    ];
    
    return cdnDomains.some(domain => url.hostname.includes(domain));
}

// Security: Check if route requires authentication
function isAuthenticatedRoute(url) {
    const authenticatedPaths = [
        '/accounts/dashboard/',
        '/accounts/profile/',
        '/salons/',
        '/admin-panel/',
        '/subscriptions/'
    ];
    
    return authenticatedPaths.some(path => url.pathname.startsWith(path));
}

// Background sync for form submissions
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    console.log('Service Worker: Background sync triggered');
    // Handle offline form submissions here
}

// Push notifications (if needed in future)
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Ver Detalhes',
                icon: '/static/icons/icon-96x96.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/icons/icon-72x72.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Sistema de Agendamento', options)
    );
});

console.log('Service Worker: Script loaded');