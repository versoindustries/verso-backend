/**
 * ReactForm Component
 * 
 * A form wrapper that handles submission, validation, and CSRF tokens.
 * This is a placeholder that will be enhanced in Phase 18.2.
 */

import { FormEvent, ReactNode, useState } from 'react'
import api from '../../../api'
import { Spinner } from '../../ui/spinner'

export interface ReactFormProps {
    /** Form action URL */
    action?: string
    /** HTTP method */
    method?: 'POST' | 'PUT' | 'PATCH' | 'DELETE'
    /** Success callback */
    onSuccess?: (data: any) => void
    /** Error callback */
    onError?: (error: string) => void
    /** Children */
    children: ReactNode
    /** Additional class */
    className?: string
    /** Redirect on success */
    redirectTo?: string
}

export function ReactForm({
    action,
    method = 'POST',
    onSuccess,
    onError,
    children,
    className = '',
    redirectTo,
}: ReactFormProps) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        const form = e.currentTarget
        const formData = new FormData(form)
        const url = action || form.action || window.location.href

        try {
            const response = await api.post(url, formData, { method })

            if (response.ok) {
                onSuccess?.(response.data)
                if (redirectTo) {
                    window.location.href = redirectTo
                }
            } else {
                const errorMsg = response.error || 'Form submission failed'
                setError(errorMsg)
                onError?.(errorMsg)
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Unknown error'
            setError(errorMsg)
            onError?.(errorMsg)
        } finally {
            setLoading(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className={`react-form ${className}`}>
            {error && (
                <div className="react-form-error" role="alert">
                    {error}
                </div>
            )}
            {children}
            {loading && <Spinner className="react-form-spinner" />}
        </form>
    )
}

export default ReactForm
