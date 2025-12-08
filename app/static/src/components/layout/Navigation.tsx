import React from 'react';

export interface NavLinkProps {
    href: string;
    children: React.ReactNode;
    className?: string;
}

export const NavLink: React.FC<NavLinkProps> = ({ href, children, className }) => {
    return (
        <a href={href} className={`verso-nav__link ${className || ''}`}>
            {children}
        </a>
    );
};

export const MobileNavLink: React.FC<NavLinkProps> = ({ href, children, className }) => {
    return (
        <a href={href} className={`verso-mobile-menu__link ${className || ''}`}>
            {children}
        </a>
    );
};
