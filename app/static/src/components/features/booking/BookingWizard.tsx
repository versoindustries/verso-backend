import { useState, useEffect, useCallback } from 'react'
import { Button } from '../../ui/button'
import { Card, CardContent } from '../../ui/card'
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
            <Card className="max-w-2xl mx-auto my-8">
                <CardContent className="p-8 text-center">
                    <h2 className="text-2xl font-bold text-green-600 mb-4">Request Received!</h2>
                    <p className="text-gray-600">
                        Thank you for booking with us. We have received your request and will contact you shortly to confirm.
                    </p>
                    <Button className="mt-6" onClick={() => window.location.reload()}>Book Another</Button>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="max-w-4xl mx-auto my-8 font-sans">
            <h2 className="text-2xl font-bold mb-6 text-center">Book an Appointment</h2>

            {/* Steps Indicator */}
            <div className="flex justify-center mb-8">
                {[1, 2, 3, 4].map(s => (
                    <div key={s} className={`flex items-center ${s < 4 ? 'w-full md:w-auto' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                            }`}>
                            {s}
                        </div>
                        {s < 4 && <div className={`h-1 w-12 mx-2 ${step > s ? 'bg-blue-600' : 'bg-gray-200'}`} />}
                    </div>
                ))}
            </div>

            <Card>
                <CardContent className="p-6">
                    {step === 1 && (
                        <div className="space-y-6">
                            <h3 className="text-xl font-semibold">Select Service & Estimator</h3>

                            <div>
                                <label className="block text-sm font-medium mb-1">Service</label>
                                <div className="grid md:grid-cols-2 gap-4">
                                    {services.map(s => (
                                        <div
                                            key={s.id}
                                            className={`p-4 border rounded-lg cursor-pointer transition-colors ${selectedService === s.id ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/10' : 'hover:border-gray-300'
                                                }`}
                                            onClick={() => setSelectedService(s.id)}
                                        >
                                            <div className="font-semibold">{s.name}</div>
                                            <div className="text-sm text-gray-500">${s.price} • {s.duration} mins</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Estimator</label>
                                <select
                                    className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700"
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

                    {step === 2 && (
                        <div className="space-y-6">
                            <h3 className="text-xl font-semibold">Select Date & Time</h3>
                            <DateTimePicker
                                selectedDate={selectedDate}
                                onDateSelect={setSelectedDate}
                                selectedTime={selectedTime}
                                onTimeSelect={setSelectedTime}
                                estimatorId={selectedEstimator || estimators[0]?.id} // Fallback to first if any
                                serviceId={selectedService}
                            />
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-6">
                            <h3 className="text-xl font-semibold">Your Information</h3>
                            <div className="grid md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">First Name</label>
                                    <input
                                        type="text"
                                        className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700"
                                        value={contactInfo.firstName}
                                        onChange={e => setContactInfo({ ...contactInfo, firstName: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Last Name</label>
                                    <input
                                        type="text"
                                        className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700"
                                        value={contactInfo.lastName}
                                        onChange={e => setContactInfo({ ...contactInfo, lastName: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Email</label>
                                    <input
                                        type="email"
                                        className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700"
                                        value={contactInfo.email}
                                        onChange={e => setContactInfo({ ...contactInfo, email: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Phone</label>
                                    <input
                                        type="tel"
                                        className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700"
                                        value={contactInfo.phone}
                                        onChange={e => setContactInfo({ ...contactInfo, phone: e.target.value })}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="space-y-6">
                            <h3 className="text-xl font-semibold">Review & Submit</h3>
                            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-2">
                                <p><strong>Service:</strong> {services.find(s => s.id === selectedService)?.name}</p>
                                <p><strong>Estimator:</strong> {selectedEstimator ? estimators.find(e => e.id === selectedEstimator)?.name : 'Any Available'}</p>
                                <p><strong>Date:</strong> {selectedDate ? format(selectedDate, 'PPP') : ''}</p>
                                <p><strong>Time:</strong> {selectedTime}</p>
                                <p><strong>Name:</strong> {contactInfo.firstName} {contactInfo.lastName}</p>
                                <p><strong>Email:</strong> {contactInfo.email}</p>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-between mt-8">
                        {step > 1 && (
                            <Button variant="outline" onClick={handleBack} disabled={loading}>Back</Button>
                        )}
                        <div className="ml-auto">
                            {step < 4 ? (
                                <Button
                                    onClick={handleNext}
                                    disabled={
                                        (step === 1 && !selectedService) ||
                                        (step === 2 && (!selectedDate || !selectedTime)) ||
                                        (step === 3 && (!contactInfo.firstName || !contactInfo.email))
                                    }
                                >
                                    Next
                                </Button>
                            ) : (
                                <Button onClick={handleSubmit} disabled={loading}>
                                    {loading ? 'Submitting...' : 'Confirm Booking'}
                                </Button>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
