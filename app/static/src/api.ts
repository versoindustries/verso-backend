/**
 * API Utilities
 * 
 * Shared utilities for making API requests with proper CSRF token handling.
 * Replaces jQuery $.ajax() calls throughout the application.
 */

// =============================================================================
// CSRF Token Handling
// =============================================================================

/**
 * Get the CSRF token from the page
 * Tries meta tag first, then cookie
 */
export function getCsrfToken(): string | null {
    // Try meta tag first
    const meta = document.querySelector('meta[name="csrf-token"]')
    if (meta) {
        return meta.getAttribute('content')
    }

    // Fallback to cookie
    const name = 'csrf_token='
    const decodedCookie = decodeURIComponent(document.cookie)
    const cookies = decodedCookie.split(';')
    for (const cookie of cookies) {
        const trimmed = cookie.trim()
        if (trimmed.indexOf(name) === 0) {
            return trimmed.substring(name.length)
        }
    }

    return null
}

// =============================================================================
// Request Configuration
// =============================================================================

interface RequestOptions extends Omit<RequestInit, 'body'> {
    body?: Record<string, any> | FormData | string
    skipCsrf?: boolean
}

export interface ApiResponse<T = any> {
    data: T | null
    error: string | null
    status: number
    ok: boolean
}

/**
 * Default headers for JSON requests
 */
function getDefaultHeaders(skipCsrf: boolean = false): HeadersInit {
    const headers: HeadersInit = {
        'X-Requested-With': 'XMLHttpRequest',
    }

    if (!skipCsrf) {
        const csrfToken = getCsrfToken()
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken
        }
    }

    return headers
}

// =============================================================================
// Core Request Functions
// =============================================================================

/**
 * Make an API request with proper error handling
 */
export async function apiRequest<T = any>(
    url: string,
    options: RequestOptions = {}
): Promise<ApiResponse<T>> {
    const { body, skipCsrf = false, ...fetchOptions } = options

    // Build headers
    const headers = new Headers(getDefaultHeaders(skipCsrf))

    // Merge custom headers
    if (fetchOptions.headers) {
        const customHeaders = new Headers(fetchOptions.headers)
        customHeaders.forEach((value, key) => {
            headers.set(key, value)
        })
    }

    // Handle body
    let processedBody: BodyInit | undefined
    if (body) {
        if (body instanceof FormData) {
            processedBody = body
            // Don't set Content-Type for FormData, browser will set it with boundary
        } else if (typeof body === 'string') {
            processedBody = body
            headers.set('Content-Type', 'application/x-www-form-urlencoded')
        } else {
            processedBody = JSON.stringify(body)
            headers.set('Content-Type', 'application/json')
        }
    }

    try {
        const response = await fetch(url, {
            ...fetchOptions,
            headers,
            body: processedBody,
            credentials: 'include', // Always include cookies for session auth
        })

        // Try to parse JSON, fall back to text
        let data: T | null = null
        const contentType = response.headers.get('content-type')
        if (contentType?.includes('application/json')) {
            data = await response.json()
        } else {
            const text = await response.text()
            data = text as any
        }

        return {
            data,
            error: response.ok ? null : `Request failed with status ${response.status}`,
            status: response.status,
            ok: response.ok,
        }
    } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        return {
            data: null,
            error: message,
            status: 0,
            ok: false,
        }
    }
}

// =============================================================================
// Convenience Methods
// =============================================================================

/**
 * GET request
 */
export async function get<T = any>(url: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return apiRequest<T>(url, { ...options, method: 'GET' })
}

/**
 * POST request with JSON body
 */
export async function post<T = any>(
    url: string,
    body?: Record<string, any> | FormData,
    options?: RequestOptions
): Promise<ApiResponse<T>> {
    return apiRequest<T>(url, { ...options, method: 'POST', body })
}

/**
 * PUT request with JSON body
 */
export async function put<T = any>(
    url: string,
    body?: Record<string, any>,
    options?: RequestOptions
): Promise<ApiResponse<T>> {
    return apiRequest<T>(url, { ...options, method: 'PUT', body })
}

/**
 * PATCH request with JSON body
 */
export async function patch<T = any>(
    url: string,
    body?: Record<string, any>,
    options?: RequestOptions
): Promise<ApiResponse<T>> {
    return apiRequest<T>(url, { ...options, method: 'PATCH', body })
}

/**
 * DELETE request
 */
export async function del<T = any>(url: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return apiRequest<T>(url, { ...options, method: 'DELETE' })
}

// =============================================================================
// Form Utilities
// =============================================================================

/**
 * Submit a form via AJAX, preserving all form data
 */
export async function submitForm<T = any>(form: HTMLFormElement): Promise<ApiResponse<T>> {
    const formData = new FormData(form)
    const url = form.action || window.location.href
    const method = form.method?.toUpperCase() || 'POST'

    return apiRequest<T>(url, {
        method,
        body: formData,
    })
}

/**
 * Convert form data to URL-encoded string
 */
export function formDataToUrlEncoded(formData: FormData): string {
    const params = new URLSearchParams()
    formData.forEach((value, key) => {
        if (typeof value === 'string') {
            params.append(key, value)
        }
    })
    return params.toString()
}

// =============================================================================
// Polling Utilities
// =============================================================================

interface PollOptions {
    interval?: number // ms between polls
    maxAttempts?: number // max number of poll attempts
    shouldStop?: (response: ApiResponse) => boolean // condition to stop polling
}

/**
 * Poll an endpoint at regular intervals
 */
export async function poll<T = any>(
    url: string,
    options: PollOptions = {}
): Promise<ApiResponse<T>> {
    const { interval = 5000, maxAttempts = 60, shouldStop } = options
    let attempts = 0

    while (attempts < maxAttempts) {
        const response = await get<T>(url)

        if (!response.ok) {
            return response
        }

        if (shouldStop && shouldStop(response)) {
            return response
        }

        attempts++
        await new Promise(resolve => setTimeout(resolve, interval))
    }

    return {
        data: null,
        error: 'Max polling attempts reached',
        status: 0,
        ok: false,
    }
}

// =============================================================================
// Export all utilities
// =============================================================================

const api = {
    getCsrfToken,
    request: apiRequest,
    get,
    post,
    put,
    patch,
    delete: del,
    submitForm,
    formDataToUrlEncoded,
    poll,
}

export default api
