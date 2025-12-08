import React from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';
import { Zap } from 'lucide-react';

/**
 * AlertBar Component
 * 
 * A top-of-page notification banner that displays important site-wide messages
 * with a call-to-action button. Built as a React island for consistency with
 * the Header and Footer components.
 * 
 * Features:
 * - Animated gradient background with pulse effect
 * - Configurable message and CTA button
 * - Modernist/futurist glassmorphism design
 * - Fully responsive
 */

interface AlertBarProps {
    message?: string;
    ctaText?: string;
    ctaUrl?: string;
    variant?: 'default' | 'promo' | 'urgent';
}

const AlertBar: React.FC<AlertBarProps> = ({
    message,
    ctaText,
    ctaUrl,
    variant = 'default'
}) => {
    const context = useVersoContext();

    // Use context for URLs if available, otherwise use props
    const contactUrl = ctaUrl || context?.urls?.contact || '/contact';
    const displayMessage = message || context?.config?.site_name || 'Demo Site';
    const buttonText = ctaText || 'Contact';

    return (
        <div className={`verso-alert-bar verso-alert-bar--${variant}`}>
            <div className="verso-alert-bar__pulse"></div>
            <div className="verso-alert-bar__content">
                <div className="verso-alert-bar__message">
                    <Zap className="verso-alert-bar__icon" />
                    <span className="verso-alert-bar__text">{displayMessage}</span>
                </div>
                <a href={contactUrl} className="verso-alert-bar__cta">
                    {buttonText}
                </a>
            </div>
        </div>
    );
};

export default AlertBar;
