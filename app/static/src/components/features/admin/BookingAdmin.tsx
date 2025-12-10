/**
 * BookingAdmin - Unified Booking System Administration
 * 
 * Cohesive dashboard for managing:
 * - Services (with pricing and payment settings)
 * - Staff/Estimators (linked to employee users)
 * - Appointment Types (with forms and resources)
 * - Resources (rooms, equipment for inventory)
 * - Booking Form Builder
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
    Edit2, Trash2, Save, Clock, UserCheck
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

interface BookingAdminProps {
    activeTab?: string
}

// =============================================================================
// Main Component
// =============================================================================

export default function BookingAdmin({ activeTab = 'services' }: BookingAdminProps) {
    const [tab, setTab] = useState(activeTab)

    const tabs = [
        {
            id: 'services',
            label: 'Services',
            icon: <Briefcase size={16} />,
            content: <ServicesPanel />
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
            <div className="booking-admin__header">
                <h1 className="booking-admin__title">Booking System</h1>
                <p className="booking-admin__subtitle">
                    Manage services, staff, appointments, and resources in one place.
                </p>
            </div>

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

function ServicesPanel() {
    const [services, setServices] = useState<Service[]>([])
    const [loading, setLoading] = useState(true)
    const [editingService, setEditingService] = useState<Partial<Service> | null>(null)
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

        try {
            if (editingService.id) {
                await api.put(`/api/admin/booking/services/${editingService.id}`, editingService)
                toast.success('Service updated')
            } else {
                await api.post('/api/admin/booking/services', editingService)
                toast.success('Service created')
            }
            closeModal()
            setEditingService(null)
            fetchServices()
        } catch {
            toast.error('Failed to save service')
        }
    }

    const handleDeleteService = async (id: number) => {
        if (!confirm('Delete this service?')) return
        try {
            await api.delete(`/api/admin/booking/services/${id}`)
            toast.success('Service deleted')
            fetchServices()
        } catch {
            toast.error('Failed to delete service')
        }
    }

    const openCreateModal = () => {
        setEditingService({ name: '', description: '', duration_minutes: 60, price: null, requires_payment: false, icon: 'fa-clipboard-list' })
        openModal()
    }

    const openEditModal = (service: Service) => {
        setEditingService({ ...service })
        openModal()
    }

    if (loading) return <Spinner />

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2>Services</h2>
                <Button onClick={openCreateModal} variant="primary" size="sm">
                    <Plus size={16} /> Add Service
                </Button>
            </div>

            <table className="booking-admin__table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Duration</th>
                        <th>Price</th>
                        <th>Payment</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {services.map(service => (
                        <tr key={service.id}>
                            <td>
                                <strong>{service.name}</strong>
                                {service.description && <br />}
                                <small className="text-muted">{service.description}</small>
                            </td>
                            <td>
                                <Clock size={14} /> {service.duration_minutes} min
                            </td>
                            <td>
                                {service.price ? (
                                    <span>${service.price.toFixed(2)}</span>
                                ) : (
                                    <span className="text-muted">Free</span>
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
                                <Button size="sm" variant="ghost" onClick={() => openEditModal(service)}>
                                    <Edit2 size={14} />
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => handleDeleteService(service.id)}>
                                    <Trash2 size={14} />
                                </Button>
                            </td>
                        </tr>
                    ))}
                    {services.length === 0 && (
                        <tr>
                            <td colSpan={5} className="text-center text-muted">
                                No services configured. Add your first service to get started.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>

            <Modal open={isOpen} onClose={closeModal} title={editingService?.id ? 'Edit Service' : 'New Service'}>
                {editingService && (
                    <div className="booking-admin__form">
                        <div className="booking-admin__form-group">
                            <label>Service Name</label>
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
                        <div className="booking-admin__form-row">
                            <div className="booking-admin__form-group">
                                <label>Duration (minutes)</label>
                                <Input
                                    type="number"
                                    value={editingService.duration_minutes || 60}
                                    onChange={e => setEditingService({ ...editingService, duration_minutes: parseInt(e.target.value) })}
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
                        <div className="booking-admin__form-actions">
                            <Button variant="ghost" onClick={closeModal}>Cancel</Button>
                            <Button variant="primary" onClick={handleSaveService}>
                                <Save size={14} /> Save Service
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>
        </Card>
    )
}

// =============================================================================
// Staff Panel (Estimators from Employees)
// =============================================================================

function StaffPanel() {
    const [staff, setStaff] = useState<Staff[]>([])
    const [employees, setEmployees] = useState<Employee[]>([])
    const [loading, setLoading] = useState(true)
    const { isOpen, openModal, closeModal } = useModal()
    const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null)
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
            toast.success('Staff member added')
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

    // Filter employees not already added as staff
    const availableEmployees = employees.filter(
        emp => !staff.some(s => s.user_id === emp.id)
    )

    if (loading) return <Spinner />

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2>Staff / Estimators</h2>
                <Button onClick={openModal} variant="primary" size="sm" disabled={availableEmployees.length === 0}>
                    <UserCheck size={16} /> Add from Employees
                </Button>
            </div>

            <p className="booking-admin__info">
                Staff members are pulled from your employee database. Add employees here to make them available for booking assignments.
            </p>

            <table className="booking-admin__table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {staff.map(member => (
                        <tr key={member.id}>
                            <td>
                                <strong>{member.user_name || member.name}</strong>
                            </td>
                            <td>{member.user_email || '-'}</td>
                            <td>
                                {member.is_active ? (
                                    <Badge variant="success">Active</Badge>
                                ) : (
                                    <Badge variant="secondary">Inactive</Badge>
                                )}
                            </td>
                            <td>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleToggleActive(member.id, member.is_active)}
                                >
                                    {member.is_active ? 'Deactivate' : 'Activate'}
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => handleRemoveStaff(member.id)}>
                                    <Trash2 size={14} />
                                </Button>
                            </td>
                        </tr>
                    ))}
                    {staff.length === 0 && (
                        <tr>
                            <td colSpan={4} className="text-center text-muted">
                                No staff members configured. Add employees to enable booking assignments.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>

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
                        <p className="booking-admin__warning">
                            All employees are already added as staff members.
                        </p>
                    )}
                    <div className="booking-admin__form-actions">
                        <Button variant="ghost" onClick={closeModal}>Cancel</Button>
                        <Button variant="primary" onClick={handleAddStaff} disabled={!selectedEmployee}>
                            <Plus size={14} /> Add Staff Member
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

    if (loading) return <Spinner />

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2>Appointment Types</h2>
                <Button variant="primary" size="sm" onClick={() => window.location.href = '/admin/scheduling/types/new'}>
                    <Plus size={16} /> Add Type
                </Button>
            </div>

            <table className="booking-admin__table">
                <thead>
                    <tr>
                        <th>Name</th>
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
                            <td>
                                <strong>{type.name}</strong>
                                <br /><small className="text-muted">/book/{type.slug}</small>
                            </td>
                            <td>{type.duration_minutes} min</td>
                            <td>{type.price ? `$${type.price}` : 'Free'}</td>
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
                    {types.length === 0 && (
                        <tr>
                            <td colSpan={6} className="text-center text-muted">
                                No appointment types configured.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
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

    if (loading) return <Spinner />

    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2>Resources</h2>
                <Button variant="primary" size="sm" onClick={() => window.location.href = '/admin/scheduling/resources/new'}>
                    <Plus size={16} /> Add Resource
                </Button>
            </div>

            <p className="booking-admin__info">
                Resources are rooms, equipment, or other items that can be booked alongside appointments.
            </p>

            <table className="booking-admin__table">
                <thead>
                    <tr>
                        <th>Name</th>
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
                    {resources.length === 0 && (
                        <tr>
                            <td colSpan={5} className="text-center text-muted">
                                No resources configured.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </Card>
    )
}

// =============================================================================
// Settings Panel
// =============================================================================

function SettingsPanel() {
    return (
        <Card className="booking-admin__panel">
            <div className="booking-admin__panel-header">
                <h2>Booking Settings</h2>
            </div>

            <div className="booking-admin__settings-grid">
                <Card className="booking-admin__settings-card">
                    <h3>Buffer Times</h3>
                    <p>Configure time buffers between appointments.</p>
                    <Button variant="secondary" size="sm">Configure</Button>
                </Card>

                <Card className="booking-admin__settings-card">
                    <h3>Booking Windows</h3>
                    <p>Set how far in advance customers can book.</p>
                    <Button variant="secondary" size="sm">Configure</Button>
                </Card>

                <Card className="booking-admin__settings-card">
                    <h3>Payment Settings</h3>
                    <p>Stripe configuration and payment policies.</p>
                    <Button variant="secondary" size="sm">Configure</Button>
                </Card>

                <Card className="booking-admin__settings-card">
                    <h3>Notifications</h3>
                    <p>Email and SMS booking notifications.</p>
                    <Button variant="secondary" size="sm">Configure</Button>
                </Card>
            </div>
        </Card>
    )
}
