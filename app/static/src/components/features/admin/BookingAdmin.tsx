/**
 * BookingAdmin - Enterprise Booking System Administration Dashboard
 * 
 * Unified dashboard for managing:
 * - Services (with pricing, duration, and cancellation policies)
 * - Staff/Estimators (linked to employee users with availability)
 * - Appointment Types (booking categories)
 * - Resources (rooms, equipment)
 * - Booking Settings (buffer times, windows, notifications)
 */

import { useState, useEffect, useCallback } from 'react'
import { Tabs } from '../../ui/tabs'
import { Card } from '../../ui/card'
import { Button } from '../../ui/button'
import { Input } from '../../ui/input'
import { Badge } from '../../ui/badge'
import { Modal, useModal } from '../../ui/modal'
import { useToast } from '../../ui/toast'
import { Spinner } from '../../ui/spinner'
import {
    Calendar, Users, Briefcase, Package, Settings, Plus,
    Edit2, Trash2, Save, Clock, UserCheck,
    TrendingUp, AlertCircle, Bell, Timer, CreditCard,
    ChevronRight, CheckCircle, XCircle
} from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface Service {
    id: number
    name: string
    description: string
    duration_minutes: number
    price: number | null
    requires_payment: boolean
    icon: string
    display_order: number
    cancellation_policy: 'full_refund' | 'partial_refund' | 'no_refund' | 'deposit_only' | 'manual'
    cancellation_window_hours: number
    refund_percentage: number
    deposit_percentage: number
}

interface Staff {
    id: number
    name: string
    user_id: number | null
    user_email?: string
    user_name?: string
    is_active: boolean
}

interface Employee {
    id: number
    username: string
    email: string
    first_name: string | null
    last_name: string | null
}

interface AppointmentType {
    id: number
    name: string
    slug: string
    duration_minutes: number
    price: number | null
    is_active: boolean
    max_attendees: number
}

interface Resource {
    id: number
    name: string
    resource_type: string
    capacity: number
    is_active: boolean
}

interface DashboardStats {
    totalServices: number
    activeStaff: number
    upcomingAppointments: number
    totalResources: number
}

interface BookingAdminProps {
    activeTab?: string
}

interface Availability {
    id?: number
    day_of_week: number
    day_name: string
    start_time: string | null
    end_time: string | null
}

interface BookingSettings {
    buffer_minutes: number
    min_notice_hours: number
    max_advance_days: number
    require_approval: boolean
    allow_cancellation: boolean
    cancellation_notice_hours: number
}

// =============================================================================
// Main Component
// =============================================================================

export default function BookingAdmin({ activeTab = 'services' }: BookingAdminProps) {
    const [tab, setTab] = useState(activeTab)
    const [stats, setStats] = useState<DashboardStats>({
        totalServices: 0,
        activeStaff: 0,
        upcomingAppointments: 0,
        totalResources: 0
    })
    const [statsLoading, setStatsLoading] = useState(true)

    // Fetch dashboard stats
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [servicesRes, staffRes, resourcesRes] = await Promise.all([
                    api.get('/api/admin/booking/services'),
                    api.get('/api/admin/booking/staff'),
                    api.get('/api/admin/booking/resources')
                ])
                setStats({
                    totalServices: servicesRes.data.length,
                    activeStaff: staffRes.data.filter((s: Staff) => s.is_active).length,
                    upcomingAppointments: 0, // Would need appointments endpoint
                    totalResources: resourcesRes.data.length
                })
            } catch {
                // Silent fail for stats
            } finally {
                setStatsLoading(false)
            }
        }
        fetchStats()
    }, [])

    const tabs = [
        {
            id: 'services',
            label: 'Services',
            icon: <Briefcase size={16} />,
            content: <ServicesPanel onUpdate={() => setStats(s => ({ ...s, totalServices: s.totalServices }))} />
        },
        {
            id: 'staff',
            label: 'Staff',
            icon: <Users size={16} />,
            content: <StaffPanel />
        },
        {
            id: 'types',
            label: 'Appointment Types',
            icon: <Calendar size={16} />,
            content: <AppointmentTypesPanel />
        },
        {
            id: 'resources',
            label: 'Resources',
            icon: <Package size={16} />,
            content: <ResourcesPanel />
        },
        {
            id: 'settings',
            label: 'Settings',
            icon: <Settings size={16} />,
            content: <SettingsPanel />
        }
    ]

    return (
        <div className="booking-admin">
            {/* KPI Stats Header */}
            <div className="booking-admin__stats-grid">
                <div className="booking-admin__stat-card booking-admin__stat-card--services">
                    <div className="booking-admin__stat-icon">
                        <Briefcase size={24} />
                    </div>
                    <div className="booking-admin__stat-content">
                        <span className="booking-admin__stat-value">
                            {statsLoading ? '...' : stats.totalServices}
                        </span>
                        <span className="booking-admin__stat-label">Services</span>
                    </div>
                </div>
                <div className="booking-admin__stat-card booking-admin__stat-card--staff">
                    <div className="booking-admin__stat-icon">
                        <Users size={24} />
                    </div>
                    <div className="booking-admin__stat-content">
                        <span className="booking-admin__stat-value">
                            {statsLoading ? '...' : stats.activeStaff}
                        </span>
                        <span className="booking-admin__stat-label">Active Staff</span>
                    </div>
                </div>
                <div className="booking-admin__stat-card booking-admin__stat-card--appointments">
                    <div className="booking-admin__stat-icon">
                        <TrendingUp size={24} />
                    </div>
                    <div className="booking-admin__stat-content">
                        <span className="booking-admin__stat-value">
                            {statsLoading ? '...' : stats.upcomingAppointments}
                        </span>
                        <span className="booking-admin__stat-label">Upcoming</span>
                    </div>
                </div>
                <div className="booking-admin__stat-card booking-admin__stat-card--resources">
                    <div className="booking-admin__stat-icon">
                        <Package size={24} />
                    </div>
                    <div className="booking-admin__stat-content">
                        <span className="booking-admin__stat-value">
                            {statsLoading ? '...' : stats.totalResources}
                        </span>
                        <span className="booking-admin__stat-label">Resources</span>
                    </div>
                </div>
            </div>

            {/* Header */}
            <div className="booking-admin__header">
                <h1 className="booking-admin__title">Booking System</h1>
                <p className="booking-admin__subtitle">
                    Manage services, staff, appointments, and resources in one place.
                </p>
            </div>

            {/* Tabs */}
            <Tabs
                tabs={tabs}
                activeTab={tab}
                onTabChange={setTab}
                variant="underline"
                className="booking-admin__tabs"
            />
        </div>
    )
}

// =============================================================================
// Services Panel
// =============================================================================

interface ServicesPanelProps {
    onUpdate?: () => void
}

function ServicesPanel({ onUpdate }: ServicesPanelProps) {
    const [services, setServices] = useState<Service[]>([])
    const [loading, setLoading] = useState(true)
    const [editingService, setEditingService] = useState<Partial<Service> | null>(null)
    const [saving, setSaving] = useState(false)
    const { isOpen, openModal, closeModal } = useModal()
    const toast = useToast()

    const fetchServices = useCallback(async () => {
        try {
            const response = await api.get('/api/admin/booking/services')
            setServices(response.data)
        } catch {
            toast.error('Failed to load services')
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchServices() }, [fetchServices])

    const handleSaveService = async () => {
        if (!editingService) return
        if (!editingService.name?.trim()) {
            toast.error('Service name is required')
            return
        }

        setSaving(true)
        try {
            if (editingService.id) {
                await api.put(`/api/admin/booking/services/${editingService.id}`, editingService)
                toast.success('Service updated successfully')
            } else {
                await api.post('/api/admin/booking/services', editingService)
                toast.success('Service created successfully')
            }
            closeModal()
            setEditingService(null)
            fetchServices()
            onUpdate?.()
        } catch {
            toast.error('Failed to save service')
        } finally {
            setSaving(false)
        }
    }

    const handleDeleteService = async (id: number) => {
        if (!confirm('Are you sure you want to delete this service? This action cannot be undone.')) return
        try {
            await api.delete(`/api/admin/booking/services/${id}`)
            toast.success('Service deleted')
            fetchServices()
            onUpdate?.()
        } catch {
            toast.error('Failed to delete service')
        }
    }

    const openCreateModal = () => {
        setEditingService({
            name: '',
            description: '',
            duration_minutes: 60,
            price: null,
            requires_payment: false,
            icon: 'fa-clipboard-list',
            cancellation_policy: 'manual',
            cancellation_window_hours: 24,
            refund_percentage: 100,
            deposit_percentage: 0
        })
        openModal()
    }

    const openEditModal = (service: Service) => {
        setEditingService({ ...service })
        openModal()
    }

    if (loading) return <div className="booking-admin__loading"><Spinner /></div>

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2><Briefcase size={18} /> Services</h2>
                <Button onClick={openCreateModal} variant="primary" size="sm">
                    <Plus size={16} /> Add Service
                </Button>
            </div>

            <div className="booking-admin__panel-body">
                {services.length === 0 ? (
                    <div className="booking-admin__empty-state">
                        <Briefcase size={48} strokeWidth={1} />
                        <h3>No Services Yet</h3>
                        <p>Create your first service to start accepting bookings.</p>
                        <Button onClick={openCreateModal} variant="primary">
                            <Plus size={16} /> Create Service
                        </Button>
                    </div>
                ) : (
                    <table className="booking-admin__table">
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Duration</th>
                                <th>Price</th>
                                <th>Payment</th>
                                <th>Policy</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {services.map(service => (
                                <tr key={service.id}>
                                    <td>
                                        <div className="booking-admin__service-cell">
                                            <strong>{service.name}</strong>
                                            {service.description && (
                                                <small>{service.description}</small>
                                            )}
                                        </div>
                                    </td>
                                    <td>
                                        <div className="booking-admin__duration">
                                            <Clock size={14} />
                                            <span>{service.duration_minutes} min</span>
                                        </div>
                                    </td>
                                    <td>
                                        {service.price ? (
                                            <span className="booking-admin__price">${service.price.toFixed(2)}</span>
                                        ) : (
                                            <Badge variant="secondary">Free</Badge>
                                        )}
                                    </td>
                                    <td>
                                        {service.requires_payment ? (
                                            <Badge variant="warning">Required</Badge>
                                        ) : (
                                            <Badge variant="secondary">Optional</Badge>
                                        )}
                                    </td>
                                    <td>
                                        <Badge variant="info">{(service.cancellation_policy || 'manual').replace('_', ' ')}</Badge>
                                    </td>
                                    <td>
                                        <div className="booking-admin__actions">
                                            <Button size="sm" variant="ghost" onClick={() => openEditModal(service)} title="Edit">
                                                <Edit2 size={14} />
                                            </Button>
                                            <Button size="sm" variant="ghost" onClick={() => handleDeleteService(service.id)} title="Delete">
                                                <Trash2 size={14} />
                                            </Button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            <Modal open={isOpen} onClose={closeModal} title={editingService?.id ? 'Edit Service' : 'New Service'}>
                {editingService && (
                    <div className="booking-admin__form">
                        <div className="booking-admin__form-section">
                            <h4>Basic Information</h4>
                            <div className="booking-admin__form-group">
                                <label>Service Name *</label>
                                <Input
                                    value={editingService.name || ''}
                                    onChange={e => setEditingService({ ...editingService, name: e.target.value })}
                                    placeholder="e.g. Initial Consultation"
                                />
                            </div>
                            <div className="booking-admin__form-group">
                                <label>Description</label>
                                <Input
                                    value={editingService.description || ''}
                                    onChange={e => setEditingService({ ...editingService, description: e.target.value })}
                                    placeholder="Brief description of this service"
                                />
                            </div>
                        </div>

                        <div className="booking-admin__form-section">
                            <h4>Duration & Pricing</h4>
                            <div className="booking-admin__form-row">
                                <div className="booking-admin__form-group">
                                    <label>Duration (minutes)</label>
                                    <Input
                                        type="number"
                                        value={editingService.duration_minutes || 60}
                                        onChange={e => setEditingService({ ...editingService, duration_minutes: parseInt(e.target.value) })}
                                        min={5}
                                        step={5}
                                    />
                                </div>
                                <div className="booking-admin__form-group">
                                    <label>Price ($)</label>
                                    <Input
                                        type="number"
                                        step="0.01"
                                        value={editingService.price || ''}
                                        onChange={e => setEditingService({ ...editingService, price: parseFloat(e.target.value) || null })}
                                        placeholder="0.00 for free"
                                    />
                                </div>
                            </div>
                            <div className="booking-admin__form-group">
                                <label className="booking-admin__checkbox">
                                    <input
                                        type="checkbox"
                                        checked={editingService.requires_payment || false}
                                        onChange={e => setEditingService({ ...editingService, requires_payment: e.target.checked })}
                                    />
                                    <span>Require upfront payment via Stripe</span>
                                </label>
                            </div>
                        </div>

                        {editingService.requires_payment && (
                            <div className="booking-admin__form-section">
                                <h4>Cancellation Policy</h4>
                                <div className="booking-admin__form-group">
                                    <label>Policy Type</label>
                                    <select
                                        className="booking-admin__select"
                                        value={editingService.cancellation_policy || 'manual'}
                                        onChange={e => setEditingService({ ...editingService, cancellation_policy: e.target.value as Service['cancellation_policy'] })}
                                    >
                                        <option value="manual">Manual Review (admin handles refunds)</option>
                                        <option value="full_refund">Full Refund (automatic)</option>
                                        <option value="partial_refund">Partial Refund (based on timing)</option>
                                        <option value="no_refund">No Refund</option>
                                        <option value="deposit_only">Non-refundable Deposit</option>
                                    </select>
                                </div>

                                {editingService.cancellation_policy === 'partial_refund' && (
                                    <div className="booking-admin__form-row">
                                        <div className="booking-admin__form-group">
                                            <label>Free Cancellation Window (hours)</label>
                                            <Input
                                                type="number"
                                                value={editingService.cancellation_window_hours || 24}
                                                onChange={e => setEditingService({ ...editingService, cancellation_window_hours: parseInt(e.target.value) || 24 })}
                                            />
                                            <small>Full refund if cancelled this many hours before</small>
                                        </div>
                                        <div className="booking-admin__form-group">
                                            <label>Late Cancellation Refund %</label>
                                            <Input
                                                type="number"
                                                min="0"
                                                max="100"
                                                value={editingService.refund_percentage || 50}
                                                onChange={e => setEditingService({ ...editingService, refund_percentage: parseInt(e.target.value) || 0 })}
                                            />
                                        </div>
                                    </div>
                                )}

                                {editingService.cancellation_policy === 'deposit_only' && (
                                    <div className="booking-admin__form-group">
                                        <label>Non-refundable Deposit %</label>
                                        <Input
                                            type="number"
                                            min="0"
                                            max="100"
                                            value={editingService.deposit_percentage || 20}
                                            onChange={e => setEditingService({ ...editingService, deposit_percentage: parseInt(e.target.value) || 20 })}
                                        />
                                        <small>This percentage is kept if customer cancels</small>
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="booking-admin__form-actions">
                            <Button variant="ghost" onClick={closeModal}>Cancel</Button>
                            <Button variant="primary" onClick={handleSaveService} disabled={saving}>
                                <Save size={14} /> {saving ? 'Saving...' : 'Save Service'}
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>
        </Card>
    )
}

// =============================================================================
// Staff Panel
// =============================================================================

function StaffPanel() {
    const [staff, setStaff] = useState<Staff[]>([])
    const [employees, setEmployees] = useState<Employee[]>([])
    const [loading, setLoading] = useState(true)
    const { isOpen, openModal, closeModal } = useModal()
    const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null)
    const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null)
    const [availability, setAvailability] = useState<Availability[]>([])
    const [availabilityModalOpen, setAvailabilityModalOpen] = useState(false)
    const [savingAvailability, setSavingAvailability] = useState(false)
    const toast = useToast()

    const fetchData = useCallback(async () => {
        try {
            const [staffRes, empRes] = await Promise.all([
                api.get('/api/admin/booking/staff'),
                api.get('/api/admin/booking/employees')
            ])
            setStaff(staffRes.data)
            setEmployees(empRes.data)
        } catch {
            toast.error('Failed to load staff data')
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchData() }, [fetchData])

    const handleAddStaff = async () => {
        if (!selectedEmployee) return
        try {
            await api.post('/api/admin/booking/staff', { user_id: selectedEmployee })
            toast.success('Staff member added with default Mon-Fri availability')
            closeModal()
            setSelectedEmployee(null)
            fetchData()
        } catch {
            toast.error('Failed to add staff member')
        }
    }

    const handleToggleActive = async (staffId: number, isActive: boolean) => {
        try {
            await api.patch(`/api/admin/booking/staff/${staffId}`, { is_active: !isActive })
            toast.success(`Staff member ${isActive ? 'deactivated' : 'activated'}`)
            fetchData()
        } catch {
            toast.error('Failed to update status')
        }
    }

    const handleRemoveStaff = async (staffId: number) => {
        if (!confirm('Remove this staff member from booking availability?')) return
        try {
            await api.delete(`/api/admin/booking/staff/${staffId}`)
            toast.success('Staff member removed')
            fetchData()
        } catch {
            toast.error('Failed to remove staff')
        }
    }

    const openAvailabilityModal = async (staffId: number) => {
        setSelectedStaffId(staffId)
        try {
            const res = await api.get(`/api/admin/booking/availability/${staffId}`)
            const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            const fullAvailability = days.map((day, idx) => {
                const existing = res.data.availability.find((a: Availability) => a.day_of_week === idx)
                return existing || { day_of_week: idx, day_name: day, start_time: null, end_time: null }
            })
            setAvailability(fullAvailability)
            setAvailabilityModalOpen(true)
        } catch {
            toast.error('Failed to load availability')
        }
    }

    const handleSaveAvailability = async () => {
        if (!selectedStaffId) return
        setSavingAvailability(true)
        try {
            const validAvailability = availability.filter(a => a.start_time && a.end_time)
            await api.post(`/api/admin/booking/availability/${selectedStaffId}`, {
                availability: validAvailability
            })
            toast.success('Availability updated')
            setAvailabilityModalOpen(false)
        } catch {
            toast.error('Failed to save availability')
        } finally {
            setSavingAvailability(false)
        }
    }

    const handleSeedAvailability = async (staffId: number) => {
        try {
            await api.post(`/api/admin/booking/availability/${staffId}/seed`)
            toast.success('Default availability seeded (Mon-Fri 9am-5pm)')
        } catch (err: unknown) {
            const error = err as { response?: { data?: { error?: string } } }
            toast.error(error.response?.data?.error || 'Failed to seed availability')
        }
    }

    const updateDayAvailability = (dayIndex: number, field: 'start_time' | 'end_time', value: string) => {
        setAvailability(prev => prev.map(a =>
            a.day_of_week === dayIndex ? { ...a, [field]: value || null } : a
        ))
    }

    const toggleDayAvailability = (dayIndex: number, enabled: boolean) => {
        setAvailability(prev => prev.map(a =>
            a.day_of_week === dayIndex
                ? { ...a, start_time: enabled ? '09:00' : null, end_time: enabled ? '17:00' : null }
                : a
        ))
    }

    const availableEmployees = employees.filter(
        emp => !staff.some(s => s.user_id === emp.id)
    )

    if (loading) return <div className="booking-admin__loading"><Spinner /></div>

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2><Users size={18} /> Staff / Estimators</h2>
                <Button onClick={openModal} variant="primary" size="sm" disabled={availableEmployees.length === 0}>
                    <UserCheck size={16} /> Add from Employees
                </Button>
            </div>

            <p className="booking-admin__info">
                Staff members are pulled from your employee database. Add employees here to make them available for booking assignments.
            </p>

            <div className="booking-admin__panel-body">
                {staff.length === 0 ? (
                    <div className="booking-admin__empty-state">
                        <Users size={48} strokeWidth={1} />
                        <h3>No Staff Members</h3>
                        <p>Add employees to enable booking assignments.</p>
                        <Button onClick={openModal} variant="primary" disabled={availableEmployees.length === 0}>
                            <UserCheck size={16} /> Add Staff Member
                        </Button>
                    </div>
                ) : (
                    <table className="booking-admin__table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Availability</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {staff.map(member => (
                                <tr key={member.id}>
                                    <td><strong>{member.user_name || member.name}</strong></td>
                                    <td>{member.user_email || '-'}</td>
                                    <td>
                                        {member.is_active ? (
                                            <Badge variant="success"><CheckCircle size={12} /> Active</Badge>
                                        ) : (
                                            <Badge variant="secondary"><XCircle size={12} /> Inactive</Badge>
                                        )}
                                    </td>
                                    <td>
                                        <Button
                                            size="sm"
                                            variant="secondary"
                                            onClick={() => openAvailabilityModal(member.id)}
                                        >
                                            <Clock size={14} /> Manage Hours
                                        </Button>
                                    </td>
                                    <td>
                                        <div className="booking-admin__actions">
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => handleToggleActive(member.id, member.is_active)}
                                                title={member.is_active ? 'Deactivate' : 'Activate'}
                                            >
                                                {member.is_active ? <XCircle size={14} /> : <CheckCircle size={14} />}
                                            </Button>
                                            <Button size="sm" variant="ghost" onClick={() => handleRemoveStaff(member.id)} title="Remove">
                                                <Trash2 size={14} />
                                            </Button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Add Staff Modal */}
            <Modal open={isOpen} onClose={closeModal} title="Add Staff Member">
                <div className="booking-admin__form">
                    <div className="booking-admin__form-group">
                        <label>Select Employee</label>
                        <select
                            className="booking-admin__select"
                            value={selectedEmployee || ''}
                            onChange={e => setSelectedEmployee(parseInt(e.target.value))}
                        >
                            <option value="">-- Select an employee --</option>
                            {availableEmployees.map(emp => (
                                <option key={emp.id} value={emp.id}>
                                    {emp.first_name || emp.username} {emp.last_name || ''} ({emp.email})
                                </option>
                            ))}
                        </select>
                    </div>
                    {availableEmployees.length === 0 && (
                        <div className="booking-admin__warning">
                            <AlertCircle size={16} />
                            <span>All employees are already added as staff members.</span>
                        </div>
                    )}
                    <p className="booking-admin__info">
                        New staff members will be auto-assigned Mon-Fri 9am-5pm availability.
                    </p>
                    <div className="booking-admin__form-actions">
                        <Button variant="ghost" onClick={closeModal}>Cancel</Button>
                        <Button variant="primary" onClick={handleAddStaff} disabled={!selectedEmployee}>
                            <Plus size={14} /> Add Staff Member
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Availability Modal */}
            <Modal
                open={availabilityModalOpen}
                onClose={() => setAvailabilityModalOpen(false)}
                title="Manage Weekly Availability"
            >
                <div className="booking-admin__form">
                    <p className="booking-admin__info">
                        Set the working hours for each day. Leave unchecked to mark as unavailable.
                    </p>

                    <div className="booking-admin__availability-grid">
                        {availability.map(day => (
                            <div key={day.day_of_week} className={`booking-admin__availability-row ${day.start_time ? 'booking-admin__availability-row--active' : ''}`}>
                                <label className="booking-admin__checkbox">
                                    <input
                                        type="checkbox"
                                        checked={!!(day.start_time && day.end_time)}
                                        onChange={e => toggleDayAvailability(day.day_of_week, e.target.checked)}
                                    />
                                    <span className="booking-admin__day-label">{day.day_name}</span>
                                </label>
                                {day.start_time && day.end_time ? (
                                    <div className="booking-admin__time-inputs">
                                        <Input
                                            type="time"
                                            value={day.start_time}
                                            onChange={e => updateDayAvailability(day.day_of_week, 'start_time', e.target.value)}
                                        />
                                        <span className="booking-admin__time-separator">to</span>
                                        <Input
                                            type="time"
                                            value={day.end_time}
                                            onChange={e => updateDayAvailability(day.day_of_week, 'end_time', e.target.value)}
                                        />
                                    </div>
                                ) : (
                                    <span className="booking-admin__unavailable">Not available</span>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="booking-admin__form-row" style={{ marginTop: '1rem' }}>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => selectedStaffId && handleSeedAvailability(selectedStaffId)}
                        >
                            Reset to Default (Mon-Fri 9-5)
                        </Button>
                    </div>

                    <div className="booking-admin__form-actions">
                        <Button variant="ghost" onClick={() => setAvailabilityModalOpen(false)}>Cancel</Button>
                        <Button variant="primary" onClick={handleSaveAvailability} disabled={savingAvailability}>
                            <Save size={14} /> {savingAvailability ? 'Saving...' : 'Save Availability'}
                        </Button>
                    </div>
                </div>
            </Modal>
        </Card>
    )
}

// =============================================================================
// Appointment Types Panel
// =============================================================================

function AppointmentTypesPanel() {
    const [types, setTypes] = useState<AppointmentType[]>([])
    const [loading, setLoading] = useState(true)
    const toast = useToast()

    const fetchTypes = useCallback(async () => {
        try {
            const response = await api.get('/api/admin/booking/appointment-types')
            setTypes(response.data)
        } catch {
            toast.error('Failed to load appointment types')
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchTypes() }, [fetchTypes])

    if (loading) return <div className="booking-admin__loading"><Spinner /></div>

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2><Calendar size={18} /> Appointment Types</h2>
                <Button variant="primary" size="sm" onClick={() => window.location.href = '/admin/scheduling/types/new'}>
                    <Plus size={16} /> Add Type
                </Button>
            </div>

            <div className="booking-admin__panel-body">
                {types.length === 0 ? (
                    <div className="booking-admin__empty-state">
                        <Calendar size={48} strokeWidth={1} />
                        <h3>No Appointment Types</h3>
                        <p>Create appointment types to define what customers can book.</p>
                        <Button variant="primary" onClick={() => window.location.href = '/admin/scheduling/types/new'}>
                            <Plus size={16} /> Create Type
                        </Button>
                    </div>
                ) : (
                    <table className="booking-admin__table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Booking URL</th>
                                <th>Duration</th>
                                <th>Price</th>
                                <th>Capacity</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {types.map(type => (
                                <tr key={type.id}>
                                    <td><strong>{type.name}</strong></td>
                                    <td>
                                        <code className="booking-admin__url">/book/{type.slug}</code>
                                    </td>
                                    <td>
                                        <div className="booking-admin__duration">
                                            <Clock size={14} />
                                            <span>{type.duration_minutes} min</span>
                                        </div>
                                    </td>
                                    <td>
                                        {type.price ? (
                                            <span className="booking-admin__price">${type.price}</span>
                                        ) : (
                                            <Badge variant="secondary">Free</Badge>
                                        )}
                                    </td>
                                    <td>{type.max_attendees}</td>
                                    <td>
                                        {type.is_active ? (
                                            <Badge variant="success">Active</Badge>
                                        ) : (
                                            <Badge variant="secondary">Inactive</Badge>
                                        )}
                                    </td>
                                    <td>
                                        <Button size="sm" variant="ghost" onClick={() => window.location.href = `/admin/scheduling/types/${type.id}/edit`}>
                                            <Edit2 size={14} />
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </Card>
    )
}

// =============================================================================
// Resources Panel
// =============================================================================

function ResourcesPanel() {
    const [resources, setResources] = useState<Resource[]>([])
    const [loading, setLoading] = useState(true)
    const toast = useToast()

    const fetchResources = useCallback(async () => {
        try {
            const response = await api.get('/api/admin/booking/resources')
            setResources(response.data)
        } catch {
            toast.error('Failed to load resources')
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchResources() }, [fetchResources])

    if (loading) return <div className="booking-admin__loading"><Spinner /></div>

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2><Package size={18} /> Resources</h2>
                <Button variant="primary" size="sm" onClick={() => window.location.href = '/admin/scheduling/resources/new'}>
                    <Plus size={16} /> Add Resource
                </Button>
            </div>

            <p className="booking-admin__info">
                Resources are rooms, equipment, or other items that can be booked alongside appointments.
            </p>

            <div className="booking-admin__panel-body">
                {resources.length === 0 ? (
                    <div className="booking-admin__empty-state">
                        <Package size={48} strokeWidth={1} />
                        <h3>No Resources</h3>
                        <p>Add resources like rooms or equipment for booking.</p>
                        <Button variant="primary" onClick={() => window.location.href = '/admin/scheduling/resources/new'}>
                            <Plus size={16} /> Add Resource
                        </Button>
                    </div>
                ) : (
                    <table className="booking-admin__table">
                        <thead>
                            <tr>
                                <th>Resource</th>
                                <th>Type</th>
                                <th>Capacity</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {resources.map(resource => (
                                <tr key={resource.id}>
                                    <td><strong>{resource.name}</strong></td>
                                    <td><Badge variant="info">{resource.resource_type}</Badge></td>
                                    <td>{resource.capacity}</td>
                                    <td>
                                        {resource.is_active ? (
                                            <Badge variant="success">Active</Badge>
                                        ) : (
                                            <Badge variant="secondary">Inactive</Badge>
                                        )}
                                    </td>
                                    <td>
                                        <Button size="sm" variant="ghost" onClick={() => window.location.href = `/admin/scheduling/resources/${resource.id}/edit`}>
                                            <Edit2 size={14} />
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </Card>
    )
}

// =============================================================================
// Settings Panel
// =============================================================================

function SettingsPanel() {
    const [settings, setSettings] = useState<BookingSettings>({
        buffer_minutes: 15,
        min_notice_hours: 2,
        max_advance_days: 30,
        require_approval: false,
        allow_cancellation: true,
        cancellation_notice_hours: 24
    })
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [activeSettingModal, setActiveSettingModal] = useState<string | null>(null)
    const toast = useToast()

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const response = await api.get('/api/admin/booking/settings')
                setSettings(response.data)
            } catch {
                // Use defaults if fetch fails
            } finally {
                setLoading(false)
            }
        }
        fetchSettings()
    }, [])

    const handleSaveSettings = async () => {
        setSaving(true)
        try {
            await api.put('/api/admin/booking/settings', settings)
            toast.success('Settings saved successfully')
            setActiveSettingModal(null)
        } catch {
            toast.error('Failed to save settings')
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <div className="booking-admin__loading"><Spinner /></div>

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2><Settings size={18} /> Booking Settings</h2>
            </div>

            <div className="booking-admin__settings-grid">
                {/* Buffer Times */}
                <div className="booking-admin__settings-card" onClick={() => setActiveSettingModal('buffer')}>
                    <div className="booking-admin__settings-icon">
                        <Timer size={24} />
                    </div>
                    <div className="booking-admin__settings-content">
                        <h3>Buffer Times</h3>
                        <p>Configure time buffers between appointments.</p>
                        <span className="booking-admin__settings-value">{settings.buffer_minutes} min buffer</span>
                    </div>
                    <ChevronRight size={20} className="booking-admin__settings-arrow" />
                </div>

                {/* Booking Windows */}
                <div className="booking-admin__settings-card" onClick={() => setActiveSettingModal('windows')}>
                    <div className="booking-admin__settings-icon">
                        <Calendar size={24} />
                    </div>
                    <div className="booking-admin__settings-content">
                        <h3>Booking Windows</h3>
                        <p>Set how far in advance customers can book.</p>
                        <span className="booking-admin__settings-value">{settings.min_notice_hours}h notice, {settings.max_advance_days}d max</span>
                    </div>
                    <ChevronRight size={20} className="booking-admin__settings-arrow" />
                </div>

                {/* Payment Settings */}
                <div className="booking-admin__settings-card" onClick={() => window.location.href = '/admin/stripe-settings'}>
                    <div className="booking-admin__settings-icon">
                        <CreditCard size={24} />
                    </div>
                    <div className="booking-admin__settings-content">
                        <h3>Payment Settings</h3>
                        <p>Stripe configuration and payment policies.</p>
                        <span className="booking-admin__settings-value">Configure Stripe</span>
                    </div>
                    <ChevronRight size={20} className="booking-admin__settings-arrow" />
                </div>

                {/* Notifications */}
                <div className="booking-admin__settings-card" onClick={() => setActiveSettingModal('notifications')}>
                    <div className="booking-admin__settings-icon">
                        <Bell size={24} />
                    </div>
                    <div className="booking-admin__settings-content">
                        <h3>Notifications</h3>
                        <p>Email and SMS booking notifications.</p>
                        <span className="booking-admin__settings-value">Cancellation: {settings.cancellation_notice_hours}h notice</span>
                    </div>
                    <ChevronRight size={20} className="booking-admin__settings-arrow" />
                </div>
            </div>

            {/* Buffer Times Modal */}
            <Modal
                open={activeSettingModal === 'buffer'}
                onClose={() => setActiveSettingModal(null)}
                title="Buffer Times"
            >
                <div className="booking-admin__form">
                    <div className="booking-admin__form-group">
                        <label>Buffer between appointments (minutes)</label>
                        <Input
                            type="number"
                            value={settings.buffer_minutes}
                            onChange={e => setSettings({ ...settings, buffer_minutes: parseInt(e.target.value) || 0 })}
                            min={0}
                            step={5}
                        />
                        <small>Time gap required between consecutive appointments</small>
                    </div>
                    <div className="booking-admin__form-actions">
                        <Button variant="ghost" onClick={() => setActiveSettingModal(null)}>Cancel</Button>
                        <Button variant="primary" onClick={handleSaveSettings} disabled={saving}>
                            <Save size={14} /> {saving ? 'Saving...' : 'Save'}
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Booking Windows Modal */}
            <Modal
                open={activeSettingModal === 'windows'}
                onClose={() => setActiveSettingModal(null)}
                title="Booking Windows"
            >
                <div className="booking-admin__form">
                    <div className="booking-admin__form-group">
                        <label>Minimum notice (hours)</label>
                        <Input
                            type="number"
                            value={settings.min_notice_hours}
                            onChange={e => setSettings({ ...settings, min_notice_hours: parseInt(e.target.value) || 0 })}
                            min={0}
                        />
                        <small>How much advance notice is required for bookings</small>
                    </div>
                    <div className="booking-admin__form-group">
                        <label>Maximum advance booking (days)</label>
                        <Input
                            type="number"
                            value={settings.max_advance_days}
                            onChange={e => setSettings({ ...settings, max_advance_days: parseInt(e.target.value) || 30 })}
                            min={1}
                        />
                        <small>How far in the future customers can book</small>
                    </div>
                    <div className="booking-admin__form-group">
                        <label className="booking-admin__checkbox">
                            <input
                                type="checkbox"
                                checked={settings.require_approval}
                                onChange={e => setSettings({ ...settings, require_approval: e.target.checked })}
                            />
                            <span>Require admin approval for all bookings</span>
                        </label>
                    </div>
                    <div className="booking-admin__form-actions">
                        <Button variant="ghost" onClick={() => setActiveSettingModal(null)}>Cancel</Button>
                        <Button variant="primary" onClick={handleSaveSettings} disabled={saving}>
                            <Save size={14} /> {saving ? 'Saving...' : 'Save'}
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Notifications Modal */}
            <Modal
                open={activeSettingModal === 'notifications'}
                onClose={() => setActiveSettingModal(null)}
                title="Notification Settings"
            >
                <div className="booking-admin__form">
                    <div className="booking-admin__form-group">
                        <label className="booking-admin__checkbox">
                            <input
                                type="checkbox"
                                checked={settings.allow_cancellation}
                                onChange={e => setSettings({ ...settings, allow_cancellation: e.target.checked })}
                            />
                            <span>Allow customers to cancel appointments</span>
                        </label>
                    </div>
                    <div className="booking-admin__form-group">
                        <label>Cancellation notice required (hours)</label>
                        <Input
                            type="number"
                            value={settings.cancellation_notice_hours}
                            onChange={e => setSettings({ ...settings, cancellation_notice_hours: parseInt(e.target.value) || 24 })}
                            min={0}
                        />
                        <small>Minimum hours before appointment that cancellation is allowed</small>
                    </div>
                    <div className="booking-admin__form-actions">
                        <Button variant="ghost" onClick={() => setActiveSettingModal(null)}>Cancel</Button>
                        <Button variant="primary" onClick={handleSaveSettings} disabled={saving}>
                            <Save size={14} /> {saving ? 'Saving...' : 'Save'}
                        </Button>
                    </div>
                </div>
            </Modal>
        </Card>
    )
}
