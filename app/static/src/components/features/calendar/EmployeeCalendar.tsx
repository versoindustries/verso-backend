/**
 * EmployeeCalendar Component
 * 
 * A calendar view for employees to manage their appointments.
 * Wraps the base Calendar component and adds appointment detail panel,
 * check-in/check-out forms, staff notes, and reschedule requests.
 */

import { useState, useCallback } from 'react'
import Calendar, { CalendarEvent } from './Calendar'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface Appointment extends CalendarEvent {
    extendedProps: {
        service: string
        phone: string
        email: string
        status: string
        staff_notes?: string
        checked_in: boolean
        checked_out: boolean
    }
}

interface RescheduleRequest {
    id: number
    appointment_id: number
    proposed_datetime: string
    status: string
}

interface EmployeeCalendarProps {
    /** URL to fetch calendar events */
    eventsUrl: string
    /** URL pattern for check-in, with {id} placeholder */
    checkinUrlPattern: string
    /** URL pattern for check-out, with {id} placeholder */
    checkoutUrlPattern: string
    /** URL pattern for notes, with {id} placeholder */
    notesUrlPattern: string
    /** URL pattern for reschedule, with {id} placeholder */
    rescheduleUrlPattern: string
    /** Pending reschedule requests to display */
    pendingReschedules?: RescheduleRequest[]
    /** ICS feed URL for external calendar sync */
    icsFeedUrl?: string
    /** Custom class name */
    className?: string
}

// =============================================================================
// Main Component
// =============================================================================

export function EmployeeCalendar({
    eventsUrl,
    checkinUrlPattern,
    checkoutUrlPattern,
    notesUrlPattern,
    rescheduleUrlPattern,
    pendingReschedules = [],
    icsFeedUrl,
    className = '',
}: EmployeeCalendarProps) {
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
    const [staffNotes, setStaffNotes] = useState('')
    const [notesStatus, setNotesStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
    const [showReschedule, setShowReschedule] = useState(false)
    const [rescheduleDate, setRescheduleDate] = useState('')
    const [rescheduleTime, setRescheduleTime] = useState('')
    const [rescheduleReason, setRescheduleReason] = useState('')

    // Handle event click - show appointment details
    const handleEventClick = useCallback((event: CalendarEvent) => {
        const appointment = event as Appointment
        setSelectedAppointment(appointment)
        setStaffNotes(appointment.extendedProps?.staff_notes || '')
        setNotesStatus('idle')
        setShowReschedule(false)
    }, [])

    // Handle check-in
    const handleCheckin = async () => {
        if (!selectedAppointment) return

        try {
            const url = checkinUrlPattern.replace('{id}', selectedAppointment.id)
            await api.post(url, {})

            // Update local state
            setSelectedAppointment({
                ...selectedAppointment,
                extendedProps: {
                    ...selectedAppointment.extendedProps,
                    checked_in: true,
                }
            })
        } catch (error) {
            console.error('Check-in failed:', error)
            alert('Failed to check in. Please try again.')
        }
    }

    // Handle check-out
    const handleCheckout = async () => {
        if (!selectedAppointment) return

        try {
            const url = checkoutUrlPattern.replace('{id}', selectedAppointment.id)
            await api.post(url, {})

            // Update local state
            setSelectedAppointment({
                ...selectedAppointment,
                extendedProps: {
                    ...selectedAppointment.extendedProps,
                    checked_out: true,
                }
            })
        } catch (error) {
            console.error('Check-out failed:', error)
            alert('Failed to check out. Please try again.')
        }
    }

    // Save staff notes
    const handleSaveNotes = async () => {
        if (!selectedAppointment) return

        setNotesStatus('saving')

        try {
            const url = notesUrlPattern.replace('{id}', selectedAppointment.id)
            await api.post(url, { staff_notes: staffNotes })
            setNotesStatus('saved')
            setTimeout(() => setNotesStatus('idle'), 2000)
        } catch (error) {
            console.error('Failed to save notes:', error)
            setNotesStatus('error')
        }
    }

    // Submit reschedule request
    const handleRescheduleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedAppointment) return

        try {
            const url = rescheduleUrlPattern.replace('{id}', selectedAppointment.id)
            await api.post(url, {
                proposed_date: rescheduleDate,
                proposed_time: rescheduleTime,
                reason: rescheduleReason,
            })

            setShowReschedule(false)
            setRescheduleDate('')
            setRescheduleTime('')
            setRescheduleReason('')
            alert('Reschedule request submitted successfully.')
        } catch (error) {
            console.error('Reschedule request failed:', error)
            alert('Failed to submit reschedule request. Please try again.')
        }
    }

    return (
        <div className={`employee-calendar-container ${className}`}>
            <div className="row">
                {/* Calendar Column */}
                <div className="col-lg-8">
                    <div className="card">
                        <div className="card-body">
                            <Calendar
                                eventsUrl={eventsUrl}
                                initialView="timeGridWeek"
                                onEventClick={handleEventClick}
                                height="auto"
                            />
                        </div>
                    </div>
                </div>

                {/* Appointment Details Column */}
                <div className="col-lg-4">
                    {/* Selected Appointment Panel */}
                    {selectedAppointment && (
                        <div className="card mb-3 appointment-panel">
                            <div className="card-header bg-primary text-white">
                                <strong>{selectedAppointment.title}</strong>
                            </div>
                            <div className="card-body">
                                <p><strong>Client:</strong> {selectedAppointment.title}</p>
                                <p><strong>Service:</strong> {selectedAppointment.extendedProps?.service}</p>
                                <p>
                                    <strong>Phone:</strong>{' '}
                                    <a href={`tel:${selectedAppointment.extendedProps?.phone}`}>
                                        {selectedAppointment.extendedProps?.phone}
                                    </a>
                                </p>
                                <p>
                                    <strong>Email:</strong>{' '}
                                    <a href={`mailto:${selectedAppointment.extendedProps?.email}`}>
                                        {selectedAppointment.extendedProps?.email}
                                    </a>
                                </p>
                                <p>
                                    <strong>Status:</strong>{' '}
                                    <span className="badge bg-info">{selectedAppointment.extendedProps?.status}</span>
                                </p>

                                <hr />

                                {/* Check In/Out Actions */}
                                <div className="checkin-actions mb-3">
                                    <button
                                        type="button"
                                        className="btn btn-success btn-sm me-2"
                                        onClick={handleCheckin}
                                        disabled={selectedAppointment.extendedProps?.checked_in}
                                    >
                                        <i className="fas fa-sign-in-alt"></i> Check In
                                    </button>
                                    <button
                                        type="button"
                                        className="btn btn-secondary btn-sm"
                                        onClick={handleCheckout}
                                        disabled={!selectedAppointment.extendedProps?.checked_in || selectedAppointment.extendedProps?.checked_out}
                                    >
                                        <i className="fas fa-sign-out-alt"></i> Check Out
                                    </button>
                                </div>

                                {/* Staff Notes */}
                                <div className="form-group mb-3">
                                    <label><i className="fas fa-sticky-note"></i> Internal Notes</label>
                                    <textarea
                                        className="form-control"
                                        rows={3}
                                        placeholder="Notes visible only to staff..."
                                        value={staffNotes}
                                        onChange={(e) => setStaffNotes(e.target.value)}
                                    />
                                    <div className="mt-2">
                                        <button
                                            type="button"
                                            className="btn btn-sm btn-outline-primary"
                                            onClick={handleSaveNotes}
                                            disabled={notesStatus === 'saving'}
                                        >
                                            <i className="fas fa-save"></i> Save Notes
                                        </button>
                                        {notesStatus === 'saved' && (
                                            <span className="ms-2 text-success">Saved!</span>
                                        )}
                                        {notesStatus === 'error' && (
                                            <span className="ms-2 text-danger">Failed to save</span>
                                        )}
                                    </div>
                                </div>

                                <hr />

                                {/* Reschedule Request */}
                                <button
                                    type="button"
                                    className="btn btn-sm btn-outline-warning"
                                    onClick={() => setShowReschedule(!showReschedule)}
                                >
                                    <i className="fas fa-calendar-plus"></i> Request Reschedule
                                </button>

                                {showReschedule && (
                                    <form className="mt-3" onSubmit={handleRescheduleSubmit}>
                                        <div className="form-group mb-2">
                                            <label>Proposed Date</label>
                                            <input
                                                type="date"
                                                className="form-control"
                                                value={rescheduleDate}
                                                onChange={(e) => setRescheduleDate(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <div className="form-group mb-2">
                                            <label>Proposed Time</label>
                                            <input
                                                type="time"
                                                className="form-control"
                                                value={rescheduleTime}
                                                onChange={(e) => setRescheduleTime(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <div className="form-group mb-2">
                                            <label>Reason</label>
                                            <textarea
                                                className="form-control"
                                                rows={2}
                                                value={rescheduleReason}
                                                onChange={(e) => setRescheduleReason(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <button type="submit" className="btn btn-warning btn-sm">
                                            <i className="fas fa-paper-plane"></i> Submit Request
                                        </button>
                                    </form>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Pending Reschedule Requests */}
                    {pendingReschedules.length > 0 && (
                        <div className="card mb-3">
                            <div className="card-header bg-warning text-dark">
                                <strong><i className="fas fa-clock"></i> Pending Reschedule Requests</strong>
                            </div>
                            <ul className="list-group list-group-flush">
                                {pendingReschedules.map((rr) => (
                                    <li key={rr.id} className="list-group-item">
                                        <small>
                                            <strong>Appt #{rr.appointment_id}</strong><br />
                                            Proposed: {rr.proposed_datetime}<br />
                                            Status: <span className="badge bg-warning">{rr.status}</span>
                                        </small>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Color Legend */}
                    <div className="card">
                        <div className="card-body bg-light">
                            <h6><i className="fas fa-palette"></i> Color Legend</h6>
                            <small>
                                <span className="badge bg-primary me-1">●</span> Scheduled<br />
                                <span className="badge bg-success me-1">●</span> In Progress<br />
                                <span className="badge bg-secondary me-1">●</span> Completed
                            </small>
                        </div>
                    </div>

                    {/* ICS Feed Link */}
                    {icsFeedUrl && (
                        <div className="mt-3">
                            <a href={icsFeedUrl} className="btn btn-sm btn-outline-secondary w-100">
                                <i className="fas fa-rss"></i> Subscribe to ICS Feed
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default EmployeeCalendar
