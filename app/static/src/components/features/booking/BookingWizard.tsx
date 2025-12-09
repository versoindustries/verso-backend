import { useState, useEffect, useCallback, useMemo } from 'react'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import 'react-day-picker/dist/style.css'
import { useToastApi } from '../../../hooks/useToastApi'

// ============================================================================
// TYPES
// ============================================================================

interface Estimator {
    id: number
    name: string
}

interface Service {
    id: number
    name: string
    price: number
    duration: number
    description?: string
    icon?: string
}

interface ContactInfo {
    firstName: string
    lastName: string
    email: string
    phone: string
}

type WizardStep = 1 | 2 | 3 | 4

// ============================================================================
// ENTERPRISE BOOKING WIZARD
// ============================================================================

export default function BookingWizard() {
    // Step management
    const [step, setStep] = useState<WizardStep>(1)
    const [animating, setAnimating] = useState(false)

    // Data state
    const [estimators, setEstimators] = useState<Estimator[]>([])
    const [services, setServices] = useState<Service[]>([])
    const [availableSlots, setAvailableSlots] = useState<string[]>([])

    // Loading states
    const [dataLoading, setDataLoading] = useState(true)
    const [slotsLoading, setSlotsLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)

    // Error states
    const [dataError, setDataError] = useState<string | null>(null)

    // Selection state
    const [selectedService, setSelectedService] = useState<number | undefined>()
    const [selectedEstimator, setSelectedEstimator] = useState<number | undefined>()
    const [selectedDate, setSelectedDate] = useState<Date | undefined>()
    const [selectedTime, setSelectedTime] = useState<string | null>(null)
    const [contactInfo, setContactInfo] = useState<ContactInfo>({
        firstName: '',
        lastName: '',
        email: '',
        phone: ''
    })

    // Final state
    const [submitted, setSubmitted] = useState(false)

    const api = useToastApi()

    const stepLabels = ['Service', 'Schedule', 'Details', 'Confirm']

    // ========================================================================
    // DATA LOADING
    // ========================================================================

    const loadInitialData = useCallback(async () => {
        setDataLoading(true)
        setDataError(null)

        try {
            const [estResponse, srvResponse] = await Promise.all([
                api.get<Estimator[]>('/api/booking/estimators', { silent: true }),
                api.get<Service[]>('/api/booking/services', { silent: true })
            ])

            if (estResponse.ok && estResponse.data) {
                setEstimators(estResponse.data)
            } else {
                throw new Error('Failed to load estimators')
            }

            if (srvResponse.ok && srvResponse.data) {
                setServices(srvResponse.data)
            } else {
                throw new Error('Failed to load services')
            }
        } catch (err) {
            setDataError('Unable to load booking options. Please try again.')
        } finally {
            setDataLoading(false)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        loadInitialData()
    }, [loadInitialData])

    // Load time slots when date changes
    const loadTimeSlots = useCallback(async (date: Date, estimatorId: number | undefined, serviceId: number | undefined) => {
        if (!estimatorId) {
            // If no specific estimator, use first available
            estimatorId = estimators[0]?.id
        }

        if (!estimatorId) {
            setAvailableSlots([])
            return
        }

        setSlotsLoading(true)
        const dateStr = format(date, 'yyyy-MM-dd')

        try {
            const response = await api.get<{ slots?: string[] }>(
                `/api/booking/slots?estimator_id=${estimatorId}&date=${dateStr}&service_id=${serviceId || ''}`,
                { silent: true }
            )

            if (response.ok && response.data?.slots) {
                setAvailableSlots(response.data.slots)
            } else {
                setAvailableSlots([])
            }
        } catch {
            setAvailableSlots([])
        } finally {
            setSlotsLoading(false)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [estimators])

    useEffect(() => {
        if (selectedDate && step === 2) {
            loadTimeSlots(selectedDate, selectedEstimator, selectedService)
        }
    }, [selectedDate, selectedEstimator, selectedService, step, loadTimeSlots])

    // ========================================================================
    // NAVIGATION
    // ========================================================================

    const handleNext = () => {
        setAnimating(true)
        setTimeout(() => {
            setStep(prev => (prev + 1) as WizardStep)
            setAnimating(false)
        }, 200)
    }

    const handleBack = () => {
        setAnimating(true)
        setTimeout(() => {
            setStep(prev => (prev - 1) as WizardStep)
            setAnimating(false)
        }, 200)
    }

    const handleDateSelect = (date: Date | undefined) => {
        setSelectedDate(date)
        setSelectedTime(null) // Reset time when date changes
    }

    // ========================================================================
    // FORM SUBMISSION
    // ========================================================================

    const handleSubmit = async () => {
        setSubmitting(true)

        const payload = {
            estimator_id: selectedEstimator || estimators[0]?.id,
            service_id: selectedService,
            date: selectedDate ? format(selectedDate, 'yyyy-MM-dd') : null,
            time: selectedTime,
            first_name: contactInfo.firstName,
            last_name: contactInfo.lastName,
            email: contactInfo.email,
            phone: contactInfo.phone
        }

        const response = await api.post('/api/booking/create', payload, {
            errorMessage: 'Booking failed. Please try again.'
        })

        if (response.ok) {
            setSubmitted(true)
        }
        setSubmitting(false)
    }

    // ========================================================================
    // COMPUTED VALUES
    // ========================================================================

    const selectedServiceData = useMemo(() =>
        services.find(s => s.id === selectedService),
        [services, selectedService]
    )

    const selectedEstimatorData = useMemo(() =>
        estimators.find(e => e.id === selectedEstimator),
        [estimators, selectedEstimator]
    )

    const canProceed = useMemo(() => {
        switch (step) {
            case 1:
                return !!selectedService
            case 2:
                return !!selectedDate && !!selectedTime
            case 3:
                return !!contactInfo.firstName.trim() &&
                    !!contactInfo.lastName.trim() &&
                    !!contactInfo.email.trim() &&
                    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactInfo.email)
            case 4:
                return true
            default:
                return false
        }
    }, [step, selectedService, selectedDate, selectedTime, contactInfo])

    const formatPrice = (price: number) => {
        if (price === 0) return 'Free'
        return `$${price.toFixed(0)}`
    }

    const formatTimeSlot = (time: string) => {
        const [hours, minutes] = time.split(':').map(Number)
        const ampm = hours >= 12 ? 'PM' : 'AM'
        const displayHours = hours % 12 || 12
        return `${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`
    }

    // ========================================================================
    // SUCCESS STATE
    // ========================================================================

    if (submitted) {
        return (
            <div className="booking-wizard">
                <div className="booking-wizard__card">
                    <div className="booking-wizard__success">
                        <div className="booking-wizard__success-icon">✓</div>
                        <h2 className="booking-wizard__success-title">Booking Confirmed!</h2>
                        <p className="booking-wizard__success-message">
                            Thank you for scheduling with us. We've received your appointment request and will send a confirmation to <strong>{contactInfo.email}</strong> shortly.
                        </p>
                        <div className="booking-wizard__success-details">
                            <div className="booking-wizard__success-item">
                                <span className="booking-wizard__success-label">Service</span>
                                <span className="booking-wizard__success-value">{selectedServiceData?.name}</span>
                            </div>
                            <div className="booking-wizard__success-item">
                                <span className="booking-wizard__success-label">Date & Time</span>
                                <span className="booking-wizard__success-value">
                                    {selectedDate ? format(selectedDate, 'PPP') : ''} at {selectedTime ? formatTimeSlot(selectedTime) : ''}
                                </span>
                            </div>
                        </div>
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

    // ========================================================================
    // STEP INDICATORS
    // ========================================================================

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

    // ========================================================================
    // RENDER
    // ========================================================================

    return (
        <div className="booking-wizard">
            <h2 className="booking-wizard__title">Book an Appointment</h2>

            {/* Progress Steps */}
            <div className="booking-wizard__steps">
                {[1, 2, 3, 4].map((s) => (
                    <div key={s} className="booking-wizard__step">
                        <div className="booking-wizard__step-content">
                            <div className={`booking-wizard__step-number ${getStepClass(s)}`}>
                                {step > s ? '✓' : s}
                            </div>
                            <span className={`booking-wizard__step-label ${step >= s ? 'booking-wizard__step-label--active' : ''}`}>
                                {stepLabels[s - 1]}
                            </span>
                        </div>
                        {s < 4 && (
                            <div className={`booking-wizard__step-connector ${getConnectorClass(s)}`} />
                        )}
                    </div>
                ))}
            </div>

            <div className={`booking-wizard__card ${animating ? 'booking-wizard__card--animating' : ''}`}>

                {/* ERROR STATE */}
                {dataError && (
                    <div className="booking-wizard__error">
                        <div className="booking-wizard__error-icon">⚠️</div>
                        <p>{dataError}</p>
                        <button
                            className="booking-wizard__btn booking-wizard__btn--outline"
                            onClick={loadInitialData}
                        >
                            Try Again
                        </button>
                    </div>
                )}

                {/* STEP 1: Service Selection */}
                {step === 1 && !dataError && (
                    <div className="booking-wizard__step-content-area">
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">📋</span>
                            Choose Your Service
                        </h3>

                        <div className="booking-wizard__services">
                            {dataLoading ? (
                                <>
                                    {[1, 2, 3].map(i => (
                                        <div key={i} className="booking-wizard__service-card booking-wizard__service-card--skeleton">
                                            <div className="booking-wizard__skeleton booking-wizard__skeleton--title" />
                                            <div className="booking-wizard__skeleton booking-wizard__skeleton--text" />
                                        </div>
                                    ))}
                                </>
                            ) : services.length === 0 ? (
                                <div className="booking-wizard__empty-state">
                                    <div className="booking-wizard__empty-icon">📋</div>
                                    <p>No services are currently available.</p>
                                    <span className="booking-wizard__empty-hint">Please check back later or contact us directly.</span>
                                </div>
                            ) : (
                                services.map(service => (
                                    <div
                                        key={service.id}
                                        className={`booking-wizard__service-card ${selectedService === service.id ? 'booking-wizard__service-card--selected' : ''}`}
                                        onClick={() => setSelectedService(service.id)}
                                        role="button"
                                        tabIndex={0}
                                        onKeyDown={(e) => e.key === 'Enter' && setSelectedService(service.id)}
                                    >
                                        {service.icon && (
                                            <div className="booking-wizard__service-icon">
                                                <i className={`fas ${service.icon}`} />
                                            </div>
                                        )}
                                        <div className="booking-wizard__service-name">{service.name}</div>
                                        {service.description && (
                                            <div className="booking-wizard__service-desc">{service.description}</div>
                                        )}
                                        <div className="booking-wizard__service-meta">
                                            <span className="booking-wizard__service-price">{formatPrice(service.price)}</span>
                                            <span className="booking-wizard__service-duration">
                                                <i className="fas fa-clock" /> {service.duration} min
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="booking-wizard__field">
                            <label className="booking-wizard__label">Preferred Staff Member (Optional)</label>
                            <select
                                className="booking-wizard__select"
                                value={selectedEstimator || ''}
                                onChange={(e) => setSelectedEstimator(e.target.value ? Number(e.target.value) : undefined)}
                            >
                                <option value="">Any Available</option>
                                {estimators.map(e => (
                                    <option key={e.id} value={e.id}>{e.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                )}

                {/* STEP 2: Date & Time Selection */}
                {step === 2 && (
                    <div className="booking-wizard__step-content-area">
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">📅</span>
                            Select Date & Time
                        </h3>

                        <div className="booking-wizard__datetime">
                            <div className="booking-wizard__calendar">
                                <DayPicker
                                    mode="single"
                                    selected={selectedDate}
                                    onSelect={handleDateSelect}
                                    disabled={{ before: new Date() }}
                                    modifiersClassNames={{
                                        selected: 'booking-wizard__day--selected',
                                        today: 'booking-wizard__day--today'
                                    }}
                                />
                            </div>

                            <div className="booking-wizard__slots">
                                <h4 className="booking-wizard__slots-title">
                                    {selectedDate ? format(selectedDate, 'EEEE, MMMM do') : 'Select a date first'}
                                </h4>

                                {slotsLoading ? (
                                    <div className="booking-wizard__slots-grid">
                                        {[1, 2, 3, 4, 5, 6].map(i => (
                                            <div key={i} className="booking-wizard__slot booking-wizard__slot--skeleton">
                                                <div className="booking-wizard__skeleton booking-wizard__skeleton--slot" />
                                            </div>
                                        ))}
                                    </div>
                                ) : !selectedDate ? (
                                    <div className="booking-wizard__placeholder">
                                        <span className="booking-wizard__placeholder-icon">👆</span>
                                        <p>Choose a date from the calendar to see available times.</p>
                                    </div>
                                ) : availableSlots.length > 0 ? (
                                    <div className="booking-wizard__slots-grid">
                                        {availableSlots.map(time => (
                                            <button
                                                key={time}
                                                type="button"
                                                className={`booking-wizard__slot ${selectedTime === time ? 'booking-wizard__slot--selected' : ''}`}
                                                onClick={() => setSelectedTime(time)}
                                            >
                                                {formatTimeSlot(time)}
                                            </button>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="booking-wizard__empty-state booking-wizard__empty-state--compact">
                                        <span className="booking-wizard__empty-icon">📅</span>
                                        <p>No available times on this date.</p>
                                        <span className="booking-wizard__empty-hint">Try selecting a different date.</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* STEP 3: Contact Information */}
                {step === 3 && (
                    <div className="booking-wizard__step-content-area">
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">👤</span>
                            Your Information
                        </h3>

                        <div className="booking-wizard__form-grid">
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">First Name *</label>
                                <input
                                    type="text"
                                    className="booking-wizard__input"
                                    placeholder="Enter your first name"
                                    value={contactInfo.firstName}
                                    onChange={e => setContactInfo({ ...contactInfo, firstName: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">Last Name *</label>
                                <input
                                    type="text"
                                    className="booking-wizard__input"
                                    placeholder="Enter your last name"
                                    value={contactInfo.lastName}
                                    onChange={e => setContactInfo({ ...contactInfo, lastName: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">Email Address *</label>
                                <input
                                    type="email"
                                    className="booking-wizard__input"
                                    placeholder="your.email@example.com"
                                    value={contactInfo.email}
                                    onChange={e => setContactInfo({ ...contactInfo, email: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="booking-wizard__field">
                                <label className="booking-wizard__label">Phone Number</label>
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

                {/* STEP 4: Review & Confirm */}
                {step === 4 && (
                    <div className="booking-wizard__step-content-area">
                        <h3 className="booking-wizard__section-title">
                            <span className="booking-wizard__section-icon">✅</span>
                            Review & Confirm
                        </h3>

                        <div className="booking-wizard__summary">
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Service</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedServiceData?.name}
                                    <span className="booking-wizard__summary-price">
                                        {formatPrice(selectedServiceData?.price || 0)}
                                    </span>
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Staff Member</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedEstimatorData?.name || 'Any Available'}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Date</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedDate ? format(selectedDate, 'PPPP') : '—'}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Time</span>
                                <span className="booking-wizard__summary-value">
                                    {selectedTime ? formatTimeSlot(selectedTime) : '—'}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-divider" />
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Name</span>
                                <span className="booking-wizard__summary-value">
                                    {contactInfo.firstName} {contactInfo.lastName}
                                </span>
                            </div>
                            <div className="booking-wizard__summary-row">
                                <span className="booking-wizard__summary-label">Email</span>
                                <span className="booking-wizard__summary-value">{contactInfo.email}</span>
                            </div>
                            {contactInfo.phone && (
                                <div className="booking-wizard__summary-row">
                                    <span className="booking-wizard__summary-label">Phone</span>
                                    <span className="booking-wizard__summary-value">{contactInfo.phone}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Navigation Buttons */}
                {!dataError && (
                    <div className="booking-wizard__actions">
                        <div>
                            {step > 1 && (
                                <button
                                    className="booking-wizard__btn booking-wizard__btn--outline"
                                    onClick={handleBack}
                                    disabled={submitting}
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
                                    disabled={!canProceed}
                                >
                                    Continue →
                                </button>
                            ) : (
                                <button
                                    className="booking-wizard__btn booking-wizard__btn--primary"
                                    onClick={handleSubmit}
                                    disabled={submitting}
                                >
                                    {submitting ? (
                                        <>
                                            <div className="booking-wizard__spinner" />
                                            Processing...
                                        </>
                                    ) : (
                                        'Confirm Booking'
                                    )}
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
