/**
 * AdminTimeCardsTab Component
 * 
 * Admin dashboard tab for viewing and managing employee time cards with:
 * - Employee filter dropdown
 * - Month/Year navigation
 * - Time entries grouped by employee
 * - Summary statistics
 * - Export to CSV functionality
 */

import { useState, useEffect, useCallback } from 'react'
import {
    Clock, ChevronLeft, ChevronRight, Download, Users,
    Calendar, Filter
} from 'lucide-react'
import api from '../../../api'
import { Spinner } from '../../ui/spinner'

// =============================================================================
// Types
// =============================================================================

interface TimeEntry {
    id: number
    date: string
    clock_in: string | null
    clock_out: string | null
    duration_minutes: number | null
    notes: string | null
    is_active: boolean
}

interface EmployeeTimeData {
    employee_id: number
    employee_name: string
    employee_email: string
    department: string
    entries: TimeEntry[]
    total_minutes: number
    total_hours: number
    days_worked: number
    avg_hours_per_day: number
}

interface AvailableEmployee {
    id: number
    name: string
}

interface TimeCardsData {
    month: number
    year: number
    month_name: string
    employees: EmployeeTimeData[]
    available_employees: AvailableEmployee[]
    summary: {
        total_employees: number
        total_hours: number
        total_entries: number
    }
}

// =============================================================================
// Main Component
// =============================================================================

export function AdminTimeCardsTab() {
    const [loading, setLoading] = useState(true)
    const [data, setData] = useState<TimeCardsData | null>(null)
    const [month, setMonth] = useState(new Date().getMonth() + 1)
    const [year, setYear] = useState(new Date().getFullYear())
    const [employeeFilter, setEmployeeFilter] = useState<number | null>(null)
    const [expandedEmployees, setExpandedEmployees] = useState<Set<number>>(new Set())

    const fetchData = useCallback(async () => {
        setLoading(true)
        try {
            let url = `/admin/api/timecards?month=${month}&year=${year}`
            if (employeeFilter) {
                url += `&employee_id=${employeeFilter}`
            }
            const response = await api.get<TimeCardsData>(url)
            if (response.ok && response.data) {
                setData(response.data)
            }
        } catch {
            // Silent fail
        } finally {
            setLoading(false)
        }
    }, [month, year, employeeFilter])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const navigateMonth = (direction: -1 | 1) => {
        let newMonth = month + direction
        let newYear = year

        if (newMonth < 1) {
            newMonth = 12
            newYear--
        } else if (newMonth > 12) {
            newMonth = 1
            newYear++
        }

        setMonth(newMonth)
        setYear(newYear)
    }

    const toggleExpanded = (employeeId: number) => {
        setExpandedEmployees(prev => {
            const newSet = new Set(prev)
            if (newSet.has(employeeId)) {
                newSet.delete(employeeId)
            } else {
                newSet.add(employeeId)
            }
            return newSet
        })
    }

    const formatDuration = (minutes: number | null) => {
        if (!minutes) return '-'
        const hrs = Math.floor(minutes / 60)
        const mins = minutes % 60
        return `${hrs}h ${mins}m`
    }

    const handleExport = () => {
        let url = `/admin/api/timecards/export?month=${month}&year=${year}`
        if (employeeFilter) {
            url += `&employee_id=${employeeFilter}`
        }
        window.location.href = url
    }

    if (loading && !data) {
        return (
            <div className="admin-tc-loading">
                <Spinner size="lg" />
                <span>Loading time cards...</span>
            </div>
        )
    }

    return (
        <div className="admin-time-cards-tab">
            {/* Header */}
            <div className="admin-tc-header">
                <div className="admin-tc-title-section">
                    <h2 className="admin-tc-title">
                        <Clock size={24} />
                        Time Cards
                    </h2>
                    <p className="admin-tc-subtitle">
                        View and export employee time entries
                    </p>
                </div>

                <div className="admin-tc-actions">
                    <button className="admin-tc-export-btn" onClick={handleExport}>
                        <Download size={18} />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="admin-tc-filters">
                {/* Month Navigation */}
                <div className="admin-tc-month-nav">
                    <button className="admin-tc-nav-btn" onClick={() => navigateMonth(-1)}>
                        <ChevronLeft size={20} />
                    </button>
                    <span className="admin-tc-month-label">{data?.month_name} {year}</span>
                    <button className="admin-tc-nav-btn" onClick={() => navigateMonth(1)}>
                        <ChevronRight size={20} />
                    </button>
                </div>

                {/* Employee Filter */}
                <div className="admin-tc-filter-group">
                    <Filter size={16} />
                    <select
                        className="admin-tc-select"
                        value={employeeFilter || ''}
                        onChange={(e) => setEmployeeFilter(e.target.value ? Number(e.target.value) : null)}
                    >
                        <option value="">All Employees</option>
                        {data?.available_employees.map(emp => (
                            <option key={emp.id} value={emp.id}>{emp.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="admin-tc-summary">
                <div className="admin-tc-summary-card">
                    <div className="admin-tc-summary-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#6366f1' }}>
                        <Users size={24} />
                    </div>
                    <div className="admin-tc-summary-content">
                        <div className="admin-tc-summary-value">{data?.summary.total_employees || 0}</div>
                        <div className="admin-tc-summary-label">Employees</div>
                    </div>
                </div>
                <div className="admin-tc-summary-card">
                    <div className="admin-tc-summary-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                        <Clock size={24} />
                    </div>
                    <div className="admin-tc-summary-content">
                        <div className="admin-tc-summary-value">{data?.summary.total_hours.toFixed(1) || 0}</div>
                        <div className="admin-tc-summary-label">Total Hours</div>
                    </div>
                </div>
                <div className="admin-tc-summary-card">
                    <div className="admin-tc-summary-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                        <Calendar size={24} />
                    </div>
                    <div className="admin-tc-summary-content">
                        <div className="admin-tc-summary-value">{data?.summary.total_entries || 0}</div>
                        <div className="admin-tc-summary-label">Entries</div>
                    </div>
                </div>
            </div>

            {/* Employee Time Cards */}
            {loading ? (
                <div className="admin-tc-loading inline">
                    <Spinner size="md" />
                    <span>Updating...</span>
                </div>
            ) : data?.employees && data.employees.length > 0 ? (
                <div className="admin-tc-employees">
                    {data.employees.map(emp => (
                        <div key={emp.employee_id} className="admin-tc-employee-card">
                            <div
                                className="admin-tc-employee-header"
                                onClick={() => toggleExpanded(emp.employee_id)}
                            >
                                <div className="admin-tc-employee-info">
                                    <div className="admin-tc-employee-name">{emp.employee_name}</div>
                                    <div className="admin-tc-employee-meta">
                                        {emp.department} • {emp.employee_email}
                                    </div>
                                </div>
                                <div className="admin-tc-employee-stats">
                                    <div className="admin-tc-stat">
                                        <span className="admin-tc-stat-value">{emp.total_hours.toFixed(1)}</span>
                                        <span className="admin-tc-stat-label">Hours</span>
                                    </div>
                                    <div className="admin-tc-stat">
                                        <span className="admin-tc-stat-value">{emp.days_worked}</span>
                                        <span className="admin-tc-stat-label">Days</span>
                                    </div>
                                    <div className="admin-tc-stat">
                                        <span className="admin-tc-stat-value">{emp.avg_hours_per_day.toFixed(1)}</span>
                                        <span className="admin-tc-stat-label">Avg/Day</span>
                                    </div>
                                </div>
                                <button className={`admin-tc-expand-btn ${expandedEmployees.has(emp.employee_id) ? 'expanded' : ''}`}>
                                    <ChevronRight size={20} />
                                </button>
                            </div>

                            {expandedEmployees.has(emp.employee_id) && (
                                <div className="admin-tc-employee-entries">
                                    <table className="admin-tc-entries-table">
                                        <thead>
                                            <tr>
                                                <th>Date</th>
                                                <th>Clock In</th>
                                                <th>Clock Out</th>
                                                <th>Duration</th>
                                                <th>Notes</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {emp.entries.map(entry => (
                                                <tr key={entry.id}>
                                                    <td>
                                                        {entry.date
                                                            ? new Date(entry.date).toLocaleDateString('en-US', {
                                                                weekday: 'short',
                                                                month: 'short',
                                                                day: 'numeric'
                                                            })
                                                            : '-'
                                                        }
                                                    </td>
                                                    <td>{entry.clock_in || '-'}</td>
                                                    <td>
                                                        {entry.is_active ? (
                                                            <span className="admin-tc-badge active">Active</span>
                                                        ) : (
                                                            entry.clock_out || '-'
                                                        )}
                                                    </td>
                                                    <td>{formatDuration(entry.duration_minutes)}</td>
                                                    <td>{entry.notes || '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <div className="admin-tc-empty">
                    <Clock size={48} />
                    <h3>No Time Entries</h3>
                    <p>No time entries found for this period.</p>
                </div>
            )}
        </div>
    )
}

export default AdminTimeCardsTab
