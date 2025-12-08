import { useState, useEffect } from 'react'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import 'react-day-picker/dist/style.css'
import { Button } from '../../ui/button'
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
        <div className="flex flex-col md:flex-row gap-8">
            <div className="p-4 border rounded-lg bg-white dark:bg-gray-800">
                <DayPicker
                    mode="single"
                    selected={selectedDate}
                    onSelect={onDateSelect}
                    disabled={{ before: new Date() }}
                    styles={{
                        caption: { color: 'var(--primary)' }
                    }}
                    classNames={{
                        day_selected: "bg-blue-600 text-white hover:bg-blue-700",
                        day_today: "font-bold text-blue-600"
                    }}
                />
            </div>

            <div className="flex-1">
                <h3 className="text-lg font-semibold mb-4">
                    {selectedDate ? format(selectedDate, 'EEEE, MMMM do') : 'Select a date'}
                </h3>

                {loading ? (
                    <div className="text-gray-500">Loading slots...</div>
                ) : selectedDate ? (
                    availableSlots.length > 0 ? (
                        <div className="grid grid-cols-3 gap-2">
                            {availableSlots.map(time => (
                                <Button
                                    key={time}
                                    variant={selectedTime === time ? 'default' : 'outline'}
                                    onClick={() => onTimeSelect(time)}
                                    className="w-full"
                                >
                                    {time}
                                </Button>
                            ))}
                        </div>
                    ) : (
                        <div className="text-amber-600">No available slots on this date.</div>
                    )
                ) : (
                    <div className="text-gray-500">Please choose a date to see available times.</div>
                )}
            </div>
        </div>
    )
}
