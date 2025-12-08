importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');

if (workbox) {
    console.log(`Workbox is loaded`);

    // Precache offline page
    // Note: This requires a build step typically to inject the revision, 
    // but for now we'll just runtime cache it or try to fetch it.

    const OFFLINE_PAGE = '/offline';

    workbox.routing.registerRoute(
        ({ request }) => request.mode === 'navigate',
        new workbox.strategies.NetworkFirst({
            cacheName: 'pages',
            plugins: [
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 50,
                }),
            ],
        })
        // In a real build, we'd use setCatchHandler to return offline page
    );

    workbox.routing.registerRoute(
        ({ request }) => request.destination === 'style' || request.destination === 'script' || request.destination === 'worker',
        new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'assets',
        })
    );

    workbox.routing.registerRoute(
        ({ request }) => request.destination === 'image',
        new workbox.strategies.CacheFirst({
            cacheName: 'images',
            plugins: [
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 60,
                    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
                }),
            ],
        })
    );

    // Catch navigation errors and show offline page
    workbox.routing.setCatchHandler(async ({ event }) => {
        // Return the precached offline page if a document is being requested
        if (event.request.destination === 'document') {
            // return workbox.precaching.matchPrecache(OFFLINE_PAGE);
            // Fallback to static offline.html if we can serve it or cache it manually?
            // For now, let's try to match a specific cache entry we might have added.
            return caches.match(OFFLINE_PAGE);
        }
        return Response.error();
    });

} else {
    console.log(`Workbox didn't load`);
}

// Listen for the "install" event, and perform caching
self.addEventListener('install', (event) => {
    const OFFLINE_PAGE = '/offline';
    event.waitUntil(
        caches.open('pages').then((cache) => {
            return cache.add(OFFLINE_PAGE);
        })
    );
});
