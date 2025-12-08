/**
 * Input Component
 * 
 * A styled form input with label and error handling.
 * 
 * Usage:
 *   <div data-react-component="Input" data-react-props='{"name": "email", "type": "email", "label": "Email"}'></div>
 */

import { forwardRef, InputHTMLAttributes, ReactNode } from 'react'

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
    /** Input label */
    label?: string
    /** Error message */
    error?: string
    /** Helper text */
    helperText?: string
    /** Left icon/addon */
    leftIcon?: ReactNode
    /** Right icon/addon */
    rightIcon?: ReactNode
    /** Input size */
    size?: 'sm' | 'md' | 'lg'
    /** Full width */
    fullWidth?: boolean
    /** Container className */
    containerClassName?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    (
        {
            label,
            error,
            helperText,
            leftIcon,
            rightIcon,
            size = 'md',
            fullWidth = false,
            containerClassName = '',
            className = '',
            id,
            ...props
        },
        ref
    ) => {
        const inputId = id || `input-${props.name || Math.random().toString(36).substr(2, 9)}`
        const hasError = !!error

        const sizeClasses = {
            sm: 'input-sm',
            md: 'input-md',
            lg: 'input-lg',
        }

        return (
            <div className={`input-container ${fullWidth ? 'input-full-width' : ''} ${containerClassName}`}>
                {label && (
                    <label htmlFor={inputId} className="input-label">
                        {label}
                        {props.required && <span className="input-required">*</span>}
                    </label>
                )}

                <div className={`input-wrapper ${leftIcon ? 'input-has-left-icon' : ''} ${rightIcon ? 'input-has-right-icon' : ''}`}>
                    {leftIcon && <span className="input-icon input-icon-left">{leftIcon}</span>}

                    <input
                        ref={ref}
                        id={inputId}
                        className={`input ${sizeClasses[size]} ${hasError ? 'input-error' : ''} ${className}`}
                        aria-invalid={hasError}
                        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
                        {...props}
                    />

                    {rightIcon && <span className="input-icon input-icon-right">{rightIcon}</span>}
                </div>

                {error && (
                    <p id={`${inputId}-error`} className="input-error-message" role="alert">
                        {error}
                    </p>
                )}

                {!error && helperText && (
                    <p id={`${inputId}-helper`} className="input-helper-text">
                        {helperText}
                    </p>
                )}
            </div>
        )
    }
)

Input.displayName = 'Input'

export default Input
