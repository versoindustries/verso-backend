/**
 * useToastApi Hook
 * 
 * Wraps the api module with automatic toast notifications for errors.
 * Components can import this to make API calls that show toasts on failure.
 * 
 * Usage:
 *   const { post, get } = useToastApi()
 *   const response = await post('/api/items', data)
 *   // On error, a toast is automatically shown
 */

import { useCallback } from 'react'
import { useToast } from '../components/ui/toast'
import api, { ApiResponse } from '../api'

type RequestOptions = Parameters<typeof api.request>[1]

interface UseToastApiOptions {
    /** Suppress toast on error (default: false) */
    silent?: boolean
    /** Custom error message (default: uses API error) */
    errorMessage?: string
}

export function useToastApi() {
    const toast = useToast()

    /**
     * Wrap an API call with toast error handling
     */
    const withToast = useCallback(async <T>(
        apiCall: () => Promise<ApiResponse<T>>,
        options: UseToastApiOptions = {}
    ): Promise<ApiResponse<T>> => {
        const response = await apiCall()

        if (!response.ok && !options.silent) {
            const message = options.errorMessage || response.error || 'An error occurred'
            toast.error(message)
        }

        return response
    }, [toast])

    /**
     * GET request with toast on error
     */
    const get = useCallback(<T = any>(
        url: string,
        options?: RequestOptions & UseToastApiOptions
    ): Promise<ApiResponse<T>> => {
        const { silent, errorMessage, ...requestOptions } = options || {}
        return withToast(() => api.get<T>(url, requestOptions), { silent, errorMessage })
    }, [withToast])

    /**
     * POST request with toast on error
     */
    const post = useCallback(<T = any>(
        url: string,
        body?: Record<string, any> | FormData,
        options?: RequestOptions & UseToastApiOptions
    ): Promise<ApiResponse<T>> => {
        const { silent, errorMessage, ...requestOptions } = options || {}
        return withToast(() => api.post<T>(url, body, requestOptions), { silent, errorMessage })
    }, [withToast])

    /**
     * PUT request with toast on error
     */
    const put = useCallback(<T = any>(
        url: string,
        body?: Record<string, any>,
        options?: RequestOptions & UseToastApiOptions
    ): Promise<ApiResponse<T>> => {
        const { silent, errorMessage, ...requestOptions } = options || {}
        return withToast(() => api.put<T>(url, body, requestOptions), { silent, errorMessage })
    }, [withToast])

    /**
     * DELETE request with toast on error
     */
    const del = useCallback(<T = any>(
        url: string,
        options?: RequestOptions & UseToastApiOptions
    ): Promise<ApiResponse<T>> => {
        const { silent, errorMessage, ...requestOptions } = options || {}
        return withToast(() => api.delete<T>(url, requestOptions), { silent, errorMessage })
    }, [withToast])

    /**
     * Show success toast
     */
    const success = useCallback((message: string) => {
        toast.success(message)
    }, [toast])

    /**
     * Show error toast manually
     */
    const error = useCallback((message: string) => {
        toast.error(message)
    }, [toast])

    return {
        get,
        post,
        put,
        delete: del,
        success,
        error,
        withToast,
        // Raw toast access for custom scenarios
        toast,
    }
}

export default useToastApi
