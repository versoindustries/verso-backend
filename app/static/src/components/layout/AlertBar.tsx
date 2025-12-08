import React, { useState, useEffect } from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';
import { Zap, X, ArrowRight, Sparkles } from 'lucide-react';

/**
 * AlertBar Component
 * 
 * A top-of-page notification banner that displays important site-wide messages
 * with a call-to-action button. Built as a React island for consistency with
 * the Header and Footer components.
 * 
 * Features:
 * - Animated gradient background with pulse effect
 * - Dismissible with smooth animation
 * - Configurable message and CTA button with arrow icon
 * - Multiple variants (default, promo, urgent)
 * - Modernist/futurist glassmorphism design
 * - Fully responsive
 */

interface AlertBarProps {
    message?: string;
    ctaText?: string;
    ctaUrl?: string;
    variant?: 'default' | 'promo' | 'urgent';
    dismissible?: boolean;
    showSparkles?: boolean;
}

const AlertBar: React.FC<AlertBarProps> = ({
    message,
    ctaText,
    ctaUrl,
    variant = 'default',
    dismissible = true,
    showSparkles = true
}) => {
    const context = useVersoContext();
    const [isVisible, setIsVisible] = useState(true);
    const [isHovered, setIsHovered] = useState(false);

    // Use context for URLs if available, otherwise use props
    const contactUrl = ctaUrl || context?.urls?.contact || '/contact';
    const displayMessage = message || 'Welcome to Verso — The Sovereign Monolith Protocol';
    const buttonText = ctaText || 'Get Started';

    const handleDismiss = () => {
        setIsVisible(false);
        // Optionally store in localStorage to not show again for this session
        sessionStorage.setItem('alertBarDismissed', 'true');
    };

    // Check if previously dismissed
    useEffect(() => {
        const dismissed = sessionStorage.getItem('alertBarDismissed');
        if (dismissed === 'true') {
            setIsVisible(false);
        }
    }, []);

    if (!isVisible) return null;

    return (
        <div className={`verso-alert-bar verso-alert-bar--${variant}`}>
            {/* Animated pulse background */}
            <div className="verso-alert-bar__pulse"></div>

            {/* Animated particles/sparkles */}
            {showSparkles && (
                <div className="verso-alert-bar__sparkles">
                    <Sparkles className="verso-alert-bar__sparkle verso-alert-bar__sparkle--1" />
                    <Sparkles className="verso-alert-bar__sparkle verso-alert-bar__sparkle--2" />
                </div>
            )}

            <div className="verso-alert-bar__content">
                {/* Message section with icon */}
                <div className="verso-alert-bar__message">
                    <div className="verso-alert-bar__icon-wrapper">
                        <Zap className="verso-alert-bar__icon" />
                    </div>
                    <span className="verso-alert-bar__text">{displayMessage}</span>
                </div>

                {/* CTA Button with hover effects */}
                <a
                    href={contactUrl}
                    className="verso-alert-bar__cta"
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                >
                    <span className="verso-alert-bar__cta-text">{buttonText}</span>
                    <ArrowRight
                        className={`verso-alert-bar__cta-arrow ${isHovered ? 'verso-alert-bar__cta-arrow--animated' : ''}`}
                    />
                    <div className="verso-alert-bar__cta-shine"></div>
                </a>

                {/* Dismiss button */}
                {dismissible && (
                    <button
                        onClick={handleDismiss}
                        className="verso-alert-bar__dismiss"
                        aria-label="Dismiss notification"
                    >
                        <X className="verso-alert-bar__dismiss-icon" />
                    </button>
                )}
            </div>
        </div>
    );
};

export default AlertBar;
