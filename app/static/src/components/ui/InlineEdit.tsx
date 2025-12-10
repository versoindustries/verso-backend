/**
 * InlineEdit Component
 * 
 * Reusable inline editing component with text input mode,
 * cancel/save functionality, and API callback pattern.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Pencil, Check, X, Loader2 } from 'lucide-react'

// =============================================================================
// Types
// =============================================================================

export interface InlineEditProps {
    /** Current value */
    value: string
    /** Callback when value is saved */
    onSave: (value: string) => Promise<void> | void
    /** Placeholder text */
    placeholder?: string
    /** Whether editing is allowed */
    editable?: boolean
    /** Element type: text, email, etc. */
    type?: 'text' | 'email' | 'number'
    /** Additional class */
    className?: string
    /** Show edit icon on hover */
    showEditIcon?: boolean
}

// =============================================================================
// Main Component
// =============================================================================

export function InlineEdit({
    value,
    onSave,
    placeholder = 'Click to edit',
    editable = true,
    type = 'text',
    className = '',
    showEditIcon = true,
}: InlineEditProps) {
    const [isEditing, setIsEditing] = useState(false)
    const [editValue, setEditValue] = useState(value)
    const [isSaving, setIsSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    // Sync with external value
    useEffect(() => {
        if (!isEditing) {
            setEditValue(value)
        }
    }, [value, isEditing])

    // Focus input when entering edit mode
    useEffect(() => {
        if (isEditing) {
            inputRef.current?.focus()
            inputRef.current?.select()
        }
    }, [isEditing])

    // Handle save
    const handleSave = useCallback(async () => {
        if (editValue === value) {
            setIsEditing(false)
            return
        }

        setIsSaving(true)
        setError(null)

        try {
            await onSave(editValue)
            setIsEditing(false)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save')
        } finally {
            setIsSaving(false)
        }
    }, [editValue, value, onSave])

    // Handle cancel
    const handleCancel = useCallback(() => {
        setEditValue(value)
        setIsEditing(false)
        setError(null)
    }, [value])

    // Handle keyboard events
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleSave()
        } else if (e.key === 'Escape') {
            handleCancel()
        }
    }, [handleSave, handleCancel])

    // Start editing
    const startEditing = useCallback(() => {
        if (editable && !isSaving) {
            setIsEditing(true)
        }
    }, [editable, isSaving])

    if (!editable) {
        return (
            <span className={`inline-edit inline-edit--readonly ${className}`}>
                {value || <span className="inline-edit__placeholder">{placeholder}</span>}
            </span>
        )
    }

    if (isEditing) {
        return (
            <div className={`inline-edit inline-edit--editing ${className}`}>
                <input
                    ref={inputRef}
                    type={type}
                    value={editValue}
                    onChange={e => setEditValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onBlur={handleSave}
                    disabled={isSaving}
                    className="inline-edit__input"
                    placeholder={placeholder}
                />
                <div className="inline-edit__actions">
                    {isSaving ? (
                        <Loader2 size={14} className="inline-edit__spinner" />
                    ) : (
                        <>
                            <button
                                type="button"
                                onClick={handleSave}
                                className="inline-edit__btn inline-edit__btn--save"
                                title="Save (Enter)"
                            >
                                <Check size={14} />
                            </button>
                            <button
                                type="button"
                                onClick={handleCancel}
                                className="inline-edit__btn inline-edit__btn--cancel"
                                title="Cancel (Esc)"
                            >
                                <X size={14} />
                            </button>
                        </>
                    )}
                </div>
                {error && <span className="inline-edit__error">{error}</span>}
            </div>
        )
    }

    return (
        <span
            className={`inline-edit inline-edit--display ${className}`}
            onClick={startEditing}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && startEditing()}
        >
            {value || <span className="inline-edit__placeholder">{placeholder}</span>}
            {showEditIcon && (
                <Pencil size={12} className="inline-edit__icon" />
            )}
        </span>
    )
}

export default InlineEdit
