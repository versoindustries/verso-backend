import { useState, useEffect } from 'react'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import 'react-day-picker/dist/style.css'
import { useToastApi } from '../../../hooks/useToastApi'

interface DateTimePickerProps {
    selectedDate: Date | undefined
    onDateSelect: (date: Date | undefined) => void
    selectedTime: string | null
    onTimeSelect: (time: string) => void
    estimatorId?: number
    serviceId?: number
}

export default function DateTimePicker({
    selectedDate,
    onDateSelect,
    selectedTime,
    onTimeSelect,
    estimatorId,
    serviceId
}: DateTimePickerProps) {
    const [availableSlots, setAvailableSlots] = useState<string[]>([])
    const [loading, setLoading] = useState(false)
    const api = useToastApi()

    useEffect(() => {
        if (selectedDate && estimatorId) {
            setLoading(true)
            const dateStr = format(selectedDate, 'yyyy-MM-dd')

            api.get<{ slots?: string[] }>(
                `/api/booking/slots?estimator_id=${estimatorId}&date=${dateStr}&service_id=${serviceId || ''}`,
                { silent: true }
            ).then(response => {
                if (response.ok && response.data?.slots) {
                    setAvailableSlots(response.data.slots)
                } else {
                    setAvailableSlots([])
                }
            }).finally(() => setLoading(false))
        } else {
            setAvailableSlots([])
        }
    }, [selectedDate, estimatorId, serviceId, api])

    return (
        <div className="booking-wizard__datetime">
            <div className="booking-wizard__calendar">
                <DayPicker
                    mode="single"
                    selected={selectedDate}
                    onSelect={onDateSelect}
                    disabled={{ before: new Date() }}
                    modifiersClassNames={{
                        selected: 'booking-wizard__day--selected',
                        today: 'booking-wizard__day--today'
                    }}
                />
            </div>

            <div className="booking-wizard__slots">
                <h4 className="booking-wizard__slots-title">
                    {selectedDate ? format(selectedDate, 'EEEE, MMMM do') : 'Select a date'}
                </h4>

                {loading ? (
                    <div className="booking-wizard__loading">
                        <div className="booking-wizard__spinner"></div>
                        <span>Loading available times...</span>
                    </div>
                ) : selectedDate ? (
                    availableSlots.length > 0 ? (
                        <div className="booking-wizard__slots-grid">
                            {availableSlots.map(time => (
                                <button
                                    key={time}
                                    type="button"
                                    className={`booking-wizard__slot ${selectedTime === time ? 'booking-wizard__slot--selected' : ''}`}
                                    onClick={() => onTimeSelect(time)}
                                >
                                    {time}
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="booking-wizard__empty-state booking-wizard__empty-state--compact">
                            <span className="booking-wizard__empty-icon">📅</span>
                            <p>No available times on this date.</p>
                            <span className="booking-wizard__empty-hint">Try selecting a different date.</span>
                        </div>
                    )
                ) : (
                    <div className="booking-wizard__placeholder">
                        <span className="booking-wizard__placeholder-icon">👆</span>
                        <p>Please choose a date to see available times.</p>
                    </div>
                )}
            </div>
        </div>
    )
}

