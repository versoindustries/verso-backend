/**
 * Pipeline Settings Panel
 * 
 * Manage pipeline stages with drag-and-drop reordering,
 * color customization, and inline editing.
 */

import { useState } from 'react'
import {
    GripVertical,
    Edit2,
    Trash2,
    CheckCircle,
    XCircle,
    Plus
} from 'lucide-react'
import { useToastApi } from '../../../hooks/useToastApi'

interface Stage {
    id: number
    name: string
    color: string
    order: number
    probability: number
    isWonStage: boolean
    isLostStage: boolean
    pipelineName: string
}

interface PipelineSettingsProps {
    stages: Stage[]
    pipelineName: string
    csrfToken: string
}

export default function PipelineSettings({
    stages: initialStages,
    pipelineName,
    csrfToken
}: PipelineSettingsProps) {
    const [stages, setStages] = useState(initialStages)
    const [editingStage, setEditingStage] = useState<Stage | null>(null)
    const [isCreating, setIsCreating] = useState(false)
    const { success, error } = useToastApi()

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        color: '#6c757d',
        order: stages.length + 1,
        probability: 0,
        isWonStage: false,
        isLostStage: false
    })

    const pipelines = [
        { value: 'default', label: 'Default Pipeline' },
        { value: 'sales', label: 'Sales Pipeline' },
        { value: 'support', label: 'Support Pipeline' }
    ]

    const handleEdit = (stage: Stage) => {
        setEditingStage(stage)
        setFormData({
            name: stage.name,
            color: stage.color,
            order: stage.order,
            probability: stage.probability,
            isWonStage: stage.isWonStage,
            isLostStage: stage.isLostStage
        })
        setIsCreating(false)
    }

    const handleCreate = () => {
        setEditingStage(null)
        setFormData({
            name: '',
            color: '#6c757d',
            order: stages.length + 1,
            probability: 0,
            isWonStage: false,
            isLostStage: false
        })
        setIsCreating(true)
    }

    const handleCancel = () => {
        setEditingStage(null)
        setIsCreating(false)
        setFormData({
            name: '',
            color: '#6c757d',
            order: stages.length + 1,
            probability: 0,
            isWonStage: false,
            isLostStage: false
        })
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        try {
            const url = '/admin/crm/pipeline/create-stage'
            const body = new FormData()
            body.append('csrf_token', csrfToken)
            body.append('name', formData.name)
            body.append('color', formData.color)
            body.append('order', String(formData.order))
            body.append('probability', String(formData.probability))
            body.append('pipeline_name', pipelineName)
            if (formData.isWonStage) body.append('is_won_stage', 'y')
            if (formData.isLostStage) body.append('is_lost_stage', 'y')
            if (editingStage) body.append('stage_id', String(editingStage.id))

            const response = await fetch(url, {
                method: 'POST',
                body
            })

            if (response.ok) {
                success(editingStage ? 'Stage updated' : 'Stage created')
                // Reload to get updated stages
                window.location.reload()
            } else {
                error('Failed to save stage')
            }
        } catch (err) {
            error('An error occurred')
        }
    }

    const handleDelete = async (stageId: number) => {
        if (!confirm('Delete this stage? Leads in this stage will need to be reassigned.')) {
            return
        }

        try {
            const body = new FormData()
            body.append('csrf_token', csrfToken)

            const response = await fetch(`/admin/crm/pipeline/delete/${stageId}`, {
                method: 'POST',
                body
            })

            if (response.ok) {
                success('Stage deleted')
                setStages(stages.filter(s => s.id !== stageId))
            } else {
                error('Failed to delete stage')
            }
        } catch (err) {
            error('An error occurred')
        }
    }

    return (
        <div className="crm-settings-layout">
            {/* Stages List */}
            <div>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '1rem'
                }}>
                    <select
                        value={pipelineName}
                        onChange={(e) => {
                            window.location.href = `/admin/crm/pipeline/settings?pipeline=${e.target.value}`
                        }}
                        className="crm-form-input"
                        style={{ width: 'auto' }}
                    >
                        {pipelines.map(p => (
                            <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                    </select>
                    <button
                        className="crm-btn crm-btn-primary"
                        onClick={handleCreate}
                    >
                        <Plus size={16} />
                        Add Stage
                    </button>
                </div>

                <ul className="crm-stages-list">
                    {stages.map((stage) => (
                        <li key={stage.id} className="crm-stage-item">
                            <div className="crm-stage-left">
                                <GripVertical size={18} style={{ opacity: 0.4, cursor: 'grab' }} />
                                <div
                                    className="crm-stage-color"
                                    style={{ backgroundColor: stage.color }}
                                />
                                <div className="crm-stage-info">
                                    <h4>
                                        {stage.name}
                                        {stage.isWonStage && (
                                            <span className="crm-stage-badge won">Won</span>
                                        )}
                                        {stage.isLostStage && (
                                            <span className="crm-stage-badge lost">Lost</span>
                                        )}
                                    </h4>
                                    <span>
                                        Order: {stage.order} • Probability: {stage.probability}%
                                    </span>
                                </div>
                            </div>
                            <div className="crm-stage-actions">
                                <button
                                    onClick={() => handleEdit(stage)}
                                    title="Edit"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button
                                    onClick={() => handleDelete(stage.id)}
                                    title="Delete"
                                    style={{ color: '#dc3545' }}
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </li>
                    ))}
                    {stages.length === 0 && (
                        <li className="crm-stage-item" style={{ justifyContent: 'center', opacity: 0.5 }}>
                            No stages configured. Add one to get started.
                        </li>
                    )}
                </ul>
            </div>

            {/* Edit/Create Form */}
            {(isCreating || editingStage) && (
                <div className="crm-stage-form">
                    <h3>{editingStage ? `Edit: ${editingStage.name}` : 'Add New Stage'}</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="crm-form-group">
                            <label className="crm-form-label">Stage Name</label>
                            <input
                                type="text"
                                className="crm-form-input"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                required
                            />
                        </div>

                        <div className="crm-form-group">
                            <label className="crm-form-label">Display Order</label>
                            <input
                                type="number"
                                className="crm-form-input"
                                value={formData.order}
                                onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) })}
                                min={1}
                                required
                            />
                        </div>

                        <div className="crm-form-group">
                            <label className="crm-form-label">Color</label>
                            <div className="crm-color-input">
                                <input
                                    type="text"
                                    className="crm-form-input"
                                    value={formData.color}
                                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                                    style={{ flex: 1 }}
                                />
                                <input
                                    type="color"
                                    value={formData.color}
                                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="crm-form-group">
                            <label className="crm-form-label">Conversion Probability (%)</label>
                            <input
                                type="number"
                                className="crm-form-input"
                                value={formData.probability}
                                onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) })}
                                min={0}
                                max={100}
                            />
                        </div>

                        <div className="crm-form-group">
                            <div className="crm-checkbox-group">
                                <label className="crm-checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={formData.isWonStage}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            isWonStage: e.target.checked,
                                            isLostStage: e.target.checked ? false : formData.isLostStage
                                        })}
                                    />
                                    <CheckCircle size={16} style={{ color: '#28a745' }} />
                                    This stage marks lead as Won
                                </label>
                                <label className="crm-checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={formData.isLostStage}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            isLostStage: e.target.checked,
                                            isWonStage: e.target.checked ? false : formData.isWonStage
                                        })}
                                    />
                                    <XCircle size={16} style={{ color: '#dc3545' }} />
                                    This stage marks lead as Lost
                                </label>
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                            <button type="submit" className="crm-btn crm-btn-primary" style={{ flex: 1 }}>
                                {editingStage ? 'Update Stage' : 'Create Stage'}
                            </button>
                            <button
                                type="button"
                                className="crm-btn crm-btn-secondary"
                                onClick={handleCancel}
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    )
}
