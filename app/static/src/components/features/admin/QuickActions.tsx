/**
 * QuickActions Component
 * 
 * Command palette for quick admin actions, triggered by Cmd/Ctrl+K.
 * Provides search-as-you-type for admin pages and actions.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
    Search, Calendar, Users, ShoppingCart, FileText,
    Settings, BarChart3, Package, X, ArrowRight
} from 'lucide-react'

// =============================================================================
// Types
// =============================================================================

interface QuickAction {
    id: string
    label: string
    description?: string
    icon: React.ReactNode
    href?: string
    action?: () => void
    category: string
}

export interface QuickActionsProps {
    /** Whether the modal is open */
    isOpen?: boolean
    /** Callback when modal closes */
    onClose?: () => void
    /** Additional class */
    className?: string
}

// =============================================================================
// Actions Configuration
// =============================================================================

const defaultActions: QuickAction[] = [
    // Navigation
    { id: 'dashboard', label: 'Dashboard', description: 'Go to admin dashboard', icon: <BarChart3 size={18} />, href: '/admin/dashboard', category: 'Navigation' },
    { id: 'calendar', label: 'Calendar', description: 'View appointment calendar', icon: <Calendar size={18} />, href: '/calendar/view', category: 'Navigation' },
    { id: 'users', label: 'Manage Users', description: 'View and edit users', icon: <Users size={18} />, href: '/admin/users', category: 'Navigation' },
    { id: 'orders', label: 'View Orders', description: 'E-commerce orders list', icon: <ShoppingCart size={18} />, href: '/admin/shop/orders', category: 'Navigation' },
    { id: 'crm', label: 'CRM Board', description: 'Lead pipeline kanban', icon: <Users size={18} />, href: '/admin/crm/board', category: 'Navigation' },

    // Create Actions
    { id: 'new-post', label: 'New Blog Post', description: 'Write a new blog post', icon: <FileText size={18} />, href: '/blog/new', category: 'Create' },
    { id: 'new-product', label: 'New Product', description: 'Add a new product', icon: <Package size={18} />, href: '/admin/shop/products/new', category: 'Create' },

    // Settings
    { id: 'settings', label: 'Business Settings', description: 'Configure business settings', icon: <Settings size={18} />, href: '/admin/business_config', category: 'Settings' },
    { id: 'theme', label: 'Theme Editor', description: 'Customize site appearance', icon: <Settings size={18} />, href: '/admin/theme', category: 'Settings' },
]

// =============================================================================
// Main Component
// =============================================================================

export function QuickActions({
    isOpen: controlledIsOpen,
    onClose,
    className = '',
}: QuickActionsProps) {
    const [isOpen, setIsOpen] = useState(controlledIsOpen ?? false)
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedIndex, setSelectedIndex] = useState(0)
    const inputRef = useRef<HTMLInputElement>(null)
    const listRef = useRef<HTMLDivElement>(null)

    // Sync with controlled prop
    useEffect(() => {
        if (controlledIsOpen !== undefined) {
            setIsOpen(controlledIsOpen)
        }
    }, [controlledIsOpen])

    // Filter actions based on search
    const filteredActions = defaultActions.filter(action =>
        action.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        action.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        action.category.toLowerCase().includes(searchQuery.toLowerCase())
    )

    // Group actions by category
    const groupedActions = filteredActions.reduce((groups, action) => {
        const category = action.category
        if (!groups[category]) {
            groups[category] = []
        }
        groups[category].push(action)
        return groups
    }, {} as Record<string, QuickAction[]>)

    // Handle close
    const handleClose = useCallback(() => {
        setIsOpen(false)
        setSearchQuery('')
        setSelectedIndex(0)
        onClose?.()
    }, [onClose])

    // Handle action selection
    const handleSelect = useCallback((action: QuickAction) => {
        if (action.href) {
            window.location.href = action.href
        } else if (action.action) {
            action.action()
        }
        handleClose()
    }, [handleClose])

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Open with Cmd/Ctrl+K
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault()
                setIsOpen(prev => !prev)
            }

            if (!isOpen) return

            // Close with Escape
            if (e.key === 'Escape') {
                handleClose()
            }

            // Navigate with arrow keys
            if (e.key === 'ArrowDown') {
                e.preventDefault()
                setSelectedIndex(prev => Math.min(prev + 1, filteredActions.length - 1))
            }

            if (e.key === 'ArrowUp') {
                e.preventDefault()
                setSelectedIndex(prev => Math.max(prev - 1, 0))
            }

            // Select with Enter
            if (e.key === 'Enter' && filteredActions[selectedIndex]) {
                e.preventDefault()
                handleSelect(filteredActions[selectedIndex])
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [isOpen, filteredActions, selectedIndex, handleClose, handleSelect])

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 50)
        }
    }, [isOpen])

    // Reset selection when search changes
    useEffect(() => {
        setSelectedIndex(0)
    }, [searchQuery])

    // Scroll selected item into view
    useEffect(() => {
        const selectedEl = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`)
        selectedEl?.scrollIntoView({ block: 'nearest' })
    }, [selectedIndex])

    if (!isOpen) return null

    let flatIndex = 0

    return (
        <div className={`quick-actions-overlay ${className}`} onClick={handleClose}>
            <div className="quick-actions-modal" onClick={e => e.stopPropagation()}>
                {/* Search Input */}
                <div className="quick-actions-search">
                    <Search size={18} className="search-icon" />
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Search actions..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="quick-actions-input"
                    />
                    <button className="quick-actions-close" onClick={handleClose}>
                        <X size={16} />
                    </button>
                </div>

                {/* Actions List */}
                <div className="quick-actions-list" ref={listRef}>
                    {Object.entries(groupedActions).map(([category, actions]) => (
                        <div key={category} className="quick-actions-category">
                            <div className="quick-actions-category-label">{category}</div>
                            {actions.map((action) => {
                                const currentIndex = flatIndex++
                                return (
                                    <button
                                        key={action.id}
                                        data-index={currentIndex}
                                        className={`quick-actions-item ${currentIndex === selectedIndex ? 'selected' : ''}`}
                                        onClick={() => handleSelect(action)}
                                        onMouseEnter={() => setSelectedIndex(currentIndex)}
                                    >
                                        <span className="quick-actions-item-icon">{action.icon}</span>
                                        <div className="quick-actions-item-content">
                                            <span className="quick-actions-item-label">{action.label}</span>
                                            {action.description && (
                                                <span className="quick-actions-item-desc">{action.description}</span>
                                            )}
                                        </div>
                                        <ArrowRight size={14} className="quick-actions-item-arrow" />
                                    </button>
                                )
                            })}
                        </div>
                    ))}

                    {filteredActions.length === 0 && (
                        <div className="quick-actions-empty">
                            No actions found for "{searchQuery}"
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="quick-actions-footer">
                    <span><kbd>↑↓</kbd> Navigate</span>
                    <span><kbd>↵</kbd> Select</span>
                    <span><kbd>esc</kbd> Close</span>
                </div>
            </div>
        </div>
    )
}

export default QuickActions
