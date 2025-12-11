/**
 * UnifiedAppointmentsDashboard Component
 * 
 * Enterprise-level appointments dashboard with:
 * - FullCalendar integration for visual scheduling
 * - Appointment detail slideout
 * - Reschedule, cancel, and request-reschedule actions
 * - Stats header with quick metrics
 * - Quick filters for common views
 */

import { useState, useEffect, useCallback } from 'react'
import {
    Calendar, Clock, User, Mail, Phone, MapPin,
    X, RefreshCw, XCircle, Send,
    AlertTriangle, Check, Loader2, Filter
} from 'lucide-react'
import api from '../../../api'
import { useToast } from '../../ui/toast'
import { Calendar as CalendarView, CalendarEvent } from '../calendar/Calendar'

// =============================================================================
// Types
// =============================================================================

interface Service {
    id: number
    name: string
    description?: string
    duration_minutes: number
    price?: number
}

interface Staff {
    id: number
    name: string
    is_active?: boolean
}

interface Location {
    id: number
    name: string
    address?: string
}

interface Appointment {
    id: number
    first_name: string
    last_name: string
    email: string
    phone: string
    status: string
    notes?: string
    staff_notes?: string
    preferred_date_time: string
    service: Service | null
    estimator: Staff | null
    location: Location | null
    payment_status?: string
    payment_amount?: number
    is_recurring?: boolean
    checked_in_at?: string
    checked_out_at?: string
    intake_form_data?: Record<string, any>
    reschedule_requests?: RescheduleRequest[]
    created_at: string
    updated_at?: string
}

interface RescheduleRequest {
    id: number
    proposed_datetime: string
    reason: string
    status: string
    created_at: string
    admin_notes?: string
}

interface Stats {
    today: number
    this_week: number
    pending: number
    pending_reschedule: number
    upcoming: number
}

interface UnifiedAppointmentsDashboardProps {
    eventsUrl?: string
    className?: string
}

// =============================================================================
// Status Badge Component
// =============================================================================

function StatusBadge({ status }: { status: string }) {
    const statusStyles: Record<string, string> = {
        'New': 'badge-info',
        'Confirmed': 'badge-success',
        'Contacted': 'badge-primary',
        'Pending': 'badge-warning',
        'Cancelled': 'badge-danger',
        'Completed': 'badge-secondary',
    }

    return (
        <span className={`unified-appt-badge ${statusStyles[status] || 'badge-secondary'}`}>
            {status}
        </span>
    )
}

// =============================================================================
// Stats Cards Component
// =============================================================================

function StatsCards({ stats, onFilterClick }: { stats: Stats | null, onFilterClick: (filter: string) => void }) {
    if (!stats) return null

    return (
        <div className="unified-appt-stats">
            <button className="unified-appt-stat-card" onClick={() => onFilterClick('today')}>
                <div className="stat-icon stat-icon--today"><Calendar size={20} /></div>
                <div className="stat-content">
                    <div className="stat-value">{stats.today}</div>
                    <div className="stat-label">Today</div>
                </div>
            </button>
            <button className="unified-appt-stat-card" onClick={() => onFilterClick('week')}>
                <div className="stat-icon stat-icon--week"><Clock size={20} /></div>
                <div className="stat-content">
                    <div className="stat-value">{stats.this_week}</div>
                    <div className="stat-label">This Week</div>
                </div>
            </button>
            <button className="unified-appt-stat-card" onClick={() => onFilterClick('pending')}>
                <div className="stat-icon stat-icon--pending"><AlertTriangle size={20} /></div>
                <div className="stat-content">
                    <div className="stat-value">{stats.pending}</div>
                    <div className="stat-label">Pending</div>
                </div>
            </button>
            <button className="unified-appt-stat-card" onClick={() => onFilterClick('reschedule')}>
                <div className="stat-icon stat-icon--reschedule"><RefreshCw size={20} /></div>
                <div className="stat-content">
                    <div className="stat-value">{stats.pending_reschedule}</div>
                    <div className="stat-label">Reschedule Requests</div>
                </div>
            </button>
        </div>
    )
}

// =============================================================================
// Appointment Detail Slideout
// =============================================================================

interface DetailSlideoutProps {
    appointment: Appointment | null
    onClose: () => void
    onReschedule: () => void
    onCancel: () => void
    onRequestReschedule: () => void
}

function AppointmentDetailSlideout({
    appointment,
    onClose,
    onReschedule,
    onCancel,
    onRequestReschedule
}: DetailSlideoutProps) {
    if (!appointment) return null

    const dateTime = new Date(appointment.preferred_date_time)

    return (
        <div className="unified-appt-slideout-overlay" onClick={onClose}>
            <div className="unified-appt-slideout" onClick={e => e.stopPropagation()}>
                <div className="slideout-header">
                    <h3>Appointment Details</h3>
                    <button className="slideout-close" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <div className="slideout-content">
                    {/* Customer Info */}
                    <div className="slideout-section">
                        <h4>Customer</h4>
                        <div className="slideout-info-row">
                            <User size={16} />
                            <span>{appointment.first_name} {appointment.last_name}</span>
                        </div>
                        <div className="slideout-info-row">
                            <Mail size={16} />
                            <a href={`mailto:${appointment.email}`}>{appointment.email}</a>
                        </div>
                        <div className="slideout-info-row">
                            <Phone size={16} />
                            <a href={`tel:${appointment.phone}`}>{appointment.phone}</a>
                        </div>
                    </div>

                    {/* Appointment Info */}
                    <div className="slideout-section">
                        <h4>Appointment</h4>
                        <div className="slideout-info-row">
                            <Calendar size={16} />
                            <span>{dateTime.toLocaleDateString('en-US', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}</span>
                        </div>
                        <div className="slideout-info-row">
                            <Clock size={16} />
                            <span>{dateTime.toLocaleTimeString('en-US', {
                                hour: 'numeric',
                                minute: '2-digit',
                                hour12: true
                            })}</span>
                        </div>
                        {appointment.service && (
                            <div className="slideout-info-row">
                                <span className="info-label">Service:</span>
                                <span>{appointment.service.name} ({appointment.service.duration_minutes}min)</span>
                            </div>
                        )}
                        {appointment.estimator && (
                            <div className="slideout-info-row">
                                <span className="info-label">Staff:</span>
                                <span>{appointment.estimator.name}</span>
                            </div>
                        )}
                        {appointment.location && (
                            <div className="slideout-info-row">
                                <MapPin size={16} />
                                <span>{appointment.location.name}</span>
                            </div>
                        )}
                    </div>

                    {/* Status */}
                    <div className="slideout-section">
                        <h4>Status</h4>
                        <StatusBadge status={appointment.status} />
                        {appointment.payment_status && appointment.payment_status !== 'not_required' && (
                            <span className={`unified-appt-badge badge-${appointment.payment_status === 'paid' ? 'success' : 'warning'}`} style={{ marginLeft: '0.5rem' }}>
                                Payment: {appointment.payment_status}
                            </span>
                        )}
                    </div>

                    {/* Notes */}
                    {appointment.notes && (
                        <div className="slideout-section">
                            <h4>Customer Notes</h4>
                            <p className="slideout-notes">{appointment.notes}</p>
                        </div>
                    )}

                    {appointment.staff_notes && (
                        <div className="slideout-section">
                            <h4>Internal Notes</h4>
                            <p className="slideout-notes slideout-notes--internal">{appointment.staff_notes}</p>
                        </div>
                    )}

                    {/* Reschedule Requests */}
                    {appointment.reschedule_requests && appointment.reschedule_requests.length > 0 && (
                        <div className="slideout-section">
                            <h4>Reschedule History</h4>
                            {appointment.reschedule_requests.map(req => (
                                <div key={req.id} className="slideout-reschedule-item">
                                    <StatusBadge status={req.status} />
                                    <span>{new Date(req.proposed_datetime).toLocaleString()}</span>
                                    {req.reason && <p>{req.reason}</p>}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="slideout-actions">
                    {appointment.status !== 'Cancelled' && (
                        <>
                            <button className="slideout-action-btn btn-primary" onClick={onReschedule}>
                                <RefreshCw size={16} />
                                Reschedule
                            </button>
                            <button className="slideout-action-btn btn-secondary" onClick={onRequestReschedule}>
                                <Send size={16} />
                                Request New Time
                            </button>
                            <button className="slideout-action-btn btn-danger" onClick={onCancel}>
                                <XCircle size={16} />
                                Cancel
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// Reschedule Modal
// =============================================================================

interface RescheduleModalProps {
    appointment: Appointment
    onClose: () => void
    onSuccess: () => void
}

function RescheduleModal({ appointment, onClose, onSuccess }: RescheduleModalProps) {
    const [newDate, setNewDate] = useState('')
    const [newTime, setNewTime] = useState('')
    const [reason, setReason] = useState('')
    const [notifyCustomer, setNotifyCustomer] = useState(true)
    const [loading, setLoading] = useState(false)
    const { addToast } = useToast()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!newDate || !newTime) {
            addToast({ type: 'warning', message: 'Please select date and time' })
            return
        }

        setLoading(true)
        try {
            const newDateTime = new Date(`${newDate}T${newTime}`).toISOString()
            const response = await api.post(`/api/admin/booking/appointments/${appointment.id}/reschedule`, {
                new_datetime: newDateTime,
                reason,
                notify_customer: notifyCustomer
            })

            if (response.ok) {
                addToast({ type: 'success', message: 'Appointment rescheduled successfully' })
                onSuccess()
                onClose()
            } else {
                addToast({ type: 'error', message: response.error || 'Failed to reschedule' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error rescheduling appointment' })
        } finally {
            setLoading(false)
        }
    }

    const currentDateTime = new Date(appointment.preferred_date_time)

    return (
        <div className="unified-appt-modal-overlay" onClick={onClose}>
            <div className="unified-appt-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Reschedule Appointment</h3>
                    <button className="modal-close" onClick={onClose}><X size={20} /></button>
                </div>

                <form onSubmit={handleSubmit} className="modal-content">
                    <div className="modal-info">
                        <p><strong>Current Time:</strong></p>
                        <p>{currentDateTime.toLocaleString()}</p>
                        <p><strong>Customer:</strong> {appointment.first_name} {appointment.last_name}</p>
                    </div>

                    <div className="form-group">
                        <label>New Date</label>
                        <input
                            type="date"
                            value={newDate}
                            onChange={e => setNewDate(e.target.value)}
                            min={new Date().toISOString().split('T')[0]}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>New Time</label>
                        <input
                            type="time"
                            value={newTime}
                            onChange={e => setNewTime(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Reason (optional)</label>
                        <textarea
                            value={reason}
                            onChange={e => setReason(e.target.value)}
                            placeholder="Reason for reschedule..."
                            rows={3}
                        />
                    </div>

                    <div className="form-group form-group--checkbox">
                        <label>
                            <input
                                type="checkbox"
                                checked={notifyCustomer}
                                onChange={e => setNotifyCustomer(e.target.checked)}
                            />
                            Notify customer via email
                        </label>
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? <Loader2 size={16} className="spinning" /> : <Check size={16} />}
                            Confirm Reschedule
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// =============================================================================
// Cancel Modal
// =============================================================================

interface CancelModalProps {
    appointment: Appointment
    onClose: () => void
    onSuccess: () => void
}

function CancelModal({ appointment, onClose, onSuccess }: CancelModalProps) {
    const [reason, setReason] = useState('')
    const [notifyCustomer, setNotifyCustomer] = useState(true)
    const [loading, setLoading] = useState(false)
    const { addToast } = useToast()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        setLoading(true)
        try {
            const response = await api.post(`/api/admin/booking/appointments/${appointment.id}/cancel`, {
                reason: reason || 'Cancelled by admin',
                notify_customer: notifyCustomer
            })

            if (response.ok) {
                addToast({ type: 'success', message: 'Appointment cancelled' })
                onSuccess()
                onClose()
            } else {
                addToast({ type: 'error', message: response.error || 'Failed to cancel' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error cancelling appointment' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="unified-appt-modal-overlay" onClick={onClose}>
            <div className="unified-appt-modal modal--danger" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Cancel Appointment</h3>
                    <button className="modal-close" onClick={onClose}><X size={20} /></button>
                </div>

                <form onSubmit={handleSubmit} className="modal-content">
                    <div className="modal-warning">
                        <AlertTriangle size={24} />
                        <p>Are you sure you want to cancel this appointment?</p>
                    </div>

                    <div className="modal-info">
                        <p><strong>Customer:</strong> {appointment.first_name} {appointment.last_name}</p>
                        <p><strong>Time:</strong> {new Date(appointment.preferred_date_time).toLocaleString()}</p>
                    </div>

                    <div className="form-group">
                        <label>Cancellation Reason</label>
                        <textarea
                            value={reason}
                            onChange={e => setReason(e.target.value)}
                            placeholder="Reason for cancellation..."
                            rows={3}
                        />
                    </div>

                    <div className="form-group form-group--checkbox">
                        <label>
                            <input
                                type="checkbox"
                                checked={notifyCustomer}
                                onChange={e => setNotifyCustomer(e.target.checked)}
                            />
                            Notify customer via email
                        </label>
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn-secondary" onClick={onClose}>Back</button>
                        <button type="submit" className="btn-danger" disabled={loading}>
                            {loading ? <Loader2 size={16} className="spinning" /> : <XCircle size={16} />}
                            Cancel Appointment
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// =============================================================================
// Request Reschedule Modal
// =============================================================================

interface RequestRescheduleModalProps {
    appointment: Appointment
    onClose: () => void
    onSuccess: () => void
}

function RequestRescheduleModal({ appointment, onClose, onSuccess }: RequestRescheduleModalProps) {
    const [reason, setReason] = useState('')
    const [loading, setLoading] = useState(false)
    const { addToast } = useToast()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        setLoading(true)
        try {
            const response = await api.post(`/api/admin/booking/appointments/${appointment.id}/request-reschedule`, {
                reason: reason || 'Please select a new appointment time.'
            })

            if (response.ok) {
                addToast({ type: 'success', message: 'Reschedule request sent to customer' })
                onSuccess()
                onClose()
            } else {
                addToast({ type: 'error', message: response.error || 'Failed to send request' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error sending reschedule request' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="unified-appt-modal-overlay" onClick={onClose}>
            <div className="unified-appt-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Request Customer to Reschedule</h3>
                    <button className="modal-close" onClick={onClose}><X size={20} /></button>
                </div>

                <form onSubmit={handleSubmit} className="modal-content">
                    <div className="modal-info">
                        <p>An email will be sent to <strong>{appointment.email}</strong> asking them to select a new appointment time.</p>
                    </div>

                    <div className="form-group">
                        <label>Message to Customer</label>
                        <textarea
                            value={reason}
                            onChange={e => setReason(e.target.value)}
                            placeholder="Explain why they need to reschedule..."
                            rows={4}
                        />
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? <Loader2 size={16} className="spinning" /> : <Send size={16} />}
                            Send Request
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function UnifiedAppointmentsDashboard({
    eventsUrl = '/calendar/api/events',
    className = ''
}: UnifiedAppointmentsDashboardProps) {
    const [stats, setStats] = useState<Stats | null>(null)
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
    const [showRescheduleModal, setShowRescheduleModal] = useState(false)
    const [showCancelModal, setShowCancelModal] = useState(false)
    const [showRequestModal, setShowRequestModal] = useState(false)
    const [activeFilter, setActiveFilter] = useState<string>('all')
    const [calendarKey, setCalendarKey] = useState(0)
    const { addToast } = useToast()

    // Load stats
    const loadStats = useCallback(async () => {
        try {
            const response = await api.get<Stats>('/api/admin/booking/appointments/stats')
            if (response.ok && response.data) {
                setStats(response.data)
            }
        } catch {
            // Silently fail
        }
    }, [])

    useEffect(() => {
        loadStats()
    }, [loadStats])

    // Handle calendar event click
    const handleEventClick = useCallback(async (event: CalendarEvent) => {
        try {
            const response = await api.get<Appointment>(`/api/admin/booking/appointments/${event.id}`)
            if (response.ok && response.data) {
                setSelectedAppointment(response.data)
            } else {
                addToast({ type: 'error', message: 'Failed to load appointment details' })
            }
        } catch {
            addToast({ type: 'error', message: 'Error loading appointment' })
        }
    }, [addToast])

    // Handle filter clicks
    const handleFilterClick = (filter: string) => {
        setActiveFilter(filter)
        // For now just visual - could add date range filtering
    }

    // Refresh after actions
    const handleActionSuccess = useCallback(() => {
        setCalendarKey(k => k + 1)
        loadStats()
        setSelectedAppointment(null)
    }, [loadStats])

    // Build filtered events URL based on active filter
    const getFilteredEventsUrl = () => {
        const now = new Date()
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        const todayEnd = new Date(todayStart.getTime() + 24 * 60 * 60 * 1000)
        const weekEnd = new Date(todayStart.getTime() + 7 * 24 * 60 * 60 * 1000)

        let url = eventsUrl
        if (activeFilter === 'today') {
            url += `?start=${todayStart.toISOString()}&end=${todayEnd.toISOString()}`
        } else if (activeFilter === 'week') {
            url += `?start=${todayStart.toISOString()}&end=${weekEnd.toISOString()}`
        }
        return url
    }

    return (
        <div className={`unified-appointments-dashboard ${className}`}>
            {/* Stats Header */}
            <StatsCards stats={stats} onFilterClick={handleFilterClick} />

            {/* Filter Tabs */}
            <div className="unified-appt-filters">
                <button
                    className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('all')}
                >
                    <Filter size={14} />
                    All
                </button>
                <button
                    className={`filter-btn ${activeFilter === 'today' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('today')}
                >
                    Today
                </button>
                <button
                    className={`filter-btn ${activeFilter === 'week' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('week')}
                >
                    This Week
                </button>
                <button
                    className={`filter-btn ${activeFilter === 'pending' ? 'active' : ''}`}
                    onClick={() => setActiveFilter('pending')}
                >
                    Pending
                </button>
            </div>

            {/* Calendar */}
            <div className="unified-appt-calendar">
                <CalendarView
                    key={calendarKey}
                    eventsUrl={getFilteredEventsUrl()}
                    initialView="dayGridMonth"
                    editable={true}
                    selectable={false}
                    onEventClick={handleEventClick}
                    height={600}
                />
            </div>

            {/* Detail Slideout */}
            {selectedAppointment && (
                <AppointmentDetailSlideout
                    appointment={selectedAppointment}
                    onClose={() => setSelectedAppointment(null)}
                    onReschedule={() => setShowRescheduleModal(true)}
                    onCancel={() => setShowCancelModal(true)}
                    onRequestReschedule={() => setShowRequestModal(true)}
                />
            )}

            {/* Modals */}
            {showRescheduleModal && selectedAppointment && (
                <RescheduleModal
                    appointment={selectedAppointment}
                    onClose={() => setShowRescheduleModal(false)}
                    onSuccess={handleActionSuccess}
                />
            )}

            {showCancelModal && selectedAppointment && (
                <CancelModal
                    appointment={selectedAppointment}
                    onClose={() => setShowCancelModal(false)}
                    onSuccess={handleActionSuccess}
                />
            )}

            {showRequestModal && selectedAppointment && (
                <RequestRescheduleModal
                    appointment={selectedAppointment}
                    onClose={() => setShowRequestModal(false)}
                    onSuccess={handleActionSuccess}
                />
            )}
        </div>
    )
}

export default UnifiedAppointmentsDashboard
