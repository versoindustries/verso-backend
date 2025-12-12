/**
 * PageEditorWidget Component
 * 
 * A floating widget that allows authorized users (Admin, Manager, Marketing, Owner)
 * to edit page content, SEO meta tags, and images directly on any page.
 * 
 * This component reads from window.versoContext to determine:
 * - User authentication and roles
 * - Current page type and ID for API calls
 */

import { useState, useEffect, useCallback } from 'react'
import { Edit2, Save, X, Eye, Settings, ChevronDown } from 'lucide-react'
import api from '../../../api'
import { useToast } from '../../ui/toast'
import type { PageEditorContext, ContentFields } from '../../../types'

// Authorized roles for editing
const EDITOR_ROLES = ['Admin', 'Manager', 'Marketing', 'Owner']

// =============================================================================
// SEO Panel Component
// =============================================================================

interface SEOPanelProps {
    visible: boolean
    content: ContentFields
    onChange: (field: keyof ContentFields, value: string) => void
    onClose: () => void
}

function SEOPanel({ visible, content, onChange, onClose }: SEOPanelProps) {
    if (!visible) return null

    const titleLength = content.metaTitle?.length || 0
    const descLength = content.metaDescription?.length || 0

    const titleStatus = titleLength === 0 ? 'empty' : titleLength > 60 ? 'long' : 'good'
    const descStatus = descLength === 0 ? 'empty' : descLength > 160 ? 'long' : descLength < 120 ? 'short' : 'good'

    return (
        <div className="page-editor-seo-panel">
            <div className="seo-panel-header">
                <h3><Settings size={16} /> SEO & Meta Tags</h3>
                <button type="button" onClick={onClose} className="seo-panel-close">
                    <X size={18} />
                </button>
            </div>

            <div className="seo-panel-content">
                {/* Meta Title */}
                <div className="seo-field">
                    <label>
                        Meta Title
                        <span className={`char-count ${titleStatus}`}>
                            {titleLength}/60
                        </span>
                    </label>
                    <input
                        type="text"
                        value={content.metaTitle || ''}
                        onChange={(e) => onChange('metaTitle', e.target.value)}
                        placeholder="Enter SEO title..."
                        maxLength={70}
                    />
                    {titleStatus === 'long' && (
                        <span className="field-hint warning">Title may be truncated in search results</span>
                    )}
                </div>

                {/* Meta Description */}
                <div className="seo-field">
                    <label>
                        Meta Description
                        <span className={`char-count ${descStatus}`}>
                            {descLength}/160
                        </span>
                    </label>
                    <textarea
                        value={content.metaDescription || ''}
                        onChange={(e) => onChange('metaDescription', e.target.value)}
                        placeholder="Enter SEO description..."
                        rows={3}
                        maxLength={200}
                    />
                    {descStatus === 'short' && (
                        <span className="field-hint info">Aim for 120-160 characters</span>
                    )}
                </div>

                <div className="seo-divider" />

                {/* Open Graph Section */}
                <h4>Social Media Preview</h4>

                <div className="seo-field">
                    <label>OG Title</label>
                    <input
                        type="text"
                        value={content.ogTitle || ''}
                        onChange={(e) => onChange('ogTitle', e.target.value)}
                        placeholder="Title for social shares..."
                    />
                </div>

                <div className="seo-field">
                    <label>OG Description</label>
                    <textarea
                        value={content.ogDescription || ''}
                        onChange={(e) => onChange('ogDescription', e.target.value)}
                        placeholder="Description for social shares..."
                        rows={2}
                    />
                </div>

                <div className="seo-field">
                    <label>OG Image URL</label>
                    <input
                        type="text"
                        value={content.ogImage || ''}
                        onChange={(e) => onChange('ogImage', e.target.value)}
                        placeholder="https://..."
                    />
                </div>

                {/* Preview Card */}
                <div className="seo-preview">
                    <label>Preview</label>
                    <div className="seo-preview-card">
                        {content.ogImage && (
                            <img src={content.ogImage} alt="OG Preview" className="seo-preview-image" />
                        )}
                        <div className="seo-preview-content">
                            <div className="seo-preview-title">
                                {content.ogTitle || content.metaTitle || 'Page Title'}
                            </div>
                            <div className="seo-preview-desc">
                                {content.ogDescription || content.metaDescription || 'Page description...'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// Main Widget Component
// =============================================================================

export function PageEditorWidget() {
    const toast = useToast()
    const [isVisible, setIsVisible] = useState(false)
    const [isExpanded, setIsExpanded] = useState(false)
    const [isEditMode, setIsEditMode] = useState(false)
    const [showSEO, setShowSEO] = useState(false)
    const [saving, setSaving] = useState(false)
    const [hasChanges, setHasChanges] = useState(false)

    const [context, setContext] = useState<PageEditorContext | null>(null)
    const [content, setContent] = useState<ContentFields>({})
    const [originalContent, setOriginalContent] = useState<ContentFields>({})

    // Initialize from window.versoContext
    useEffect(() => {
        const versoContext = window.versoContext

        if (!versoContext?.user?.isAuthenticated) {
            setIsVisible(false)
            return
        }

        const userRoles = versoContext.user.roles || []
        const canEdit = userRoles.some(role => EDITOR_ROLES.includes(role))

        if (!canEdit) {
            setIsVisible(false)
            return
        }

        // Check for page editor context
        if (versoContext.pageEditor) {
            setContext(versoContext.pageEditor)
            if (versoContext.pageEditor.initialData) {
                setContent(versoContext.pageEditor.initialData)
                setOriginalContent(versoContext.pageEditor.initialData)
            }
        } else {
            // Default context - assume static page
            setContext({
                contentType: 'static',
                contentId: 0,
                canEdit: true
            })
        }

        setIsVisible(true)
    }, [])

    // Enable edit mode
    const enableEditMode = useCallback(() => {
        setIsEditMode(true)
        setOriginalContent({ ...content })

        // Find editable elements and make them contenteditable
        const editableSelectors = [
            { selector: 'h1', field: 'title' },
            { selector: '.page-content, .post-content, .product-description', field: 'content' }
        ]

        editableSelectors.forEach(({ selector }) => {
            const element = document.querySelector(selector)
            if (element) {
                (element as HTMLElement).contentEditable = 'true'
                element.classList.add('page-editor-editable')
            }
        })

        toast.info('Edit mode enabled. Click on content to edit.')
    }, [content, toast])

    // Cancel edit mode
    const cancelEditMode = useCallback(() => {
        // Restore original content
        const editableSelectors = [
            { selector: 'h1', field: 'title' as keyof ContentFields },
            { selector: '.page-content, .post-content, .product-description', field: 'content' as keyof ContentFields }
        ]

        editableSelectors.forEach(({ selector, field }) => {
            const element = document.querySelector(selector)
            if (element) {
                (element as HTMLElement).contentEditable = 'false'
                element.classList.remove('page-editor-editable')

                if (originalContent[field]) {
                    if (field === 'content') {
                        element.innerHTML = originalContent[field] as string
                    } else {
                        element.textContent = originalContent[field] as string
                    }
                }
            }
        })

        setContent(originalContent)
        setIsEditMode(false)
        setShowSEO(false)
        setHasChanges(false)
    }, [originalContent])

    // Save content
    const saveContent = useCallback(async () => {
        if (!context || context.contentType === 'static') {
            toast.warning('Cannot save static pages. Please use the admin panel.')
            return
        }

        setSaving(true)

        // Collect content from DOM
        const updatedContent: ContentFields = { ...content }

        const titleEl = document.querySelector('h1')
        if (titleEl) {
            updatedContent.title = titleEl.textContent || ''
        }

        const contentEl = document.querySelector('.page-content, .post-content, .product-description')
        if (contentEl) {
            updatedContent.content = contentEl.innerHTML
        }

        // Determine API endpoint
        const endpointMap: Record<string, string> = {
            'page': `/api/page/${context.contentId}/content`,
            'post': `/api/post/${context.contentId}/content`,
            'product': `/shop/api/product/${context.contentId}/content`
        }

        const endpoint = endpointMap[context.contentType]
        if (!endpoint) {
            toast.error('Unknown content type')
            setSaving(false)
            return
        }

        try {
            const response = await api.patch(endpoint, updatedContent)

            if (response.ok) {
                setContent(updatedContent)
                setOriginalContent(updatedContent)
                setHasChanges(false)

                // Disable editable mode
                document.querySelectorAll('.page-editor-editable').forEach(el => {
                    (el as HTMLElement).contentEditable = 'false'
                    el.classList.remove('page-editor-editable')
                })

                setIsEditMode(false)
                setShowSEO(false)
                toast.success('Content saved successfully!')
            } else {
                toast.error(response.error || 'Failed to save content')
            }
        } catch (error) {
            console.error('Save error:', error)
            toast.error('An error occurred while saving')
        } finally {
            setSaving(false)
        }
    }, [context, content, toast])

    // Handle SEO field changes
    const handleSEOChange = useCallback((field: keyof ContentFields, value: string) => {
        setContent(prev => ({ ...prev, [field]: value }))
        setHasChanges(true)
    }, [])

    // Handle content changes in DOM
    useEffect(() => {
        if (!isEditMode) return

        const handleInput = () => {
            setHasChanges(true)
        }

        const editables = document.querySelectorAll('.page-editor-editable')
        editables.forEach(el => {
            el.addEventListener('input', handleInput)
        })

        return () => {
            editables.forEach(el => {
                el.removeEventListener('input', handleInput)
            })
        }
    }, [isEditMode])

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (isEditMode && e.key === 'Escape') {
                cancelEditMode()
            }
            if (isEditMode && e.key === 's' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault()
                saveContent()
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [isEditMode, cancelEditMode, saveContent])

    if (!isVisible) return null

    return (
        <>
            <div className={`page-editor-widget ${isExpanded ? 'expanded' : ''} ${isEditMode ? 'editing' : ''}`}>
                {/* Collapsed state - just a button */}
                {!isExpanded && !isEditMode && (
                    <button
                        type="button"
                        className="page-editor-toggle"
                        onClick={() => setIsExpanded(true)}
                        title="Edit Page"
                    >
                        <Edit2 size={20} />
                    </button>
                )}

                {/* Expanded state - control bar */}
                {(isExpanded || isEditMode) && (
                    <div className="page-editor-controls">
                        {!isEditMode ? (
                            <>
                                <button
                                    type="button"
                                    className="page-editor-btn primary"
                                    onClick={enableEditMode}
                                >
                                    <Edit2 size={16} />
                                    Edit Page
                                </button>
                                <button
                                    type="button"
                                    className="page-editor-btn secondary"
                                    onClick={() => setIsExpanded(false)}
                                    title="Collapse"
                                >
                                    <ChevronDown size={16} />
                                </button>
                            </>
                        ) : (
                            <>
                                <button
                                    type="button"
                                    className="page-editor-btn info"
                                    onClick={() => setShowSEO(!showSEO)}
                                >
                                    <Eye size={16} />
                                    SEO
                                </button>
                                <button
                                    type="button"
                                    className="page-editor-btn cancel"
                                    onClick={cancelEditMode}
                                    disabled={saving}
                                >
                                    <X size={16} />
                                    Cancel
                                </button>
                                <button
                                    type="button"
                                    className="page-editor-btn success"
                                    onClick={saveContent}
                                    disabled={saving || (!hasChanges && context?.contentType !== 'static')}
                                >
                                    <Save size={16} />
                                    {saving ? 'Saving...' : 'Save'}
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* SEO Panel */}
            <SEOPanel
                visible={showSEO}
                content={content}
                onChange={handleSEOChange}
                onClose={() => setShowSEO(false)}
            />
        </>
    )
}

export default PageEditorWidget
