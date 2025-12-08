import { useState, useMemo, useEffect } from 'react'
import { ChevronDown, ChevronUp, ChevronsUpDown, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { Button } from '../../ui/button'
import api from '../../../api'

interface Column {
    accessorKey: string
    header: string
    cell?: (value: any, row: any) => React.ReactNode
}

interface DataTableProps {
    columns: Column[]
    data?: any[]
    dataUrl?: string
}

export default function DataTable({ columns, data: initialData = [], dataUrl }: DataTableProps) {
    const [data, setData] = useState<any[]>(initialData)
    const [sorting, setSorting] = useState<{ key: string, direction: 'asc' | 'desc' } | null>(null)
    const [globalFilter, setGlobalFilter] = useState('')
    const [currentPage, setCurrentPage] = useState(1)
    const pageSize = 10
    const [loading, setLoading] = useState(false)

    // Fetch data if URL provided
    useEffect(() => {
        if (dataUrl && initialData.length === 0) {
            setLoading(true)
            api.get(dataUrl)
                .then(response => {
                    if (response.ok && response.data) {
                        const d = response.data
                        if (Array.isArray(d)) setData(d)
                        else if (d.data) setData(d.data)
                    }
                })
                .finally(() => setLoading(false))
        }
    }, [dataUrl, initialData.length])

    // Filter
    const filteredData = useMemo(() => {
        if (!globalFilter) return data
        return data.filter(row =>
            Object.values(row).some(val =>
                String(val).toLowerCase().includes(globalFilter.toLowerCase())
            )
        )
    }, [data, globalFilter])

    // Sort
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

    // Paginate
    const paginatedData = useMemo(() => {
        const start = (currentPage - 1) * pageSize
        return sortedData.slice(start, start + pageSize)
    }, [sortedData, currentPage])

    const totalPages = Math.ceil(sortedData.length / pageSize)

    const handleSort = (key: string) => {
        setSorting(current => {
            if (current?.key === key) {
                return current.direction === 'asc'
                    ? { key, direction: 'desc' }
                    : null
            }
            return { key, direction: 'asc' }
        })
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div className="relative w-72">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
                    <input
                        placeholder="Search..."
                        value={globalFilter}
                        onChange={(e) => setGlobalFilter(e.target.value)}
                        className="pl-8 h-10 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>

            <div className="rounded-md border dark:border-gray-700">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
                            <tr>
                                {columns.map(col => (
                                    <th
                                        key={col.accessorKey}
                                        className="h-12 px-4 align-middle font-medium text-gray-500 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100"
                                        onClick={() => handleSort(col.accessorKey)}
                                    >
                                        <div className="flex items-center gap-2">
                                            {col.header}
                                            {sorting?.key === col.accessorKey ? (
                                                sorting.direction === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />
                                            ) : (
                                                <ChevronsUpDown className="h-4 w-4 opacity-50" />
                                            )}
                                        </div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y dark:divide-gray-700">
                            {loading ? (
                                <tr>
                                    <td colSpan={columns.length} className="h-24 text-center">Loading...</td>
                                </tr>
                            ) : paginatedData.length === 0 ? (
                                <tr>
                                    <td colSpan={columns.length} className="h-24 text-center">No results.</td>
                                </tr>
                            ) : (
                                paginatedData.map((row, i) => (
                                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                        {columns.map(col => (
                                            <td key={col.accessorKey} className="p-4 align-middle">
                                                {col.cell ? col.cell(row[col.accessorKey], row) : row[col.accessorKey]}
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="flex items-center justify-end space-x-2">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                </Button>
                <div className="text-sm">
                    Page {currentPage} of {totalPages || 1}
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages || totalPages === 0}
                >
                    Next
                    <ChevronRight className="h-4 w-4" />
                </Button>
            </div>
        </div>
    )
}
