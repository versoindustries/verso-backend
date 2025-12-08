import React from 'react';

export interface NavLinkProps {
    href: string;
    children: React.ReactNode;
    className?: string; // Allow overrides
}

export const NavLink: React.FC<NavLinkProps> = ({ href, children, className }) => {
    return (
        <a
            href={href}
            className={`text-gray-200 hover:text-white hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 uppercase tracking-wider ${className || ''}`}
        >
            {children}
        </a>
    );
};

export const MobileNavLink: React.FC<NavLinkProps> = ({ href, children, className }) => {
    return (
        <a
            href={href}
            className={`block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors uppercase ${className || ''}`}
        >
            {children}
        </a>
    );
};
