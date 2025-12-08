/**
 * Push Notification Subscription Client
 * Handles service worker registration and push subscription
 */

class PushManager {
    constructor() {
        this.swRegistration = null;
        this.isSubscribed = false;
    }

    /**
     * Initialize push notifications
     */
    async init() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.log('Push notifications not supported');
            return false;
        }

        try {
            // Register service worker
            this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('Service Worker registered');

            // Check current subscription status
            const subscription = await this.swRegistration.pushManager.getSubscription();
            this.isSubscribed = subscription !== null;

            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }

    /**
     * Request notification permission and subscribe
     */
    async subscribe() {
        if (!this.swRegistration) {
            await this.init();
        }

        // Request permission
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            console.log('Notification permission denied');
            return null;
        }

        try {
            // Get VAPID public key from server
            const response = await fetch('/api/push/vapid-public-key');
            const data = await response.json();

            if (!data.configured) {
                console.error('Push notifications not configured on server');
                return null;
            }

            // Base64 decode the VAPID key
            const vapidPublicKey = this.urlBase64ToUint8Array(data.publicKey);

            // Subscribe to push
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: vapidPublicKey
            });

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);

            this.isSubscribed = true;
            console.log('Push subscription successful');

            return subscription;
        } catch (error) {
            console.error('Push subscription failed:', error);
            return null;
        }
    }

    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        if (!this.swRegistration) {
            return;
        }

        try {
            const subscription = await this.swRegistration.pushManager.getSubscription();

            if (subscription) {
                // Unsubscribe from browser
                await subscription.unsubscribe();

                // Notify server
                await fetch('/api/push/unsubscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ endpoint: subscription.endpoint })
                });
            }

            this.isSubscribed = false;
            console.log('Push unsubscription successful');
        } catch (error) {
            console.error('Push unsubscription failed:', error);
        }
    }

    /**
     * Send subscription data to server
     */
    async sendSubscriptionToServer(subscription) {
        const response = await fetch('/api/push/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(subscription.toJSON())
        });

        return response.json();
    }

    /**
     * Update category preferences
     */
    async updatePreferences(categories) {
        const response = await fetch('/api/push/preferences', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ categories })
        });

        return response.json();
    }

    /**
     * Get current preferences
     */
    async getPreferences() {
        const response = await fetch('/api/push/preferences');
        return response.json();
    }

    /**
     * Convert VAPID key from base64 to Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }

    /**
     * Check if push notifications are supported
     */
    static isSupported() {
        return 'serviceWorker' in navigator && 'PushManager' in window;
    }

    /**
     * Check current permission status
     */
    static getPermissionStatus() {
        if (!('Notification' in window)) {
            return 'unsupported';
        }
        return Notification.permission;
    }
}

// Export for use
window.PushManager = PushManager;

// Auto-initialize if user is logged in
document.addEventListener('DOMContentLoaded', function () {
    if (PushManager.isSupported() && document.body.dataset.userLoggedIn === 'true') {
        const pushManager = new PushManager();
        window.pushManager = pushManager;
        pushManager.init();
    }
});
