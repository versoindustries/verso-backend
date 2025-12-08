/**
 * Select Component
 * 
 * A styled form select with label and error handling.
 * 
 * Usage:
 *   <div data-react-component="Select" data-react-props='{"name": "country", "options": [{"value": "us", "label": "United States"}]}'></div>
 */

import { forwardRef, SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'

export interface SelectOption {
    value: string
    label: string
    disabled?: boolean
}

export interface SelectOptionGroup {
    label: string
    options: SelectOption[]
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
    /** Select label */
    label?: string
    /** Error message */
    error?: string
    /** Helper text */
    helperText?: string
    /** Options array */
    options?: SelectOption[]
    /** Option groups */
    optionGroups?: SelectOptionGroup[]
    /** Placeholder option */
    placeholder?: string
    /** Select size */
    size?: 'sm' | 'md' | 'lg'
    /** Full width */
    fullWidth?: boolean
    /** Container className */
    containerClassName?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
    (
        {
            label,
            error,
            helperText,
            options = [],
            optionGroups = [],
            placeholder,
            size = 'md',
            fullWidth = false,
            containerClassName = '',
            className = '',
            id,
            children,
            ...props
        },
        ref
    ) => {
        const selectId = id || `select-${props.name || Math.random().toString(36).substr(2, 9)}`
        const hasError = !!error

        const sizeClasses = {
            sm: 'select-sm',
            md: 'select-md',
            lg: 'select-lg',
        }

        return (
            <div className={`select-container ${fullWidth ? 'select-full-width' : ''} ${containerClassName}`}>
                {label && (
                    <label htmlFor={selectId} className="select-label">
                        {label}
                        {props.required && <span className="select-required">*</span>}
                    </label>
                )}

                <div className="select-wrapper">
                    <select
                        ref={ref}
                        id={selectId}
                        className={`select ${sizeClasses[size]} ${hasError ? 'select-error' : ''} ${className}`}
                        aria-invalid={hasError}
                        aria-describedby={error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined}
                        {...props}
                    >
                        {placeholder && (
                            <option value="" disabled>
                                {placeholder}
                            </option>
                        )}

                        {options.map((option) => (
                            <option key={option.value} value={option.value} disabled={option.disabled}>
                                {option.label}
                            </option>
                        ))}

                        {optionGroups.map((group) => (
                            <optgroup key={group.label} label={group.label}>
                                {group.options.map((option) => (
                                    <option key={option.value} value={option.value} disabled={option.disabled}>
                                        {option.label}
                                    </option>
                                ))}
                            </optgroup>
                        ))}

                        {children}
                    </select>

                    <ChevronDown className="select-chevron" />
                </div>

                {error && (
                    <p id={`${selectId}-error`} className="select-error-message" role="alert">
                        {error}
                    </p>
                )}

                {!error && helperText && (
                    <p id={`${selectId}-helper`} className="select-helper-text">
                        {helperText}
                    </p>
                )}
            </div>
        )
    }
)

Select.displayName = 'Select'

export default Select
