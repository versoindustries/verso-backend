import { useState, useEffect, useCallback } from 'react'
import { Button } from '../../ui/button'
import { Card, CardContent } from '../../ui/card'
import { format } from 'date-fns'
import { DayPicker } from 'react-day-picker'
import 'react-day-picker/dist/style.css'
import { useToastApi } from '../../../hooks/useToastApi'

interface AppointmentType {
    id: number
    name: string
    slug: string
    duration_minutes: number
    price: number | null
    description: string
    max_attendees: number
}

interface BookingPageProps {
    appointmentType: AppointmentType
    slotsApiUrl: string
    submitUrl: string
    csrfToken: string
}

export default function BookingPage({
    appointmentType,
    slotsApiUrl,
    submitUrl,
    csrfToken
}: BookingPageProps) {
    const [step, setStep] = useState(1)
    const [selectedDate, setSelectedDate] = useState<Date | undefined>()
    const [availableSlots, setAvailableSlots] = useState<string[]>([])
    const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [submitted, setSubmitted] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const api = useToastApi()

    // Form data
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        attendees: 1
    })

    // Fetch available slots when date is selected
    const fetchSlots = useCallback(async (date: Date) => {
        setLoading(true)
        setError(null)
        const dateStr = format(date, 'yyyy-MM-dd')

        const response = await api.get<{ slots?: string[] }>(
            `${slotsApiUrl}?date=${dateStr}`,
            { silent: true }
        )

        if (response.ok && response.data?.slots) {
            setAvailableSlots(response.data.slots)
        } else if (!response.ok) {
            setError('Failed to load available times')
            setAvailableSlots([])
        } else {
            setAvailableSlots([])
        }
        setLoading(false)
    }, [api, slotsApiUrl])

    useEffect(() => {
        if (selectedDate) {
            fetchSlots(selectedDate)
        } else {
            setAvailableSlots([])
        }
    }, [selectedDate, fetchSlots])

    const handleSlotSelect = (slotIso: string) => {
        setSelectedSlot(slotIso)
        setStep(2)
    }

    const handleBack = () => {
        setStep(1)
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setSubmitting(true)
        setError(null)

        const payload = {
            csrf_token: csrfToken,
            datetime: selectedSlot || '',
            first_name: formData.firstName,
            last_name: formData.lastName,
            email: formData.email,
            phone: formData.phone,
            ...(appointmentType.max_attendees > 1 && { attendees: formData.attendees })
        }

        const response = await api.post(submitUrl, payload, {
            errorMessage: 'Booking failed. Please try again.'
        })

        if (response.ok) {
            setSubmitted(true)
        } else {
            setError('Booking failed. Please try again.')
        }
        setSubmitting(false)
    }

    // Format time from ISO string
    const formatTime = (isoString: string) => {
        try {
            const date = new Date(isoString)
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        } catch {
            return isoString
        }
    }

    if (submitted) {
        return (
            <Card className="booking-page-card booking-success">
                <CardContent className="text-center py-8">
                    <div className="success-icon mb-4">
                        <svg className="w-16 h-16 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-green-600 mb-4">Booking Confirmed!</h2>
                    <p className="text-gray-600 mb-2">
                        Thank you for booking <strong>{appointmentType.name}</strong>.
                    </p>
                    <p className="text-gray-600 mb-4">
                        We'll send a confirmation email to <strong>{formData.email}</strong> shortly.
                    </p>
                    <div className="booking-summary bg-gray-50 p-4 rounded-lg mb-6">
                        <p><strong>Date:</strong> {selectedDate ? format(selectedDate, 'PPPP') : ''}</p>
                        <p><strong>Time:</strong> {selectedSlot ? formatTime(selectedSlot) : ''}</p>
                    </div>
                    <Button onClick={() => window.location.href = '/'}>Return Home</Button>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="booking-page py-5">
            <div className="booking-page-grid">
                {/* Sidebar - Service Info */}
                <div className="booking-sidebar">
                    <Card className="booking-page-card">
                        <CardContent className="p-4">
                            <h3 className="text-xl font-semibold mb-2">{appointmentType.name}</h3>
                            <p className="text-gray-500 mb-2">
                                <i className="fas fa-clock me-1"></i>
                                {appointmentType.duration_minutes} Minutes
                            </p>
                            {appointmentType.price && (
                                <p className="text-2xl font-bold text-primary mb-3">
                                    ${appointmentType.price.toFixed(2)}
                                </p>
                            )}
                            <p className="text-gray-600 mb-4">{appointmentType.description}</p>

                            {selectedSlot && selectedDate && (
                                <>
                                    <hr className="my-4" />
                                    <div className="selected-slot-info">
                                        <h4 className="font-semibold mb-2">Selected Time:</h4>
                                        <p className="text-primary font-bold">
                                            {format(selectedDate, 'PPP')} at {formatTime(selectedSlot)}
                                        </p>
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content */}
                <div className="booking-main">
                    <Card className="booking-page-card">
                        <CardContent className="p-6">
                            {step === 1 && (
                                <div className="step-1">
                                    <h3 className="text-xl font-semibold mb-4">
                                        <span className="step-number">1</span> Select Date & Time
                                    </h3>

                                    <div className="date-time-picker-grid">
                                        <div className="calendar-container">
                                            <DayPicker
                                                mode="single"
                                                selected={selectedDate}
                                                onSelect={setSelectedDate}
                                                disabled={{ before: new Date() }}
                                                classNames={{
                                                    day_selected: 'rdp-day-selected',
                                                    day_today: 'rdp-day-today'
                                                }}
                                            />
                                        </div>

                                        <div className="slots-container">
                                            <h4 className="font-medium mb-3">
                                                {selectedDate ? format(selectedDate, 'EEEE, MMMM do') : 'Select a date'}
                                            </h4>

                                            {loading ? (
                                                <div className="text-gray-500">
                                                    <div className="spinner-border spinner-border-sm me-2" role="status">
                                                        <span className="visually-hidden">Loading...</span>
                                                    </div>
                                                    Loading available times...
                                                </div>
                                            ) : error ? (
                                                <div className="text-danger">{error}</div>
                                            ) : !selectedDate ? (
                                                <p className="text-gray-500">Please choose a date to see available times.</p>
                                            ) : availableSlots.length === 0 ? (
                                                <p className="text-warning">No slots available on this date.</p>
                                            ) : (
                                                <div className="slots-grid">
                                                    {availableSlots.map((slot) => (
                                                        <Button
                                                            key={slot}
                                                            variant={selectedSlot === slot ? 'default' : 'outline'}
                                                            onClick={() => handleSlotSelect(slot)}
                                                            className="slot-button"
                                                        >
                                                            {formatTime(slot)}
                                                        </Button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {step === 2 && (
                                <div className="step-2">
                                    <h3 className="text-xl font-semibold mb-4">
                                        <span className="step-number">2</span> Your Details
                                    </h3>

                                    <form onSubmit={handleSubmit}>
                                        <div className="form-grid">
                                            <div className="form-group">
                                                <label className="form-label">First Name *</label>
                                                <input
                                                    type="text"
                                                    name="firstName"
                                                    className="form-control"
                                                    value={formData.firstName}
                                                    onChange={handleInputChange}
                                                    required
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">Last Name *</label>
                                                <input
                                                    type="text"
                                                    name="lastName"
                                                    className="form-control"
                                                    value={formData.lastName}
                                                    onChange={handleInputChange}
                                                    required
                                                />
                                            </div>
                                        </div>

                                        <div className="form-group mb-3">
                                            <label className="form-label">Email *</label>
                                            <input
                                                type="email"
                                                name="email"
                                                className="form-control"
                                                value={formData.email}
                                                onChange={handleInputChange}
                                                required
                                            />
                                        </div>

                                        <div className="form-group mb-3">
                                            <label className="form-label">Phone *</label>
                                            <input
                                                type="tel"
                                                name="phone"
                                                className="form-control"
                                                value={formData.phone}
                                                onChange={handleInputChange}
                                                required
                                            />
                                        </div>

                                        {appointmentType.max_attendees > 1 && (
                                            <div className="form-group mb-3">
                                                <label className="form-label">Number of People</label>
                                                <input
                                                    type="number"
                                                    name="attendees"
                                                    className="form-control"
                                                    value={formData.attendees}
                                                    onChange={handleInputChange}
                                                    min={1}
                                                    max={appointmentType.max_attendees}
                                                />
                                            </div>
                                        )}

                                        {error && (
                                            <div className="alert alert-danger mb-3">{error}</div>
                                        )}

                                        <div className="button-group">
                                            <Button
                                                type="submit"
                                                className="btn-lg"
                                                disabled={submitting}
                                            >
                                                {submitting ? 'Confirming...' : 'Confirm Booking'}
                                            </Button>
                                            <Button
                                                type="button"
                                                variant="outline"
                                                onClick={handleBack}
                                                disabled={submitting}
                                            >
                                                Back
                                            </Button>
                                        </div>
                                    </form>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
