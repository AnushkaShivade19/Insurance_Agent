// static/js/serviceworker.js

const CACHE_NAME = 'bimasakhi-v2'; // Bump version to force update
const OFFLINE_URL = '/offline/';

// 1. FILES TO CACHE IMMEDIATELY (The Core App)
const PRE_CACHE_ASSETS = [
    '/',
    '/offline/',
    '/static/css/base.css',
    '/static/js/base.js',
    '/static/images/logo.png',
    '/static/css/base.css',
    '/static/js/base.js',
    '/static/js/offline_bot.js',     // <-- CACHE YOUR QUESTIONS
    '/static/chatbot/js/chat.js',    // <-- CACHE THE LOGIC
    '/chatbot/',                     // <-- CACHE THE CHAT PAGE URL

];

// INSTALL: Cache the core files
self.addEventListener('install', (event) => {
    self.skipWaiting(); // Force this worker to activate immediately
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRE_CACHE_ASSETS);
        })
    );
});

// ACTIVATE: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// FETCH: The "Smart" Caching Logic
self.addEventListener('fetch', (event) => {
    
    // STRATEGY 1: HTML Pages (Network First -> Cache -> Offline Page)
    // We want fresh data for pages, but if offline, show the saved version.
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then((networkResponse) => {
                    return caches.open(CACHE_NAME).then((cache) => {
                        // Save the page we just visited
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                })
                .catch(() => {
                    // If offline, look in cache
                    return caches.match(event.request).then((cachedResponse) => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // If not in cache, show the Custom Offline Page
                        return caches.match(OFFLINE_URL);
                    });
                })
        );
        return;
    }

    // STRATEGY 2: Static Assets (Cache First -> Network)
    // Images/CSS/JS don't change often, so load from phone first (Fast!)
    if (event.request.destination === 'style' || 
        event.request.destination === 'script' || 
        event.request.destination === 'image') {
        
        event.respondWith(
            caches.match(event.request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(event.request).then((networkResponse) => {
                    return caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                });
            })
        );
        return;
    }

    // DEFAULT STRATEGY (Network Only)
    // For API calls or other random requests
    event.respondWith(fetch(event.request));
});