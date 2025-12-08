/**
 * Calendar Component
 * 
 * A calendar wrapper for displaying and managing appointments.
 * Placeholder for Phase 18.2.
 */

import { useEffect, useRef } from 'react'

export interface CalendarEvent {
    id: string
    title: string
    start: string | Date
    end?: string | Date
    allDay?: boolean
    color?: string
    extendedProps?: Record<string, any>
}

export interface CalendarProps {
    /** Initial events */
    events?: CalendarEvent[]
    /** Events URL for fetching */
    eventsUrl?: string
    /** Initial view */
    initialView?: 'dayGridMonth' | 'timeGridWeek' | 'timeGridDay' | 'listWeek'
    /** Editable (drag/drop) */
    editable?: boolean
    /** Selectable (click to create) */
    selectable?: boolean
    /** Event click callback */
    onEventClick?: (event: CalendarEvent) => void
    /** Date select callback */
    onDateSelect?: (start: Date, end: Date) => void
    /** Event change callback (drag/drop) */
    onEventChange?: (event: CalendarEvent) => void
    /** Height */
    height?: number | string
    /** Additional class */
    className?: string
}

export function Calendar({
    events = [],
    eventsUrl,
    initialView = 'dayGridMonth',
    editable = false,
    selectable = false,
    onEventClick,
    onDateSelect,
    onEventChange,
    height = 'auto',
    className = '',
}: CalendarProps) {
    const containerRef = useRef<HTMLDivElement>(null)
    const calendarRef = useRef<any>(null)

    useEffect(() => {
        const loadCalendar = async () => {
            if (!containerRef.current) return

            // Dynamic import of FullCalendar
            const { Calendar: FC } = await import('@fullcalendar/core')
            const dayGridPlugin = (await import('@fullcalendar/daygrid')).default
            const timeGridPlugin = (await import('@fullcalendar/timegrid')).default
            const listPlugin = (await import('@fullcalendar/list')).default
            const interactionPlugin = (await import('@fullcalendar/interaction')).default

            // Destroy existing calendar
            if (calendarRef.current) {
                calendarRef.current.destroy()
            }

            calendarRef.current = new FC(containerRef.current, {
                plugins: [dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin],
                initialView,
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
                },
                events: eventsUrl || events,
                editable,
                selectable,
                height,
                eventClick: onEventClick ? (info: any) => {
                    onEventClick({
                        id: info.event.id,
                        title: info.event.title,
                        start: info.event.start,
                        end: info.event.end,
                        allDay: info.event.allDay,
                        extendedProps: info.event.extendedProps,
                    })
                } : undefined,
                select: onDateSelect ? (info: any) => {
                    onDateSelect(info.start, info.end)
                } : undefined,
                eventDrop: onEventChange ? (info: any) => {
                    onEventChange({
                        id: info.event.id,
                        title: info.event.title,
                        start: info.event.start,
                        end: info.event.end,
                        allDay: info.event.allDay,
                        extendedProps: info.event.extendedProps,
                    })
                } : undefined,
            })

            calendarRef.current.render()
        }

        loadCalendar()

        return () => {
            if (calendarRef.current) {
                calendarRef.current.destroy()
            }
        }
    }, [events, eventsUrl, initialView, editable, selectable, height])

    return (
        <div ref={containerRef} className={`calendar-wrapper ${className}`} />
    )
}

export default Calendar
