/**
 * Spinner Component
 * 
 * A loading indicator.
 * 
 * Usage:
 *   <div data-react-component="Spinner" data-react-props='{"size": "lg"}'></div>
 */

export interface SpinnerProps {
    /** Spinner size */
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
    /** Spinner color */
    color?: 'primary' | 'secondary' | 'white' | 'current'
    /** Screen reader label */
    label?: string
    /** Additional CSS class */
    className?: string
}

export function Spinner({
    size = 'md',
    color = 'primary',
    label = 'Loading...',
    className = '',
}: SpinnerProps) {
    const sizeClasses = {
        xs: 'spinner-xs',
        sm: 'spinner-sm',
        md: 'spinner-md',
        lg: 'spinner-lg',
        xl: 'spinner-xl',
    }

    const colorClasses = {
        primary: 'spinner-primary',
        secondary: 'spinner-secondary',
        white: 'spinner-white',
        current: 'spinner-current',
    }

    return (
        <div className={`spinner ${sizeClasses[size]} ${colorClasses[color]} ${className}`} role="status">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle
                    className="spinner-track"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="3"
                />
                <path
                    className="spinner-head"
                    d="M12 2C6.47715 2 2 6.47715 2 12"
                    stroke="currentColor"
                    strokeWidth="3"
                    strokeLinecap="round"
                />
            </svg>
            <span className="sr-only">{label}</span>
        </div>
    )
}

// Overlay spinner for full-page or container loading
export interface SpinnerOverlayProps extends SpinnerProps {
    /** Loading text */
    text?: string
    /** Translucent background */
    translucent?: boolean
}

export function SpinnerOverlay({
    text,
    translucent = true,
    ...spinnerProps
}: SpinnerOverlayProps) {
    return (
        <div className={`spinner-overlay ${translucent ? 'spinner-overlay-translucent' : ''}`}>
            <div className="spinner-overlay-content">
                <Spinner {...spinnerProps} size={spinnerProps.size || 'lg'} />
                {text && <p className="spinner-overlay-text">{text}</p>}
            </div>
        </div>
    )
}

export default Spinner
