/**
 * Email Templates Panel
 * 
 * Grid display of email templates with quick preview,
 * create/edit functionality, and status management.
 */

import { useState } from 'react'
import {
    Edit2,
    Trash2,
    Eye,
    Plus,
    X,
    Check
} from 'lucide-react'
import { useToastApi } from '../../../hooks/useToastApi'

interface EmailTemplate {
    id: number
    name: string
    type: string
    subject: string
    body: string
    isActive: boolean
}

interface EmailTemplatesProps {
    templates: EmailTemplate[]
    csrfToken: string
}

export default function EmailTemplates({
    templates: initialTemplates,
    csrfToken
}: EmailTemplatesProps) {
    const [templates, setTemplates] = useState(initialTemplates)
    const [showModal, setShowModal] = useState(false)
    const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
    const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null)
    const { success, error } = useToastApi()

    const [formData, setFormData] = useState({
        name: '',
        type: 'general',
        subject: '',
        body: '',
        isActive: true
    })

    const templateTypes = [
        { value: 'general', label: 'General' },
        { value: 'follow_up', label: 'Follow Up' },
        { value: 'welcome', label: 'Welcome' },
        { value: 'reminder', label: 'Reminder' },
        { value: 'proposal', label: 'Proposal' },
        { value: 'thank_you', label: 'Thank You' }
    ]

    const handleCreate = () => {
        setEditingTemplate(null)
        setFormData({
            name: '',
            type: 'general',
            subject: '',
            body: '',
            isActive: true
        })
        setShowModal(true)
    }

    const handleEdit = (template: EmailTemplate) => {
        setEditingTemplate(template)
        setFormData({
            name: template.name,
            type: template.type,
            subject: template.subject,
            body: template.body,
            isActive: template.isActive
        })
        setShowModal(true)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        try {
            const body = new FormData()
            body.append('csrf_token', csrfToken)
            body.append('name', formData.name)
            body.append('template_type', formData.type)
            body.append('subject', formData.subject)
            body.append('body', formData.body)
            if (formData.isActive) body.append('is_active', 'y')
            if (editingTemplate) body.append('template_id', String(editingTemplate.id))

            const response = await fetch('/admin/crm/templates', {
                method: 'POST',
                body
            })

            if (response.ok) {
                success(editingTemplate ? 'Template updated' : 'Template created')
                window.location.reload()
            } else {
                error('Failed to save template')
            }
        } catch (err) {
            error('An error occurred')
        }
    }

    const handleDelete = async (templateId: number) => {
        if (!confirm('Delete this template?')) {
            return
        }

        try {
            const body = new FormData()
            body.append('csrf_token', csrfToken)

            const response = await fetch(`/admin/crm/templates/delete/${templateId}`, {
                method: 'POST',
                body
            })

            if (response.ok) {
                success('Template deleted')
                setTemplates(templates.filter(t => t.id !== templateId))
            } else {
                error('Failed to delete template')
            }
        } catch (err) {
            error('An error occurred')
        }
    }

    return (
        <>
            {/* Templates Grid */}
            <div className="crm-templates-grid">
                {templates.map((template) => (
                    <div
                        key={template.id}
                        className="crm-template-card"
                        onClick={() => setPreviewTemplate(template)}
                    >
                        <div className="crm-template-header">
                            <h4 className="crm-template-name">{template.name}</h4>
                            <span className="crm-template-type">{template.type}</span>
                        </div>
                        <p className="crm-template-subject">{template.subject}</p>
                        <div className="crm-template-footer">
                            <div className={`crm-template-status ${template.isActive ? 'active' : 'inactive'}`}>
                                <span className="crm-template-status-dot" />
                                {template.isActive ? 'Active' : 'Inactive'}
                            </div>
                            <div style={{ display: 'flex', gap: '0.25rem' }}>
                                <button
                                    className="crm-btn-icon"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        setPreviewTemplate(template)
                                    }}
                                    title="Preview"
                                >
                                    <Eye size={14} />
                                </button>
                                <button
                                    className="crm-btn-icon"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        handleEdit(template)
                                    }}
                                    title="Edit"
                                >
                                    <Edit2 size={14} />
                                </button>
                                <button
                                    className="crm-btn-icon"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        handleDelete(template.id)
                                    }}
                                    title="Delete"
                                    style={{ color: '#dc3545' }}
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        </div>
                    </div>
                ))}

                {/* Add Template Card */}
                <div
                    className="crm-template-card"
                    onClick={handleCreate}
                    style={{
                        border: '2px dashed rgba(65, 105, 225, 0.3)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minHeight: '150px',
                        cursor: 'pointer'
                    }}
                >
                    <Plus size={32} style={{ opacity: 0.4, marginBottom: '0.5rem' }} />
                    <span style={{ color: 'rgba(255,255,255,0.5)' }}>Add Template</span>
                </div>
            </div>

            {/* Preview Modal */}
            {previewTemplate && (
                <div
                    className="crm-modal-overlay"
                    onClick={() => setPreviewTemplate(null)}
                    style={{
                        position: 'fixed',
                        inset: 0,
                        background: 'rgba(0,0,0,0.7)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000
                    }}
                >
                    <div
                        className="crm-modal"
                        onClick={(e) => e.stopPropagation()}
                        style={{
                            background: 'var(--crm-glass-bg, rgba(31, 31, 31, 0.95))',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(65, 105, 225, 0.3)',
                            borderRadius: '12px',
                            width: '90%',
                            maxWidth: '600px',
                            maxHeight: '80vh',
                            overflow: 'auto'
                        }}
                    >
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '1rem 1.5rem',
                            borderBottom: '1px solid rgba(255,255,255,0.1)'
                        }}>
                            <h3 style={{ margin: 0, fontFamily: 'Neon-Heavy', color: '#fff' }}>
                                {previewTemplate.name}
                            </h3>
                            <button
                                className="crm-btn-icon"
                                onClick={() => setPreviewTemplate(null)}
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <div style={{ padding: '1.5rem' }}>
                            <div style={{ marginBottom: '1rem' }}>
                                <label style={{
                                    fontSize: '0.75rem',
                                    color: 'rgba(255,255,255,0.5)',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px'
                                }}>
                                    Subject
                                </label>
                                <p style={{
                                    margin: '0.25rem 0 0',
                                    fontSize: '1rem',
                                    color: '#fff'
                                }}>
                                    {previewTemplate.subject}
                                </p>
                            </div>
                            <div>
                                <label style={{
                                    fontSize: '0.75rem',
                                    color: 'rgba(255,255,255,0.5)',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px'
                                }}>
                                    Body
                                </label>
                                <div style={{
                                    marginTop: '0.5rem',
                                    padding: '1rem',
                                    background: 'rgba(0,0,0,0.2)',
                                    borderRadius: '8px',
                                    fontSize: '0.9rem',
                                    lineHeight: '1.6',
                                    color: 'rgba(255,255,255,0.8)',
                                    whiteSpace: 'pre-wrap'
                                }}>
                                    {previewTemplate.body}
                                </div>
                            </div>
                        </div>
                        <div style={{
                            display: 'flex',
                            gap: '0.5rem',
                            padding: '1rem 1.5rem',
                            borderTop: '1px solid rgba(255,255,255,0.1)'
                        }}>
                            <button
                                className="crm-btn crm-btn-primary"
                                onClick={() => {
                                    handleEdit(previewTemplate)
                                    setPreviewTemplate(null)
                                }}
                            >
                                <Edit2 size={16} />
                                Edit Template
                            </button>
                            <button
                                className="crm-btn crm-btn-secondary"
                                onClick={() => setPreviewTemplate(null)}
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div
                    className="crm-modal-overlay"
                    onClick={() => setShowModal(false)}
                    style={{
                        position: 'fixed',
                        inset: 0,
                        background: 'rgba(0,0,0,0.7)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000
                    }}
                >
                    <div
                        className="crm-modal"
                        onClick={(e) => e.stopPropagation()}
                        style={{
                            background: 'var(--crm-glass-bg, rgba(31, 31, 31, 0.95))',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(65, 105, 225, 0.3)',
                            borderRadius: '12px',
                            width: '90%',
                            maxWidth: '600px',
                            maxHeight: '80vh',
                            overflow: 'auto'
                        }}
                    >
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '1rem 1.5rem',
                            borderBottom: '1px solid rgba(255,255,255,0.1)'
                        }}>
                            <h3 style={{ margin: 0, fontFamily: 'Neon-Heavy', color: '#fff' }}>
                                {editingTemplate ? 'Edit Template' : 'Create Template'}
                            </h3>
                            <button
                                className="crm-btn-icon"
                                onClick={() => setShowModal(false)}
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div style={{ padding: '1.5rem' }}>
                                <div className="crm-form-group">
                                    <label className="crm-form-label">Template Name</label>
                                    <input
                                        type="text"
                                        className="crm-form-input"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="crm-form-group">
                                    <label className="crm-form-label">Type</label>
                                    <select
                                        className="crm-form-input"
                                        value={formData.type}
                                        onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                    >
                                        {templateTypes.map(t => (
                                            <option key={t.value} value={t.value}>{t.label}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="crm-form-group">
                                    <label className="crm-form-label">Subject</label>
                                    <input
                                        type="text"
                                        className="crm-form-input"
                                        value={formData.subject}
                                        onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="crm-form-group">
                                    <label className="crm-form-label">Body</label>
                                    <textarea
                                        className="crm-form-input"
                                        value={formData.body}
                                        onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                                        rows={8}
                                        required
                                        style={{ resize: 'vertical' }}
                                    />
                                    <small style={{
                                        display: 'block',
                                        marginTop: '0.5rem',
                                        fontSize: '0.75rem',
                                        color: 'rgba(255,255,255,0.4)'
                                    }}>
                                        Placeholders: {'{{first_name}}'}, {'{{last_name}}'}, {'{{email}}'}, {'{{company}}'}
                                    </small>
                                </div>

                                <div className="crm-form-group">
                                    <label className="crm-checkbox-label">
                                        <input
                                            type="checkbox"
                                            checked={formData.isActive}
                                            onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                                        />
                                        <Check size={16} style={{ color: '#28a745' }} />
                                        Active
                                    </label>
                                </div>
                            </div>

                            <div style={{
                                display: 'flex',
                                gap: '0.5rem',
                                padding: '1rem 1.5rem',
                                borderTop: '1px solid rgba(255,255,255,0.1)'
                            }}>
                                <button type="submit" className="crm-btn crm-btn-primary" style={{ flex: 1 }}>
                                    {editingTemplate ? 'Update Template' : 'Create Template'}
                                </button>
                                <button
                                    type="button"
                                    className="crm-btn crm-btn-secondary"
                                    onClick={() => setShowModal(false)}
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    )
}
