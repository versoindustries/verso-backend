import React, { useState } from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';
import { Menu, X, ChevronDown, User, LogOut, LayoutDashboard, MessageSquare, Briefcase, MapPin } from 'lucide-react';
import ShoppingCartWidget from '../features/cart/ShoppingCartWidget';
import NotificationBell from '../features/notifications/NotificationBell';
import { NavLink, MobileNavLink } from './Navigation';

const Header: React.FC = () => {
    const context = useVersoContext();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

    if (!context) return null;

    const { user, config, urls } = context;

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const toggleUserMenu = () => setIsUserMenuOpen(!isUserMenuOpen);

    return (
        <header className="verso-header">
            <div className="verso-header__inner">
                {/* Logo */}
                <div className="verso-header__logo" onClick={() => window.location.href = urls.index}>
                    <img className="verso-header__logo-img" src="/static/images/logo.png" alt={config.site_name} />
                    <span className="verso-header__logo-text">{config.site_name}</span>
                </div>

                {/* Desktop Navigation */}
                <nav className="verso-nav">
                    <NavLink href={urls.index}>Home</NavLink>

                    <div className="verso-nav__dropdown">
                        <button className="verso-nav__dropdown-trigger">
                            About <ChevronDown className="verso-nav__dropdown-icon" />
                        </button>
                        <div className="verso-nav__dropdown-menu">
                            <a href={urls.blogIndex} className="verso-nav__dropdown-item">Blog</a>
                        </div>
                    </div>

                    <div className="verso-nav__dropdown">
                        <button className="verso-nav__dropdown-trigger">
                            Services <ChevronDown className="verso-nav__dropdown-icon" />
                        </button>
                    </div>

                    <NavLink href={urls.contact}>Contact</NavLink>

                    {/* Blogger Menu */}
                    {user.isAuthenticated && user.roles?.includes('blogger') && (
                        <div className="verso-nav__dropdown">
                            <button className="verso-nav__dropdown-trigger">
                                Blog Mgmt <ChevronDown className="verso-nav__dropdown-icon" />
                            </button>
                            <div className="verso-nav__dropdown-menu">
                                <a href={urls.blogManage} className="verso-nav__dropdown-item">Manage Posts</a>
                                <a href={urls.blogNew} className="verso-nav__dropdown-item">New Post</a>
                            </div>
                        </div>
                    )}
                </nav>

                {/* Right Side Actions */}
                <div className="verso-header__actions">
                    {user.isAuthenticated ? (
                        <>
                            <div className="verso-header__location">
                                <MapPin className="verso-header__location-icon" />
                                <span>HQ</span>
                            </div>
                            <ShoppingCartWidget />
                            <NotificationBell initialCount={context.unreadNotificationsCount} />

                            {/* User Dropdown */}
                            <div className={`verso-user-menu ${isUserMenuOpen ? 'verso-user-menu--open' : ''}`}>
                                <button onClick={toggleUserMenu} className="verso-user-menu__trigger">
                                    <span className="sr-only">Open user menu</span>
                                    {user.firstName ? user.firstName[0] : <User style={{ width: 20, height: 20 }} />}
                                </button>

                                <div className="verso-user-menu__dropdown" onMouseLeave={() => setIsUserMenuOpen(false)}>
                                    <div className="verso-user-menu__header">
                                        <p className="verso-user-menu__label">Signed in as</p>
                                        <p className="verso-user-menu__name">{user.firstName || 'User'}</p>
                                    </div>
                                    <div className="verso-user-menu__section">
                                        <a href={urls.employeeDashboard} className="verso-user-menu__item">
                                            <Briefcase className="verso-user-menu__item-icon" />
                                            Employee Portal
                                        </a>
                                        <a href={urls.messaging} className="verso-user-menu__item">
                                            <MessageSquare className="verso-user-menu__item-icon" />
                                            Messages
                                        </a>
                                        {user.roles?.includes('admin') && (
                                            <a href={urls.adminDashboard} className="verso-user-menu__item">
                                                <LayoutDashboard className="verso-user-menu__item-icon" />
                                                Admin Dashboard
                                            </a>
                                        )}
                                    </div>
                                    <div className="verso-user-menu__section">
                                        <a href={urls.logout} className="verso-user-menu__item">
                                            <LogOut className="verso-user-menu__item-icon" />
                                            Sign out
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="verso-header__auth">
                            <a href={urls.login} className="verso-btn--ghost">Login</a>
                            <a href={urls.register} className="verso-btn--primary">Register</a>
                        </div>
                    )}
                </div>

                {/* Mobile Menu Toggle */}
                <button onClick={toggleMenu} className="verso-header__mobile-toggle">
                    <span className="sr-only">Open main menu</span>
                    {isMenuOpen ? <X className="verso-header__mobile-toggle-icon" /> : <Menu className="verso-header__mobile-toggle-icon" />}
                </button>
            </div>

            {/* Mobile Menu */}
            <div className={`verso-mobile-menu ${isMenuOpen ? 'verso-mobile-menu--open' : ''}`}>
                <nav className="verso-mobile-menu__nav">
                    <MobileNavLink href={urls.index}>Home</MobileNavLink>
                    <MobileNavLink href={urls.about}>About</MobileNavLink>
                    <MobileNavLink href={urls.services}>Services</MobileNavLink>
                    <MobileNavLink href={urls.blogIndex}>Blog</MobileNavLink>
                    <MobileNavLink href={urls.contact}>Contact</MobileNavLink>
                </nav>
                {user.isAuthenticated ? (
                    <div className="verso-mobile-menu__user">
                        <div className="verso-mobile-menu__avatar">
                            {user.firstName ? user.firstName[0] : <User />}
                        </div>
                        <span className="verso-mobile-menu__user-name">{user.firstName}</span>
                        <div className="verso-mobile-menu__widgets">
                            <ShoppingCartWidget />
                            <NotificationBell initialCount={context.unreadNotificationsCount} />
                        </div>
                    </div>
                ) : (
                    <div className="verso-mobile-menu__nav">
                        <MobileNavLink href={urls.login}>Login</MobileNavLink>
                        <MobileNavLink href={urls.register}>Register</MobileNavLink>
                    </div>
                )}
                {user.isAuthenticated && (
                    <nav className="verso-mobile-menu__nav">
                        <MobileNavLink href={urls.employeeDashboard}>Employee Portal</MobileNavLink>
                        <MobileNavLink href={urls.messaging}>Messages</MobileNavLink>
                        {user.roles?.includes('admin') && (
                            <MobileNavLink href={urls.adminDashboard}>Admin Dashboard</MobileNavLink>
                        )}
                        <MobileNavLink href={urls.logout}>Sign out</MobileNavLink>
                    </nav>
                )}
            </div>
        </header>
    );
};

export default Header;
