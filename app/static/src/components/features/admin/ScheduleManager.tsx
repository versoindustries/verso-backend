/**
 * ScheduleManager - Enterprise Employee Scheduling Interface
 * 
 * Complete enterprise-level rewrite following admin-dashboard.css patterns.
 * Uses design tokens from base.css and theme-variables.css for consistency.
 * 
 * Features:
 * - Monthly calendar grid with premium glassmorphism styling
 * - Shift template sidebar with drag-drop support
 * - Employee list with search and filtering
 * - Premium modals for shift creation and template management
 * - Staggered animations and micro-interactions
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import './ScheduleManager.css'

// =============================================================================
// Types
// =============================================================================

interface ShiftTemplate {
    id: number
    name: string
    description: string | null
    start_time: string
    end_time: string
    duration_minutes: number
    color: string
    icon: string | null
    shift_type: string
    is_active: boolean
}

interface Schedule {
    id: number
    user_id: number
    user_name: string
    date: string
    start_time: string
    end_time: string
    duration_minutes: number
    shift_type: string
    status: string
    notes: string | null
    color: string
    location_id: number | null
    location_name: string | null
    template_id: number | null
    template_name: string | null
}

interface Employee {
    id: number
    username: string
    first_name: string | null
    last_name: string | null
    full_name: string
    email: string
    department: string | null
}

interface ScheduleStats {
    total_shifts: number
    total_hours: number
    employees_scheduled: number
    pending_swaps: number
}

interface ToastMessage {
    id: number
    type: 'success' | 'error' | 'info'
    message: string
}

// =============================================================================
// API Helper with error handling
// =============================================================================

const api = {
    async get<T>(url: string): Promise<T> {
        const res = await fetch(url, {
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin'
        })
        if (!res.ok) {
            const error = await res.text()
            throw new Error(error || `HTTP ${res.status}`)
        }
        return res.json()
    },
    async post<T>(url: string, data: unknown): Promise<T> {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        if (!res.ok) {
            const error = await res.text()
            throw new Error(error || `HTTP ${res.status}`)
        }
        return res.json()
    },
    async put<T>(url: string, data: unknown): Promise<T> {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        if (!res.ok) {
            const error = await res.text()
            throw new Error(error || `HTTP ${res.status}`)
        }
        return res.json()
    },
    async delete<T>(url: string): Promise<T> {
        const res = await fetch(url, {
            method: 'DELETE',
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin'
        })
        if (!res.ok) {
            const error = await res.text()
            throw new Error(error || `HTTP ${res.status}`)
        }
        return res.json()
    }
}

// =============================================================================
// Date Utilities
// =============================================================================

const formatDate = (date: Date): string => date.toISOString().split('T')[0]
const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']

const getMonthCalendarDays = (year: number, month: number): Date[] => {
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const days: Date[] = []

    // Pad start with days from previous month
    for (let i = firstDay.getDay() - 1; i >= 0; i--) {
        days.push(new Date(year, month, -i))
    }

    // Add all days of current month
    for (let day = 1; day <= lastDay.getDate(); day++) {
        days.push(new Date(year, month, day))
    }

    // Pad end to complete the last week
    const endPadding = 6 - lastDay.getDay()
    for (let i = 1; i <= endPadding; i++) {
        days.push(new Date(year, month + 1, i))
    }

    return days
}

// =============================================================================
// Toast Notification Component
// =============================================================================

interface ToastContainerProps {
    toasts: ToastMessage[]
    onDismiss: (id: number) => void
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => (
    <div className="toast-container">
        {toasts.map(toast => (
            <div
                key={toast.id}
                className={`toast toast-${toast.type}`}
                onClick={() => onDismiss(toast.id)}
            >
                <i className={`fas ${toast.type === 'success' ? 'fa-check-circle' :
                        toast.type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'
                    }`} />
                <span>{toast.message}</span>
            </div>
        ))}
    </div>
)

// =============================================================================
// Stat Card Component
// =============================================================================

interface StatCardProps {
    value: string | number
    label: string
    icon: string
    variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
    animate?: boolean
    delay?: number
}

const StatCard: React.FC<StatCardProps> = ({
    value,
    label,
    icon,
    variant = 'primary',
    delay = 0
}) => (
    <div
        className={`stat-card stat-card--${variant}`}
        style={{ animationDelay: `${delay}ms` }}
    >
        <div className="stat-card__icon">
            <i className={`fas ${icon}`} />
        </div>
        <div className="stat-card__content">
            <span className="stat-card__value">{value}</span>
            <span className="stat-card__label">{label}</span>
        </div>
        <div className="stat-card__glow" />
    </div>
)

// =============================================================================
// Template Sidebar Component
// =============================================================================

interface TemplateSidebarProps {
    templates: ShiftTemplate[]
    selectedTemplate: ShiftTemplate | null
    onSelectTemplate: (template: ShiftTemplate | null) => void
    onDragStart: (template: ShiftTemplate) => void
    onAddTemplate: () => void
}

const TemplateSidebar: React.FC<TemplateSidebarProps> = ({
    templates,
    selectedTemplate,
    onSelectTemplate,
    onDragStart,
    onAddTemplate
}) => (
    <aside className="sidebar sidebar--templates">
        <div className="sidebar__header">
            <h3 className="sidebar__title">
                <i className="fas fa-clock" />
                Shift Templates
            </h3>
            <button
                className="btn-icon btn-icon--primary"
                onClick={onAddTemplate}
                title="Create Template"
            >
                <i className="fas fa-plus" />
            </button>
        </div>
        <p className="sidebar__hint">
            Select a template, then click on the calendar to add shifts
        </p>
        <div className="sidebar__content">
            {templates.length === 0 ? (
                <div className="empty-state">
                    <i className="fas fa-clock empty-state__icon" />
                    <p>No templates yet</p>
                    <button className="btn btn--outline" onClick={onAddTemplate}>
                        Create First Template
                    </button>
                </div>
            ) : (
                <div className="template-list">
                    {templates.map((template, idx) => (
                        <div
                            key={template.id}
                            className={`template-card ${selectedTemplate?.id === template.id ? 'template-card--selected' : ''}`}
                            style={{
                                '--template-color': template.color,
                                animationDelay: `${idx * 50}ms`
                            } as React.CSSProperties}
                            draggable
                            onClick={() => onSelectTemplate(
                                selectedTemplate?.id === template.id ? null : template
                            )}
                            onDragStart={(e) => {
                                e.dataTransfer.setData('template', JSON.stringify(template))
                                onDragStart(template)
                            }}
                        >
                            <div className="template-card__indicator" />
                            <div className="template-card__content">
                                <span className="template-card__name">{template.name}</span>
                                <span className="template-card__time">
                                    {template.start_time.slice(0, 5)} - {template.end_time.slice(0, 5)}
                                </span>
                                <span className="template-card__duration">
                                    {Math.floor(template.duration_minutes / 60)}h {template.duration_minutes % 60}m
                                </span>
                            </div>
                            <span className="template-card__badge">{template.shift_type}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    </aside>
)

// =============================================================================
// Employee Sidebar Component
// =============================================================================

interface EmployeeSidebarProps {
    employees: Employee[]
    selectedEmployee: number | null
    onSelectEmployee: (id: number | null) => void
    schedulesByUser: Record<number, number>
}

const EmployeeSidebar: React.FC<EmployeeSidebarProps> = ({
    employees,
    selectedEmployee,
    onSelectEmployee,
    schedulesByUser
}) => {
    const [search, setSearch] = useState('')

    const filtered = useMemo(() =>
        employees.filter(e =>
            e.full_name.toLowerCase().includes(search.toLowerCase()) ||
            e.email.toLowerCase().includes(search.toLowerCase())
        ),
        [employees, search]
    )

    return (
        <aside className="sidebar sidebar--employees">
            <div className="sidebar__header">
                <h3 className="sidebar__title">
                    <i className="fas fa-users" />
                    Employees
                </h3>
                <span className="badge badge--primary">{employees.length}</span>
            </div>
            <div className="sidebar__search">
                <i className="fas fa-search" />
                <input
                    type="text"
                    placeholder="Search employees..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>
            <div className="sidebar__content">
                <div
                    className={`employee-item ${selectedEmployee === null ? 'employee-item--selected' : ''}`}
                    onClick={() => onSelectEmployee(null)}
                >
                    <div className="employee-item__avatar employee-item__avatar--all">
                        <i className="fas fa-users" />
                    </div>
                    <div className="employee-item__info">
                        <span className="employee-item__name">All Employees</span>
                    </div>
                </div>
                {filtered.map((employee, idx) => (
                    <div
                        key={employee.id}
                        className={`employee-item ${selectedEmployee === employee.id ? 'employee-item--selected' : ''}`}
                        style={{ animationDelay: `${idx * 30}ms` }}
                        onClick={() => onSelectEmployee(employee.id)}
                    >
                        <div className="employee-item__avatar">
                            {employee.first_name?.[0] || employee.username[0]}
                            {employee.last_name?.[0] || ''}
                        </div>
                        <div className="employee-item__info">
                            <span className="employee-item__name">{employee.full_name}</span>
                            {employee.department && (
                                <span className="employee-item__dept">{employee.department}</span>
                            )}
                        </div>
                        {schedulesByUser[employee.id] > 0 && (
                            <span className="badge badge--gradient">
                                {schedulesByUser[employee.id]}
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </aside>
    )
}

// =============================================================================
// Calendar Day Cell Component
// =============================================================================

interface CalendarDayCellProps {
    date: Date
    isCurrentMonth: boolean
    isToday: boolean
    schedules: Schedule[]
    selectedEmployee: number | null
    selectedTemplate: ShiftTemplate | null
    onAddShift: (date: string) => void
    onEditSchedule: (schedule: Schedule) => void
    onDeleteSchedule: (scheduleId: number) => void
    onDrop: (date: string, template: ShiftTemplate) => void
}

const CalendarDayCell: React.FC<CalendarDayCellProps> = ({
    date,
    isCurrentMonth,
    isToday,
    schedules,
    selectedEmployee,
    selectedTemplate,
    onAddShift,
    onEditSchedule,
    onDeleteSchedule,
    onDrop
}) => {
    const [isDragOver, setIsDragOver] = useState(false)
    const dateStr = formatDate(date)

    const filteredSchedules = selectedEmployee
        ? schedules.filter(s => s.user_id === selectedEmployee)
        : schedules

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(true)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)
        const templateData = e.dataTransfer.getData('template')
        if (templateData) {
            onDrop(dateStr, JSON.parse(templateData))
        }
    }

    const handleCellClick = (e: React.MouseEvent) => {
        if ((e.target as HTMLElement).closest('.shift-block')) return
        onAddShift(dateStr)
    }

    const cellClasses = [
        'calendar-cell',
        !isCurrentMonth && 'calendar-cell--other-month',
        isToday && 'calendar-cell--today',
        isDragOver && 'calendar-cell--drag-over',
        selectedTemplate && 'calendar-cell--template-active'
    ].filter(Boolean).join(' ')

    return (
        <div
            className={cellClasses}
            onClick={handleCellClick}
            onDragOver={handleDragOver}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
        >
            <div className="calendar-cell__header">
                <span className="calendar-cell__day">{date.getDate()}</span>
                {isToday && <span className="calendar-cell__today-badge">Today</span>}
            </div>
            <div className="calendar-cell__shifts">
                {filteredSchedules.slice(0, 3).map(schedule => (
                    <div
                        key={schedule.id}
                        className={`shift-block shift-block--${schedule.status}`}
                        style={{ '--shift-color': schedule.color } as React.CSSProperties}
                        onClick={(e) => {
                            e.stopPropagation()
                            onEditSchedule(schedule)
                        }}
                    >
                        <span className="shift-block__time">{schedule.start_time.slice(0, 5)}</span>
                        <span className="shift-block__name">{schedule.user_name.split(' ')[0]}</span>
                        <button
                            className="shift-block__delete"
                            onClick={(e) => {
                                e.stopPropagation()
                                onDeleteSchedule(schedule.id)
                            }}
                            title="Cancel shift"
                        >
                            <i className="fas fa-times" />
                        </button>
                    </div>
                ))}
                {filteredSchedules.length > 3 && (
                    <div className="calendar-cell__more">
                        +{filteredSchedules.length - 3} more
                    </div>
                )}
            </div>
            <div className="calendar-cell__add-hint">
                <i className="fas fa-plus" />
            </div>
        </div>
    )
}

// =============================================================================
// Modal Components
// =============================================================================

interface ModalProps {
    isOpen: boolean
    onClose: () => void
    title: string
    children: React.ReactNode
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal__header">
                    <h3 className="modal__title">{title}</h3>
                    <button className="modal__close" onClick={onClose}>
                        <i className="fas fa-times" />
                    </button>
                </div>
                <div className="modal__body">
                    {children}
                </div>
            </div>
        </div>
    )
}

// Color options for templates
const COLOR_OPTIONS = [
    '#4169e1', '#10B981', '#8B5CF6', '#F59E0B',
    '#EF4444', '#EC4899', '#06B6D4', '#84CC16',
]

interface TemplateModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (template: Omit<ShiftTemplate, 'id' | 'is_active' | 'duration_minutes'>) => void
    editingTemplate?: ShiftTemplate | null
}

const TemplateModal: React.FC<TemplateModalProps> = ({
    isOpen,
    onClose,
    onSave,
    editingTemplate
}) => {
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [startTime, setStartTime] = useState('09:00')
    const [endTime, setEndTime] = useState('17:00')
    const [color, setColor] = useState('#4169e1')
    const [shiftType, setShiftType] = useState('regular')

    useEffect(() => {
        if (editingTemplate) {
            setName(editingTemplate.name)
            setDescription(editingTemplate.description || '')
            setStartTime(editingTemplate.start_time)
            setEndTime(editingTemplate.end_time)
            setColor(editingTemplate.color)
            setShiftType(editingTemplate.shift_type)
        } else {
            setName('')
            setDescription('')
            setStartTime('09:00')
            setEndTime('17:00')
            setColor('#4169e1')
            setShiftType('regular')
        }
    }, [editingTemplate, isOpen])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        onSave({
            name,
            description: description || null,
            start_time: startTime,
            end_time: endTime,
            color,
            icon: null,
            shift_type: shiftType
        })
    }

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={editingTemplate ? 'Edit Template' : 'Create Shift Template'}
        >
            <form onSubmit={handleSubmit} className="form">
                <div className="form-group">
                    <label className="form-label">Template Name</label>
                    <input
                        type="text"
                        className="form-input"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g., Morning Shift"
                        required
                    />
                </div>
                <div className="form-group">
                    <label className="form-label">Description</label>
                    <input
                        type="text"
                        className="form-input"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Optional description"
                    />
                </div>
                <div className="form-row">
                    <div className="form-group">
                        <label className="form-label">Start Time</label>
                        <input
                            type="time"
                            className="form-input"
                            value={startTime}
                            onChange={(e) => setStartTime(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">End Time</label>
                        <input
                            type="time"
                            className="form-input"
                            value={endTime}
                            onChange={(e) => setEndTime(e.target.value)}
                            required
                        />
                    </div>
                </div>
                <div className="form-group">
                    <label className="form-label">Shift Type</label>
                    <select
                        className="form-select"
                        value={shiftType}
                        onChange={(e) => setShiftType(e.target.value)}
                    >
                        <option value="regular">Regular</option>
                        <option value="overtime">Overtime</option>
                        <option value="on_call">On Call</option>
                        <option value="field">Field</option>
                        <option value="training">Training</option>
                    </select>
                </div>
                <div className="form-group">
                    <label className="form-label">Color</label>
                    <div className="color-picker">
                        {COLOR_OPTIONS.map(c => (
                            <button
                                key={c}
                                type="button"
                                className={`color-picker__option ${color === c ? 'color-picker__option--selected' : ''}`}
                                style={{ background: c }}
                                onClick={() => setColor(c)}
                            />
                        ))}
                    </div>
                </div>
                <div className="form-actions">
                    <button type="button" className="btn btn--secondary" onClick={onClose}>
                        Cancel
                    </button>
                    <button type="submit" className="btn btn--primary">
                        {editingTemplate ? 'Update Template' : 'Create Template'}
                    </button>
                </div>
            </form>
        </Modal>
    )
}

interface AddShiftModalProps {
    isOpen: boolean
    onClose: () => void
    onSave: (shift: {
        user_id: number
        date: string
        start_time: string
        end_time: string
        shift_type: string
        color: string
    }) => void
    date: string
    employees: Employee[]
    preselectedEmployee: number | null
    preselectedTemplate: ShiftTemplate | null
}

const AddShiftModal: React.FC<AddShiftModalProps> = ({
    isOpen,
    onClose,
    onSave,
    date,
    employees,
    preselectedEmployee,
    preselectedTemplate
}) => {
    const [userId, setUserId] = useState<number | ''>('')
    const [startTime, setStartTime] = useState('09:00')
    const [endTime, setEndTime] = useState('17:00')
    const [shiftType, setShiftType] = useState('regular')
    const [color, setColor] = useState('#4169e1')

    useEffect(() => {
        if (isOpen) {
            setUserId(preselectedEmployee || '')
            setStartTime(preselectedTemplate?.start_time || '09:00')
            setEndTime(preselectedTemplate?.end_time || '17:00')
            setShiftType(preselectedTemplate?.shift_type || 'regular')
            setColor(preselectedTemplate?.color || '#4169e1')
        }
    }, [isOpen, preselectedEmployee, preselectedTemplate])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (userId === '') return
        onSave({
            user_id: userId as number,
            date,
            start_time: startTime,
            end_time: endTime,
            shift_type: shiftType,
            color
        })
    }

    const displayDate = date ? new Date(date + 'T12:00:00') : new Date()

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Add Shift - ${displayDate.toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'short',
                day: 'numeric'
            })}`}
        >
            <form onSubmit={handleSubmit} className="form">
                <div className="form-group">
                    <label className="form-label">Employee</label>
                    <select
                        className="form-select"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value ? Number(e.target.value) : '')}
                        required
                    >
                        <option value="">Select an employee...</option>
                        {employees.map(emp => (
                            <option key={emp.id} value={emp.id}>{emp.full_name}</option>
                        ))}
                    </select>
                </div>
                <div className="form-row">
                    <div className="form-group">
                        <label className="form-label">Start Time</label>
                        <input
                            type="time"
                            className="form-input"
                            value={startTime}
                            onChange={(e) => setStartTime(e.target.value)}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">End Time</label>
                        <input
                            type="time"
                            className="form-input"
                            value={endTime}
                            onChange={(e) => setEndTime(e.target.value)}
                            required
                        />
                    </div>
                </div>
                <div className="form-group">
                    <label className="form-label">Shift Type</label>
                    <select
                        className="form-select"
                        value={shiftType}
                        onChange={(e) => setShiftType(e.target.value)}
                    >
                        <option value="regular">Regular</option>
                        <option value="overtime">Overtime</option>
                        <option value="on_call">On Call</option>
                        <option value="field">Field</option>
                        <option value="training">Training</option>
                    </select>
                </div>
                <div className="form-group">
                    <label className="form-label">Color</label>
                    <div className="color-picker">
                        {COLOR_OPTIONS.map(c => (
                            <button
                                key={c}
                                type="button"
                                className={`color-picker__option ${color === c ? 'color-picker__option--selected' : ''}`}
                                style={{ background: c }}
                                onClick={() => setColor(c)}
                            />
                        ))}
                    </div>
                </div>
                <div className="form-actions">
                    <button type="button" className="btn btn--secondary" onClick={onClose}>
                        Cancel
                    </button>
                    <button
                        type="submit"
                        className="btn btn--primary"
                        disabled={userId === ''}
                    >
                        Add Shift
                    </button>
                </div>
            </form>
        </Modal>
    )
}

// Confirmation Modal
interface ConfirmModalProps {
    isOpen: boolean
    onClose: () => void
    onConfirm: () => void
    title: string
    message: string
    confirmText?: string
    variant?: 'danger' | 'primary'
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirm',
    variant = 'danger'
}) => (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
        <div className="confirm-modal">
            <p className="confirm-modal__message">{message}</p>
            <div className="form-actions">
                <button className="btn btn--secondary" onClick={onClose}>
                    Cancel
                </button>
                <button
                    className={`btn btn--${variant}`}
                    onClick={() => { onConfirm(); onClose(); }}
                >
                    {confirmText}
                </button>
            </div>
        </div>
    </Modal>
)

// =============================================================================
// Main Schedule Manager Component
// =============================================================================

export default function ScheduleManager() {
    // Date state
    const [currentDate, setCurrentDate] = useState(() => {
        const now = new Date()
        return new Date(now.getFullYear(), now.getMonth(), 1)
    })

    // Data state
    const [templates, setTemplates] = useState<ShiftTemplate[]>([])
    const [schedules, setSchedules] = useState<Schedule[]>([])
    const [employees, setEmployees] = useState<Employee[]>([])
    const [stats, setStats] = useState<ScheduleStats | null>(null)

    // Selection state
    const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null)
    const [selectedTemplate, setSelectedTemplate] = useState<ShiftTemplate | null>(null)

    // UI state
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [toasts, setToasts] = useState<ToastMessage[]>([])

    // Modal state
    const [templateModalOpen, setTemplateModalOpen] = useState(false)
    const [editingTemplate, setEditingTemplate] = useState<ShiftTemplate | null>(null)
    const [addShiftModalOpen, setAddShiftModalOpen] = useState(false)
    const [addShiftDate, setAddShiftDate] = useState<string>('')
    const [confirmModal, setConfirmModal] = useState<{
        isOpen: boolean
        title: string
        message: string
        onConfirm: () => void
    }>({ isOpen: false, title: '', message: '', onConfirm: () => { } })

    // Derived values
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const calendarDays = useMemo(() => getMonthCalendarDays(year, month), [year, month])

    const startDateStr = useMemo(() => formatDate(calendarDays[0]), [calendarDays])
    const endDateStr = useMemo(() => formatDate(calendarDays[calendarDays.length - 1]), [calendarDays])

    const todayStr = formatDate(new Date())

    const schedulesByUser = useMemo(() => {
        const map: Record<number, number> = {}
        schedules.forEach(s => {
            map[s.user_id] = (map[s.user_id] || 0) + 1
        })
        return map
    }, [schedules])

    // Toast management
    const showToast = useCallback((type: 'success' | 'error' | 'info', message: string) => {
        const id = Date.now()
        setToasts(prev => [...prev, { id, type, message }])
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 4000)
    }, [])

    const dismissToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    // Data fetching
    useEffect(() => {
        let cancelled = false

        const fetchData = async () => {
            setLoading(true)
            setError(null)

            try {
                const [templatesRes, schedulesRes, employeesRes, statsRes] = await Promise.all([
                    api.get<{ templates: ShiftTemplate[] }>('/admin/api/shift-templates'),
                    api.get<{ schedules: Schedule[] }>(`/admin/api/schedules?start_date=${startDateStr}&end_date=${endDateStr}`),
                    api.get<{ employees: Employee[] }>('/admin/api/schedulable-employees'),
                    api.get<{ stats: ScheduleStats }>(`/admin/api/schedules/stats?start_date=${startDateStr}&end_date=${endDateStr}`)
                ])

                if (!cancelled) {
                    setTemplates(templatesRes.templates || [])
                    setSchedules(schedulesRes.schedules || [])
                    setEmployees(employeesRes.employees || [])
                    setStats(statsRes.stats || null)
                    setLoading(false)
                }
            } catch (err) {
                if (!cancelled) {
                    console.error('Failed to load schedule data:', err)
                    setError('Failed to load schedule data. Please try again.')
                    setLoading(false)
                }
            }
        }

        fetchData()
        return () => { cancelled = true }
    }, [startDateStr, endDateStr])

    // Navigation handlers
    const goToPreviousMonth = () => setCurrentDate(new Date(year, month - 1, 1))
    const goToNextMonth = () => setCurrentDate(new Date(year, month + 1, 1))
    const goToToday = () => {
        const now = new Date()
        setCurrentDate(new Date(now.getFullYear(), now.getMonth(), 1))
    }

    // Get schedules for a specific date
    const getSchedulesForDate = useCallback((dateStr: string): Schedule[] => {
        return schedules.filter(s => s.date === dateStr)
    }, [schedules])

    // Shift creation
    const handleAddShiftClick = (dateStr: string) => {
        if (selectedTemplate && selectedEmployee) {
            // Quick add with selected template and employee
            handleCreateShift({
                user_id: selectedEmployee,
                date: dateStr,
                start_time: selectedTemplate.start_time,
                end_time: selectedTemplate.end_time,
                shift_type: selectedTemplate.shift_type,
                color: selectedTemplate.color
            })
        } else {
            setAddShiftDate(dateStr)
            setAddShiftModalOpen(true)
        }
    }

    const handleTemplateDrop = (dateStr: string, template: ShiftTemplate) => {
        if (selectedEmployee) {
            handleCreateShift({
                user_id: selectedEmployee,
                date: dateStr,
                start_time: template.start_time,
                end_time: template.end_time,
                shift_type: template.shift_type,
                color: template.color
            })
        } else {
            setSelectedTemplate(template)
            setAddShiftDate(dateStr)
            setAddShiftModalOpen(true)
        }
    }

    const handleCreateShift = async (shiftData: {
        user_id: number
        date: string
        start_time: string
        end_time: string
        shift_type: string
        color: string
    }) => {
        try {
            const res = await api.post<{ success: boolean; schedule: Schedule; message?: string }>(
                '/admin/api/schedules',
                { ...shiftData, template_id: selectedTemplate?.id }
            )

            if (res.success) {
                setSchedules(prev => [...prev, res.schedule])
                setAddShiftModalOpen(false)
                showToast('success', 'Shift created successfully')
            } else {
                showToast('error', res.message || 'Failed to create shift')
            }
        } catch (err) {
            console.error(err)
            showToast('error', 'Failed to create shift')
        }
    }

    // Shift deletion
    const handleDeleteSchedule = (scheduleId: number) => {
        setConfirmModal({
            isOpen: true,
            title: 'Cancel Shift',
            message: 'Are you sure you want to cancel this shift? This action cannot be undone.',
            onConfirm: async () => {
                try {
                    await api.delete(`/admin/api/schedules/${scheduleId}`)
                    setSchedules(prev => prev.filter(s => s.id !== scheduleId))
                    showToast('success', 'Shift cancelled successfully')
                } catch (err) {
                    console.error(err)
                    showToast('error', 'Failed to cancel shift')
                }
            }
        })
    }

    // Template management
    const handleSaveTemplate = async (
        templateData: Omit<ShiftTemplate, 'id' | 'is_active' | 'duration_minutes'>
    ) => {
        try {
            if (editingTemplate) {
                const res = await api.put<{ success: boolean; template: ShiftTemplate }>(
                    `/admin/api/shift-templates/${editingTemplate.id}`,
                    templateData
                )
                if (res.success) {
                    setTemplates(prev => prev.map(t =>
                        t.id === editingTemplate.id ? res.template : t
                    ))
                    showToast('success', 'Template updated successfully')
                }
            } else {
                const res = await api.post<{ success: boolean; template: ShiftTemplate }>(
                    '/admin/api/shift-templates',
                    templateData
                )
                if (res.success) {
                    setTemplates(prev => [...prev, res.template])
                    showToast('success', 'Template created successfully')
                }
            }
            setTemplateModalOpen(false)
            setEditingTemplate(null)
        } catch (err) {
            console.error(err)
            showToast('error', 'Failed to save template')
        }
    }

    // Edit schedule placeholder
    const handleEditSchedule = (schedule: Schedule) => {
        console.log('Edit schedule:', schedule)
        // TODO: Implement edit modal
    }

    return (
        <div className="schedule-manager">
            {/* Toast Notifications */}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            {/* Header */}
            <header className="schedule-header">
                <div className="schedule-header__title">
                    <h1>
                        <i className="fas fa-calendar-alt" />
                        Employee Schedules
                    </h1>
                </div>

                <nav className="schedule-nav">
                    <button className="btn btn--ghost" onClick={goToPreviousMonth}>
                        <i className="fas fa-chevron-left" />
                    </button>
                    <button className="btn btn--primary" onClick={goToToday}>
                        Today
                    </button>
                    <button className="btn btn--ghost" onClick={goToNextMonth}>
                        <i className="fas fa-chevron-right" />
                    </button>
                    <span className="schedule-nav__month">
                        {MONTH_NAMES[month]} {year}
                    </span>
                </nav>

                {stats && (
                    <div className="schedule-stats">
                        <StatCard
                            value={stats.total_shifts}
                            label="Shifts"
                            icon="fa-calendar-check"
                            variant="primary"
                            delay={100}
                        />
                        <StatCard
                            value={`${stats.total_hours}h`}
                            label="Hours"
                            icon="fa-clock"
                            variant="info"
                            delay={200}
                        />
                        <StatCard
                            value={stats.employees_scheduled}
                            label="Employees"
                            icon="fa-users"
                            variant="success"
                            delay={300}
                        />
                        {stats.pending_swaps > 0 && (
                            <StatCard
                                value={stats.pending_swaps}
                                label="Swap Requests"
                                icon="fa-exchange-alt"
                                variant="warning"
                                delay={400}
                            />
                        )}
                    </div>
                )}
            </header>

            {/* Main Content */}
            <div className="schedule-content">
                {/* Left Sidebar - Templates */}
                <TemplateSidebar
                    templates={templates}
                    selectedTemplate={selectedTemplate}
                    onSelectTemplate={setSelectedTemplate}
                    onDragStart={() => { }}
                    onAddTemplate={() => {
                        setEditingTemplate(null)
                        setTemplateModalOpen(true)
                    }}
                />

                {/* Calendar */}
                <main className="schedule-calendar">
                    {loading ? (
                        <div className="loading-state">
                            <div className="loading-spinner">
                                <i className="fas fa-spinner" />
                            </div>
                            <span>Loading schedules...</span>
                        </div>
                    ) : error ? (
                        <div className="error-state">
                            <i className="fas fa-exclamation-triangle" />
                            <span>{error}</span>
                            <button className="btn btn--primary" onClick={() => window.location.reload()}>
                                Retry
                            </button>
                        </div>
                    ) : (
                        <div className="calendar">
                            <div className="calendar__header">
                                {DAY_NAMES.map(day => (
                                    <div key={day} className="calendar__day-name">{day}</div>
                                ))}
                            </div>
                            <div className="calendar__grid">
                                {calendarDays.map((day, idx) => {
                                    const dateStr = formatDate(day)
                                    return (
                                        <CalendarDayCell
                                            key={idx}
                                            date={day}
                                            isCurrentMonth={day.getMonth() === month}
                                            isToday={dateStr === todayStr}
                                            schedules={getSchedulesForDate(dateStr)}
                                            selectedEmployee={selectedEmployee}
                                            selectedTemplate={selectedTemplate}
                                            onAddShift={handleAddShiftClick}
                                            onEditSchedule={handleEditSchedule}
                                            onDeleteSchedule={handleDeleteSchedule}
                                            onDrop={handleTemplateDrop}
                                        />
                                    )
                                })}
                            </div>
                        </div>
                    )}
                </main>

                {/* Right Sidebar - Employees */}
                <EmployeeSidebar
                    employees={employees}
                    selectedEmployee={selectedEmployee}
                    onSelectEmployee={setSelectedEmployee}
                    schedulesByUser={schedulesByUser}
                />
            </div>

            {/* Modals */}
            <TemplateModal
                isOpen={templateModalOpen}
                onClose={() => {
                    setTemplateModalOpen(false)
                    setEditingTemplate(null)
                }}
                onSave={handleSaveTemplate}
                editingTemplate={editingTemplate}
            />

            <AddShiftModal
                isOpen={addShiftModalOpen}
                onClose={() => {
                    setAddShiftModalOpen(false)
                    setAddShiftDate('')
                }}
                onSave={handleCreateShift}
                date={addShiftDate}
                employees={employees}
                preselectedEmployee={selectedEmployee}
                preselectedTemplate={selectedTemplate}
            />

            <ConfirmModal
                isOpen={confirmModal.isOpen}
                onClose={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
                onConfirm={confirmModal.onConfirm}
                title={confirmModal.title}
                message={confirmModal.message}
                confirmText="Cancel Shift"
                variant="danger"
            />
        </div>
    )
}
