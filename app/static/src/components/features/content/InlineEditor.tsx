/**
 * InlineEditor Component
 * 
 * Provides in-page content editing for pages and blog posts.
 * Admins and Marketing users can edit content directly on the page.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Edit2, Save, X, Eye, Type, Link, AlignLeft, AlignCenter, AlignRight, Bold, Italic, Underline } from 'lucide-react'
import api from '../../../api'
import { useToast } from '../../ui/toast'

// =============================================================================
// Types
// =============================================================================

export interface InlineEditorProps {
    /** Content type: 'page', 'post', or 'product' */
    contentType: 'page' | 'post' | 'product'
    /** ID of the content in database */
    contentId: number
    /** Whether user can edit */
    canEdit: boolean
    /** Initial content fields */
    initialContent?: ContentFields
    /** API endpoint for saving */
    saveEndpoint?: string
    /** Callback after save */
    onSave?: (content: ContentFields) => void
    /** Additional class */
    className?: string
}

export interface ContentFields {
    title?: string
    content?: string
    excerpt?: string
    metaTitle?: string
    metaDescription?: string
    ogTitle?: string
    ogDescription?: string
    ogImage?: string
    slug?: string
}

interface EditableField {
    selector: string
    field: keyof ContentFields
    type: 'text' | 'html' | 'image'
}

// =============================================================================
// Toolbar Component
// =============================================================================

interface ToolbarProps {
    onFormat: (command: string, value?: string) => void
    visible: boolean
    position: { top: number; left: number }
}

function EditToolbar({ onFormat, visible, position }: ToolbarProps) {
    if (!visible) return null

    return (
        <div
            className="inline-editor-toolbar"
            style={{ top: position.top, left: position.left }}
        >
            <button type="button" onClick={() => onFormat('bold')} title="Bold">
                <Bold size={16} />
            </button>
            <button type="button" onClick={() => onFormat('italic')} title="Italic">
                <Italic size={16} />
            </button>
            <button type="button" onClick={() => onFormat('underline')} title="Underline">
                <Underline size={16} />
            </button>
            <div className="toolbar-divider" />
            <button type="button" onClick={() => onFormat('justifyLeft')} title="Align Left">
                <AlignLeft size={16} />
            </button>
            <button type="button" onClick={() => onFormat('justifyCenter')} title="Align Center">
                <AlignCenter size={16} />
            </button>
            <button type="button" onClick={() => onFormat('justifyRight')} title="Align Right">
                <AlignRight size={16} />
            </button>
            <div className="toolbar-divider" />
            <button type="button" onClick={() => onFormat('createLink')} title="Insert Link">
                <Link size={16} />
            </button>
        </div>
    )
}

// =============================================================================
// SEO Sidebar Component
// =============================================================================

interface SEOSidebarProps {
    visible: boolean
    content: ContentFields
    onChange: (field: keyof ContentFields, value: string) => void
    onClose: () => void
}

function SEOSidebar({ visible, content, onChange, onClose }: SEOSidebarProps) {
    if (!visible) return null

    const titleLength = content.metaTitle?.length || 0
    const descLength = content.metaDescription?.length || 0

    const titleStatus = titleLength === 0 ? 'empty' : titleLength > 60 ? 'long' : 'good'
    const descStatus = descLength === 0 ? 'empty' : descLength > 160 ? 'long' : descLength < 120 ? 'short' : 'good'

    return (
        <div className="seo-sidebar">
            <div className="seo-sidebar-header">
                <h3><Type size={18} /> SEO Settings</h3>
                <button type="button" className="seo-sidebar-close" onClick={onClose}>
                    <X size={20} />
                </button>
            </div>

            <div className="seo-sidebar-content">
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
                        <span className="field-hint info">Aim for 120-160 characters for best results</span>
                    )}
                </div>

                {/* Slug */}
                <div className="seo-field">
                    <label>URL Slug</label>
                    <input
                        type="text"
                        value={content.slug || ''}
                        onChange={(e) => onChange('slug', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))}
                        placeholder="url-friendly-slug"
                    />
                </div>

                <div className="seo-divider" />

                {/* Open Graph */}
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
                    <div className="seo-preview-card">
                        {content.ogImage && (
                            <img src={content.ogImage} alt="OG Preview" className="seo-preview-image" />
                        )}
                        <div className="seo-preview-content">
                            <div className="seo-preview-title">{content.ogTitle || content.metaTitle || 'Page Title'}</div>
                            <div className="seo-preview-desc">{content.ogDescription || content.metaDescription || 'Page description...'}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function InlineEditor({
    contentType,
    contentId,
    canEdit,
    initialContent = {},
    saveEndpoint,
    onSave,
    className = '',
}: InlineEditorProps) {
    const toast = useToast()
    const [isEditMode, setIsEditMode] = useState(false)
    const [showSEO, setShowSEO] = useState(false)
    const [content, setContent] = useState<ContentFields>(initialContent)
    const [originalContent, setOriginalContent] = useState<ContentFields>(initialContent)
    const [hasChanges, setHasChanges] = useState(false)
    const [saving, setSaving] = useState(false)
    const [toolbarVisible, setToolbarVisible] = useState(false)
    const [toolbarPosition, setToolbarPosition] = useState({ top: 0, left: 0 })
    const editorRef = useRef<HTMLDivElement>(null)

    // Editable fields based on content type
    const editableFields: EditableField[] = contentType === 'post'
        ? [
            { selector: 'h1', field: 'title', type: 'text' },
            { selector: '.post-content', field: 'content', type: 'html' },
            { selector: '.post-excerpt', field: 'excerpt', type: 'text' },
        ]
        : contentType === 'product'
            ? [
                { selector: 'h1', field: 'title', type: 'text' },
                { selector: '.product-description', field: 'content', type: 'html' },
            ]
            : [
                { selector: 'h1', field: 'title', type: 'text' },
                { selector: '.page-content', field: 'content', type: 'html' },
            ]

    // Handle text selection for toolbar
    const handleSelection = useCallback(() => {
        const selection = window.getSelection()
        if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
            const range = selection.getRangeAt(0)
            const rect = range.getBoundingClientRect()
            setToolbarPosition({
                top: rect.top - 50 + window.scrollY,
                left: rect.left + rect.width / 2 - 100
            })
            setToolbarVisible(true)
        } else {
            setToolbarVisible(false)
        }
    }, [])

    // Apply formatting command
    const handleFormat = useCallback((command: string, value?: string) => {
        if (command === 'createLink') {
            const url = prompt('Enter URL:')
            if (url) {
                document.execCommand(command, false, url)
            }
        } else {
            document.execCommand(command, false, value)
        }
        setHasChanges(true)
    }, [])

    // Enable edit mode
    const enableEditMode = useCallback(() => {
        setIsEditMode(true)
        setOriginalContent({ ...content })

        // Make fields editable
        editableFields.forEach(({ selector, type }) => {
            const element = document.querySelector(selector)
            if (element) {
                (element as HTMLElement).contentEditable = 'true'
                element.classList.add('inline-editable')
                if (type === 'html') {
                    element.addEventListener('mouseup', handleSelection)
                }
            }
        })

        toast.info('Edit mode enabled. Click on text to edit.')
    }, [content, editableFields, handleSelection])

    // Disable edit mode
    const disableEditMode = useCallback((save: boolean = false) => {
        // Collect content from editable fields
        const updatedContent: ContentFields = { ...content }
        editableFields.forEach(({ selector, field, type }) => {
            const element = document.querySelector(selector)
            if (element) {
                (element as HTMLElement).contentEditable = 'false'
                element.classList.remove('inline-editable')
                element.removeEventListener('mouseup', handleSelection)

                if (type === 'html') {
                    updatedContent[field] = element.innerHTML
                } else {
                    updatedContent[field] = element.textContent || ''
                }
            }
        })

        if (!save) {
            // Restore original content
            editableFields.forEach(({ selector, field, type }) => {
                const element = document.querySelector(selector)
                if (element && originalContent[field]) {
                    if (type === 'html') {
                        element.innerHTML = originalContent[field] as string
                    } else {
                        element.textContent = originalContent[field] as string
                    }
                }
            })
            setContent(originalContent)
        } else {
            setContent(updatedContent)
        }

        setIsEditMode(false)
        setShowSEO(false)
        setToolbarVisible(false)
        setHasChanges(false)
    }, [content, originalContent, editableFields, handleSelection])

    // Save content
    const saveContent = useCallback(async () => {
        setSaving(true)

        // Collect current content from DOM
        const updatedContent: ContentFields = { ...content }
        editableFields.forEach(({ selector, field, type }) => {
            const element = document.querySelector(selector)
            if (element) {
                if (type === 'html') {
                    updatedContent[field] = element.innerHTML
                } else {
                    updatedContent[field] = element.textContent || ''
                }
            }
        })

        const endpoint = saveEndpoint || `/api/${contentType}/${contentId}/content`

        try {
            const response = await api.patch(endpoint, updatedContent)

            if (response.ok) {
                setContent(updatedContent)
                setOriginalContent(updatedContent)
                setHasChanges(false)
                toast.success('Content saved successfully!')
                onSave?.(updatedContent)
                disableEditMode(true)
            } else {
                toast.error(response.error || 'Failed to save content')
            }
        } catch (error) {
            console.error('Save error:', error)
            toast.error('An error occurred while saving')
        } finally {
            setSaving(false)
        }
    }, [content, contentType, contentId, saveEndpoint, editableFields, onSave, disableEditMode])

    // Handle SEO field changes
    const handleSEOChange = useCallback((field: keyof ContentFields, value: string) => {
        setContent(prev => ({ ...prev, [field]: value }))
        setHasChanges(true)
    }, [])

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (isEditMode && e.key === 'Escape') {
                disableEditMode(false)
            }
            if (isEditMode && e.key === 's' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault()
                saveContent()
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [isEditMode, disableEditMode, saveContent])

    if (!canEdit) return null

    return (
        <div ref={editorRef} className={`inline-editor ${className}`}>
            {/* Edit Mode Controls */}
            <div className={`inline-editor-controls ${isEditMode ? 'editing' : ''}`}>
                {!isEditMode ? (
                    <button
                        type="button"
                        className="edit-mode-btn"
                        onClick={enableEditMode}
                    >
                        <Edit2 size={16} />
                        Edit Page
                    </button>
                ) : (
                    <>
                        <button
                            type="button"
                            className="edit-mode-btn seo"
                            onClick={() => setShowSEO(!showSEO)}
                        >
                            <Eye size={16} />
                            SEO
                        </button>
                        <button
                            type="button"
                            className="edit-mode-btn cancel"
                            onClick={() => disableEditMode(false)}
                            disabled={saving}
                        >
                            <X size={16} />
                            Cancel
                        </button>
                        <button
                            type="button"
                            className="edit-mode-btn save"
                            onClick={saveContent}
                            disabled={saving || !hasChanges}
                        >
                            <Save size={16} />
                            {saving ? 'Saving...' : 'Save'}
                        </button>
                    </>
                )}
            </div>

            {/* Floating Toolbar */}
            {isEditMode && (
                <EditToolbar
                    onFormat={handleFormat}
                    visible={toolbarVisible}
                    position={toolbarPosition}
                />
            )}

            {/* SEO Sidebar */}
            <SEOSidebar
                visible={showSEO}
                content={content}
                onChange={handleSEOChange}
                onClose={() => setShowSEO(false)}
            />
        </div>
    )
}

export default InlineEditor
