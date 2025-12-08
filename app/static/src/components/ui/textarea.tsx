/**
 * Textarea Component
 * 
 * A styled form textarea with label and error handling.
 * 
 * Usage:
 *   <div data-react-component="Textarea" data-react-props='{"name": "message", "label": "Message"}'></div>
 */

import { forwardRef, TextareaHTMLAttributes } from 'react'

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    /** Textarea label */
    label?: string
    /** Error message */
    error?: string
    /** Helper text */
    helperText?: string
    /** Show character count */
    showCount?: boolean
    /** Full width */
    fullWidth?: boolean
    /** Container className */
    containerClassName?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    (
        {
            label,
            error,
            helperText,
            showCount = false,
            fullWidth = false,
            containerClassName = '',
            className = '',
            id,
            maxLength,
            value,
            ...props
        },
        ref
    ) => {
        const textareaId = id || `textarea-${props.name || Math.random().toString(36).substr(2, 9)}`
        const hasError = !!error
        const charCount = typeof value === 'string' ? value.length : 0

        return (
            <div className={`textarea-container ${fullWidth ? 'textarea-full-width' : ''} ${containerClassName}`}>
                {label && (
                    <label htmlFor={textareaId} className="textarea-label">
                        {label}
                        {props.required && <span className="textarea-required">*</span>}
                    </label>
                )}

                <textarea
                    ref={ref}
                    id={textareaId}
                    className={`textarea ${hasError ? 'textarea-error' : ''} ${className}`}
                    aria-invalid={hasError}
                    aria-describedby={error ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : undefined}
                    maxLength={maxLength}
                    value={value}
                    {...props}
                />

                <div className="textarea-footer">
                    {error && (
                        <p id={`${textareaId}-error`} className="textarea-error-message" role="alert">
                            {error}
                        </p>
                    )}

                    {!error && helperText && (
                        <p id={`${textareaId}-helper`} className="textarea-helper-text">
                            {helperText}
                        </p>
                    )}

                    {showCount && maxLength && (
                        <span className="textarea-count">
                            {charCount}/{maxLength}
                        </span>
                    )}
                </div>
            </div>
        )
    }
)

Textarea.displayName = 'Textarea'

export default Textarea
