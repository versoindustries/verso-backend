/**
 * AdminDataTable Component
 * 
 * Enhanced data table with bulk actions, export, and pagination.
 * Replaces jQuery DataTables for admin interfaces.
 */

import { useState, useMemo, useCallback } from 'react'
import {
    ChevronDown, ChevronUp, ChevronsUpDown,
    ChevronLeft, ChevronRight, Search, Download
} from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

export interface Column {
    accessorKey: string
    header: string
    sortable?: boolean
    /** If true, render cell value as HTML using dangerouslySetInnerHTML */
    html?: boolean
    cell?: (value: any, row: any) => React.ReactNode
}

export interface BulkAction {
    value: string
    label: string
    icon?: React.ReactNode
    confirmMessage?: string
    destructive?: boolean
}

export interface AdminDataTableProps {
    /** Column definitions */
    columns: Column[]
    /** Initial data */
    data?: any[]
    /** Row ID key */
    idKey?: string
    /** Bulk actions to display */
    bulkActions?: BulkAction[]
    /** Bulk action URL */
    bulkActionUrl?: string
    /** Export CSV URL */
    exportCsvUrl?: string
    /** CSRF token */
    csrfToken?: string
    /** Page size options */
    pageSizeOptions?: number[]
    /** Default page size */
    defaultPageSize?: number
    /** Empty state message */
    emptyMessage?: string
    /** Additional class */
    className?: string
    /** Row click handler */
    onRowClick?: (row: any) => void
}

// =============================================================================
// Main Component
// =============================================================================

export function AdminDataTable({
    columns,
    data: initialData = [],
    idKey = 'id',
    bulkActions = [],
    bulkActionUrl,
    exportCsvUrl,
    pageSizeOptions = [10, 25, 50, 100],
    defaultPageSize = 25,
    emptyMessage = 'No data available',
    className = '',
    onRowClick,
}: AdminDataTableProps) {
    const [data] = useState<any[]>(initialData)
    const [sorting, setSorting] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null)
    const [globalFilter, setGlobalFilter] = useState('')
    const [currentPage, setCurrentPage] = useState(1)
    const [pageSize, setPageSize] = useState(defaultPageSize)
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set())
    const [selectedAction, setSelectedAction] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

    // Filter data
    const filteredData = useMemo(() => {
        if (!globalFilter) return data
        const lower = globalFilter.toLowerCase()
        return data.filter(row =>
            Object.values(row).some(val =>
                String(val).toLowerCase().includes(lower)
            )
        )
    }, [data, globalFilter])

    // Sort data
    const sortedData = useMemo(() => {
        if (!sorting) return filteredData
        return [...filteredData].sort((a, b) => {
            const valA = a[sorting.key]
            const valB = b[sorting.key]
            if (valA < valB) return sorting.direction === 'asc' ? -1 : 1
            if (valA > valB) return sorting.direction === 'asc' ? 1 : -1
            return 0
        })
    }, [filteredData, sorting])

    // Paginate data
    const paginatedData = useMemo(() => {
        const start = (currentPage - 1) * pageSize
        return sortedData.slice(start, start + pageSize)
    }, [sortedData, currentPage, pageSize])

    const totalPages = Math.ceil(sortedData.length / pageSize)
    const startRow = (currentPage - 1) * pageSize + 1
    const endRow = Math.min(currentPage * pageSize, sortedData.length)

    // Handle sort
    const handleSort = useCallback((key: string) => {
        setSorting(current => {
            if (current?.key === key) {
                return current.direction === 'asc'
                    ? { key, direction: 'desc' }
                    : null
            }
            return { key, direction: 'asc' }
        })
    }, [])

    // Handle select all
    const handleSelectAll = useCallback((checked: boolean) => {
        if (checked) {
            setSelectedIds(new Set(paginatedData.map(row => row[idKey])))
        } else {
            setSelectedIds(new Set())
        }
    }, [paginatedData, idKey])

    // Handle row select
    const handleRowSelect = useCallback((id: string | number, checked: boolean) => {
        setSelectedIds(prev => {
            const newSet = new Set(prev)
            if (checked) {
                newSet.add(id)
            } else {
                newSet.delete(id)
            }
            return newSet
        })
    }, [])

    // Handle bulk action
    const handleBulkAction = async () => {
        if (!selectedAction || selectedIds.size === 0 || !bulkActionUrl) return

        const action = bulkActions.find(a => a.value === selectedAction)
        if (action?.confirmMessage) {
            const confirmed = window.confirm(
                action.confirmMessage.replace('{count}', String(selectedIds.size))
            )
            if (!confirmed) return
        }

        setLoading(true)
        setMessage(null)

        try {
            const response = await api.post(bulkActionUrl, {
                action: selectedAction,
                user_ids: Array.from(selectedIds),
            })

            if (response.ok) {
                setMessage({ type: 'success', text: `Action applied to ${selectedIds.size} item(s)` })
                setSelectedIds(new Set())
                setSelectedAction('')
                // Reload page to reflect changes
                setTimeout(() => window.location.reload(), 1500)
            } else {
                setMessage({ type: 'error', text: response.error || 'Action failed' })
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to execute action' })
        } finally {
            setLoading(false)
        }
    }

    // Check if all on current page are selected
    const allSelected = paginatedData.length > 0 &&
        paginatedData.every(row => selectedIds.has(row[idKey]))
    const someSelected = selectedIds.size > 0 && !allSelected

    return (
        <div className={`admin-data-table ${className}`}>
            {/* Toolbar */}
            <div className="admin-data-table-toolbar">
                {/* Search */}
                <div className="admin-data-table-search">
                    <Search className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search..."
                        value={globalFilter}
                        onChange={(e) => {
                            setGlobalFilter(e.target.value)
                            setCurrentPage(1)
                        }}
                    />
                </div>

                {/* Bulk Actions */}
                {bulkActions.length > 0 && (
                    <div className="admin-data-table-bulk">
                        <select
                            value={selectedAction}
                            onChange={(e) => setSelectedAction(e.target.value)}
                        >
                            <option value="">Select action...</option>
                            {bulkActions.map(action => (
                                <option key={action.value} value={action.value}>
                                    {action.label}
                                </option>
                            ))}
                        </select>
                        <button
                            onClick={handleBulkAction}
                            disabled={loading || !selectedAction || selectedIds.size === 0}
                        >
                            {loading ? 'Applying...' : 'Apply'}
                        </button>
                        <span className="selected-count">
                            {selectedIds.size} selected
                        </span>
                    </div>
                )}

                {/* Export */}
                {exportCsvUrl && (
                    <div className="admin-data-table-export">
                        <a href={exportCsvUrl} className="export-btn">
                            <Download size={16} />
                            Export CSV
                        </a>
                    </div>
                )}
            </div>

            {/* Message */}
            {message && (
                <div className={`admin-data-table-message ${message.type}`}>
                    {message.text}
                </div>
            )}

            {/* Table */}
            <div className="admin-data-table-container">
                <table>
                    <thead>
                        <tr>
                            {bulkActions.length > 0 && (
                                <th className="checkbox-col">
                                    <input
                                        type="checkbox"
                                        checked={allSelected}
                                        ref={el => {
                                            if (el) el.indeterminate = someSelected
                                        }}
                                        onChange={(e) => handleSelectAll(e.target.checked)}
                                    />
                                </th>
                            )}
                            {columns.map(col => (
                                <th
                                    key={col.accessorKey}
                                    className={col.sortable !== false ? 'sortable' : ''}
                                    onClick={() => col.sortable !== false && handleSort(col.accessorKey)}
                                >
                                    <div className="th-content">
                                        {col.header}
                                        {col.sortable !== false && (
                                            sorting?.key === col.accessorKey ? (
                                                sorting.direction === 'asc'
                                                    ? <ChevronUp size={14} />
                                                    : <ChevronDown size={14} />
                                            ) : (
                                                <ChevronsUpDown size={14} className="sort-icon-inactive" />
                                            )
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedData.length === 0 ? (
                            <tr>
                                <td
                                    colSpan={columns.length + (bulkActions.length > 0 ? 1 : 0)}
                                    className="empty-state"
                                >
                                    {emptyMessage}
                                </td>
                            </tr>
                        ) : (
                            paginatedData.map((row, idx) => (
                                <tr
                                    key={row[idKey] || idx}
                                    className={selectedIds.has(row[idKey]) ? 'selected' : ''}
                                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                                >
                                    {bulkActions.length > 0 && (
                                        <td className="checkbox-col">
                                            <input
                                                type="checkbox"
                                                checked={selectedIds.has(row[idKey])}
                                                onChange={(e) => {
                                                    e.stopPropagation()
                                                    handleRowSelect(row[idKey], e.target.checked)
                                                }}
                                                onClick={(e) => e.stopPropagation()}
                                            />
                                        </td>
                                    )}
                                    {columns.map(col => (
                                        <td key={col.accessorKey}>
                                            {col.cell
                                                ? col.cell(row[col.accessorKey], row)
                                                : col.html
                                                    ? <span dangerouslySetInnerHTML={{ __html: row[col.accessorKey] }} />
                                                    : row[col.accessorKey]}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="admin-data-table-pagination">
                <div className="page-size">
                    <span>Show</span>
                    <select
                        value={pageSize}
                        onChange={(e) => {
                            setPageSize(Number(e.target.value))
                            setCurrentPage(1)
                        }}
                    >
                        {pageSizeOptions.map(size => (
                            <option key={size} value={size}>{size}</option>
                        ))}
                    </select>
                    <span>per page</span>
                </div>

                <div className="page-info">
                    Showing {startRow} to {endRow} of {sortedData.length}
                </div>

                <div className="page-nav">
                    <button
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                    >
                        <ChevronLeft size={16} />
                        Previous
                    </button>
                    <span className="page-number">
                        Page {currentPage} of {totalPages || 1}
                    </span>
                    <button
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage >= totalPages}
                    >
                        Next
                        <ChevronRight size={16} />
                    </button>
                </div>
            </div>
        </div>
    )
}

export default AdminDataTable
