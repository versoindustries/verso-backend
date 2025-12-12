/**
 * UnifiedAutomationDashboard - Enterprise Workflow Automation
 * 
 * A comprehensive React component for managing automation workflows
 * with glassmorphism design matching the admin dashboard theme.
 */

import React, { useState, useEffect, useCallback } from 'react'
import { useToast } from '../../ui/toast'
import { Sheet } from '../../ui/sheet'
import api from '../../../api'
import './automation-dashboard.css'

// =============================================================================
// Types
// =============================================================================

interface TriggerEvent {
    value: string
    label: string
    description: string
}

interface ActionTypeField {
    name: string
    label: string
    type: 'text' | 'textarea' | 'number' | 'select'
    placeholder?: string
    options?: string[]
    required: boolean
}

interface ActionType {
    value: string
    label: string
    icon: string
    description: string
    fields: ActionTypeField[]
}

interface ContextVariable {
    name: string
    description: string
}

interface WorkflowStep {
    id: number
    workflow_id: number
    action_type: string
    config: Record<string, unknown>
    order: number
    created_at: string | null
}

interface Workflow {
    id: number
    name: string
    description: string | null
    trigger_event: string
    is_active: boolean
    steps_count: number
    steps?: WorkflowStep[]
    created_at: string | null
    updated_at: string | null
}

interface DashboardStats {
    total: number
    active_count: number
    inactive_count: number
    total_steps: number
}

// =============================================================================
// Icons
// =============================================================================

const WorkflowIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4h4v4H4zM16 4h4v4h-4zM4 16h4v4H4zM16 16h4v4h-4z" />
        <path d="M8 6h8M6 8v8M18 8v8M8 18h8" />
    </svg>
)

const PlusIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 5v14M5 12h14" />
    </svg>
)

const EditIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
)

const TrashIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
)

const ChevronDownIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="6 9 12 15 18 9" />
    </svg>
)

const GripVerticalIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="9" cy="5" r="1" fill="currentColor" />
        <circle cx="15" cy="5" r="1" fill="currentColor" />
        <circle cx="9" cy="12" r="1" fill="currentColor" />
        <circle cx="15" cy="12" r="1" fill="currentColor" />
        <circle cx="9" cy="19" r="1" fill="currentColor" />
        <circle cx="15" cy="19" r="1" fill="currentColor" />
    </svg>
)

const ZapIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
)

const RefreshIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="23 4 23 10 17 10" />
        <polyline points="1 20 1 14 7 14" />
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
)

const CloseIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
)

// =============================================================================
// Main Component
// =============================================================================

const UnifiedAutomationDashboard: React.FC = () => {
    const toast = useToast()

    // State
    const [workflows, setWorkflows] = useState<Workflow[]>([])
    const [stats, setStats] = useState<DashboardStats>({ total: 0, active_count: 0, inactive_count: 0, total_steps: 0 })
    const [loading, setLoading] = useState(true)
    const [triggerEvents, setTriggerEvents] = useState<TriggerEvent[]>([])
    const [actionTypes, setActionTypes] = useState<ActionType[]>([])
    const [contextVariables, setContextVariables] = useState<ContextVariable[]>([])

    // Editor state
    const [editorOpen, setEditorOpen] = useState(false)
    const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null)
    const [workflowForm, setWorkflowForm] = useState({
        name: '',
        description: '',
        trigger_event: '',
        is_active: true
    })
    const [saving, setSaving] = useState(false)

    // Step modal state
    const [stepModalOpen, setStepModalOpen] = useState(false)
    const [editingStep, setEditingStep] = useState<WorkflowStep | null>(null)
    const [stepForm, setStepForm] = useState<{ action_type: string; config: Record<string, unknown> }>({
        action_type: '',
        config: {}
    })

    // =============================================================================
    // Data Fetching
    // =============================================================================

    const fetchWorkflows = useCallback(async () => {
        try {
            const response = await api.get('/admin/automation/api/workflows') as {
                data?: { workflows: Workflow[], total: number, active_count: number, inactive_count: number, total_steps: number }
            } & { workflows?: Workflow[], total?: number, active_count?: number, inactive_count?: number, total_steps?: number }

            const data = response.data || response
            setWorkflows(data.workflows || [])
            setStats({
                total: data.total || 0,
                active_count: data.active_count || 0,
                inactive_count: data.inactive_count || 0,
                total_steps: data.total_steps || 0
            })
        } catch (error) {
            console.error('Failed to fetch workflows:', error)
            toast.error('Failed to load workflows')
        } finally {
            setLoading(false)
        }
    }, [toast])

    const fetchMetadata = useCallback(async () => {
        try {
            const [eventsRes, actionsRes, varsRes] = await Promise.all([
                api.get('/admin/automation/api/events') as Promise<{ events?: TriggerEvent[], data?: { events: TriggerEvent[] } }>,
                api.get('/admin/automation/api/action-types') as Promise<{ action_types?: ActionType[], data?: { action_types: ActionType[] } }>,
                api.get('/admin/automation/api/context-variables') as Promise<{ variables?: ContextVariable[], data?: { variables: ContextVariable[] } }>
            ])
            setTriggerEvents((eventsRes.data?.events || eventsRes.events) || [])
            setActionTypes((actionsRes.data?.action_types || actionsRes.action_types) || [])
            setContextVariables((varsRes.data?.variables || varsRes.variables) || [])
        } catch (error) {
            console.error('Failed to fetch metadata:', error)
        }
    }, [])

    useEffect(() => {
        fetchWorkflows()
        fetchMetadata()

        // Check URL for edit parameter
        const params = new URLSearchParams(window.location.search)
        const editId = params.get('edit')
        const action = params.get('action')

        if (editId) {
            loadWorkflowForEdit(parseInt(editId))
        } else if (action === 'new') {
            openNewWorkflow()
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // =============================================================================
    // Workflow CRUD
    // =============================================================================

    const loadWorkflowForEdit = async (workflowId: number) => {
        try {
            const response = await api.get(`/admin/automation/api/workflows/${workflowId}`) as {
                workflow?: Workflow, data?: { workflow: Workflow }
            }
            const workflow = response.data?.workflow || response.workflow
            if (!workflow) {
                toast.error('Workflow not found')
                return
            }
            setEditingWorkflow(workflow)
            setWorkflowForm({
                name: workflow.name,
                description: workflow.description || '',
                trigger_event: workflow.trigger_event,
                is_active: workflow.is_active
            })
            setEditorOpen(true)
        } catch (error) {
            console.error('Failed to load workflow:', error)
            toast.error('Failed to load workflow')
        }
    }

    const openNewWorkflow = () => {
        setEditingWorkflow(null)
        setWorkflowForm({
            name: '',
            description: '',
            trigger_event: '',
            is_active: true
        })
        setEditorOpen(true)
    }

    const saveWorkflow = async () => {
        if (!workflowForm.name.trim() || !workflowForm.trigger_event) {
            toast.error('Please fill in required fields')
            return
        }

        setSaving(true)
        try {
            if (editingWorkflow) {
                const response = await api.put(`/admin/automation/api/workflows/${editingWorkflow.id}`, workflowForm) as {
                    workflow?: Workflow, data?: { workflow: Workflow }
                }
                const workflow = response.data?.workflow || response.workflow
                if (workflow) setEditingWorkflow(workflow)
                toast.success('Workflow updated successfully')
            } else {
                const response = await api.post('/admin/automation/api/workflows', workflowForm) as {
                    workflow?: Workflow, data?: { workflow: Workflow }
                }
                const workflow = response.data?.workflow || response.workflow
                if (workflow) setEditingWorkflow(workflow)
                toast.success('Workflow created successfully')
            }
            fetchWorkflows()
        } catch (error) {
            console.error('Failed to save workflow:', error)
            toast.error('Failed to save workflow')
        } finally {
            setSaving(false)
        }
    }

    const deleteWorkflow = async (workflow: Workflow) => {
        if (!confirm(`Delete workflow "${workflow.name}"? This cannot be undone.`)) return

        try {
            await api.delete(`/admin/automation/api/workflows/${workflow.id}`)
            toast.success('Workflow deleted')
            if (editingWorkflow?.id === workflow.id) {
                closeEditor()
            }
            fetchWorkflows()
        } catch (error) {
            console.error('Failed to delete workflow:', error)
            toast.error('Failed to delete workflow')
        }
    }

    const toggleWorkflow = async (workflow: Workflow) => {
        try {
            const response = await api.post(`/admin/automation/api/workflows/${workflow.id}/toggle`) as {
                is_active?: boolean, message?: string, data?: { is_active: boolean, message: string }
            }
            const is_active = response.data?.is_active ?? response.is_active ?? !workflow.is_active
            const message = response.data?.message || response.message || (is_active ? 'Workflow activated' : 'Workflow deactivated')

            setWorkflows(prev => prev.map(w =>
                w.id === workflow.id ? { ...w, is_active } : w
            ))
            if (editingWorkflow?.id === workflow.id) {
                setEditingWorkflow(prev => prev ? { ...prev, is_active } : null)
                setWorkflowForm(prev => ({ ...prev, is_active }))
            }
            toast.success(message)
        } catch (error) {
            console.error('Failed to toggle workflow:', error)
            toast.error('Failed to toggle workflow status')
        }
    }

    const closeEditor = () => {
        setEditorOpen(false)
        setEditingWorkflow(null)
        // Clean up URL params
        window.history.replaceState({}, '', window.location.pathname)
    }

    // =============================================================================
    // Step CRUD
    // =============================================================================

    const openAddStep = () => {
        setEditingStep(null)
        setStepForm({ action_type: '', config: {} })
        setStepModalOpen(true)
    }

    const openEditStep = (step: WorkflowStep) => {
        setEditingStep(step)
        setStepForm({
            action_type: step.action_type,
            config: { ...step.config }
        })
        setStepModalOpen(true)
    }

    const saveStep = async () => {
        if (!editingWorkflow) return
        if (!stepForm.action_type) {
            toast.error('Please select an action type')
            return
        }

        try {
            if (editingStep) {
                await api.put(`/admin/automation/api/steps/${editingStep.id}`, stepForm)
                toast.success('Step updated')
            } else {
                await api.post(`/admin/automation/api/workflows/${editingWorkflow.id}/steps`, stepForm)
                toast.success('Step added')
            }
            // Reload workflow to get updated steps
            await loadWorkflowForEdit(editingWorkflow.id)
            setStepModalOpen(false)
        } catch (error) {
            console.error('Failed to save step:', error)
            toast.error('Failed to save step')
        }
    }

    const deleteStep = async (step: WorkflowStep) => {
        if (!confirm('Delete this step?')) return
        if (!editingWorkflow) return

        try {
            await api.delete(`/admin/automation/api/steps/${step.id}`)
            toast.success('Step deleted')
            await loadWorkflowForEdit(editingWorkflow.id)
        } catch (error) {
            console.error('Failed to delete step:', error)
            toast.error('Failed to delete step')
        }
    }

    const getActionTypeInfo = (value: string) => {
        return actionTypes.find(at => at.value === value)
    }

    const getTriggerEventLabel = (value: string) => {
        return triggerEvents.find(e => e.value === value)?.label || value
    }

    // =============================================================================
    // Render
    // =============================================================================

    if (loading) {
        return (
            <div className="automation-dashboard">
                <div className="automation-loading">
                    <div className="spinner" />
                    <span>Loading automation workflows...</span>
                </div>
            </div>
        )
    }

    // Editor sheet content
    const editorContent = (
        <div className="automation-editor-content">
            {/* Workflow Form */}
            <section className="editor-section">
                <h4>Workflow Settings</h4>

                <div className="form-group">
                    <label>Name *</label>
                    <input
                        type="text"
                        value={workflowForm.name}
                        onChange={e => setWorkflowForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., Welcome Email Sequence"
                        className="form-input"
                    />
                </div>

                <div className="form-group">
                    <label>Trigger Event *</label>
                    <select
                        value={workflowForm.trigger_event}
                        onChange={e => setWorkflowForm(prev => ({ ...prev, trigger_event: e.target.value }))}
                        className="form-select"
                    >
                        <option value="">Select a trigger...</option>
                        {triggerEvents.map(event => (
                            <option key={event.value} value={event.value}>
                                {event.label}
                            </option>
                        ))}
                    </select>
                    {workflowForm.trigger_event && (
                        <small className="form-hint">
                            {triggerEvents.find(e => e.value === workflowForm.trigger_event)?.description}
                        </small>
                    )}
                </div>

                <div className="form-group">
                    <label>Description</label>
                    <textarea
                        value={workflowForm.description}
                        onChange={e => setWorkflowForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="What does this workflow do?"
                        className="form-textarea"
                        rows={3}
                    />
                </div>

                <div className="form-group form-row">
                    <label className="toggle-label">
                        <input
                            type="checkbox"
                            checked={workflowForm.is_active}
                            onChange={e => setWorkflowForm(prev => ({ ...prev, is_active: e.target.checked }))}
                        />
                        <span>Active</span>
                    </label>
                </div>

                <button
                    className="save-workflow-btn"
                    onClick={saveWorkflow}
                    disabled={saving}
                >
                    {saving ? 'Saving...' : (editingWorkflow ? 'Update Workflow' : 'Create Workflow')}
                </button>
            </section>

            {/* Steps Section (only show if workflow exists) */}
            {editingWorkflow && (
                <section className="editor-section steps-section">
                    <div className="steps-header">
                        <h4>Workflow Steps</h4>
                        <button className="add-step-btn" onClick={openAddStep}>
                            <PlusIcon />
                            Add Step
                        </button>
                    </div>

                    {(!editingWorkflow.steps || editingWorkflow.steps.length === 0) ? (
                        <div className="steps-empty">
                            <p>No steps defined. Add actions to perform when the event triggers.</p>
                        </div>
                    ) : (
                        <div className="steps-list">
                            {editingWorkflow.steps.map((step, index) => {
                                const actionInfo = getActionTypeInfo(step.action_type)
                                return (
                                    <div key={step.id} className="step-card">
                                        <div className="step-drag-handle">
                                            <GripVerticalIcon />
                                        </div>
                                        <div className="step-order">{index + 1}</div>
                                        <div className="step-content">
                                            <div className="step-header">
                                                <span className="step-icon">{actionInfo?.icon || '⚙️'}</span>
                                                <span className="step-type">{actionInfo?.label || step.action_type}</span>
                                            </div>
                                            <div className="step-config">
                                                {step.action_type === 'send_email' && (
                                                    <span>To: {String(step.config.recipient || 'N/A')} | Subject: {String(step.config.subject || 'N/A')}</span>
                                                )}
                                                {step.action_type === 'log_activity' && (
                                                    <span>Message: {String(step.config.message || 'N/A')}</span>
                                                )}
                                                {step.action_type === 'send_webhook' && (
                                                    <span>URL: {String(step.config.url || 'N/A')}</span>
                                                )}
                                                {step.action_type === 'delay' && (
                                                    <span>Wait: {String(step.config.duration || 'N/A')} {String(step.config.unit || 'minutes')}</span>
                                                )}
                                                {step.action_type === 'create_task' && (
                                                    <span>Task: {String(step.config.title || 'N/A')}</span>
                                                )}
                                                {step.action_type === 'send_notification' && (
                                                    <span>To: {String(step.config.user_id || 'N/A')} | {String(step.config.title || 'N/A')}</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="step-actions">
                                            <button
                                                className="step-action-btn"
                                                onClick={() => openEditStep(step)}
                                                title="Edit step"
                                            >
                                                <EditIcon />
                                            </button>
                                            <button
                                                className="step-action-btn delete"
                                                onClick={() => deleteStep(step)}
                                                title="Delete step"
                                            >
                                                <TrashIcon />
                                            </button>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </section>
            )}

            {/* Context Variables Reference */}
            <section className="editor-section variables-section">
                <h4>
                    <ChevronDownIcon />
                    Available Variables
                </h4>
                <div className="variables-list">
                    {contextVariables.map(v => (
                        <div key={v.name} className="variable-item">
                            <code>{`{{${v.name}}}`}</code>
                            <span>{v.description}</span>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    )

    return (
        <div className="automation-dashboard">
            {/* Header */}
            <header className="automation-header">
                <div className="automation-header-left">
                    <div className="automation-title">
                        <WorkflowIcon />
                        <h1>Automation Workflows</h1>
                    </div>
                    <p className="automation-subtitle">
                        Create automated actions triggered by system events
                    </p>
                </div>
                <div className="automation-header-right">
                    <button
                        className="automation-refresh-btn"
                        onClick={() => fetchWorkflows()}
                        title="Refresh"
                    >
                        <RefreshIcon />
                    </button>
                    <button
                        className="automation-add-btn"
                        onClick={openNewWorkflow}
                    >
                        <PlusIcon />
                        New Workflow
                    </button>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="automation-stats">
                <div className="automation-stat-card">
                    <div className="stat-value">{stats.total}</div>
                    <div className="stat-label">Total Workflows</div>
                </div>
                <div className="automation-stat-card stat-active">
                    <div className="stat-value">{stats.active_count}</div>
                    <div className="stat-label">Active</div>
                </div>
                <div className="automation-stat-card stat-inactive">
                    <div className="stat-value">{stats.inactive_count}</div>
                    <div className="stat-label">Inactive</div>
                </div>
                <div className="automation-stat-card stat-steps">
                    <div className="stat-value">{stats.total_steps}</div>
                    <div className="stat-label">Total Steps</div>
                </div>
            </div>

            {/* Workflow List */}
            {workflows.length === 0 ? (
                <div className="automation-empty">
                    <div className="empty-icon">
                        <ZapIcon />
                    </div>
                    <h3>No Workflows Yet</h3>
                    <p>Create your first automation workflow to start automating tasks based on system events.</p>
                    <button className="automation-add-btn" onClick={openNewWorkflow}>
                        <PlusIcon />
                        Create First Workflow
                    </button>
                </div>
            ) : (
                <div className="automation-grid">
                    {workflows.map(workflow => (
                        <div
                            key={workflow.id}
                            className={`workflow-card ${workflow.is_active ? 'active' : 'inactive'}`}
                        >
                            <div className="workflow-card-header">
                                <div className="workflow-info">
                                    <h3 className="workflow-name">{workflow.name}</h3>
                                    {workflow.description && (
                                        <p className="workflow-description">{workflow.description}</p>
                                    )}
                                </div>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={workflow.is_active}
                                        onChange={() => toggleWorkflow(workflow)}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="workflow-meta">
                                <div className="workflow-trigger">
                                    <ZapIcon />
                                    <span>{getTriggerEventLabel(workflow.trigger_event)}</span>
                                </div>
                                <div className="workflow-steps-count">
                                    {workflow.steps_count} {workflow.steps_count === 1 ? 'step' : 'steps'}
                                </div>
                            </div>

                            <div className="workflow-actions">
                                <button
                                    className="workflow-action-btn edit"
                                    onClick={() => loadWorkflowForEdit(workflow.id)}
                                >
                                    <EditIcon />
                                    Edit
                                </button>
                                <button
                                    className="workflow-action-btn delete"
                                    onClick={() => deleteWorkflow(workflow)}
                                >
                                    <TrashIcon />
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Workflow Editor Sheet */}
            <Sheet isOpen={editorOpen} onClose={closeEditor} width="550px">
                <div className="automation-editor-sheet-content">
                    <div className="editor-sheet-header">
                        <h2>{editingWorkflow ? 'Edit Workflow' : 'New Workflow'}</h2>
                        <button className="sheet-close-btn" onClick={closeEditor}>
                            <CloseIcon />
                        </button>
                    </div>
                    {editorContent}
                </div>
            </Sheet>

            {/* Step Configuration Modal */}
            {stepModalOpen && (
                <div className="step-modal-overlay" onClick={() => setStepModalOpen(false)}>
                    <div className="step-modal" onClick={e => e.stopPropagation()}>
                        <div className="step-modal-header">
                            <h3>{editingStep ? 'Edit Step' : 'Add Step'}</h3>
                            <button className="modal-close-btn" onClick={() => setStepModalOpen(false)}>
                                <CloseIcon />
                            </button>
                        </div>

                        <div className="step-modal-body">
                            <div className="form-group">
                                <label>Action Type *</label>
                                <select
                                    value={stepForm.action_type}
                                    onChange={e => setStepForm({ action_type: e.target.value, config: {} })}
                                    className="form-select"
                                >
                                    <option value="">Select an action...</option>
                                    {actionTypes.map(action => (
                                        <option key={action.value} value={action.value}>
                                            {action.icon} {action.label}
                                        </option>
                                    ))}
                                </select>
                                {stepForm.action_type && (
                                    <small className="form-hint">
                                        {getActionTypeInfo(stepForm.action_type)?.description}
                                    </small>
                                )}
                            </div>

                            {/* Dynamic Fields */}
                            {stepForm.action_type && getActionTypeInfo(stepForm.action_type)?.fields.map(field => (
                                <div key={field.name} className="form-group">
                                    <label>
                                        {field.label} {field.required && '*'}
                                    </label>
                                    {field.type === 'textarea' ? (
                                        <textarea
                                            value={String(stepForm.config[field.name] || '')}
                                            onChange={e => setStepForm(prev => ({
                                                ...prev,
                                                config: { ...prev.config, [field.name]: e.target.value }
                                            }))}
                                            placeholder={field.placeholder}
                                            className="form-textarea"
                                            rows={3}
                                        />
                                    ) : field.type === 'select' ? (
                                        <select
                                            value={String(stepForm.config[field.name] || '')}
                                            onChange={e => setStepForm(prev => ({
                                                ...prev,
                                                config: { ...prev.config, [field.name]: e.target.value }
                                            }))}
                                            className="form-select"
                                        >
                                            <option value="">Select...</option>
                                            {field.options?.map(opt => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            type={field.type === 'number' ? 'number' : 'text'}
                                            value={String(stepForm.config[field.name] || '')}
                                            onChange={e => setStepForm(prev => ({
                                                ...prev,
                                                config: { ...prev.config, [field.name]: e.target.value }
                                            }))}
                                            placeholder={field.placeholder}
                                            className="form-input"
                                        />
                                    )}
                                </div>
                            ))}
                        </div>

                        <div className="step-modal-footer">
                            <button
                                className="modal-cancel-btn"
                                onClick={() => setStepModalOpen(false)}
                            >
                                Cancel
                            </button>
                            <button
                                className="modal-save-btn"
                                onClick={saveStep}
                            >
                                {editingStep ? 'Update Step' : 'Add Step'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default UnifiedAutomationDashboard
