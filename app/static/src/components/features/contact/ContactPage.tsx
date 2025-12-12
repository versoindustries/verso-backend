/**
 * ContactPage - Enterprise Contact Form React Island
 * 
 * World-class design with glassmorphism, micro-animations, and premium UX.
 * Features:
 * - Animated form fields with validation
 * - Success/error state handling  
 * - CSRF protection
 * - Responsive design
 * - Accessibility compliant
 */

import { useState, useRef } from 'react'
import {
    User,
    Mail,
    Phone,
    MessageSquare,
    CheckCircle,
    AlertCircle,
    Sparkles,
    Building2,
    ArrowRight,
    MapPin,
    Clock,
    Shield
} from 'lucide-react'
import './contact-page.css'

interface ContactFormData {
    firstName: string
    lastName: string
    email: string
    phone: string
    message: string
}

interface FormErrors {
    firstName?: string
    lastName?: string
    email?: string
    phone?: string
    message?: string
}

interface ContactPageProps {
    csrfToken: string
    submitUrl: string
    confirmationUrl: string
    businessName?: string
    businessEmail?: string
    businessPhone?: string
    businessAddress?: string
    businessHours?: string
}

type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error'

export default function ContactPage({
    csrfToken,
    submitUrl,
    confirmationUrl,
    businessName = 'Verso Industries',
    businessEmail = 'contact@versoindustries.com',
    businessPhone = '(555) 123-4567',
    businessAddress = '123 Innovation Drive, Tech City, TC 12345',
    businessHours = 'Mon-Fri: 9AM - 6PM'
}: ContactPageProps) {
    const [formData, setFormData] = useState<ContactFormData>({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        message: ''
    })
    const [errors, setErrors] = useState<FormErrors>({})
    const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle')
    const [focusedField, setFocusedField] = useState<string | null>(null)
    const formRef = useRef<HTMLFormElement>(null)

    // Validate email format
    const validateEmail = (email: string): boolean => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        return emailRegex.test(email)
    }

    // Validate phone format (flexible)
    const validatePhone = (phone: string): boolean => {
        if (!phone) return true // Phone is optional
        const phoneRegex = /^[\d\s\-\(\)\+]+$/
        return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10
    }

    // Validate form
    const validateForm = (): boolean => {
        const newErrors: FormErrors = {}

        if (!formData.firstName.trim()) {
            newErrors.firstName = 'First name is required'
        }

        if (!formData.lastName.trim()) {
            newErrors.lastName = 'Last name is required'
        }

        if (!formData.email.trim()) {
            newErrors.email = 'Email is required'
        } else if (!validateEmail(formData.email)) {
            newErrors.email = 'Please enter a valid email address'
        }

        if (formData.phone && !validatePhone(formData.phone)) {
            newErrors.phone = 'Please enter a valid phone number'
        }

        if (!formData.message.trim()) {
            newErrors.message = 'Message is required'
        } else if (formData.message.trim().length < 10) {
            newErrors.message = 'Message must be at least 10 characters'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    // Handle input change
    const handleChange = (field: keyof ContactFormData, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: undefined }))
        }
    }

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateForm()) {
            return
        }

        setSubmitStatus('submitting')

        try {
            const formPayload = new FormData()
            formPayload.append('csrf_token', csrfToken)
            formPayload.append('first_name', formData.firstName)
            formPayload.append('last_name', formData.lastName)
            formPayload.append('email', formData.email)
            formPayload.append('phone', formData.phone)
            formPayload.append('message', formData.message)

            const response = await fetch(submitUrl, {
                method: 'POST',
                body: formPayload,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })

            if (response.ok) {
                setSubmitStatus('success')
                // Redirect after showing success message
                setTimeout(() => {
                    window.location.href = confirmationUrl
                }, 1500)
            } else {
                setSubmitStatus('error')
            }
        } catch (error) {
            console.error('Form submission error:', error)
            setSubmitStatus('error')
        }
    }

    // Render floating label input
    const renderInput = (
        field: keyof ContactFormData,
        label: string,
        icon: React.ReactNode,
        type: string = 'text',
        required: boolean = true
    ) => {
        const hasValue = formData[field].length > 0
        const isFocused = focusedField === field
        const hasError = !!errors[field]

        return (
            <div className={`contact-form-field ${hasError ? 'has-error' : ''} ${isFocused ? 'is-focused' : ''} ${hasValue ? 'has-value' : ''}`}>
                <div className="field-icon">{icon}</div>
                <input
                    type={type}
                    id={field}
                    name={field}
                    value={formData[field]}
                    onChange={(e) => handleChange(field, e.target.value)}
                    onFocus={() => setFocusedField(field)}
                    onBlur={() => setFocusedField(null)}
                    required={required}
                    className="contact-input"
                    autoComplete={field === 'email' ? 'email' : field === 'phone' ? 'tel' : 'off'}
                />
                <label htmlFor={field} className="floating-label">
                    {label} {required && <span className="required-star">*</span>}
                </label>
                <div className="field-highlight"></div>
                {hasError && (
                    <div className="field-error">
                        <AlertCircle size={14} />
                        <span>{errors[field]}</span>
                    </div>
                )}
            </div>
        )
    }

    // Success state
    if (submitStatus === 'success') {
        return (
            <div className="contact-page">
                <div className="contact-success-container">
                    <div className="success-icon-wrapper">
                        <CheckCircle size={64} />
                        <div className="success-ripple"></div>
                    </div>
                    <h2>Message Sent!</h2>
                    <p>Thank you for reaching out. We'll get back to you shortly.</p>
                    <div className="success-redirect">
                        <span>Redirecting you...</span>
                        <div className="redirect-loader"></div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="contact-page">
            {/* Hero Section */}
            <div className="contact-hero">
                <div className="hero-content">
                    <div className="hero-badge">
                        <Sparkles size={16} />
                        <span>Get in Touch</span>
                    </div>
                    <h1>Let's Start a Conversation</h1>
                    <p>Have a question or want to learn more? We'd love to hear from you.</p>
                </div>
                <div className="hero-decoration">
                    <div className="decoration-circle circle-1"></div>
                    <div className="decoration-circle circle-2"></div>
                    <div className="decoration-circle circle-3"></div>
                </div>
            </div>

            {/* Main Content */}
            <div className="contact-main">
                {/* Contact Info Cards */}
                <div className="contact-info-section">
                    <div className="info-card">
                        <div className="info-icon">
                            <Building2 size={24} />
                        </div>
                        <div className="info-content">
                            <h3>Company</h3>
                            <p>{businessName}</p>
                        </div>
                    </div>

                    <div className="info-card">
                        <div className="info-icon">
                            <Mail size={24} />
                        </div>
                        <div className="info-content">
                            <h3>Email</h3>
                            <a href={`mailto:${businessEmail}`}>{businessEmail}</a>
                        </div>
                    </div>

                    <div className="info-card">
                        <div className="info-icon">
                            <Phone size={24} />
                        </div>
                        <div className="info-content">
                            <h3>Phone</h3>
                            <a href={`tel:${businessPhone.replace(/\D/g, '')}`}>{businessPhone}</a>
                        </div>
                    </div>

                    <div className="info-card">
                        <div className="info-icon">
                            <MapPin size={24} />
                        </div>
                        <div className="info-content">
                            <h3>Location</h3>
                            <p>{businessAddress}</p>
                        </div>
                    </div>

                    <div className="info-card">
                        <div className="info-icon">
                            <Clock size={24} />
                        </div>
                        <div className="info-content">
                            <h3>Business Hours</h3>
                            <p>{businessHours}</p>
                        </div>
                    </div>
                </div>

                {/* Contact Form */}
                <div className="contact-form-section">
                    <div className="form-header">
                        <h2>Send Us a Message</h2>
                        <p>Fill out the form below and we'll respond within 24 hours.</p>
                    </div>

                    <form
                        ref={formRef}
                        onSubmit={handleSubmit}
                        className="contact-form"
                    >
                        <input type="hidden" name="csrf_token" value={csrfToken} />

                        {/* Honeypot field for spam prevention */}
                        <div style={{ display: 'none' }}>
                            <input type="text" name="hp_field" tabIndex={-1} autoComplete="off" />
                        </div>

                        <div className="form-row">
                            {renderInput('firstName', 'First Name', <User size={18} />)}
                            {renderInput('lastName', 'Last Name', <User size={18} />)}
                        </div>

                        <div className="form-row">
                            {renderInput('email', 'Email Address', <Mail size={18} />, 'email')}
                            {renderInput('phone', 'Phone Number', <Phone size={18} />, 'tel', false)}
                        </div>

                        <div className="form-row full-width">
                            <div className={`contact-form-field textarea-field ${errors.message ? 'has-error' : ''} ${focusedField === 'message' ? 'is-focused' : ''} ${formData.message.length > 0 ? 'has-value' : ''}`}>
                                <div className="field-icon textarea-icon">
                                    <MessageSquare size={18} />
                                </div>
                                <textarea
                                    id="message"
                                    name="message"
                                    value={formData.message}
                                    onChange={(e) => handleChange('message', e.target.value)}
                                    onFocus={() => setFocusedField('message')}
                                    onBlur={() => setFocusedField(null)}
                                    required
                                    rows={5}
                                    className="contact-textarea"
                                />
                                <label htmlFor="message" className="floating-label">
                                    Your Message <span className="required-star">*</span>
                                </label>
                                <div className="field-highlight"></div>
                                {errors.message && (
                                    <div className="field-error">
                                        <AlertCircle size={14} />
                                        <span>{errors.message}</span>
                                    </div>
                                )}
                                <div className="char-count">
                                    {formData.message.length} characters
                                </div>
                            </div>
                        </div>

                        {submitStatus === 'error' && (
                            <div className="form-error-banner">
                                <AlertCircle size={20} />
                                <span>Something went wrong. Please try again.</span>
                            </div>
                        )}

                        <div className="form-footer">
                            <div className="security-badge">
                                <Shield size={16} />
                                <span>Your information is secure and encrypted</span>
                            </div>

                            <button
                                type="submit"
                                className={`submit-button ${submitStatus === 'submitting' ? 'is-loading' : ''}`}
                                disabled={submitStatus === 'submitting'}
                            >
                                {submitStatus === 'submitting' ? (
                                    <>
                                        <div className="button-spinner"></div>
                                        <span>Sending...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Send Message</span>
                                        <ArrowRight size={18} />
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}
