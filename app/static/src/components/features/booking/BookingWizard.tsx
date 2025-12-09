import { useState, useEffect, useCallback } from 'react'
import DateTimePicker from './DateTimePicker'
import { format } from 'date-fns'
import { useToastApi } from '../../../hooks/useToastApi'

interface Estimator {
    id: number
    name: string
}

interface Service {
    id: number
    name: string
    price: number
    duration: number
}

export default function BookingWizard() {
    const [step, setStep] = useState(1)
    const [estimators, setEstimators] = useState<Estimator[]>([])
    const [services, setServices] = useState<Service[]>([])
    const [loading, setLoading] = useState(false)
    const api = useToastApi()

    // Selection State
    const [selectedEstimator, setSelectedEstimator] = useState<number | undefined>()
    const [selectedService, setSelectedService] = useState<number | undefined>()
    const [selectedDate, setSelectedDate] = useState<Date | undefined>()
    const [selectedTime, setSelectedTime] = useState<string | null>(null)
    const [contactInfo, setContactInfo] = useState({
        firstName: '',
        lastName: '',
        email: '',
        phone: ''
    })
    const [submitted, setSubmitted] = useState(false)

    const loadData = useCallback(async () => {
        const [estResponse, srvResponse] = await Promise.all([
            api.get<Estimator[]>('/api/booking/estimators', { silent: true }),
            api.get<Service[]>('/api/booking/services', { silent: true })
        ])
        if (estResponse.ok && estResponse.data) {
            setEstimators(estResponse.data)
        }
        if (srvResponse.ok && srvResponse.data) {
            setServices(srvResponse.data)
        }
    }, [api])

    useEffect(() => {
        loadData()
    }, [loadData])

    const handleNext = () => {
        setStep(prev => prev + 1)
    }

    const handleBack = () => {
        setStep(prev => prev - 1)
    }

    const handleSubmit = async () => {
        setLoading(true)
        const payload = {
            estimator_id: selectedEstimator,
            service_id: selectedService,
            date: selectedDate ? format(selectedDate, 'yyyy-MM-dd') : null,
            time: selectedTime,
            ...contactInfo
        }

        const response = await api.post('/api/booking/create', payload, {
            errorMessage: 'Booking failed. Please try again.'
        })

        if (response.ok) {
            setSubmitted(true)
        }
        setLoading(false)
    }

    if (submitted) {
        return (
            <div className="booking-wizard">
                <div className="booking-wizard__card">
                    <div className="booking-wizard__success">
                        <div className="booking-wizard__success-icon">✓</div>
                        <h2 className="booking-wizard__success-title">Request Received!</h2>
                        <p className="booking-wizard__success-message">
                            Thank you for booking with us. We have received your request and will contact you shortly to confirm your appointment.
                        </p>
                        <button
                            className="booking-wizard__btn booking-wizard__btn--primary"
                            onClick={() => window.location.reload()}
                        >
                            Book Another Appointment
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    const getStepClass = (stepNumber: number) => {
        if (step > stepNumber) return 'booking-wizard__step-number--completed'
        if (step === stepNumber) return 'booking-wizard__step-number--active'
        return 'booking-wizard__step-number--inactive'
    }

    const getConnectorClass = (afterStep: number) => {
        return step > afterStep
            ? 'booking-wizard__step-connector--active'
            : 'booking-wizard__step-connector--inactive'
    }

    return (
        <div className="booking-wizard">
            <h2 className="booking-wizard__title">Book an Appointment</h2>

            {/* Steps Indicator */}
            <div className="booking-wizard__steps">
                {[1, 2, 3, 4].map((s) => (
                    <div key={s} className="booking-wizard__step">
                        <div className={`booking-wizard__step-number ${getStepClass(s)}`}>
                            {step > s ? '✓' : s}
                        </div>
                        {s < 4 && (
                            <div className={`booking-wizard__step-connector ${getConnectorClass(s)}`} />
                        )}
                    </div>
                ))}
            </div>

            <div className="booking-wizard__card">
                {/* Step 1: Service & Estimator Selection */}
                {step === 1 && (
                    <div>
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">📋</span>
                            Select Service & Estimator
                        </h3>

                        <div className="booking-wizard__field">
                            <label className="booking-wizard__label">Choose a Service</label>
                            <div className="booking-wizard__services">
                                {services.length === 0 ? (
                                    <div className="booking-wizard__loading">
                                        <div className="booking-wizard__spinner"></div>
                                        <span>Loading services...</span>
                                    </div>
                                ) : (
                                    services.map(s => (
                                        <div
                                            key={s.id}
                                            className={`booking-wizard__service-card ${selectedService === s.id ? 'booking-wizard__service-card--selected' : ''
                                                }`}
                                            onClick={() => setSelectedService(s.id)}
                                        >
                                            <div className="booking-wizard__service-name">{s.name}</div>
                                            <div className="booking-wizard__service-meta">
                                                <span className="booking-wizard__service-price">${s.price}</span>
                                                <span>{s.duration} mins</span>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        <div className="booking-wizard__field">
                            <label className="booking-wizard__label">Preferred Estimator</label>
                            <select
                                className="booking-wizard__select"
                                value={selectedEstimator || ''}
                                onChange={(e) => setSelectedEstimator(Number(e.target.value))}
                            >
                                <option value="">Any Available Estimator</option>
                                {estimators.map(e => (
                                    <option key={e.id} value={e.id}>{e.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                )}

                {/* Step 2: Date & Time Selection */}
                {step === 2 && (
                    <div>
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">📅</span>
                            Select Date & Time
                        </h3>
                        <div className="booking-wizard__datetime">
                            <DateTimePicker
                                selectedDate={selectedDate}
                                onDateSelect={setSelectedDate}
                                selectedTime={selectedTime}
                                onTimeSelect={setSelectedTime}
                                estimatorId={selectedEstimator || estimators[0]?.id}
                                serviceId={selectedService}
                            />
                        </div>
                    </div>
                )}

                {/* Step 3: Contact Information */}
                {step === 3 && (
                    <div>
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">👤</span>
                            Your Information
                        </h3>
                        <div className="booking-wizard__form-grid">
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">First Name</label>
                                <input
                                    type="text"
                                    className="booking-wizard__input"
                                    placeholder="Enter your first name"
                                    value={contactInfo.firstName}
                                    onChange={e => setContactInfo({ ...contactInfo, firstName: e.target.value })}
                                />
                            </div>
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">Last Name</label>
                                <input
                                    type="text"
                                    className="booking-wizard__input"
                                    placeholder="Enter your last name"
                                    value={contactInfo.lastName}
                                    onChange={e => setContactInfo({ ...contactInfo, lastName: e.target.value })}
                                />
                            </div>
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">Email</label>
                                <input
                                    type="email"
                                    className="booking-wizard__input"
                                    placeholder="your.email@example.com"
                                    value={contactInfo.email}
                                    onChange={e => setContactInfo({ ...contactInfo, email: e.target.value })}
                                />
                            </div>
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">Phone</label>
                                <input
                                    type="tel"
                                    className="booking-wizard__input"
                                    placeholder="(555) 123-4567"
                                    value={contactInfo.phone}
                                    onChange={e => setContactInfo({ ...contactInfo, phone: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 4: Review & Submit */}
                {step === 4 && (
                    <div>
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">✅</span>
                            Review & Confirm
                        </h3>
                        <div className="booking-wizard__summary">
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Service</span>
                                <span className="booking-wizard__summary-value">
                                    {services.find(s => s.id === selectedService)?.name}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Estimator</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedEstimator
                                        ? estimators.find(e => e.id === selectedEstimator)?.name
                                        : 'Any Available'}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Date</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedDate ? format(selectedDate, 'PPP') : '—'}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Time</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedTime || '—'}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Name</span>
                                <span className="booking-wizard__summary-value">
                                    {contactInfo.firstName} {contactInfo.lastName}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Email</span>
                                <span className="booking-wizard__summary-value">
                                    {contactInfo.email}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Phone</span>
                                <span className="booking-wizard__summary-value">
                                    {contactInfo.phone || '—'}
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Navigation Buttons */}
                <div className="booking-wizard__actions">
                    <div>
                        {step > 1 && (
                            <button
                                className="booking-wizard__btn booking-wizard__btn--outline"
                                onClick={handleBack}
                                disabled={loading}
                            >
                                ← Back
                            </button>
                        )}
                    </div>
                    <div>
                        {step < 4 ? (
                            <button
                                className="booking-wizard__btn booking-wizard__btn--primary"
                                onClick={handleNext}
                                disabled={
                                    (step === 1 && !selectedService) ||
                                    (step === 2 && (!selectedDate || !selectedTime)) ||
                                    (step === 3 && (!contactInfo.firstName || !contactInfo.email))
                                }
                            >
                                Next →
                            </button>
                        ) : (
                            <button
                                className="booking-wizard__btn booking-wizard__btn--primary"
                                onClick={handleSubmit}
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <div className="booking-wizard__spinner"></div>
                                        Submitting...
                                    </>
                                ) : (
                                    'Confirm Booking'
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
