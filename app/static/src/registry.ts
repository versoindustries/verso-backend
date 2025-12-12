/**
 * React Component Registry
 * 
 * Central registry for lazy-loaded React components used in the Islands Architecture.
 * Components are mounted to DOM elements with the `data-react-component` attribute.
 * 
 * Usage in Jinja2 templates:
 *   <div data-react-component="ComponentName" data-react-props='{"prop1": "value"}'></div>
 */

import React, { ComponentType, LazyExoticComponent } from 'react'

// Type for registered components
type LazyComponent = LazyExoticComponent<ComponentType<any>>

// Component registry map
const componentRegistry = new Map<string, LazyComponent>()

/**
 * Register a component with lazy loading
 * Supports both default exports and named exports
 */
export function registerComponent(
    name: string,
    loader: () => Promise<{ default: ComponentType<any> } | { [key: string]: ComponentType<any> }>,
    exportName?: string
) {
    const lazyComponent = React.lazy(async () => {
        const module = await loader()
        // If exportName is provided, use that export; otherwise use default or first export
        if (exportName && exportName in module) {
            return { default: (module as any)[exportName] }
        }
        if ('default' in module) {
            return module as { default: ComponentType<any> }
        }
        // Fallback: use the first exported component
        const firstExport = Object.values(module)[0]
        if (typeof firstExport === 'function') {
            return { default: firstExport as ComponentType<any> }
        }
        throw new Error(`No valid component export found for ${name}`)
    })
    componentRegistry.set(name, lazyComponent)
}

/**
 * Get a registered component by name
 */
export function getComponent(name: string): LazyComponent | undefined {
    return componentRegistry.get(name)
}

/**
 * Check if a component is registered
 */
export function hasComponent(name: string): boolean {
    return componentRegistry.has(name)
}

/**
 * Get all registered component names
 */
export function getRegisteredComponents(): string[] {
    return Array.from(componentRegistry.keys())
}

// =============================================================================
// REGISTER ALL COMPONENTS BELOW
// =============================================================================

// UI Primitives - Existing (named exports)
registerComponent('Button', () => import('./components/ui/button'), 'Button')
registerComponent('Card', () => import('./components/ui/card'), 'Card')
registerComponent('Sheet', () => import('./components/ui/sheet'), 'Sheet')

// UI Primitives - New (default exports)
registerComponent('Modal', () => import('./components/ui/modal'))
registerComponent('Toast', () => import('./components/ui/toast'))
registerComponent('Dropdown', () => import('./components/ui/dropdown'))
registerComponent('Tabs', () => import('./components/ui/tabs'))
registerComponent('Select', () => import('./components/ui/select'))
registerComponent('Input', () => import('./components/ui/input'))
registerComponent('Textarea', () => import('./components/ui/textarea'))
registerComponent('Checkbox', () => import('./components/ui/checkbox'))
registerComponent('Radio', () => import('./components/ui/radio'))
registerComponent('Badge', () => import('./components/ui/badge'))
registerComponent('Spinner', () => import('./components/ui/spinner'))
registerComponent('Table', () => import('./components/ui/table'))
registerComponent('InlineEdit', () => import('./components/ui/InlineEdit'))

// Layout Components
registerComponent('Header', () => import('./components/layout/Header'))
registerComponent('Footer', () => import('./components/layout/Footer'))
registerComponent('AlertBar', () => import('./components/layout/AlertBar'))
registerComponent('FlashAlerts', () => import('./components/layout/FlashAlerts'))
registerComponent('HomePage', () => import('./pages/HomePage'))

// Feature Components - Existing
registerComponent('Counter', () => import('./components/Counter'))
registerComponent('NotificationBell', () => import('./components/features/notifications/NotificationBell'))
registerComponent('ShoppingCartWidget', () => import('./components/features/cart/ShoppingCartWidget'))
registerComponent('BookingWizard', () => import('./components/features/booking/BookingWizard'))
registerComponent('BookingPage', () => import('./components/features/booking/BookingPage'))
registerComponent('KanbanBoard', () => import('./components/features/crm/KanbanBoard'))
registerComponent('CRMDashboard', () => import('./components/features/crm/CRMDashboard'))
registerComponent('EmailTemplateCards', () => import('./components/features/crm/EmailTemplateCards'))
registerComponent('DataTable', () => import('./components/features/admin/DataTable'))

// Feature Components - Forms (to be created)
registerComponent('ReactForm', () => import('./components/features/forms/ReactForm'))
registerComponent('FormField', () => import('./components/features/forms/FormField'))
registerComponent('FileUpload', () => import('./components/features/forms/FileUpload'))

// Feature Components - Charts (to be created)
registerComponent('Chart', () => import('./components/features/charts/Chart'))
registerComponent('KPICard', () => import('./components/features/charts/KPICard'))

// Feature Components - Calendar (to be created)
registerComponent('Calendar', () => import('./components/features/calendar/Calendar'))
registerComponent('EmployeeCalendar', () => import('./components/features/calendar/EmployeeCalendar'))
registerComponent('AdminCalendar', () => import('./components/features/calendar/AdminCalendar'))

// Feature Components - Interactive
registerComponent('ImageGallery', () => import('./components/features/interactive/ImageGallery'))

// Feature Components - Admin
registerComponent('AdminDashboard', () => import('./components/features/admin/AdminDashboard'))
registerComponent('AdminDataTable', () => import('./components/features/admin/AdminDataTable'))
registerComponent('AdminSidebar', () => import('./components/features/admin/AdminSidebar'))
registerComponent('QuickActions', () => import('./components/features/admin/QuickActions'))
registerComponent('ActivityFeed', () => import('./components/features/admin/ActivityFeed'))
registerComponent('ThemeEditor', () => import('./components/features/admin/ThemeEditor'))
registerComponent('UserManagement', () => import('./components/features/admin/UserManagement'))
registerComponent('BookingAdmin', () => import('./components/features/admin/BookingAdmin'))
registerComponent('LocationManagement', () => import('./components/features/admin/LocationManagement'))
registerComponent('UnifiedAppointmentsDashboard', () => import('./components/features/admin/UnifiedAppointmentsDashboard'))
registerComponent('DataManagement', () => import('./components/features/admin/DataManagement'))
registerComponent('UnifiedShopDashboard', () => import('./components/features/admin/UnifiedShopDashboard'))
registerComponent('UnifiedAutomationDashboard', () => import('./components/features/admin/UnifiedAutomationDashboard'))

// Feature Components - Shop
registerComponent('ShopStorefront', () => import('./components/features/shop/ShopStorefront'))
registerComponent('ProductView', () => import('./components/features/shop/ProductView'))
registerComponent('CartPage', () => import('./components/features/shop/CartPage'))

// Feature Components - Analytics
registerComponent('AnalyticsDashboard', () => import('./components/features/analytics/AnalyticsDashboard'))

// Feature Components - Messaging
registerComponent('MessagingChannel', () => import('./components/features/messaging/MessagingChannel'))
registerComponent('UnifiedMessagingDashboard', () => import('./components/features/messaging/UnifiedMessagingDashboard'))

// Feature Components - User Dashboard
registerComponent('UserDashboard', () => import('./components/features/user/UserDashboard'))
registerComponent('UnifiedUserSettingsDashboard', () => import('./components/features/user/UnifiedUserSettingsDashboard'))


// Feature Components - Subscriptions
registerComponent('SubscriptionsDashboard', () => import('./components/features/subscriptions/SubscriptionsDashboard'))

// Feature Components - Employee Dashboard
registerComponent('EmployeeDashboard', () => import('./components/features/employee/EmployeeDashboard'))

// Feature Components - Blog
registerComponent('BlogPostUtils', () => import('./components/features/blog/BlogPostUtils'))
registerComponent('BlogManagement', () => import('./components/features/blog/BlogManagement'))
registerComponent('BlogPostEditor', () => import('./components/features/blog/BlogPostEditor'))

// Feature Components - Content Editing (Phase D)
registerComponent('InlineEditor', () => import('./components/features/content/InlineEditor'))
registerComponent('PageEditorWidget', () => import('./components/features/content/PageEditorWidget'))

// Feature Components - Contact
registerComponent('ContactPage', () => import('./components/features/contact/ContactPage'))

export default componentRegistry
