/**
 * EmployeeDashboard Component
 * 
 * Enterprise-level employee dashboard with:
 * - Tab navigation: Overview | Time Tracking | Leave | My Calendar
 * - KPI cards: Today's Appointments, This Week, Leave Balance, Hours
 * - Time clock widget with clock in/out
 * - Time tracking history with month navigation
 * - Leave balances and request history
 * - Calendar integration via EmployeeCalendar component
 */

import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import {
    Calendar, Clock, Briefcase, Users, LogIn, LogOut,
    LayoutDashboard, ChevronRight, ChevronLeft, FileText, AlertCircle,
    History
} from 'lucide-react'
import api from '../../../api'
import { useToast } from '../../ui/toast'
import { Spinner } from '../../ui/spinner'

// Lazy load the calendar component
const EmployeeCalendar = lazy(() => import('../calendar/EmployeeCalendar'))

// =============================================================================
// Types
// =============================================================================

interface Stats {
    today_appointments: number
    week_appointments: number
    pending_leave: number
    hours_this_week: number
    is_clocked_in: boolean
    clock_in_time: string | null
}

interface Appointment {
    id: number
    name: string
    datetime: string
    service: string
    status: string
    checked_in: boolean
    checked_out: boolean
}

interface LeaveBalance {
    type: string
    total: number
    used: number
    remaining: number
}

interface TimeEntry {
    id: number
    date: string
    clock_in: string | null
    clock_out: string | null
    duration_minutes: number | null
    notes: string | null
    is_active: boolean
}

interface TimeHistoryData {
    month: number
    year: number
    month_name: string
    entries: TimeEntry[]
    summary: {
        total_hours: number
        total_minutes: number
        days_worked: number
        avg_hours_per_day: number
    }
}

interface LeaveRequest {
    id: number
    leave_type: string
    start_date: string
    end_date: string
    status: string
    reason: string
    created_at: string
}

interface LeaveBalanceData {
    id: number
    leave_type: string
    total_days: number
    used_days: number
    remaining_days: number
}

interface LeaveData {
    year: number
    balances: LeaveBalanceData[]
    requests: LeaveRequest[]
}

interface EmployeeDashboardProps {
    /** Initial stats from server */
    initialStats?: Stats
    /** Upcoming appointments */
    upcomingAppointments?: Appointment[]
    /** Leave balances */
    leaveBalances?: LeaveBalance[]
    /** Calendar events URL */
    eventsUrl?: string
    /** Has estimator profile */
    hasEstimatorProfile?: boolean
    /** Estimator ID for ICS feed */
    estimatorId?: number
    /** Additional class */
    className?: string
}

// =============================================================================
// KPI Card Component
// =============================================================================

interface KPICardProps {
    title: string
    value: string | number
    icon: React.ReactNode
    iconColor: string
    subtitle?: string
}

function KPICard({ title, value, icon, iconColor, subtitle }: KPICardProps) {
    return (
        <div className="emp-kpi-card">
            <div className="emp-kpi-icon" style={{ background: `${iconColor}15`, color: iconColor }}>
                {icon}
            </div>
            <div className="emp-kpi-content">
                <div className="emp-kpi-value">{value}</div>
                <div className="emp-kpi-title">{title}</div>
                {subtitle && <div className="emp-kpi-subtitle">{subtitle}</div>}
            </div>
        </div>
    )
}

// =============================================================================
// Time Clock Widget
// =============================================================================

interface TimeClockProps {
    isClockedIn: boolean
    clockInTime: string | null
    onClockIn: () => void
    onClockOut: () => void
    loading: boolean
}

function TimeClock({ isClockedIn, clockInTime, onClockIn, onClockOut, loading }: TimeClockProps) {
    const [elapsed, setElapsed] = useState('')

    useEffect(() => {
        if (!isClockedIn || !clockInTime) {
            setElapsed('')
            return
        }

        const updateElapsed = () => {
            const start = new Date(clockInTime)
            const now = new Date()
            const diff = Math.floor((now.getTime() - start.getTime()) / 1000)
            const hours = Math.floor(diff / 3600)
            const mins = Math.floor((diff % 3600) / 60)
            setElapsed(`${hours}h ${mins}m`)
        }

        updateElapsed()
        const interval = setInterval(updateElapsed, 60000) // Update every minute
        return () => clearInterval(interval)
    }, [isClockedIn, clockInTime])

    return (
        <div className={`emp-time-clock ${isClockedIn ? 'clocked-in' : ''}`}>
            <div className="emp-time-clock-header">
                <Clock size={20} />
                <span>Time Clock</span>
            </div>
            <div className="emp-time-clock-body">
                {isClockedIn ? (
                    <>
                        <div className="emp-time-status">
                            <span className="status-indicator active" />
                            Working
                        </div>
                        <div className="emp-time-elapsed">{elapsed}</div>
                        <button
                            className="emp-clock-btn clock-out"
                            onClick={onClockOut}
                            disabled={loading}
                        >
                            <LogOut size={18} />
                            Clock Out
                        </button>
                    </>
                ) : (
                    <>
                        <div className="emp-time-status">
                            <span className="status-indicator" />
                            Not Clocked In
                        </div>
                        <button
                            className="emp-clock-btn clock-in"
                            onClick={onClockIn}
                            disabled={loading}
                        >
                            <LogIn size={18} />
                            Clock In
                        </button>
                    </>
                )}
            </div>
        </div>
    )
}

// =============================================================================
// Upcoming Appointments Widget
// =============================================================================

interface UpcomingAppointmentsProps {
    appointments: Appointment[]
    onCheckin: (id: number) => void
}

function UpcomingAppointments({ appointments, onCheckin }: UpcomingAppointmentsProps) {
    if (appointments.length === 0) {
        return (
            <div className="emp-widget">
                <div className="emp-widget-header">
                    <Calendar size={18} />
                    <span>Upcoming Appointments</span>
                </div>
                <div className="emp-widget-empty">
                    <Calendar size={32} />
                    <p>No upcoming appointments</p>
                </div>
            </div>
        )
    }

    return (
        <div className="emp-widget">
            <div className="emp-widget-header">
                <Calendar size={18} />
                <span>Upcoming Appointments</span>
                <a href="/employee/calendar" className="emp-widget-link">
                    View All <ChevronRight size={14} />
                </a>
            </div>
            <div className="emp-widget-list">
                {appointments.map(appt => {
                    const dt = new Date(appt.datetime)
                    return (
                        <div key={appt.id} className="emp-appointment-item">
                            <div className="emp-appointment-time">
                                <span className="date">{dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                                <span className="time">{dt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}</span>
                            </div>
                            <div className="emp-appointment-details">
                                <div className="name">{appt.name}</div>
                                <div className="service">{appt.service}</div>
                            </div>
                            <div className="emp-appointment-actions">
                                {appt.checked_out ? (
                                    <span className="badge completed">Completed</span>
                                ) : appt.checked_in ? (
                                    <span className="badge in-progress">In Progress</span>
                                ) : (
                                    <button
                                        className="emp-checkin-btn"
                                        onClick={() => onCheckin(appt.id)}
                                    >
                                        Check In
                                    </button>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

// =============================================================================
// Leave Balances Widget (for Overview tab)
// =============================================================================

interface LeaveBalancesProps {
    balances: LeaveBalance[]
}

function LeaveBalancesWidget({ balances }: LeaveBalancesProps) {
    if (balances.length === 0) {
        return (
            <div className="emp-widget">
                <div className="emp-widget-header">
                    <Briefcase size={18} />
                    <span>Leave Balances</span>
                </div>
                <div className="emp-widget-empty">
                    <p>No leave balances configured</p>
                </div>
            </div>
        )
    }

    return (
        <div className="emp-widget">
            <div className="emp-widget-header">
                <Briefcase size={18} />
                <span>Leave Balances</span>
            </div>
            <div className="emp-leave-balances">
                {balances.map((lb, idx) => {
                    const percent = lb.total > 0 ? (lb.used / lb.total) * 100 : 0
                    return (
                        <div key={idx} className="emp-leave-item">
                            <div className="emp-leave-header">
                                <span className="type">{lb.type}</span>
                                <span className="remaining">{lb.remaining} days left</span>
                            </div>
                            <div className="emp-leave-bar">
                                <div
                                    className="emp-leave-fill"
                                    style={{ width: `${percent}%` }}
                                />
                            </div>
                            <div className="emp-leave-stats">
                                <span>Used: {lb.used}</span>
                                <span>Total: {lb.total}</span>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

// =============================================================================
// Time Tracking Tab Component
// =============================================================================

function TimeTrackingTab() {
    const [loading, setLoading] = useState(true)
    const [data, setData] = useState<TimeHistoryData | null>(null)
    const [month, setMonth] = useState(new Date().getMonth() + 1)
    const [year, setYear] = useState(new Date().getFullYear())

    const fetchData = useCallback(async () => {
        setLoading(true)
        try {
            const response = await api.get<TimeHistoryData>(`/employee/api/time-history?month=${month}&year=${year}`)
            if (response.ok && response.data) {
                setData(response.data)
            }
        } catch {
            // Silent fail
        } finally {
            setLoading(false)
        }
    }, [month, year])

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

    const formatDuration = (minutes: number | null) => {
        if (!minutes) return '-'
        const hrs = Math.floor(minutes / 60)
        const mins = minutes % 60
        return `${hrs}h ${mins}m`
    }

    if (loading) {
        return (
            <div className="emp-loading">
                <Spinner size="lg" />
                <span>Loading time entries...</span>
            </div>
        )
    }

    return (
        <div className="emp-time-tracking-tab">
            {/* Header with navigation */}
            <div className="emp-tab-header">
                <div className="emp-month-nav">
                    <button className="emp-nav-btn" onClick={() => navigateMonth(-1)}>
                        <ChevronLeft size={20} />
                    </button>
                    <h2 className="emp-month-title">{data?.month_name} {year}</h2>
                    <button className="emp-nav-btn" onClick={() => navigateMonth(1)}>
                        <ChevronRight size={20} />
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="emp-summary-cards">
                <div className="emp-summary-card">
                    <div className="emp-summary-value">{data?.summary.total_hours.toFixed(1) || 0}</div>
                    <div className="emp-summary-label">Total Hours</div>
                </div>
                <div className="emp-summary-card">
                    <div className="emp-summary-value">{data?.summary.days_worked || 0}</div>
                    <div className="emp-summary-label">Days Worked</div>
                </div>
                <div className="emp-summary-card">
                    <div className="emp-summary-value">{data?.summary.avg_hours_per_day.toFixed(1) || 0}</div>
                    <div className="emp-summary-label">Avg Hours/Day</div>
                </div>
            </div>

            {/* Time Entries Table */}
            {data?.entries && data.entries.length > 0 ? (
                <div className="emp-table-wrapper">
                    <table className="emp-data-table">
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
                            {data.entries.map(entry => (
                                <tr key={entry.id}>
                                    <td>{entry.date ? new Date(entry.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) : '-'}</td>
                                    <td>{entry.clock_in || '-'}</td>
                                    <td>
                                        {entry.is_active ? (
                                            <span className="emp-status-badge active">Active</span>
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
            ) : (
                <div className="emp-empty-state">
                    <Clock size={48} />
                    <h3>No Time Entries</h3>
                    <p>No time entries recorded for this month.</p>
                </div>
            )}
        </div>
    )
}

// =============================================================================
// Leave Tab Component
// =============================================================================

function LeaveTab() {
    const [loading, setLoading] = useState(true)
    const [data, setData] = useState<LeaveData | null>(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.get<LeaveData>('/employee/api/leave-balances')
                if (response.ok && response.data) {
                    setData(response.data)
                }
            } catch {
                // Silent fail
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    const getStatusBadgeClass = (status: string) => {
        switch (status.toLowerCase()) {
            case 'approved': return 'emp-status-badge approved'
            case 'rejected': return 'emp-status-badge rejected'
            case 'pending': return 'emp-status-badge pending'
            default: return 'emp-status-badge'
        }
    }

    if (loading) {
        return (
            <div className="emp-loading">
                <Spinner size="lg" />
                <span>Loading leave data...</span>
            </div>
        )
    }

    return (
        <div className="emp-leave-tab">
            {/* Leave Balances */}
            <div className="emp-tab-section">
                <h3 className="emp-section-title">
                    <Briefcase size={20} />
                    Leave Balances - {data?.year}
                </h3>

                {data?.balances && data.balances.length > 0 ? (
                    <div className="emp-balance-cards">
                        {data.balances.map(balance => {
                            const percent = balance.total_days > 0
                                ? (balance.used_days / balance.total_days) * 100
                                : 0
                            return (
                                <div key={balance.id} className="emp-balance-card">
                                    <div className="emp-balance-type">{balance.leave_type}</div>
                                    <div className="emp-balance-remaining">
                                        <span className="emp-balance-number">{balance.remaining_days}</span>
                                        <span className="emp-balance-label">days remaining</span>
                                    </div>
                                    <div className="emp-balance-bar">
                                        <div
                                            className="emp-balance-fill"
                                            style={{ width: `${Math.min(percent, 100)}%` }}
                                        />
                                    </div>
                                    <div className="emp-balance-details">
                                        <span>Used: {balance.used_days}</span>
                                        <span>Total: {balance.total_days}</span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                ) : (
                    <div className="emp-empty-state small">
                        <p>No leave balances configured for this year.</p>
                    </div>
                )}
            </div>

            {/* Leave Requests */}
            <div className="emp-tab-section">
                <div className="emp-section-header">
                    <h3 className="emp-section-title">
                        <History size={20} />
                        Leave Requests
                    </h3>
                    <a href="/employee/leave/request" className="emp-action-btn">
                        + Request Leave
                    </a>
                </div>

                {data?.requests && data.requests.length > 0 ? (
                    <div className="emp-table-wrapper">
                        <table className="emp-data-table">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Dates</th>
                                    <th>Status</th>
                                    <th>Reason</th>
                                    <th>Submitted</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.requests.map(req => (
                                    <tr key={req.id}>
                                        <td>{req.leave_type}</td>
                                        <td>
                                            {req.start_date ? new Date(req.start_date).toLocaleDateString() : '-'}
                                            {' → '}
                                            {req.end_date ? new Date(req.end_date).toLocaleDateString() : '-'}
                                        </td>
                                        <td>
                                            <span className={getStatusBadgeClass(req.status)}>
                                                {req.status}
                                            </span>
                                        </td>
                                        <td>{req.reason || '-'}</td>
                                        <td>{req.created_at ? new Date(req.created_at).toLocaleDateString() : '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="emp-empty-state small">
                        <p>No leave requests found.</p>
                    </div>
                )}
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

type TabType = 'overview' | 'time' | 'leave' | 'calendar'

export function EmployeeDashboard({
    initialStats,
    upcomingAppointments = [],
    leaveBalances = [],
    eventsUrl = '/employee/calendar/api/events',
    hasEstimatorProfile = false,
    estimatorId,
    className = ''
}: EmployeeDashboardProps) {
    const [activeTab, setActiveTab] = useState<TabType>('overview')
    const [stats, setStats] = useState<Stats>(initialStats || {
        today_appointments: 0,
        week_appointments: 0,
        pending_leave: 0,
        hours_this_week: 0,
        is_clocked_in: false,
        clock_in_time: null
    })
    const [appointments, setAppointments] = useState<Appointment[]>(upcomingAppointments)
    const [clockLoading, setClockLoading] = useState(false)
    const { addToast } = useToast()

    // Refresh stats
    const refreshStats = useCallback(async () => {
        try {
            const response = await api.get<Stats>('/employee/api/dashboard-stats')
            if (response.ok && response.data) {
                setStats(response.data)
            }
        } catch {
            // Silent fail
        }
    }, [])

    // Clock in - use new JSON API
    const handleClockIn = async () => {
        setClockLoading(true)
        try {
            const response = await api.post<{ success: boolean; message: string; clock_in_time?: string }>('/employee/api/clock-in', {})
            if (response.ok && response.data) {
                if (response.data.success) {
                    addToast({ type: 'success', message: response.data.message })
                    refreshStats()
                } else {
                    addToast({ type: 'warning', message: response.data.message })
                }
            } else {
                addToast({ type: 'error', message: 'Failed to clock in' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error clocking in' })
        } finally {
            setClockLoading(false)
        }
    }

    // Clock out - use new JSON API
    const handleClockOut = async () => {
        setClockLoading(true)
        try {
            const response = await api.post<{ success: boolean; message: string; duration_minutes?: number }>('/employee/api/clock-out', {})
            if (response.ok && response.data) {
                if (response.data.success) {
                    addToast({ type: 'success', message: response.data.message })
                    refreshStats()
                } else {
                    addToast({ type: 'warning', message: response.data.message })
                }
            } else {
                addToast({ type: 'error', message: 'Failed to clock out' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error clocking out' })
        } finally {
            setClockLoading(false)
        }
    }

    // Check in appointment
    const handleCheckin = async (appointmentId: number) => {
        try {
            const response = await api.post(`/employee/appointment/${appointmentId}/checkin`, {})
            if (response.ok) {
                addToast({ type: 'success', message: 'Checked in!' })
                // Update local state
                setAppointments(prev => prev.map(a =>
                    a.id === appointmentId ? { ...a, checked_in: true } : a
                ))
            } else {
                addToast({ type: 'error', message: 'Failed to check in' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error checking in' })
        }
    }

    return (
        <div className={`employee-dashboard ${className}`}>
            {/* Tab Navigation */}
            <div className="emp-tabs">
                <button
                    className={`emp-tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    <LayoutDashboard size={18} />
                    Overview
                </button>
                <button
                    className={`emp-tab ${activeTab === 'time' ? 'active' : ''}`}
                    onClick={() => setActiveTab('time')}
                >
                    <Clock size={18} />
                    Time Tracking
                </button>
                <button
                    className={`emp-tab ${activeTab === 'leave' ? 'active' : ''}`}
                    onClick={() => setActiveTab('leave')}
                >
                    <Briefcase size={18} />
                    Leave
                </button>
                <button
                    className={`emp-tab ${activeTab === 'calendar' ? 'active' : ''}`}
                    onClick={() => setActiveTab('calendar')}
                >
                    <Calendar size={18} />
                    My Calendar
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'calendar' ? (
                <div className="emp-calendar-tab">
                    {hasEstimatorProfile ? (
                        <Suspense fallback={<div className="emp-loading"><Spinner size="lg" /><span>Loading calendar...</span></div>}>
                            <EmployeeCalendar
                                eventsUrl={eventsUrl}
                                checkinUrlPattern="/employee/appointment/{id}/checkin"
                                checkoutUrlPattern="/employee/appointment/{id}/checkout"
                                notesUrlPattern="/employee/appointment/{id}/notes"
                                rescheduleUrlPattern="/employee/appointment/{id}/reschedule"
                                icsFeedUrl={estimatorId ? `/calendar/ics/${estimatorId}` : undefined}
                            />
                        </Suspense>
                    ) : (
                        <div className="emp-no-estimator">
                            <AlertCircle size={48} />
                            <h3>No Estimator Profile</h3>
                            <p>Your account is not linked to an estimator profile. Contact an administrator to set this up.</p>
                        </div>
                    )}
                </div>
            ) : activeTab === 'time' ? (
                <TimeTrackingTab />
            ) : activeTab === 'leave' ? (
                <LeaveTab />
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="emp-kpi-grid">
                        <KPICard
                            title="Today's Appointments"
                            value={stats.today_appointments}
                            icon={<Calendar size={24} />}
                            iconColor="#10b981"
                        />
                        <KPICard
                            title="This Week"
                            value={stats.week_appointments}
                            icon={<Users size={24} />}
                            iconColor="#6366f1"
                        />
                        <KPICard
                            title="Pending Leave"
                            value={stats.pending_leave}
                            icon={<Briefcase size={24} />}
                            iconColor="#f59e0b"
                            subtitle="requests"
                        />
                        <KPICard
                            title="Hours This Week"
                            value={stats.hours_this_week}
                            icon={<Clock size={24} />}
                            iconColor="#a855f7"
                            subtitle="hours"
                        />
                    </div>

                    {/* Main Content Grid */}
                    <div className="emp-content-grid">
                        {/* Left Column */}
                        <div className="emp-column-main">
                            <UpcomingAppointments
                                appointments={appointments}
                                onCheckin={handleCheckin}
                            />
                        </div>

                        {/* Right Column */}
                        <div className="emp-column-side">
                            <TimeClock
                                isClockedIn={stats.is_clocked_in}
                                clockInTime={stats.clock_in_time}
                                onClockIn={handleClockIn}
                                onClockOut={handleClockOut}
                                loading={clockLoading}
                            />
                            <LeaveBalancesWidget balances={leaveBalances} />
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div className="emp-quick-links">
                        <button
                            className="emp-quick-link"
                            onClick={() => setActiveTab('calendar')}
                        >
                            <Calendar size={18} />
                            Full Calendar
                        </button>
                        <button
                            className="emp-quick-link"
                            onClick={() => setActiveTab('leave')}
                        >
                            <Briefcase size={18} />
                            Leave History
                        </button>
                        <button
                            className="emp-quick-link"
                            onClick={() => setActiveTab('time')}
                        >
                            <Clock size={18} />
                            Timesheet
                        </button>
                        <a href="/employee/docs/shared-with-me" className="emp-quick-link">
                            <FileText size={18} />
                            Shared Documents
                        </a>
                    </div>
                </>
            )}
        </div>
    )
}

export default EmployeeDashboard
