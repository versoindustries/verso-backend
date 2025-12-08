/**
 * Radio Component
 * 
 * A styled radio button group.
 * 
 * Usage:
 *   <div data-react-component="Radio" data-react-props='{"name": "plan", "options": [{"value": "free", "label": "Free"}]}'></div>
 */

import { forwardRef, InputHTMLAttributes, ReactNode } from 'react'

export interface RadioOption {
    value: string
    label: ReactNode
    description?: string
    disabled?: boolean
}

export interface RadioGroupProps {
    /** Group name */
    name: string
    /** Radio options */
    options: RadioOption[]
    /** Selected value */
    value?: string
    /** Change handler */
    onChange?: (value: string) => void
    /** Error message */
    error?: string
    /** Group label */
    label?: string
    /** Layout direction */
    direction?: 'horizontal' | 'vertical'
    /** Radio size */
    size?: 'sm' | 'md' | 'lg'
    /** Container className */
    className?: string
}

export function RadioGroup({
    name,
    options,
    value,
    onChange,
    error,
    label,
    direction = 'vertical',
    size = 'md',
    className = '',
}: RadioGroupProps) {
    const groupId = `radio-group-${name}`
    const hasError = !!error

    const sizeClasses = {
        sm: 'radio-sm',
        md: 'radio-md',
        lg: 'radio-lg',
    }

    return (
        <div
            className={`radio-group ${direction === 'horizontal' ? 'radio-group-horizontal' : ''} ${className}`}
            role="radiogroup"
            aria-labelledby={label ? `${groupId}-label` : undefined}
            aria-describedby={hasError ? `${groupId}-error` : undefined}
        >
            {label && (
                <span id={`${groupId}-label`} className="radio-group-label">
                    {label}
                </span>
            )}

            <div className={`radio-options ${direction === 'horizontal' ? 'radio-options-horizontal' : ''}`}>
                {options.map((option) => (
                    <label
                        key={option.value}
                        className={`radio-label-wrapper ${sizeClasses[size]} ${option.disabled ? 'radio-disabled' : ''}`}
                    >
                        <span className="radio-input-wrapper">
                            <input
                                type="radio"
                                name={name}
                                value={option.value}
                                checked={value === option.value}
                                disabled={option.disabled}
                                onChange={() => onChange?.(option.value)}
                                className={`radio-input ${hasError ? 'radio-error' : ''}`}
                            />
                            <span className="radio-custom" aria-hidden="true" />
                        </span>

                        <span className="radio-content">
                            <span className="radio-label">{option.label}</span>
                            {option.description && (
                                <span className="radio-description">{option.description}</span>
                            )}
                        </span>
                    </label>
                ))}
            </div>

            {error && (
                <p id={`${groupId}-error`} className="radio-error-message" role="alert">
                    {error}
                </p>
            )}
        </div>
    )
}

// Single radio for controlled usage
export interface RadioProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
    label?: ReactNode
    description?: string
    size?: 'sm' | 'md' | 'lg'
    containerClassName?: string
}

export const Radio = forwardRef<HTMLInputElement, RadioProps>(
    (
        {
            label,
            description,
            size = 'md',
            containerClassName = '',
            className = '',
            ...props
        },
        ref
    ) => {
        const sizeClasses = {
            sm: 'radio-sm',
            md: 'radio-md',
            lg: 'radio-lg',
        }

        return (
            <label className={`radio-label-wrapper ${sizeClasses[size]} ${containerClassName}`}>
                <span className="radio-input-wrapper">
                    <input
                        ref={ref}
                        type="radio"
                        className={`radio-input ${className}`}
                        {...props}
                    />
                    <span className="radio-custom" aria-hidden="true" />
                </span>

                {(label || description) && (
                    <span className="radio-content">
                        {label && <span className="radio-label">{label}</span>}
                        {description && <span className="radio-description">{description}</span>}
                    </span>
                )}
            </label>
        )
    }
)

Radio.displayName = 'Radio'

export default RadioGroup
