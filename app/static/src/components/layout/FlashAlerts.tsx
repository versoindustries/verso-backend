import React from 'react';
import { Toast } from '../ui/toast';

type FlashTuple = [string, string];
interface FlashMessageObj {
    category: string;
    message: string;
}

interface FlashAlertsProps {
    messages: (FlashTuple | FlashMessageObj)[];
}

/**
 * FlashAlerts Component
 * 
 * Renders server-side flash messages using the React Toast component.
 * Mounted in base.html to replace the Jinja2 flash message loop.
 */
const FlashAlerts: React.FC<FlashAlertsProps> = ({ messages }) => {
    if (!messages || messages.length === 0) return null;

    const normalizedMessages = messages.map(msg => {
        if (Array.isArray(msg)) {
            return { category: msg[0], message: msg[1] };
        }
        return msg;
    });

    return (
        <div className="flash-alerts-section w-full z-50 pointer-events-none relative">
            <div className="container mx-auto px-4 py-4 space-y-2 pointer-events-auto">
                {normalizedMessages.map((msg, i) => {
                    let type: 'success' | 'error' | 'warning' | 'info' = 'info';

                    // Map Flask categories to Toast types
                    if (msg.category === 'success') type = 'success';
                    else if (msg.category === 'error' || msg.category === 'danger') type = 'error';
                    else if (msg.category === 'warning') type = 'warning';

                    return (
                        <div key={i} className="flex justify-center">
                            <Toast
                                message={msg.message}
                                type={type}
                                duration={0} // Persist until dismissed or navigated
                                showCloseButton={true}
                                className="w-full max-w-3xl shadow-lg animate-in"
                            />
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default FlashAlerts;
