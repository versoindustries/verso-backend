/**
 * Modal Component
 * 
 * A reusable modal/dialog component with proper accessibility.
 * 
 * Usage:
 *   <div data-react-component="Modal" data-react-props='{"title": "Confirm", "open": true}'></div>
 */

import { useEffect, useRef, ReactNode } from 'react'
import { X } from 'lucide-react'
import { Button } from './button'

export interface ModalProps {
    /** Whether the modal is open */
    open?: boolean
    /** Callback when modal should close */
    onClose?: () => void
    /** Modal title */
    title?: string
    /** Modal content */
    children?: ReactNode
    /** Show close button */
    showCloseButton?: boolean
    /** Close on overlay click */
    closeOnOverlayClick?: boolean
    /** Close on Escape key */
    closeOnEscape?: boolean
    /** Modal size */
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
    /** Additional CSS class */
    className?: string
}

const sizeClasses = {
    sm: 'modal-sm',
    md: 'modal-md',
    lg: 'modal-lg',
    xl: 'modal-xl',
    full: 'modal-full',
}

export function Modal({
    open = false,
    onClose,
    title,
    children,
    showCloseButton = true,
    closeOnOverlayClick = true,
    closeOnEscape = true,
    size = 'md',
    className = '',
}: ModalProps) {
    const modalRef = useRef<HTMLDivElement>(null)
    const previousActiveElement = useRef<HTMLElement | null>(null)

    // Handle escape key
    useEffect(() => {
        if (!open || !closeOnEscape) return

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose?.()
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [open, closeOnEscape, onClose])

    // Trap focus and handle body scroll
    useEffect(() => {
        if (open) {
            // Save current focus
            previousActiveElement.current = document.activeElement as HTMLElement

            // Prevent body scroll
            document.body.style.overflow = 'hidden'

            // Focus the modal
            modalRef.current?.focus()
        } else {
            // Restore body scroll
            document.body.style.overflow = ''

            // Restore focus
            previousActiveElement.current?.focus()
        }

        return () => {
            document.body.style.overflow = ''
        }
    }, [open])

    if (!open) return null

    const handleOverlayClick = (e: React.MouseEvent) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
            onClose?.()
        }
    }

    return (
        <div
            className="modal-overlay"
            onClick={handleOverlayClick}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? 'modal-title' : undefined}
        >
            <div
                ref={modalRef}
                className={`modal-content ${sizeClasses[size]} ${className}`}
                tabIndex={-1}
            >
                {(title || showCloseButton) && (
                    <div className="modal-header">
                        {title && (
                            <h2 id="modal-title" className="modal-title">
                                {title}
                            </h2>
                        )}
                        {showCloseButton && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={onClose}
                                aria-label="Close modal"
                                className="modal-close"
                            >
                                <X className="w-5 h-5" />
                            </Button>
                        )}
                    </div>
                )}
                <div className="modal-body">{children}</div>
            </div>
        </div>
    )
}

// Convenience components for modal sections
export function ModalFooter({ children, className = '' }: { children: ReactNode; className?: string }) {
    return <div className={`modal-footer ${className}`}>{children}</div>
}

// Hook for managing modal state
import { useState, useCallback } from 'react'

export function useModal(initialState = false) {
    const [isOpen, setIsOpen] = useState(initialState)

    const openModal = useCallback(() => setIsOpen(true), [])
    const closeModal = useCallback(() => setIsOpen(false), [])
    const toggleModal = useCallback(() => setIsOpen(prev => !prev), [])

    return { isOpen, openModal, closeModal, toggleModal }
}

export default Modal
