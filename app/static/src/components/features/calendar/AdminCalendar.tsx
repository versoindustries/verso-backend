/**
 * AdminCalendar Component
 * 
 * Admin-specific calendar wrapper that handles event drag-and-drop updates
 * with CSRF protection and confirmation dialogs.
 */

import { useState, useCallback, useEffect } from 'react'
import { Calendar, CalendarEvent } from './Calendar'
import api from '../../../api'

interface Location {
    id: number
    name: string
}

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
    /** Show location filter dropdown */
    showLocationFilter?: boolean
}

export function AdminCalendar({
    eventsUrl,
    updateUrlPattern,
    initialView = 'dayGridMonth',
    height = 600,
    className = '',
    showLocationFilter = true,
}: AdminCalendarProps) {
    const [isUpdating, setIsUpdating] = useState(false)
    const [locations, setLocations] = useState<Location[]>([])
    const [selectedLocation, setSelectedLocation] = useState<number | null>(null)

    // Fetch locations for filter dropdown
    useEffect(() => {
        if (!showLocationFilter) return

        const fetchLocations = async () => {
            try {
                const response = await api.get<Location[]>('/admin/api/locations')
                if (response.data) {
                    setLocations(response.data)
                }
            } catch {
                // Silently fail - location filter just won't be available
            }
        }
        fetchLocations()
    }, [showLocationFilter])

    // Build events URL with location filter
    const filteredEventsUrl = selectedLocation
        ? `${eventsUrl}${eventsUrl.includes('?') ? '&' : '?'}location_id=${selectedLocation}`
        : eventsUrl

    const handleEventClick = useCallback((event: CalendarEvent) => {
        const props = event.extendedProps || {}
        const startStr = event.start instanceof Date
            ? event.start.toLocaleString()
            : new Date(event.start).toLocaleString()

        const locationInfo = props.location_name ? `\nLocation: ${props.location_name}` : ''

        alert(
            `Event: ${event.title}\n` +
            `Start: ${startStr}` +
            locationInfo + '\n' +
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
            {showLocationFilter && locations.length > 0 && (
                <div className="admin-calendar__filters">
                    <select
                        className="admin-calendar__location-filter"
                        value={selectedLocation || ''}
                        onChange={(e) => setSelectedLocation(e.target.value ? parseInt(e.target.value) : null)}
                    >
                        <option value="">All Locations</option>
                        {locations.map(loc => (
                            <option key={loc.id} value={loc.id}>{loc.name}</option>
                        ))}
                    </select>
                </div>
            )}
            {isUpdating && (
                <div className="admin-calendar-overlay">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Updating...</span>
                    </div>
                </div>
            )}
            <Calendar
                eventsUrl={filteredEventsUrl}
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

