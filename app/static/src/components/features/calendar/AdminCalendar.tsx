/**
 * AdminCalendar Component
 * 
 * Admin-specific calendar wrapper that handles event drag-and-drop updates
 * with CSRF protection and confirmation dialogs.
 */

import { useState, useCallback } from 'react'
import { Calendar, CalendarEvent } from './Calendar'
import api from '../../../api'

export interface AdminCalendarProps {
    /** URL to fetch events from */
    eventsUrl: string
    /** URL pattern for updating events - {id} will be replaced with event ID */
    updateUrlPattern: string
    /** Initial calendar view */
    initialView?: 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay' | 'listWeek'
    /** Calendar height */
    height?: number | string
    /** Additional CSS class */
    className?: string
}

export function AdminCalendar({
    eventsUrl,
    updateUrlPattern,
    initialView = 'dayGridMonth',
    height = 600,
    className = '',
}: AdminCalendarProps) {
    const [isUpdating, setIsUpdating] = useState(false)

    const handleEventClick = useCallback((event: CalendarEvent) => {
        const props = event.extendedProps || {}
        const startStr = event.start instanceof Date
            ? event.start.toLocaleString()
            : new Date(event.start).toLocaleString()

        alert(
            `Event: ${event.title}\n` +
            `Start: ${startStr}\n` +
            (props.description || '')
        )
    }, [])

    const handleEventChange = useCallback(async (event: CalendarEvent) => {
        if (!confirm('Are you sure about this change?')) {
            // Need to reload to revert - FullCalendar handles this via info.revert()
            window.location.reload()
            return
        }

        setIsUpdating(true)

        try {
            const updateUrl = updateUrlPattern.replace('{id}', event.id)
            const startStr = event.start instanceof Date
                ? event.start.toISOString()
                : new Date(event.start).toISOString()

            const formData = new FormData()
            formData.append('start', startStr)

            const response = await api.post<{ status: string; message?: string }>(updateUrl, formData)

            if (!response.ok || response.data?.status !== 'success') {
                const errorMsg = response.data?.message || response.error || 'Unknown error'
                alert('Update failed: ' + errorMsg)
                window.location.reload()
            }
        } catch (error) {
            alert('Error updating event: ' + (error instanceof Error ? error.message : 'Unknown error'))
            window.location.reload()
        } finally {
            setIsUpdating(false)
        }
    }, [updateUrlPattern])

    return (
        <div className={`admin-calendar ${className} ${isUpdating ? 'updating' : ''}`}>
            {isUpdating && (
                <div className="admin-calendar-overlay">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Updating...</span>
                    </div>
                </div>
            )}
            <Calendar
                eventsUrl={eventsUrl}
                initialView={initialView}
                editable={true}
                selectable={false}
                onEventClick={handleEventClick}
                onEventChange={handleEventChange}
                height={height}
            />
        </div>
    )
}

export default AdminCalendar
