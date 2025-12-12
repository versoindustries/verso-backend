/**
 * Enterprise Footer Component - World Class Design
 * 
 * Features:
 * - Glassmorphism design with animated gradients
 * - Working language selector that redirects properly
 * - Social links with hover animations
 * - Newsletter signup integration
 * - Fully responsive design
 * - Accessibility compliant
 */

import React, { useState, useCallback, useRef, useEffect, memo } from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';
import {
    Globe, ChevronDown, Github, Linkedin, Twitter,
    Mail, Sparkles, ArrowRight, Check, ExternalLink
} from 'lucide-react';
import './enterprise-footer.css';

// =============================================================================
// Types
// =============================================================================

interface Language {
    code: string;
    name: string;
    flag: string;
}

// =============================================================================
// Sub-Components
// =============================================================================

interface FooterLinkProps {
    href: string;
    children: React.ReactNode;
}

const FooterLink = memo(({ href, children }: FooterLinkProps) => (
    <li>
        <a href={href} className="enterprise-footer__link">
            <span className="enterprise-footer__link-text">{children}</span>
            <span className="enterprise-footer__link-arrow">→</span>
        </a>
    </li>
));
FooterLink.displayName = 'FooterLink';

// =============================================================================
// Main Footer Component
// =============================================================================

const Footer: React.FC = () => {
    const context = useVersoContext();
    const [isLangOpen, setIsLangOpen] = useState(false);
    const [isChangingLang, setIsChangingLang] = useState(false);
    const [email, setEmail] = useState('');
    const [isSubscribing, setIsSubscribing] = useState(false);
    const [subscribeSuccess, setSubscribeSuccess] = useState(false);
    const [subscribeError, setSubscribeError] = useState('');
    const langDropdownRef = useRef<HTMLDivElement>(null);

    // Available languages
    const languages: Language[] = [
        { code: 'en', name: 'English', flag: '🇺🇸' },
        { code: 'es', name: 'Español', flag: '🇪🇸' }
    ];

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (langDropdownRef.current && !langDropdownRef.current.contains(event.target as Node)) {
                setIsLangOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Get language URL based on code
    const getLanguageUrl = useCallback((langCode: string): string => {
        if (!context) return '#';
        return langCode === 'en' ? context.urls.setLanguageEn : context.urls.setLanguageEs;
    }, [context]);

    // Language change handler - performs actual navigation
    const handleLanguageChange = useCallback((lang: Language) => {
        if (!context) return;

        if (lang.code === context.currentLanguage) {
            setIsLangOpen(false);
            return;
        }

        setIsChangingLang(true);
        const url = getLanguageUrl(lang.code);
        // Use window.location.href for full page navigation
        window.location.href = url;
    }, [context, getLanguageUrl]);

    // Newsletter handler
    const handleNewsletterSubmit = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email || isSubscribing) return;

        setSubscribeError('');
        setIsSubscribing(true);

        try {
            const response = await fetch('/api/newsletter/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ email })
            });

            if (response.ok) {
                setSubscribeSuccess(true);
                setEmail('');
                setTimeout(() => setSubscribeSuccess(false), 4000);
            } else {
                const data = await response.json().catch(() => ({}));
                setSubscribeError(data.error || 'Subscription failed. Please try again.');
                setTimeout(() => setSubscribeError(''), 4000);
            }
        } catch (error) {
            console.error('Newsletter subscription failed:', error);
            setSubscribeError('Network error. Please try again.');
            setTimeout(() => setSubscribeError(''), 4000);
        } finally {
            setIsSubscribing(false);
        }
    }, [email, isSubscribing]);

    // Toggle language dropdown
    const toggleLangDropdown = useCallback(() => {
        setIsLangOpen(prev => !prev);
    }, []);

    // Handle email input change
    const handleEmailChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setEmail(e.target.value);
    }, []);

    // Early return with loading state AFTER all hooks
    if (!context) {
        return (
            <footer className="enterprise-footer enterprise-footer--loading">
                <div className="enterprise-footer__container">
                    <div className="enterprise-footer__skeleton" />
                </div>
            </footer>
        );
    }

    const { urls, config, year, version, currentLanguage } = context;
    const currentLang = languages.find(l => l.code === currentLanguage) || languages[0];

    // Footer link groups
    const companyLinks = [
        { label: 'About Us', href: urls.about },
        { label: 'Services', href: urls.services },
        { label: 'Blog', href: urls.blogIndex },
        { label: 'Careers', href: '/careers' }
    ];

    const resourceLinks = [
        { label: 'Documentation', href: '/docs' },
        { label: 'API Reference', href: '/api/docs' },
        { label: 'Support', href: '/support' },
        { label: 'Status', href: '/status' }
    ];

    const legalLinks = [
        { label: 'Privacy Policy', href: '/privacy' },
        { label: 'Terms of Service', href: '/terms' },
        { label: 'Cookie Policy', href: '/cookies' },
        { label: 'Accessibility', href: '/accessibility' }
    ];

    const socialLinks = [
        { icon: Github, href: 'https://github.com/versoindustries', label: 'GitHub' },
        { icon: Linkedin, href: 'https://linkedin.com/company/versoindustries', label: 'LinkedIn' },
        { icon: Twitter, href: 'https://twitter.com/versoindustries', label: 'Twitter' }
    ];

    return (
        <footer className="enterprise-footer" role="contentinfo">
            {/* Animated Background */}
            <div className="enterprise-footer__bg">
                <div className="enterprise-footer__bg-gradient" />
                <div className="enterprise-footer__bg-noise" />
                <div className="enterprise-footer__bg-glow" />
            </div>

            <div className="enterprise-footer__container">
                {/* Main Grid */}
                <div className="enterprise-footer__grid">
                    {/* Brand Column */}
                    <div className="enterprise-footer__brand">
                        <div className="enterprise-footer__logo">
                            <Sparkles className="enterprise-footer__logo-icon" />
                            <span className="enterprise-footer__logo-text">
                                {config?.site_name || 'Verso'}
                            </span>
                        </div>
                        <p className="enterprise-footer__tagline">
                            The Sovereign Monolith Protocol.<br />
                            <span className="enterprise-footer__tagline-accent">Ship finished truths.</span>
                        </p>

                        {/* Newsletter */}
                        <form className="enterprise-footer__newsletter" onSubmit={handleNewsletterSubmit}>
                            <span className="enterprise-footer__newsletter-label">
                                Stay updated with our latest innovations
                            </span>
                            <div className={`enterprise-footer__newsletter-input-group ${subscribeError ? 'error' : ''}`}>
                                <Mail className="enterprise-footer__newsletter-icon" />
                                <input
                                    type="email"
                                    placeholder="Enter your email"
                                    value={email}
                                    onChange={handleEmailChange}
                                    className="enterprise-footer__newsletter-input"
                                    required
                                    aria-label="Email address for newsletter"
                                    disabled={isSubscribing}
                                />
                                <button
                                    type="submit"
                                    className={`enterprise-footer__newsletter-btn ${subscribeSuccess ? 'success' : ''}`}
                                    disabled={isSubscribing || !email}
                                    aria-label="Subscribe to newsletter"
                                >
                                    {isSubscribing ? (
                                        <span className="enterprise-footer__newsletter-spinner" />
                                    ) : subscribeSuccess ? (
                                        <Check className="enterprise-footer__newsletter-btn-icon" />
                                    ) : (
                                        <ArrowRight className="enterprise-footer__newsletter-btn-icon" />
                                    )}
                                </button>
                            </div>
                            {subscribeError && (
                                <span className="enterprise-footer__newsletter-error">{subscribeError}</span>
                            )}
                        </form>

                        {/* Social Links */}
                        <div className="enterprise-footer__social">
                            {socialLinks.map((social) => (
                                <a
                                    key={social.label}
                                    href={social.href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="enterprise-footer__social-link"
                                    aria-label={social.label}
                                >
                                    <social.icon className="enterprise-footer__social-icon" />
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Company Links */}
                    <div className="enterprise-footer__column">
                        <h3 className="enterprise-footer__heading">Company</h3>
                        <ul className="enterprise-footer__list" role="list">
                            {companyLinks.map((link) => (
                                <FooterLink key={link.label} href={link.href}>
                                    {link.label}
                                </FooterLink>
                            ))}
                        </ul>
                    </div>

                    {/* Resources Links */}
                    <div className="enterprise-footer__column">
                        <h3 className="enterprise-footer__heading">Resources</h3>
                        <ul className="enterprise-footer__list" role="list">
                            {resourceLinks.map((link) => (
                                <FooterLink key={link.label} href={link.href}>
                                    {link.label}
                                </FooterLink>
                            ))}
                        </ul>
                    </div>

                    {/* Legal + Language */}
                    <div className="enterprise-footer__column">
                        <h3 className="enterprise-footer__heading">Legal</h3>
                        <ul className="enterprise-footer__list" role="list">
                            {legalLinks.map((link) => (
                                <FooterLink key={link.label} href={link.href}>
                                    {link.label}
                                </FooterLink>
                            ))}
                        </ul>

                        {/* Language Selector */}
                        <div className="enterprise-footer__lang-section">
                            <h3 className="enterprise-footer__heading">Language</h3>
                            <div
                                className="enterprise-footer__lang-dropdown"
                                ref={langDropdownRef}
                            >
                                <button
                                    type="button"
                                    className={`enterprise-footer__lang-trigger ${isLangOpen ? 'open' : ''} ${isChangingLang ? 'loading' : ''}`}
                                    onClick={toggleLangDropdown}
                                    aria-expanded={isLangOpen}
                                    aria-haspopup="listbox"
                                    aria-label="Select language"
                                    disabled={isChangingLang}
                                >
                                    <Globe className="enterprise-footer__lang-globe" />
                                    <span className="enterprise-footer__lang-flag">{currentLang.flag}</span>
                                    <span className="enterprise-footer__lang-name">{currentLang.name}</span>
                                    {isChangingLang ? (
                                        <span className="enterprise-footer__lang-spinner" />
                                    ) : (
                                        <ChevronDown className={`enterprise-footer__lang-chevron ${isLangOpen ? 'rotated' : ''}`} />
                                    )}
                                </button>

                                {isLangOpen && (
                                    <ul
                                        className="enterprise-footer__lang-menu"
                                        role="listbox"
                                        aria-label="Available languages"
                                    >
                                        {languages.map((lang) => (
                                            <li
                                                key={lang.code}
                                                role="option"
                                                aria-selected={lang.code === currentLanguage}
                                            >
                                                <button
                                                    type="button"
                                                    className={`enterprise-footer__lang-option ${lang.code === currentLanguage ? 'active' : ''}`}
                                                    onClick={() => handleLanguageChange(lang)}
                                                >
                                                    <span className="enterprise-footer__lang-flag">{lang.flag}</span>
                                                    <span className="enterprise-footer__lang-name">{lang.name}</span>
                                                    {lang.code === currentLanguage && (
                                                        <Check className="enterprise-footer__lang-check" />
                                                    )}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="enterprise-footer__bottom">
                    <div className="enterprise-footer__bottom-left">
                        <p className="enterprise-footer__copyright">
                            © {year || new Date().getFullYear()} {config?.site_name || 'Verso Industries'}. All rights reserved.
                        </p>
                    </div>
                    <div className="enterprise-footer__bottom-right">
                        <span className="enterprise-footer__version">
                            Powered by Verso v{version || '2.0'}
                        </span>
                        <a
                            href="https://github.com/versoindustries"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="enterprise-footer__source-link"
                        >
                            <ExternalLink className="enterprise-footer__source-icon" />
                            View Source
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default memo(Footer);
