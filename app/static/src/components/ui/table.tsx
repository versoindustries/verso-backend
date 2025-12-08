/**
 * Table Component
 * 
 * Table primitives for building data tables.
 * 
 * Usage:
 *   <Table>
 *     <TableHeader>
 *       <TableRow><TableHead>Name</TableHead></TableRow>
 *     </TableHeader>
 *     <TableBody>
 *       <TableRow><TableCell>John</TableCell></TableRow>
 *     </TableBody>
 *   </Table>
 */

import { forwardRef, HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes, ReactNode } from 'react'

// =============================================================================
// Table Root
// =============================================================================

export interface TableProps extends HTMLAttributes<HTMLTableElement> {
    /** Striped rows */
    striped?: boolean
    /** Hoverable rows */
    hoverable?: boolean
    /** Compact size */
    compact?: boolean
    /** Bordered */
    bordered?: boolean
    /** Container className */
    containerClassName?: string
}

export const Table = forwardRef<HTMLTableElement, TableProps>(
    (
        {
            striped = false,
            hoverable = true,
            compact = false,
            bordered = false,
            containerClassName = '',
            className = '',
            children,
            ...props
        },
        ref
    ) => {
        return (
            <div className={`table-container ${containerClassName}`}>
                <table
                    ref={ref}
                    className={`table ${striped ? 'table-striped' : ''} ${hoverable ? 'table-hoverable' : ''} ${compact ? 'table-compact' : ''} ${bordered ? 'table-bordered' : ''} ${className}`}
                    {...props}
                >
                    {children}
                </table>
            </div>
        )
    }
)

Table.displayName = 'Table'

// =============================================================================
// Table Header
// =============================================================================

export const TableHeader = forwardRef<
    HTMLTableSectionElement,
    HTMLAttributes<HTMLTableSectionElement>
>(({ className = '', ...props }, ref) => (
    <thead ref={ref} className={`table-header ${className}`} {...props} />
))

TableHeader.displayName = 'TableHeader'

// =============================================================================
// Table Body
// =============================================================================

export const TableBody = forwardRef<
    HTMLTableSectionElement,
    HTMLAttributes<HTMLTableSectionElement>
>(({ className = '', ...props }, ref) => (
    <tbody ref={ref} className={`table-body ${className}`} {...props} />
))

TableBody.displayName = 'TableBody'

// =============================================================================
// Table Footer
// =============================================================================

export const TableFooter = forwardRef<
    HTMLTableSectionElement,
    HTMLAttributes<HTMLTableSectionElement>
>(({ className = '', ...props }, ref) => (
    <tfoot ref={ref} className={`table-footer ${className}`} {...props} />
))

TableFooter.displayName = 'TableFooter'

// =============================================================================
// Table Row
// =============================================================================

export interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> {
    selected?: boolean
}

export const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
    ({ selected = false, className = '', ...props }, ref) => (
        <tr
            ref={ref}
            className={`table-row ${selected ? 'table-row-selected' : ''} ${className}`}
            aria-selected={selected}
            {...props}
        />
    )
)

TableRow.displayName = 'TableRow'

// =============================================================================
// Table Head Cell
// =============================================================================

export interface TableHeadProps extends ThHTMLAttributes<HTMLTableCellElement> {
    sortable?: boolean
    sorted?: 'asc' | 'desc' | false
    onSort?: () => void
}

export const TableHead = forwardRef<HTMLTableCellElement, TableHeadProps>(
    ({ sortable = false, sorted = false, onSort, className = '', children, ...props }, ref) => {
        const handleKeyDown = (e: React.KeyboardEvent) => {
            if (sortable && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault()
                onSort?.()
            }
        }

        return (
            <th
                ref={ref}
                className={`table-head ${sortable ? 'table-head-sortable' : ''} ${sorted ? `table-head-sorted-${sorted}` : ''} ${className}`}
                onClick={sortable ? onSort : undefined}
                onKeyDown={handleKeyDown}
                tabIndex={sortable ? 0 : undefined}
                aria-sort={sorted ? (sorted === 'asc' ? 'ascending' : 'descending') : undefined}
                {...props}
            >
                <span className="table-head-content">
                    {children}
                    {sortable && (
                        <span className="table-sort-icon" aria-hidden="true">
                            {sorted === 'asc' ? '↑' : sorted === 'desc' ? '↓' : '↕'}
                        </span>
                    )}
                </span>
            </th>
        )
    }
)

TableHead.displayName = 'TableHead'

// =============================================================================
// Table Cell
// =============================================================================

export const TableCell = forwardRef<HTMLTableCellElement, TdHTMLAttributes<HTMLTableCellElement>>(
    ({ className = '', ...props }, ref) => (
        <td ref={ref} className={`table-cell ${className}`} {...props} />
    )
)

TableCell.displayName = 'TableCell'

// =============================================================================
// Table Caption
// =============================================================================

export const TableCaption = forwardRef<
    HTMLTableCaptionElement,
    HTMLAttributes<HTMLTableCaptionElement>
>(({ className = '', ...props }, ref) => (
    <caption ref={ref} className={`table-caption ${className}`} {...props} />
))

TableCaption.displayName = 'TableCaption'

// =============================================================================
// Empty State
// =============================================================================

export interface TableEmptyProps {
    colSpan: number
    message?: string
    icon?: ReactNode
    children?: ReactNode
}

export function TableEmpty({
    colSpan,
    message = 'No data available',
    icon,
    children,
}: TableEmptyProps) {
    return (
        <TableRow>
            <TableCell colSpan={colSpan} className="table-empty">
                {icon && <span className="table-empty-icon">{icon}</span>}
                <span className="table-empty-message">{message}</span>
                {children}
            </TableCell>
        </TableRow>
    )
}

export default Table
