/**
 * React Islands Architecture - Main Entry Point
 * 
 * This module handles mounting React components into Jinja2 templates.
 * Components are identified by the `data-react-component` attribute on DOM elements.
 * Props can be passed via `data-react-props` as a JSON string.
 * 
 * Key features:
 * - Lazy loading of components via registry
 * - MutationObserver for dynamically added content (HTMX, AJAX)
 * - Error boundaries for component isolation
 * - Proper cleanup on unmount
 * - Global toast notifications via ToastProvider
 */

import React, { Component, ErrorInfo, ReactNode, Suspense } from 'react'
import ReactDOM from 'react-dom/client'
// Import the entire registry module to ensure all registerComponent calls execute
import './registry'
import { getComponent, hasComponent, getRegisteredComponents } from './registry'
import { ToastProvider } from './components/ui/toast'
import './index.css'

// =============================================================================
// Error Boundary Component
// =============================================================================

interface ErrorBoundaryProps {
    componentName: string
    children: ReactNode
}

interface ErrorBoundaryState {
    hasError: boolean
    error: Error | null
}

class ComponentErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`Error in React component "${this.props.componentName}":`, error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="react-component-error" style={{
                    padding: '1rem',
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '0.375rem',
                    color: '#991b1b',
                    fontSize: '0.875rem'
                }}>
                    <strong>Component Error:</strong> {this.props.componentName}
                    <br />
                    <small>{this.state.error?.message}</small>
                </div>
            )
        }

        return this.props.children
    }
}

// =============================================================================
// Loading Fallback
// =============================================================================

interface LoadingProps {
    componentName: string
}

function LoadingFallback({ componentName }: LoadingProps) {
    return (
        <div className="react-component-loading" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1rem',
            color: '#6b7280'
        }}>
            <svg
                className="animate-spin"
                style={{
                    animation: 'spin 1s linear infinite',
                    height: '1.25rem',
                    width: '1.25rem',
                    marginRight: '0.5rem'
                }}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
            >
                <circle
                    style={{ opacity: 0.25 }}
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                />
                <path
                    style={{ opacity: 0.75 }}
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
            </svg>
            Loading {componentName}...
        </div>
    )
}

// =============================================================================
// Component Mounting
// =============================================================================

// Track mounted roots for cleanup
const mountedRoots = new WeakMap<Element, ReactDOM.Root>()

/**
 * Parse props from data attribute
 */
function parseProps(element: Element): Record<string, any> {
    const propsStr = element.getAttribute('data-react-props')
    if (!propsStr) {
        return {}
    }

    try {
        return JSON.parse(propsStr)
    } catch (err) {
        console.error('Failed to parse React props:', err)
        return {}
    }
}

/**
 * Mount a React component to a DOM element
 */
function mountComponent(element: Element): void {
    // Skip if already mounted
    if (element.hasAttribute('data-react-mounted')) {
        return
    }

    const componentName = element.getAttribute('data-react-component')
    if (!componentName) {
        console.warn('Element has data-react-component attribute but no component name')
        return
    }

    // Check if component is registered
    if (!hasComponent(componentName)) {
        console.warn(
            `React component "${componentName}" not found in registry. ` +
            `Available components: ${getRegisteredComponents().join(', ')}`
        )
        return
    }

    const Component = getComponent(componentName)!
    const props = parseProps(element)

    // Create React root and mount
    const root = ReactDOM.createRoot(element)
    mountedRoots.set(element, root)

    root.render(
        <React.StrictMode>
            <ToastProvider position="top-right" maxToasts={5}>
                <ComponentErrorBoundary componentName={componentName}>
                    <Suspense fallback={<LoadingFallback componentName={componentName} />}>
                        <Component {...props} />
                    </Suspense>
                </ComponentErrorBoundary>
            </ToastProvider>
        </React.StrictMode>
    )

    // Mark as mounted
    element.setAttribute('data-react-mounted', 'true')
}

/**
 * Unmount a React component from a DOM element
 */
function unmountComponent(element: Element): void {
    const root = mountedRoots.get(element)
    if (root) {
        root.unmount()
        mountedRoots.delete(element)
        element.removeAttribute('data-react-mounted')
    }
}

/**
 * Mount all React components in a container (or document)
 */
function mountComponents(container: Element | Document = document): void {
    const elements = container.querySelectorAll('[data-react-component]')
    elements.forEach(mountComponent)
}

/**
 * Unmount all React components in a container
 */
function unmountComponents(container: Element | Document = document): void {
    const elements = container.querySelectorAll('[data-react-mounted]')
    elements.forEach(unmountComponent)
}

// =============================================================================
// MutationObserver for Dynamic Content
// =============================================================================

let observer: MutationObserver | null = null

/**
 * Start observing DOM for dynamically added React components
 */
function startObserving(): void {
    if (observer) {
        return
    }

    observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            // Handle added nodes
            for (const node of mutation.addedNodes) {
                if (node instanceof Element) {
                    // Check if the node itself is a React component
                    if (node.hasAttribute('data-react-component')) {
                        mountComponent(node)
                    }
                    // Check for nested React components
                    mountComponents(node)
                }
            }

            // Handle removed nodes - cleanup
            for (const node of mutation.removedNodes) {
                if (node instanceof Element) {
                    if (node.hasAttribute('data-react-mounted')) {
                        unmountComponent(node)
                    }
                    // Cleanup nested components
                    const nestedMounted = node.querySelectorAll('[data-react-mounted]')
                    nestedMounted.forEach(unmountComponent)
                }
            }
        }
    })

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    })
}

/**
 * Stop observing DOM mutations
 */
function stopObserving(): void {
    if (observer) {
        observer.disconnect()
        observer = null
    }
}

// =============================================================================
// Global API
// =============================================================================

// Expose utilities globally for manual triggering from Jinja2/JS
declare global {
    interface Window {
        ReactIslands: {
            mount: typeof mountComponents
            unmount: typeof unmountComponents
            mountElement: typeof mountComponent
            unmountElement: typeof unmountComponent
            startObserving: typeof startObserving
            stopObserving: typeof stopObserving
            getRegisteredComponents: typeof getRegisteredComponents
        }
    }
}

window.ReactIslands = {
    mount: mountComponents,
    unmount: unmountComponents,
    mountElement: mountComponent,
    unmountElement: unmountComponent,
    startObserving,
    stopObserving,
    getRegisteredComponents,
}

// =============================================================================
// Initialization
// =============================================================================

/**
 * Initialize React Islands
 */
function init(): void {
    // Mount all existing components
    mountComponents()

    // Start observing for dynamic content
    startObserving()
}

// Mount on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
} else {
    init()
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopObserving()
    unmountComponents()
})

// Add CSS for spinner animation
const style = document.createElement('style')
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`
document.head.appendChild(style)
