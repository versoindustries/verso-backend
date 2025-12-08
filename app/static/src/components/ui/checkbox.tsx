/**
 * Checkbox Component
 * 
 * A styled checkbox with label.
 * 
 * Usage:
 *   <div data-react-component="Checkbox" data-react-props='{"name": "agree", "label": "I agree to the terms"}'></div>
 */

import { forwardRef, InputHTMLAttributes, ReactNode } from 'react'
import { Check, Minus } from 'lucide-react'

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
    /** Checkbox label */
    label?: ReactNode
    /** Error message */
    error?: string
    /** Helper text */
    helperText?: string
    /** Checkbox size */
    size?: 'sm' | 'md' | 'lg'
    /** Indeterminate state */
    indeterminate?: boolean
    /** Container className */
    containerClassName?: string
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
    (
        {
            label,
            error,
            helperText,
            size = 'md',
            indeterminate = false,
            containerClassName = '',
            className = '',
            id,
            ...props
        },
        ref
    ) => {
        const checkboxId = id || `checkbox-${props.name || Math.random().toString(36).substr(2, 9)}`
        const hasError = !!error

        const sizeClasses = {
            sm: 'checkbox-sm',
            md: 'checkbox-md',
            lg: 'checkbox-lg',
        }

        return (
            <div className={`checkbox-container ${containerClassName}`}>
                <label className={`checkbox-label-wrapper ${sizeClasses[size]}`}>
                    <span className="checkbox-input-wrapper">
                        <input
                            ref={ref}
                            type="checkbox"
                            id={checkboxId}
                            className={`checkbox-input ${hasError ? 'checkbox-error' : ''} ${className}`}
                            aria-invalid={hasError}
                            aria-describedby={error ? `${checkboxId}-error` : helperText ? `${checkboxId}-helper` : undefined}
                            {...props}
                        />
                        <span className="checkbox-custom" aria-hidden="true">
                            {indeterminate ? (
                                <Minus className="checkbox-icon" />
                            ) : (
                                <Check className="checkbox-icon" />
                            )}
                        </span>
                    </span>

                    {label && (
                        <span className="checkbox-label">
                            {label}
                            {props.required && <span className="checkbox-required">*</span>}
                        </span>
                    )}
                </label>

                {error && (
                    <p id={`${checkboxId}-error`} className="checkbox-error-message" role="alert">
                        {error}
                    </p>
                )}

                {!error && helperText && (
                    <p id={`${checkboxId}-helper`} className="checkbox-helper-text">
                        {helperText}
                    </p>
                )}
            </div>
        )
    }
)

Checkbox.displayName = 'Checkbox'

export default Checkbox
