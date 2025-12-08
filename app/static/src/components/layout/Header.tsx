import React, { useState } from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';
import { Menu, X, ChevronDown, User, LogOut, LayoutDashboard, MessageSquare, Briefcase, MapPin } from 'lucide-react';
import ShoppingCartWidget from '../features/cart/ShoppingCartWidget';
// Import as default if it is default export, will fix if not
import NotificationBell from '../features/notifications/NotificationBell';
import { NavLink, MobileNavLink } from './Navigation';

const Header: React.FC = () => {
    const context = useVersoContext();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);


    if (!context) return null; // Logic to handle loading state if necessary

    const { user, config, urls } = context;

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const toggleUserMenu = () => setIsUserMenuOpen(!isUserMenuOpen);

    return (
        <header className="sticky top-0 z-50 w-full transition-all duration-300 bg-black/30 backdrop-blur-md border-b border-white/10 shadow-lg hover:shadow-xl hover:bg-black/40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-20">
                    {/* Logo */}
                    <div className="flex-shrink-0 flex items-center gap-4 cursor-pointer" onClick={() => window.location.href = urls.index}>
                        <img className="h-10 w-auto transition-transform hover:scale-105 duration-300" src="/static/images/logo.png" alt={config.site_name} />
                        <span className="hidden md:block font-neon-heavy text-xl md:text-2xl text-white tracking-widest uppercase truncate shadow-neon">
                            {config.site_name}
                        </span>
                    </div>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center space-x-6">
                        <NavLink href={urls.index}>Home</NavLink>

                        <div className="relative group">
                            <button className="flex items-center text-gray-200 hover:text-white px-3 py-2 text-sm font-medium uppercase tracking-wider transition-colors">
                                About <ChevronDown className="ml-1 h-4 w-4" />
                            </button>
                            <div className="absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-gray-900 ring-1 ring-black ring-opacity-5 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform origin-top-left">
                                <div className="py-1">
                                    <a href={urls.blogIndex} className="block px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">Blog</a>
                                </div>
                            </div>
                        </div>

                        <div className="relative group">
                            <button className="flex items-center text-gray-200 hover:text-white px-3 py-2 text-sm font-medium uppercase tracking-wider transition-colors">
                                Services <ChevronDown className="ml-1 h-4 w-4" />
                            </button>
                            {/* Dropdown content if needed */}
                        </div>

                        <NavLink href={urls.contact}>Contact</NavLink>

                        {/* Blogger Menu */}
                        {user.isAuthenticated && user.roles?.includes('blogger') && (
                            <div className="relative group">
                                <button className="flex items-center text-gray-200 hover:text-white px-3 py-2 text-sm font-medium uppercase tracking-wider transition-colors">
                                    Blog Mgmt <ChevronDown className="ml-1 h-4 w-4" />
                                </button>
                                <div className="absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-gray-900 ring-1 ring-black ring-opacity-5 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform origin-top-left">
                                    <div className="py-1">
                                        <a href={urls.blogManage} className="block px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">Manage Posts</a>
                                        <a href={urls.blogNew} className="block px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">New Post</a>
                                    </div>
                                </div>
                            </div>
                        )}
                    </nav>

                    {/* Right Side Icons */}
                    <div className="hidden md:flex items-center space-x-4">
                        {user.isAuthenticated ? (
                            <>
                                <div className="flex items-center space-x-2 text-gray-400 text-sm border-r border-gray-600 pr-4 mr-2">
                                    <MapPin className="h-4 w-4" />
                                    <span>HQ</span>
                                </div>
                                <ShoppingCartWidget />
                                <NotificationBell initialCount={context.unreadNotificationsCount} />

                                {/* User Dropdown */}
                                <div className="relative ml-3">
                                    <button
                                        onClick={toggleUserMenu}
                                        className="flex items-center max-w-xs text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500"
                                    >
                                        <span className="sr-only">Open user menu</span>
                                        <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold border border-indigo-400">
                                            {user.firstName ? user.firstName[0] : <User className="h-5 w-5" />}
                                        </div>
                                    </button>

                                    {isUserMenuOpen && (
                                        <div
                                            className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-gray-900 ring-1 ring-black ring-opacity-5 z-50 divide-y divide-gray-700"
                                            onMouseLeave={() => setIsUserMenuOpen(false)}
                                        >
                                            <div className="px-4 py-3">
                                                <p className="text-sm text-white">Signed in as</p>
                                                <p className="text-sm font-medium text-gray-300 truncate">{user.firstName || 'User'}</p>
                                            </div>
                                            <div className="py-1">
                                                <a href={urls.employeeDashboard} className="group flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">
                                                    <Briefcase className="mr-3 h-4 w-4 text-gray-400 group-hover:text-white" />
                                                    Employee Portal
                                                </a>
                                                <a href={urls.messaging} className="group flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">
                                                    <MessageSquare className="mr-3 h-4 w-4 text-gray-400 group-hover:text-white" />
                                                    Messages
                                                </a>
                                                {user.roles?.includes('admin') && (
                                                    <a href={urls.adminDashboard} className="group flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">
                                                        <LayoutDashboard className="mr-3 h-4 w-4 text-gray-400 group-hover:text-white" />
                                                        Admin Dashboard
                                                    </a>
                                                )}
                                            </div>
                                            <div className="py-1">
                                                <a href={urls.logout} className="group flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-indigo-600 hover:text-white">
                                                    <LogOut className="mr-3 h-4 w-4 text-gray-400 group-hover:text-white" />
                                                    Sign out
                                                </a>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : (
                            <div className="flex items-center space-x-3">
                                <a href={urls.login} className="text-gray-300 hover:text-white font-medium text-sm uppercase tracking-wider px-3 py-2 rounded-md hover:bg-white/10 transition-colors">Login</a>
                                <a href={urls.register} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-sm uppercase tracking-wider px-4 py-2 rounded-md shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5">Register</a>
                            </div>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="-mr-2 flex md:hidden">
                        <button
                            onClick={toggleMenu}
                            className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white"
                        >
                            <span className="sr-only">Open main menu</span>
                            {isMenuOpen ? <X className="block h-6 w-6" /> : <Menu className="block h-6 w-6" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            {isMenuOpen && (
                <div className="md:hidden bg-gray-900 border-t border-gray-800">
                    <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                        <MobileNavLink href={urls.index}>Home</MobileNavLink>
                        <MobileNavLink href={urls.about}>About</MobileNavLink>
                        <MobileNavLink href={urls.services}>Services</MobileNavLink>
                        <MobileNavLink href={urls.blogIndex}>Blog</MobileNavLink>
                        <MobileNavLink href={urls.contact}>Contact</MobileNavLink>
                    </div>
                    {user.isAuthenticated ? (
                        <div className="pt-4 pb-3 border-t border-gray-700">
                            <div className="flex items-center px-5">
                                <div className="flex-shrink-0">
                                    <div className="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold">
                                        {user.firstName ? user.firstName[0] : <User />}
                                    </div>
                                </div>
                                <div className="ml-3">
                                    <div className="text-base font-medium leading-none text-white">{user.firstName}</div>
                                </div>
                                <div className="ml-auto flex items-center space-x-3">
                                    <ShoppingCartWidget />
                                    <NotificationBell initialCount={context.unreadNotificationsCount} />
                                </div>
                            </div>
                            <div className="mt-3 px-2 space-y-1">
                                <MobileNavLink href={urls.employeeDashboard}>Employee Portal</MobileNavLink>
                                <MobileNavLink href={urls.messaging}>Messages</MobileNavLink>
                                {user.roles?.includes('admin') && (
                                    <MobileNavLink href={urls.adminDashboard}>Admin Dashboard</MobileNavLink>
                                )}
                                <MobileNavLink href={urls.logout}>Sign out</MobileNavLink>
                            </div>
                        </div>
                    ) : (
                        <div className="pt-4 pb-3 border-t border-gray-700">
                            <div className="px-2 space-y-1">
                                <MobileNavLink href={urls.login}>Login</MobileNavLink>
                                <MobileNavLink href={urls.register}>Register</MobileNavLink>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </header>
    );
};

export default Header;
