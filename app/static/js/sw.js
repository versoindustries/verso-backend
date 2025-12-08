/**
 * Push Notification Service Worker
 * Handles incoming push notifications and click events
 */

// Install event
self.addEventListener('install', function (event) {
    console.log('Service Worker: Installing...');
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', function (event) {
    console.log('Service Worker: Activated');
    event.waitUntil(clients.claim());
});

// Push event - handle incoming push notifications
self.addEventListener('push', function (event) {
    console.log('Service Worker: Push received');

    let data = {
        title: 'Notification',
        body: 'You have a new notification',
        icon: '/static/img/notification-icon.png',
        url: '/'
    };

    // Try to parse push data
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: data.icon || '/static/img/notification-icon.png',
        badge: '/static/img/badge-icon.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/',
            category: data.category || 'general'
        },
        actions: [
            { action: 'open', title: 'Open' },
            { action: 'close', title: 'Dismiss' }
        ],
        requireInteraction: false,
        tag: data.category || 'default'
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click event
self.addEventListener('notificationclick', function (event) {
    console.log('Service Worker: Notification clicked');

    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    const url = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(function (clientList) {
                // Check if there's already a window open
                for (let i = 0; i < clientList.length; i++) {
                    const client = clientList[i];
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open a new window
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// Notification close event
self.addEventListener('notificationclose', function (event) {
    console.log('Service Worker: Notification closed');
});

// Fetch event - can be used for offline caching
self.addEventListener('fetch', function (event) {
    // Pass through all requests
    event.respondWith(fetch(event.request));
});
