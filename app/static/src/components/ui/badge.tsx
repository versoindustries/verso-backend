/**
 * Badge Component
 * 
 * A small status indicator.
 * 
 * Usage:
 *   <div data-react-component="Badge" data-react-props='{"variant": "success", "children": "Active"}'></div>
 */

import { ReactNode } from 'react'

export interface BadgeProps {
    /** Badge content */
    children: ReactNode
    /** Badge variant */
    variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info'
    /** Badge size */
    size?: 'sm' | 'md' | 'lg'
    /** Rounded pill style */
    pill?: boolean
    /** Outline style */
    outline?: boolean
    /** With dot indicator */
    dot?: boolean
    /** Additional CSS class */
    className?: string
}

export function Badge({
    children,
    variant = 'default',
    size = 'md',
    pill = false,
    outline = false,
    dot = false,
    className = '',
}: BadgeProps) {
    const variantClasses = {
        default: 'badge-default',
        primary: 'badge-primary',
        secondary: 'badge-secondary',
        success: 'badge-success',
        warning: 'badge-warning',
        danger: 'badge-danger',
        info: 'badge-info',
    }

    const sizeClasses = {
        sm: 'badge-sm',
        md: 'badge-md',
        lg: 'badge-lg',
    }

    return (
        <span
            className={`badge ${variantClasses[variant]} ${sizeClasses[size]} ${pill ? 'badge-pill' : ''} ${outline ? 'badge-outline' : ''} ${className}`}
        >
            {dot && <span className="badge-dot" />}
            {children}
        </span>
    )
}

export default Badge
