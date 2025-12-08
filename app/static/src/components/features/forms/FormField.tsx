/**
 * FormField Component
 * 
 * Wrapper for form fields with label, validation, and error display.
 * This is a placeholder that will be enhanced in Phase 18.2.
 */

import { ReactNode } from 'react'

export interface FormFieldProps {
    /** Field name */
    name: string
    /** Field label */
    label?: string
    /** Error message */
    error?: string
    /** Helper text */
    helperText?: string
    /** Required field */
    required?: boolean
    /** Children (the actual input) */
    children: ReactNode
    /** Additional class */
    className?: string
}

export function FormField({
    name,
    label,
    error,
    helperText,
    required = false,
    children,
    className = '',
}: FormFieldProps) {
    const fieldId = `field-${name}`
    const hasError = !!error

    return (
        <div className={`form-field ${hasError ? 'form-field-error' : ''} ${className}`}>
            {label && (
                <label htmlFor={fieldId} className="form-field-label">
                    {label}
                    {required && <span className="form-field-required">*</span>}
                </label>
            )}

            <div className="form-field-input">
                {children}
            </div>

            {error && (
                <p className="form-field-error-message" role="alert">
                    {error}
                </p>
            )}

            {!error && helperText && (
                <p className="form-field-helper">
                    {helperText}
                </p>
            )}
        </div>
    )
}

export default FormField
