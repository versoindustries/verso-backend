/**
 * AdminSidebar Component
 * 
 * Collapsible navigation sidebar for admin pages with categorized links,
 * theme variable integration, and localStorage persistence.
 */

import { useState, useEffect } from 'react'
import {
    LayoutDashboard, Users, ShoppingCart, FileText, Mail,
    Calendar, BarChart3, Palette, Database, MapPin,
    History, Building, MessageSquare, FileEdit, ChevronLeft,
    ChevronRight, Kanban, ClipboardList, Zap
} from 'lucide-react'

// =============================================================================
// Types
// =============================================================================

interface NavItem {
    label: string
    href: string
    icon: React.ReactNode
    badge?: number
}

interface NavCategory {
    label: string
    items: NavItem[]
}

export interface AdminSidebarProps {
    /** Current active path */
    activePath?: string
    /** URL mappings from window.versoContext.urls */
    urls?: Record<string, string>
    /** Additional class */
    className?: string
}

// =============================================================================
// Navigation Configuration
// =============================================================================

function getNavCategories(_urls: Record<string, string>): NavCategory[] {
    return [
        {
            label: 'Overview',
            items: [
                { label: 'Dashboard', href: '/admin/dashboard', icon: <LayoutDashboard size={18} /> },
                { label: 'Calendar', href: '/calendar/view', icon: <Calendar size={18} /> },
            ]
        },
        {
            label: 'CRM',
            items: [
                { label: 'CRM Dashboard', href: '/admin/crm/dashboard', icon: <Kanban size={18} /> },
                { label: 'Duplicates', href: '/admin/crm/duplicates', icon: <Users size={18} /> },
            ]
        },
        {
            label: 'E-Commerce',
            items: [
                { label: 'Orders', href: '/admin/shop/orders', icon: <ShoppingCart size={18} /> },
                { label: 'Products', href: '/admin/shop/products', icon: <ClipboardList size={18} /> },
            ]
        },
        {
            label: 'Content',
            items: [
                { label: 'Blog Posts', href: '/blog/manage', icon: <FileEdit size={18} /> },
                { label: 'Pages', href: '/admin/pages', icon: <FileText size={18} /> },
            ]
        },
        {
            label: 'Communications',
            items: [
                { label: 'Email Templates', href: '/admin/email/templates', icon: <Mail size={18} /> },
                { label: 'Messaging', href: '/messaging/', icon: <MessageSquare size={18} /> },
            ]
        },
        {
            label: 'Analytics',
            items: [
                { label: 'Analytics', href: '/admin/analytics', icon: <BarChart3 size={18} /> },
            ]
        },
        {
            label: 'Settings',
            items: [
                { label: 'User Management', href: '/admin/user-management', icon: <Users size={18} /> },
                { label: 'Locations', href: '/admin/locations', icon: <MapPin size={18} /> },
                { label: 'Business Config', href: '/admin/business_config', icon: <Building size={18} /> },
                { label: 'Theme Editor', href: '/admin/theme', icon: <Palette size={18} /> },
                { label: 'Audit Logs', href: '/admin/audit-logs', icon: <History size={18} /> },
                { label: 'Data Management', href: '/admin/data-management', icon: <Database size={18} /> },
            ]
        },
        {
            label: 'Scheduling',
            items: [
                { label: 'Booking', href: '/admin/booking', icon: <Calendar size={18} /> },
                { label: 'Automation', href: '/admin/automation', icon: <Zap size={18} /> },
            ]
        }
    ]
}

// =============================================================================
// Main Component
// =============================================================================

export function AdminSidebar({
    activePath = '',
    urls = {},
    className = '',
}: AdminSidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('admin-sidebar-collapsed') === 'true'
        }
        return false
    })
    const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Overview', 'Settings']))

    // Persist collapse state
    useEffect(() => {
        localStorage.setItem('admin-sidebar-collapsed', String(isCollapsed))
    }, [isCollapsed])

    // Get current path
    const currentPath = activePath || (typeof window !== 'undefined' ? window.location.pathname : '')

    const navCategories = getNavCategories(urls)

    const toggleCategory = (label: string) => {
        setExpandedCategories(prev => {
            const next = new Set(prev)
            if (next.has(label)) {
                next.delete(label)
            } else {
                next.add(label)
            }
            return next
        })
    }

    const isActive = (href: string) => currentPath === href || currentPath.startsWith(href + '/')

    return (
        <aside className={`admin-sidebar ${isCollapsed ? 'collapsed' : ''} ${className}`}>
            {/* Header */}
            <div className="admin-sidebar-header">
                {!isCollapsed && <span className="admin-sidebar-title">Admin</span>}
                <button
                    className="admin-sidebar-toggle"
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                    {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            {/* Navigation */}
            <nav className="admin-sidebar-nav">
                {navCategories.map((category) => (
                    <div key={category.label} className="admin-sidebar-category">
                        {!isCollapsed && (
                            <button
                                className="admin-sidebar-category-header"
                                onClick={() => toggleCategory(category.label)}
                            >
                                <span>{category.label}</span>
                                <ChevronRight
                                    size={14}
                                    className={`category-chevron ${expandedCategories.has(category.label) ? 'expanded' : ''}`}
                                />
                            </button>
                        )}

                        {(isCollapsed || expandedCategories.has(category.label)) && (
                            <ul className="admin-sidebar-items">
                                {category.items.map((item) => (
                                    <li key={item.href}>
                                        <a
                                            href={item.href}
                                            className={`admin-sidebar-link ${isActive(item.href) ? 'active' : ''}`}
                                            title={isCollapsed ? item.label : undefined}
                                        >
                                            {item.icon}
                                            {!isCollapsed && <span>{item.label}</span>}
                                            {item.badge && !isCollapsed && (
                                                <span className="admin-sidebar-badge">{item.badge}</span>
                                            )}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                ))}
            </nav>
        </aside>
    )
}

export default AdminSidebar
