/**
 * Tabs Component
 * 
 * A tab panel component with proper accessibility.
 * 
 * Usage:
 *   <div data-react-component="Tabs" data-react-props='{"tabs": [{"id": "tab1", "label": "Tab 1", "content": "..."}]}'></div>
 */

import { useState, useRef, ReactNode, KeyboardEvent } from 'react'

export interface Tab {
    /** Unique tab identifier */
    id: string
    /** Tab label */
    label: string | ReactNode
    /** Tab content */
    content?: ReactNode
    /** Tab icon */
    icon?: ReactNode
    /** Disabled state */
    disabled?: boolean
    /** Badge count */
    badge?: number
}

export interface TabsProps {
    /** Array of tabs */
    tabs: Tab[]
    /** Currently active tab ID */
    activeTab?: string
    /** Callback when tab changes */
    onTabChange?: (tabId: string) => void
    /** Tab variant */
    variant?: 'default' | 'pills' | 'underline'
    /** Full width tabs */
    fullWidth?: boolean
    /** Additional CSS class */
    className?: string
    /** Render content */
    renderContent?: boolean
}

export function Tabs({
    tabs,
    activeTab: controlledActiveTab,
    onTabChange,
    variant = 'default',
    fullWidth = false,
    className = '',
    renderContent = true,
}: TabsProps) {
    // Use controlled or uncontrolled state
    const [internalActiveTab, setInternalActiveTab] = useState(tabs[0]?.id || '')
    const activeTab = controlledActiveTab ?? internalActiveTab

    const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map())

    const handleTabChange = (tabId: string) => {
        if (!controlledActiveTab) {
            setInternalActiveTab(tabId)
        }
        onTabChange?.(tabId)
    }

    // Keyboard navigation
    const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
        const enabledTabs = tabs.filter(t => !t.disabled)
        const currentEnabledIndex = enabledTabs.findIndex(t => t.id === tabs[currentIndex].id)

        let nextTab: Tab | undefined

        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault()
                nextTab = enabledTabs[currentEnabledIndex - 1] || enabledTabs[enabledTabs.length - 1]
                break
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault()
                nextTab = enabledTabs[currentEnabledIndex + 1] || enabledTabs[0]
                break
            case 'Home':
                e.preventDefault()
                nextTab = enabledTabs[0]
                break
            case 'End':
                e.preventDefault()
                nextTab = enabledTabs[enabledTabs.length - 1]
                break
        }

        if (nextTab) {
            handleTabChange(nextTab.id)
            tabRefs.current.get(nextTab.id)?.focus()
        }
    }

    const activeTabData = tabs.find(t => t.id === activeTab)

    return (
        <div className={`tabs tabs-${variant} ${className}`}>
            <div
                className={`tabs-list ${fullWidth ? 'tabs-full-width' : ''}`}
                role="tablist"
                aria-orientation="horizontal"
            >
                {tabs.map((tab, index) => (
                    <button
                        key={tab.id}
                        ref={(el) => el && tabRefs.current.set(tab.id, el)}
                        type="button"
                        role="tab"
                        id={`tab-${tab.id}`}
                        aria-selected={activeTab === tab.id}
                        aria-controls={`tabpanel-${tab.id}`}
                        tabIndex={activeTab === tab.id ? 0 : -1}
                        disabled={tab.disabled}
                        className={`tab ${activeTab === tab.id ? 'tab-active' : ''} ${tab.disabled ? 'tab-disabled' : ''}`}
                        onClick={() => !tab.disabled && handleTabChange(tab.id)}
                        onKeyDown={(e) => handleKeyDown(e, index)}
                    >
                        {tab.icon && <span className="tab-icon">{tab.icon}</span>}
                        <span className="tab-label">{tab.label}</span>
                        {tab.badge !== undefined && (
                            <span className="tab-badge">{tab.badge}</span>
                        )}
                    </button>
                ))}
            </div>

            {renderContent && activeTabData && (
                <div
                    id={`tabpanel-${activeTab}`}
                    role="tabpanel"
                    aria-labelledby={`tab-${activeTab}`}
                    className="tabs-content"
                    tabIndex={0}
                >
                    {activeTabData.content}
                </div>
            )}
        </div>
    )
}

// Convenience component for building tabs declaratively
export function TabPanel({
    children,
    className = '',
}: {
    children: ReactNode
    className?: string
}) {
    return <div className={`tab-panel ${className}`}>{children}</div>
}

export default Tabs
