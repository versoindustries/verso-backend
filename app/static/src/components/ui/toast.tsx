/**
 * Toast Notification Component
 * 
 * A notification system for showing temporary messages.
 * 
 * Usage:
 *   <div data-react-component="Toast" data-react-props='{"message": "Success!", "type": "success"}'></div>
 *   
 * Or programmatically via the useToast hook (when we add state management)
 */

import { useState, useEffect, ReactNode, createContext, useContext, useCallback } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastProps {
    /** Toast message */
    message: string
    /** Toast type */
    type?: ToastType
    /** Auto-dismiss duration in ms (0 to disable) */
    duration?: number
    /** Callback when toast is dismissed */
    onDismiss?: () => void
    /** Show close button */
    showCloseButton?: boolean
    /** Additional CSS class */
    className?: string
}

const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
}

const typeClasses = {
    success: 'toast-success',
    error: 'toast-error',
    warning: 'toast-warning',
    info: 'toast-info',
}

export function Toast({
    message,
    type = 'info',
    duration = 5000,
    onDismiss,
    showCloseButton = true,
    className = '',
}: ToastProps) {
    const [isVisible, setIsVisible] = useState(true)
    const [isLeaving, setIsLeaving] = useState(false)

    const dismiss = useCallback(() => {
        setIsLeaving(true)
        setTimeout(() => {
            setIsVisible(false)
            onDismiss?.()
        }, 300) // Match animation duration
    }, [onDismiss])

    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(dismiss, duration)
            return () => clearTimeout(timer)
        }
    }, [duration, dismiss])

    if (!isVisible) return null

    const Icon = icons[type]

    return (
        <div
            className={`toast ${typeClasses[type]} ${isLeaving ? 'toast-leaving' : ''} ${className}`}
            role="alert"
            aria-live="polite"
        >
            <Icon className="toast-icon" />
            <span className="toast-message">{message}</span>
            {showCloseButton && (
                <button
                    onClick={dismiss}
                    className="toast-close"
                    aria-label="Dismiss notification"
                >
                    <X className="w-4 h-4" />
                </button>
            )}
        </div>
    )
}

// =============================================================================
// Toast Container & Context for Multiple Toasts
// =============================================================================

interface ToastItem extends ToastProps {
    id: string
}

interface ToastContextValue {
    toasts: ToastItem[]
    addToast: (props: Omit<ToastProps, 'onDismiss'>) => string
    removeToast: (id: string) => void
    success: (message: string, options?: Partial<ToastProps>) => string
    error: (message: string, options?: Partial<ToastProps>) => string
    warning: (message: string, options?: Partial<ToastProps>) => string
    info: (message: string, options?: Partial<ToastProps>) => string
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider')
    }
    return context
}

interface ToastProviderProps {
    children: ReactNode
    /** Position of toast container */
    position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
    /** Max number of visible toasts */
    maxToasts?: number
}

export function ToastProvider({
    children,
    position = 'top-right',
    maxToasts = 5,
}: ToastProviderProps) {
    const [toasts, setToasts] = useState<ToastItem[]>([])

    const addToast = useCallback((props: Omit<ToastProps, 'onDismiss'>) => {
        const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        setToasts(prev => {
            const newToasts = [...prev, { ...props, id }]
            // Limit number of toasts
            return newToasts.slice(-maxToasts)
        })
        return id
    }, [maxToasts])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    const success = useCallback((message: string, options?: Partial<ToastProps>) => {
        return addToast({ message, type: 'success', ...options })
    }, [addToast])

    const error = useCallback((message: string, options?: Partial<ToastProps>) => {
        return addToast({ message, type: 'error', ...options })
    }, [addToast])

    const warning = useCallback((message: string, options?: Partial<ToastProps>) => {
        return addToast({ message, type: 'warning', ...options })
    }, [addToast])

    const info = useCallback((message: string, options?: Partial<ToastProps>) => {
        return addToast({ message, type: 'info', ...options })
    }, [addToast])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
            {children}
            <div className={`toast-container toast-${position}`}>
                {toasts.map(toast => (
                    <Toast
                        key={toast.id}
                        {...toast}
                        onDismiss={() => removeToast(toast.id)}
                    />
                ))}
            </div>
        </ToastContext.Provider>
    )
}

export default Toast
