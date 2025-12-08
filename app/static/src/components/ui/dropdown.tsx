/**
 * Dropdown Component
 * 
 * A dropdown menu component with proper accessibility.
 * 
 * Usage:
 *   <div data-react-component="Dropdown" data-react-props='{"trigger": "Menu", "items": [...]}'></div>
 */

import { useState, useRef, useEffect, ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'

export interface DropdownItem {
    /** Item label */
    label: string
    /** Item value or action */
    value?: string
    /** Click handler */
    onClick?: () => void
    /** Link href */
    href?: string
    /** Icon component */
    icon?: ReactNode
    /** Whether item is disabled */
    disabled?: boolean
    /** Whether item is a divider */
    divider?: boolean
    /** Danger styling */
    danger?: boolean
}

export interface DropdownProps {
    /** Trigger content */
    trigger: ReactNode
    /** Dropdown items */
    items: DropdownItem[]
    /** Alignment */
    align?: 'left' | 'right'
    /** Show chevron icon */
    showChevron?: boolean
    /** Additional CSS class for trigger */
    triggerClassName?: string
    /** Additional CSS class for menu */
    menuClassName?: string
    /** Disabled state */
    disabled?: boolean
}

export function Dropdown({
    trigger,
    items,
    align = 'left',
    showChevron = true,
    triggerClassName = '',
    menuClassName = '',
    disabled = false,
}: DropdownProps) {
    const [isOpen, setIsOpen] = useState(false)
    const dropdownRef = useRef<HTMLDivElement>(null)
    const triggerRef = useRef<HTMLButtonElement>(null)

    // Close on outside click
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside)
            return () => document.removeEventListener('mousedown', handleClickOutside)
        }
    }, [isOpen])

    // Keyboard navigation
    useEffect(() => {
        function handleKeyDown(event: KeyboardEvent) {
            if (!isOpen) return

            switch (event.key) {
                case 'Escape':
                    setIsOpen(false)
                    triggerRef.current?.focus()
                    break
                case 'ArrowDown':
                    event.preventDefault()
                    // Focus next item
                    break
                case 'ArrowUp':
                    event.preventDefault()
                    // Focus previous item
                    break
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [isOpen])

    const handleItemClick = (item: DropdownItem) => {
        if (item.disabled) return

        if (item.onClick) {
            item.onClick()
        }

        if (!item.href) {
            setIsOpen(false)
        }
    }

    return (
        <div className="dropdown" ref={dropdownRef}>
            <button
                ref={triggerRef}
                type="button"
                className={`dropdown-trigger ${triggerClassName}`}
                onClick={() => !disabled && setIsOpen(!isOpen)}
                aria-haspopup="true"
                aria-expanded={isOpen}
                disabled={disabled}
            >
                {trigger}
                {showChevron && (
                    <ChevronDown
                        className={`dropdown-chevron ${isOpen ? 'dropdown-chevron-open' : ''}`}
                    />
                )}
            </button>

            {isOpen && (
                <div
                    className={`dropdown-menu dropdown-${align} ${menuClassName}`}
                    role="menu"
                >
                    {items.map((item, index) => {
                        if (item.divider) {
                            return <div key={index} className="dropdown-divider" role="separator" />
                        }

                        const className = [
                            'dropdown-item',
                            item.disabled && 'dropdown-item-disabled',
                            item.danger && 'dropdown-item-danger',
                        ]
                            .filter(Boolean)
                            .join(' ')

                        if (item.href) {
                            return (
                                <a
                                    key={index}
                                    href={item.href}
                                    className={className}
                                    role="menuitem"
                                    onClick={() => handleItemClick(item)}
                                >
                                    {item.icon && <span className="dropdown-item-icon">{item.icon}</span>}
                                    {item.label}
                                </a>
                            )
                        }

                        return (
                            <button
                                key={index}
                                type="button"
                                className={className}
                                role="menuitem"
                                disabled={item.disabled}
                                onClick={() => handleItemClick(item)}
                            >
                                {item.icon && <span className="dropdown-item-icon">{item.icon}</span>}
                                {item.label}
                            </button>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

export default Dropdown
