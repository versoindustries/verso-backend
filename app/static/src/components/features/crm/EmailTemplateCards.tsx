import { useState } from 'react'
import { Edit2, Trash2, Mail, Eye, EyeOff } from 'lucide-react'
import { Button } from '../../ui/button'

interface Template {
    id: number
    name: string
    subject: string
    body: string
    template_type: string
    is_active: boolean
}

interface EmailTemplateCardsProps {
    templates: Template[]
    csrfToken: string
    deleteUrlPattern: string
    editUrlPattern: string
}

export default function EmailTemplateCards({
    templates,
    csrfToken,
    deleteUrlPattern,
    editUrlPattern,
}: EmailTemplateCardsProps) {
    const [previewId, setPreviewId] = useState<number | null>(null)
    const [confirmDelete, setConfirmDelete] = useState<number | null>(null)

    const typeColors: Record<string, string> = {
        general: '#6c757d',
        welcome: '#28a745',
        follow_up: '#17a2b8',
        reminder: '#ffc107',
        notification: '#6610f2',
    }

    const handleDelete = async (templateId: number) => {
        const form = document.createElement('form')
        form.method = 'POST'
        form.action = deleteUrlPattern.replace('__ID__', String(templateId))

        const csrf = document.createElement('input')
        csrf.type = 'hidden'
        csrf.name = 'csrf_token'
        csrf.value = csrfToken
        form.appendChild(csrf)

        document.body.appendChild(form)
        form.submit()
    }

    if (templates.length === 0) {
        return (
            <div className="empty-state">
                <Mail className="w-12 h-12 text-gray-300 mb-3" />
                <p className="text-gray-500">No email templates yet.</p>
                <p className="text-gray-400 text-sm">Create your first template to get started!</p>
            </div>
        )
    }

    return (
        <div className="email-templates-grid">
            {templates.map((template) => (
                <div
                    key={template.id}
                    className={`template-card ${previewId === template.id ? 'previewing' : ''}`}
                    onMouseEnter={() => setPreviewId(template.id)}
                    onMouseLeave={() => {
                        setPreviewId(null)
                        setConfirmDelete(null)
                    }}
                >
                    <div className="template-card-header">
                        <span
                            className="template-type"
                            style={{ backgroundColor: typeColors[template.template_type] || '#6c757d' }}
                        >
                            {template.template_type}
                        </span>
                        <span className={`template-status ${template.is_active ? 'active' : 'inactive'}`}>
                            {template.is_active ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                        </span>
                    </div>

                    <h4 className="template-name">{template.name}</h4>
                    <p className="template-subject">{template.subject}</p>

                    {/* Preview Panel */}
                    <div className={`template-preview ${previewId === template.id ? 'visible' : ''}`}>
                        <div className="preview-content">
                            <strong>Subject:</strong> {template.subject}
                            <hr />
                            <div
                                className="preview-body"
                                dangerouslySetInnerHTML={{
                                    __html: template.body.replace(/\n/g, '<br>').slice(0, 300) +
                                        (template.body.length > 300 ? '...' : '')
                                }}
                            />
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="template-actions">
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.location.href = editUrlPattern.replace('__ID__', String(template.id))}
                        >
                            <Edit2 className="w-3 h-3 mr-1" /> Edit
                        </Button>

                        {confirmDelete === template.id ? (
                            <div className="confirm-delete">
                                <span className="text-sm text-red-600">Delete?</span>
                                <Button
                                    size="sm"
                                    variant="default"
                                    className="bg-red-600 hover:bg-red-700"
                                    onClick={() => handleDelete(template.id)}
                                >
                                    Yes
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setConfirmDelete(null)}
                                >
                                    No
                                </Button>
                            </div>
                        ) : (
                            <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-500"
                                onClick={() => setConfirmDelete(template.id)}
                            >
                                <Trash2 className="w-3 h-3" />
                            </Button>
                        )}
                    </div>
                </div>
            ))}
        </div>
    )
}
