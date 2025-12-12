/**
 * Enterprise Header Component - World Class Design
 * 
 * Features:
 * - Glassmorphism design with animated gradients
 * - Full dropdown navigation system
 * - Notification bell with dropdown
 * - Shopping cart widget integration
 * - User menu with role-based options
 * - Fully responsive design
 * - Accessibility compliant
 * - Micro-animations and transitions
 */

import React, { useState, useCallback, useRef, useEffect, memo } from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';
import {
    Menu, X, ChevronDown, User as UserIcon, LogOut, LayoutDashboard,
    MessageSquare, Briefcase, MapPin, Home, Info, Wrench, Phone,
    BookOpen, PenSquare, FileText
} from 'lucide-react';
import ShoppingCartWidget from '../features/cart/ShoppingCartWidget';
import NotificationBell from '../features/notifications/NotificationBell';
import './enterprise-header.css';

// =============================================================================
// Sub-Components
// =============================================================================

interface NavLinkProps {
    href: string;
    children: React.ReactNode;
    icon?: React.ReactNode;
}

const NavLink = memo(({ href, children, icon }: NavLinkProps) => (
    <a href={href} className="enterprise-header__nav-link">
        {icon && <span className="enterprise-header__nav-link-icon">{icon}</span>}
        <span className="enterprise-header__nav-link-text">{children}</span>
    </a>
));
NavLink.displayName = 'NavLink';

interface DropdownProps {
    label: string;
    items: Array<{ label: string; href: string; icon?: React.ReactNode }>;
}

const NavDropdown = memo(({ label, items }: DropdownProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const handleMouseEnter = useCallback(() => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setIsOpen(true);
    }, []);

    const handleMouseLeave = useCallback(() => {
        timeoutRef.current = setTimeout(() => setIsOpen(false), 150);
    }, []);

    useEffect(() => {
        return () => {
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, []);

    return (
        <div
            className="enterprise-header__dropdown"
            ref={dropdownRef}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <button
                className={`enterprise-header__dropdown-trigger ${isOpen ? 'open' : ''}`}
                aria-expanded={isOpen}
                aria-haspopup="true"
            >
                <span>{label}</span>
                <ChevronDown className={`enterprise-header__dropdown-chevron ${isOpen ? 'rotated' : ''}`} />
            </button>
            <div className={`enterprise-header__dropdown-menu ${isOpen ? 'open' : ''}`}>
                {items.map((item) => (
                    <a
                        key={item.label}
                        href={item.href}
                        className="enterprise-header__dropdown-item"
                    >
                        {item.icon && <span className="enterprise-header__dropdown-item-icon">{item.icon}</span>}
                        <span>{item.label}</span>
                    </a>
                ))}
            </div>
        </div>
    );
});
NavDropdown.displayName = 'NavDropdown';

// =============================================================================
// Main Header Component
// =============================================================================

const Header: React.FC = () => {
    const context = useVersoContext();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);
    const userMenuRef = useRef<HTMLDivElement>(null);

    // Handle scroll for sticky header effect
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Close user menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
                setIsUserMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Close mobile menu on window resize
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth > 768) {
                setIsMobileMenuOpen(false);
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const toggleMobileMenu = useCallback(() => {
        setIsMobileMenuOpen(prev => !prev);
    }, []);

    const toggleUserMenu = useCallback(() => {
        setIsUserMenuOpen(prev => !prev);
    }, []);

    // Early return with loading placeholder if context not ready
    if (!context) {
        return (
            <header className="enterprise-header enterprise-header--loading">
                <div className="enterprise-header__container">
                    <div className="enterprise-header__skeleton" />
                </div>
            </header>
        );
    }

    const { user, config, urls } = context;
    const isAdmin = user.roles?.some(role => ['Admin', 'Owner', 'Manager'].includes(role));
    const isBlogger = user.roles?.includes('blogger');

    // Navigation items
    const aboutItems = [
        { label: 'About Us', href: urls.about, icon: <Info size={16} /> },
        { label: 'Blog', href: urls.blogIndex, icon: <BookOpen size={16} /> },
    ];

    const serviceItems = [
        { label: 'Our Services', href: urls.services, icon: <Wrench size={16} /> },
    ];

    const blogMgmtItems = [
        { label: 'Manage Posts', href: urls.blogManage, icon: <FileText size={16} /> },
        { label: 'New Post', href: urls.blogNew, icon: <PenSquare size={16} /> },
    ];

    return (
        <header className={`enterprise-header ${isScrolled ? 'scrolled' : ''} ${isMobileMenuOpen ? 'menu-open' : ''}`}>
            {/* Animated Background Effects */}
            <div className="enterprise-header__bg">
                <div className="enterprise-header__bg-gradient" />
                <div className="enterprise-header__bg-glow" />
            </div>

            <div className="enterprise-header__container">
                {/* Logo */}
                <a href={urls.index} className="enterprise-header__logo">
                    <img
                        src="/static/images/logo.png"
                        alt={config.site_name}
                        className="enterprise-header__logo-img"
                        loading="eager"
                    />
                    <span className="enterprise-header__logo-text">{config.site_name}</span>
                </a>

                {/* Desktop Navigation */}
                <nav className="enterprise-header__nav" role="navigation" aria-label="Main navigation">
                    <NavLink href={urls.index} icon={<Home size={16} />}>Home</NavLink>
                    <NavDropdown label="About" items={aboutItems} />
                    <NavDropdown label="Services" items={serviceItems} />
                    <NavLink href={urls.contact} icon={<Phone size={16} />}>Contact</NavLink>

                    {/* Blogger Menu */}
                    {user.isAuthenticated && isBlogger && (
                        <NavDropdown label="Blog Mgmt" items={blogMgmtItems} />
                    )}
                </nav>

                {/* Right Side Actions */}
                <div className="enterprise-header__actions">
                    {user.isAuthenticated ? (
                        <>
                            {/* Location Indicator */}
                            <div className="enterprise-header__location">
                                <MapPin size={16} />
                                <span>HQ</span>
                            </div>

                            {/* Shopping Cart */}
                            <ShoppingCartWidget />

                            {/* Notifications */}
                            <NotificationBell initialCount={context.unreadNotificationsCount} />

                            {/* User Menu */}
                            <div
                                className={`enterprise-header__user-menu ${isUserMenuOpen ? 'open' : ''}`}
                                ref={userMenuRef}
                            >
                                <button
                                    className="enterprise-header__user-trigger"
                                    onClick={toggleUserMenu}
                                    aria-expanded={isUserMenuOpen}
                                    aria-haspopup="true"
                                    aria-label="User menu"
                                >
                                    <span className="enterprise-header__user-avatar">
                                        {user.firstName ? user.firstName[0].toUpperCase() : <UserIcon size={18} />}
                                    </span>
                                </button>

                                <div className="enterprise-header__user-dropdown">
                                    <div className="enterprise-header__user-header">
                                        <p className="enterprise-header__user-label">Signed in as</p>
                                        <p className="enterprise-header__user-name">{user.firstName || 'User'}</p>
                                    </div>

                                    <div className="enterprise-header__user-section">
                                        <a href={urls.employeeDashboard} className="enterprise-header__user-item">
                                            <Briefcase size={18} />
                                            <span>Employee Portal</span>
                                        </a>
                                        <a href={urls.messaging} className="enterprise-header__user-item">
                                            <MessageSquare size={18} />
                                            <span>Messages</span>
                                        </a>
                                        {isAdmin && (
                                            <a href={urls.adminDashboard} className="enterprise-header__user-item">
                                                <LayoutDashboard size={18} />
                                                <span>Admin Portal</span>
                                            </a>
                                        )}
                                    </div>

                                    <div className="enterprise-header__user-section">
                                        <a href={urls.logout} className="enterprise-header__user-item enterprise-header__user-item--danger">
                                            <LogOut size={18} />
                                            <span>Sign out</span>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="enterprise-header__auth">
                            <a href={urls.login} className="enterprise-header__auth-link">Login</a>
                            <a href={urls.register} className="enterprise-header__auth-btn">Register</a>
                        </div>
                    )}
                </div>

                {/* Mobile Menu Toggle */}
                <button
                    className="enterprise-header__mobile-toggle"
                    onClick={toggleMobileMenu}
                    aria-expanded={isMobileMenuOpen}
                    aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
                >
                    {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Mobile Menu */}
            <div className={`enterprise-header__mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
                <nav className="enterprise-header__mobile-nav">
                    <a href={urls.index} className="enterprise-header__mobile-link">
                        <Home size={20} />
                        <span>Home</span>
                    </a>
                    <a href={urls.about} className="enterprise-header__mobile-link">
                        <Info size={20} />
                        <span>About</span>
                    </a>
                    <a href={urls.services} className="enterprise-header__mobile-link">
                        <Wrench size={20} />
                        <span>Services</span>
                    </a>
                    <a href={urls.blogIndex} className="enterprise-header__mobile-link">
                        <BookOpen size={20} />
                        <span>Blog</span>
                    </a>
                    <a href={urls.contact} className="enterprise-header__mobile-link">
                        <Phone size={20} />
                        <span>Contact</span>
                    </a>
                </nav>

                {user.isAuthenticated ? (
                    <>
                        {/* Mobile User Info */}
                        <div className="enterprise-header__mobile-user">
                            <div className="enterprise-header__mobile-avatar">
                                {user.firstName ? user.firstName[0].toUpperCase() : <UserIcon size={24} />}
                            </div>
                            <span className="enterprise-header__mobile-username">{user.firstName || 'User'}</span>
                            <div className="enterprise-header__mobile-widgets">
                                <ShoppingCartWidget />
                                <NotificationBell initialCount={context.unreadNotificationsCount} />
                            </div>
                        </div>

                        {/* Mobile Portal Links */}
                        <nav className="enterprise-header__mobile-nav enterprise-header__mobile-nav--secondary">
                            <a href={urls.employeeDashboard} className="enterprise-header__mobile-link">
                                <Briefcase size={20} />
                                <span>Employee Portal</span>
                            </a>
                            <a href={urls.messaging} className="enterprise-header__mobile-link">
                                <MessageSquare size={20} />
                                <span>Messages</span>
                            </a>
                            {isAdmin && (
                                <a href={urls.adminDashboard} className="enterprise-header__mobile-link">
                                    <LayoutDashboard size={20} />
                                    <span>Admin Portal</span>
                                </a>
                            )}
                            <a href={urls.logout} className="enterprise-header__mobile-link enterprise-header__mobile-link--danger">
                                <LogOut size={20} />
                                <span>Sign out</span>
                            </a>
                        </nav>
                    </>
                ) : (
                    <div className="enterprise-header__mobile-auth">
                        <a href={urls.login} className="enterprise-header__mobile-auth-link">Login</a>
                        <a href={urls.register} className="enterprise-header__mobile-auth-btn">Register</a>
                    </div>
                )}
            </div>
        </header>
    );
};

export default memo(Header);
