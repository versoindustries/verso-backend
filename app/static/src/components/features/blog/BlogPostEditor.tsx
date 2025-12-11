/**
 * BlogPostEditor React Component
 * 
 * Enterprise-level blog post editor with:
 * - Title input with character count
 * - Functional markdown toolbar with keyboard shortcuts
 * - Split-pane layout with live preview
 * - Image upload with drag-and-drop
 * - Tag input with chips
 * - Link/image insertion modals
 * - Scheduling date picker
 * - SEO preview panel
 * - Publishing options
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { useMarkdownEditor } from '../../../hooks/useMarkdownEditor'
import { parseMarkdown } from '../../../utils/MarkdownParser'

export interface BlogCategory {
    id: number
    name: string
}

export interface PostSeries {
    id: number
    title: string
}

export interface BlogPostEditorProps {
    /** Available blog categories */
    categories: BlogCategory[]
    /** Available post series */
    series: PostSeries[]
    /** CSRF token for form submission */
    csrfToken: string
    /** API endpoint for creating posts */
    apiEndpoint: string
    /** URL to redirect after successful creation */
    redirectUrl: string
}

interface FormData {
    title: string
    content: string
    category: string
    blogCategoryId: number
    tags: string[]
    isFeatured: boolean
    publishAt: string
    metaDescription: string
    seriesId: number
    seriesOrder: number
    isPublished: boolean
    image: File | null
}

type ViewMode = 'edit' | 'preview' | 'split'

export function BlogPostEditor({
    categories: initialCategories,
    series: initialSeries,
    csrfToken,
    apiEndpoint,
    redirectUrl
}: BlogPostEditorProps) {
    // Local state for categories/series (can be updated when new ones are created)
    const [categories, setCategories] = useState<BlogCategory[]>(initialCategories)
    const [series, setSeries] = useState<PostSeries[]>(initialSeries)

    // Form state
    const [formData, setFormData] = useState<FormData>({
        title: '',
        content: '',
        category: '',
        blogCategoryId: 0,
        tags: [],
        isFeatured: false,
        publishAt: '',
        metaDescription: '',
        seriesId: 0,
        seriesOrder: 0,
        isPublished: false,
        image: null
    })

    const [tagInput, setTagInput] = useState('')
    const [imagePreview, setImagePreview] = useState<string | null>(null)
    const [isDragging, setIsDragging] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errors, setErrors] = useState<Record<string, string>>({})
    const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

    // View mode state
    const [viewMode, setViewMode] = useState<ViewMode>('split')

    // Modal states
    const [showLinkModal, setShowLinkModal] = useState(false)
    const [linkText, setLinkText] = useState('')
    const [linkUrl, setLinkUrl] = useState('')
    const [showImageModal, setShowImageModal] = useState(false)
    const [imageAlt, setImageAlt] = useState('')
    const [imageUrl, setImageUrl] = useState('')

    // Inline creation state
    const [showNewCategory, setShowNewCategory] = useState(false)
    const [newCategoryName, setNewCategoryName] = useState('')
    const [isCreatingCategory, setIsCreatingCategory] = useState(false)
    const [showNewSeries, setShowNewSeries] = useState(false)
    const [newSeriesTitle, setNewSeriesTitle] = useState('')
    const [isCreatingSeries, setIsCreatingSeries] = useState(false)

    const fileInputRef = useRef<HTMLInputElement>(null)
    const previewRef = useRef<HTMLDivElement>(null)

    // Initialize markdown editor hook
    const markdownEditor = useMarkdownEditor({
        initialContent: formData.content,
        onChange: (content) => {
            setFormData(prev => ({ ...prev, content }))
        }
    })

    // Sync content with form data
    useEffect(() => {
        if (markdownEditor.content !== formData.content) {
            setFormData(prev => ({ ...prev, content: markdownEditor.content }))
        }
    }, [markdownEditor.content])

    // Auto-hide toast
    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 5000)
            return () => clearTimeout(timer)
        }
    }, [toast])

    // Synchronized scrolling
    const handleEditorScroll = useCallback((e: React.UIEvent<HTMLTextAreaElement>) => {
        if (viewMode === 'split' && previewRef.current) {
            const textarea = e.currentTarget
            const scrollRatio = textarea.scrollTop / (textarea.scrollHeight - textarea.clientHeight)
            const previewScrollTop = scrollRatio * (previewRef.current.scrollHeight - previewRef.current.clientHeight)
            previewRef.current.scrollTop = previewScrollTop
        }
    }, [viewMode])

    // Handle input changes for non-content fields
    const handleChange = useCallback((field: keyof FormData, value: string | number | boolean) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        if (errors[field]) {
            setErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors[field]
                return newErrors
            })
        }
    }, [errors])

    // Handle tag input
    const handleTagKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            const tag = tagInput.trim()
            if (tag && !formData.tags.includes(tag)) {
                setFormData(prev => ({ ...prev, tags: [...prev.tags, tag] }))
                setTagInput('')
            }
        } else if (e.key === 'Backspace' && !tagInput && formData.tags.length > 0) {
            setFormData(prev => ({ ...prev, tags: prev.tags.slice(0, -1) }))
        }
    }, [tagInput, formData.tags])

    const removeTag = useCallback((tagToRemove: string) => {
        setFormData(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tagToRemove) }))
    }, [])

    // Handle image upload
    const handleImageChange = useCallback((file: File | null) => {
        if (file) {
            const validTypes = ['image/png', 'image/jpeg', 'image/jpg']
            if (!validTypes.includes(file.type)) {
                setErrors(prev => ({ ...prev, image: 'Only PNG, JPG, and JPEG files are allowed.' }))
                return
            }
            if (file.size > 5 * 1024 * 1024) {
                setErrors(prev => ({ ...prev, image: 'Image must be less than 5MB.' }))
                return
            }

            setFormData(prev => ({ ...prev, image: file }))
            const reader = new FileReader()
            reader.onload = (e) => setImagePreview(e.target?.result as string)
            reader.readAsDataURL(file)
            setErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors.image
                return newErrors
            })
        }
    }, [])

    const removeImage = useCallback(() => {
        setFormData(prev => ({ ...prev, image: null }))
        setImagePreview(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }, [])

    // Drag and drop handlers
    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback(() => {
        setIsDragging(false)
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        const file = e.dataTransfer.files[0]
        if (file) {
            handleImageChange(file)
        }
    }, [handleImageChange])

    // Word count calculation
    const wordCount = formData.content.trim().split(/\s+/).filter(Boolean).length
    const charCount = formData.content.length
    const readTime = Math.ceil(wordCount / 200)

    // SEO preview slug
    const slug = formData.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')

    // Rendered markdown preview
    const renderedContent = parseMarkdown(formData.content)

    // Handler to create a new category
    const handleCreateCategory = useCallback(async () => {
        if (!newCategoryName.trim()) return

        setIsCreatingCategory(true)
        try {
            const response = await fetch('/api/blog/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ name: newCategoryName.trim() }),
                credentials: 'same-origin'
            })

            const result = await response.json()

            if (result.success) {
                setCategories(prev => [...prev, result.category])
                handleChange('blogCategoryId', result.category.id)
                setNewCategoryName('')
                setShowNewCategory(false)
                setToast({ type: 'success', message: 'Category created!' })
            } else {
                setToast({ type: 'error', message: result.message || 'Failed to create category.' })
            }
        } catch (error) {
            console.error('Create category error:', error)
            setToast({ type: 'error', message: 'An error occurred. Please try again.' })
        } finally {
            setIsCreatingCategory(false)
        }
    }, [newCategoryName, csrfToken, handleChange])

    // Handler to create a new series
    const handleCreateSeries = useCallback(async () => {
        if (!newSeriesTitle.trim()) return

        setIsCreatingSeries(true)
        try {
            const response = await fetch('/api/blog/series', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ title: newSeriesTitle.trim() }),
                credentials: 'same-origin'
            })

            const result = await response.json()

            if (result.success) {
                setSeries(prev => [...prev, result.series])
                handleChange('seriesId', result.series.id)
                setNewSeriesTitle('')
                setShowNewSeries(false)
                setToast({ type: 'success', message: 'Series created!' })
            } else {
                setToast({ type: 'error', message: result.message || 'Failed to create series.' })
            }
        } catch (error) {
            console.error('Create series error:', error)
            setToast({ type: 'error', message: 'An error occurred. Please try again.' })
        } finally {
            setIsCreatingSeries(false)
        }
    }, [newSeriesTitle, csrfToken, handleChange])

    // Link modal handlers
    const handleOpenLinkModal = useCallback(() => {
        setLinkText('')
        setLinkUrl('')
        setShowLinkModal(true)
    }, [])

    const handleInsertLink = useCallback(() => {
        if (linkUrl) {
            markdownEditor.insertLink(linkText || linkUrl, linkUrl)
            setShowLinkModal(false)
        }
    }, [linkText, linkUrl, markdownEditor])

    // Image modal handlers
    const handleOpenImageModal = useCallback(() => {
        setImageAlt('')
        setImageUrl('')
        setShowImageModal(true)
    }, [])

    const handleInsertImage = useCallback(() => {
        if (imageUrl) {
            markdownEditor.insertImage(imageAlt || 'image', imageUrl)
            setShowImageModal(false)
        }
    }, [imageAlt, imageUrl, markdownEditor])

    // Form validation
    const validateForm = useCallback((): boolean => {
        const newErrors: Record<string, string> = {}

        if (!formData.title.trim()) {
            newErrors.title = 'Title is required.'
        } else if (formData.title.length > 200) {
            newErrors.title = 'Title must be 200 characters or less.'
        }

        if (!formData.content.trim()) {
            newErrors.content = 'Content is required.'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }, [formData])

    // Form submission
    const handleSubmit = useCallback(async (publish: boolean) => {
        if (!validateForm()) return

        setIsSubmitting(true)
        setFormData(prev => ({ ...prev, isPublished: publish }))

        try {
            const submitData = new FormData()
            submitData.append('csrf_token', csrfToken)
            submitData.append('title', formData.title)
            submitData.append('content', formData.content)
            submitData.append('category', formData.category)
            submitData.append('blog_category_id', String(formData.blogCategoryId))
            submitData.append('tags_input', formData.tags.join(','))
            submitData.append('is_featured', String(formData.isFeatured))
            submitData.append('publish_at', formData.publishAt)
            submitData.append('meta_description', formData.metaDescription)
            submitData.append('series_id', String(formData.seriesId))
            submitData.append('series_order', String(formData.seriesOrder))
            submitData.append('is_published', String(publish))

            if (formData.image) {
                submitData.append('image', formData.image)
            }

            const response = await fetch(apiEndpoint, {
                method: 'POST',
                body: submitData,
                credentials: 'same-origin'
            })

            const result = await response.json()

            if (result.success) {
                setToast({ type: 'success', message: publish ? 'Post published successfully!' : 'Draft saved successfully!' })
                setTimeout(() => {
                    window.location.href = redirectUrl
                }, 1500)
            } else {
                setErrors(result.errors || {})
                setToast({ type: 'error', message: result.message || 'Failed to save post.' })
            }
        } catch (error) {
            console.error('Submit error:', error)
            setToast({ type: 'error', message: 'An error occurred. Please try again.' })
        } finally {
            setIsSubmitting(false)
        }
    }, [formData, csrfToken, apiEndpoint, redirectUrl, validateForm])

    return (
        <div className="blog-editor-wrapper">
            {/* Breadcrumb */}
            <nav className="editor-breadcrumb">
                <a href="/blog/manage">Manage Posts</a> &gt; <span>New Post</span>
            </nav>

            {/* Header */}
            <div className="blog-editor-header">
                <h1><i className="fas fa-pen-fancy"></i> Create New Post</h1>
            </div>

            {/* Two Column Layout */}
            <div className="blog-editor-layout">
                {/* Main Editor */}
                <div className="blog-editor-main">
                    {/* Title */}
                    <div className="editor-panel" style={{ position: 'relative' }}>
                        <div className="editor-panel-body">
                            <div className="title-input-wrapper">
                                <input
                                    type="text"
                                    className="title-input"
                                    placeholder="Enter your post title..."
                                    value={formData.title}
                                    onChange={(e) => handleChange('title', e.target.value)}
                                    maxLength={200}
                                />
                                <span className={`title-char-count ${formData.title.length > 180 ? (formData.title.length > 200 ? 'error' : 'warning') : ''}`}>
                                    {formData.title.length}/200
                                </span>
                            </div>
                            {errors.title && <span className="form-error" style={{ color: '#e74c3c', fontSize: '0.85rem', marginTop: '0.5rem', display: 'block' }}>{errors.title}</span>}
                        </div>
                    </div>

                    {/* Content Editor */}
                    <div className="editor-panel" style={{ position: 'relative' }}>
                        <div className="editor-panel-header">
                            <span className="editor-panel-title"><i className="fas fa-align-left"></i> Content</span>
                            {/* View Mode Toggle */}
                            <div className="view-mode-toggle">
                                <button
                                    type="button"
                                    className={`view-mode-btn ${viewMode === 'edit' ? 'active' : ''}`}
                                    onClick={() => setViewMode('edit')}
                                    title="Editor only"
                                >
                                    <i className="fas fa-edit"></i>
                                </button>
                                <button
                                    type="button"
                                    className={`view-mode-btn ${viewMode === 'split' ? 'active' : ''}`}
                                    onClick={() => setViewMode('split')}
                                    title="Split view"
                                >
                                    <i className="fas fa-columns"></i>
                                </button>
                                <button
                                    type="button"
                                    className={`view-mode-btn ${viewMode === 'preview' ? 'active' : ''}`}
                                    onClick={() => setViewMode('preview')}
                                    title="Preview only"
                                >
                                    <i className="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>

                        {/* Toolbar */}
                        <div className="content-toolbar">
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('bold')} title="Bold (Ctrl+B)">
                                <i className="fas fa-bold"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('italic')} title="Italic (Ctrl+I)">
                                <i className="fas fa-italic"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('strikethrough')} title="Strikethrough">
                                <i className="fas fa-strikethrough"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={handleOpenLinkModal} title="Insert Link (Ctrl+K)">
                                <i className="fas fa-link"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={handleOpenImageModal} title="Insert Image">
                                <i className="fas fa-image"></i>
                            </button>
                            <span className="toolbar-separator"></span>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.cycleHeading()} title="Heading (Ctrl+H)">
                                <i className="fas fa-heading"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('quote')} title="Quote">
                                <i className="fas fa-quote-right"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('code')} title="Inline Code">
                                <i className="fas fa-code"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('codeBlock')} title="Code Block">
                                <i className="fas fa-file-code"></i>
                            </button>
                            <span className="toolbar-separator"></span>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('ul')} title="Bulleted List">
                                <i className="fas fa-list-ul"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('ol')} title="Numbered List">
                                <i className="fas fa-list-ol"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('task')} title="Task List">
                                <i className="fas fa-tasks"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.applyAction('hr')} title="Horizontal Rule">
                                <i className="fas fa-minus"></i>
                            </button>
                            <span className="toolbar-separator"></span>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.undo()} title="Undo (Ctrl+Z)" disabled={!markdownEditor.canUndo}>
                                <i className="fas fa-undo"></i>
                            </button>
                            <button type="button" className="toolbar-btn" onClick={() => markdownEditor.redo()} title="Redo (Ctrl+Shift+Z)" disabled={!markdownEditor.canRedo}>
                                <i className="fas fa-redo"></i>
                            </button>
                        </div>

                        {/* Editor/Preview Split */}
                        <div className={`content-split-wrapper view-${viewMode}`}>
                            {/* Editor Pane */}
                            {(viewMode === 'edit' || viewMode === 'split') && (
                                <div className="content-editor-pane">
                                    <textarea
                                        ref={markdownEditor.setTextareaRef}
                                        className="content-textarea"
                                        placeholder="Write your post content here... Markdown is supported."
                                        value={markdownEditor.content}
                                        onChange={markdownEditor.handleChange}
                                        onKeyDown={markdownEditor.handleKeyDown}
                                        onScroll={handleEditorScroll}
                                    />
                                </div>
                            )}

                            {/* Preview Pane */}
                            {(viewMode === 'preview' || viewMode === 'split') && (
                                <div className="content-preview-pane" ref={previewRef}>
                                    <div
                                        className="markdown-preview"
                                        dangerouslySetInnerHTML={{ __html: renderedContent || '<p class="md-placeholder">Your preview will appear here...</p>' }}
                                    />
                                </div>
                            )}
                        </div>

                        <div className="content-footer">
                            <div className="word-count">
                                <span>{wordCount} words</span>
                                <span>{charCount} characters</span>
                                <span>~{readTime} min read</span>
                            </div>
                            <div className="keyboard-hints">
                                <span>Ctrl+B Bold</span>
                                <span>Ctrl+I Italic</span>
                                <span>Ctrl+K Link</span>
                            </div>
                        </div>
                        {errors.content && <span className="form-error" style={{ color: '#e74c3c', fontSize: '0.85rem', padding: '0 1.5rem 1rem', display: 'block' }}>{errors.content}</span>}
                    </div>

                    {/* Featured Image */}
                    <div className="editor-panel" style={{ position: 'relative' }}>
                        <div className="editor-panel-header">
                            <span className="editor-panel-title"><i className="fas fa-image"></i> Featured Image</span>
                        </div>
                        <div className="editor-panel-body">
                            <div
                                className={`image-upload-zone ${isDragging ? 'drag-over' : ''} ${imagePreview ? 'has-image' : ''}`}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                            >
                                {imagePreview ? (
                                    <>
                                        <img src={imagePreview} alt="Preview" className="image-preview" />
                                        <div className="image-preview-overlay">
                                            <button type="button" className="image-action-btn" onClick={() => fileInputRef.current?.click()}>
                                                <i className="fas fa-sync-alt"></i> Replace
                                            </button>
                                            <button type="button" className="image-action-btn danger" onClick={removeImage}>
                                                <i className="fas fa-trash"></i> Remove
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <i className="fas fa-cloud-upload-alt image-upload-icon"></i>
                                        <p className="image-upload-text">Drag and drop an image or click to browse</p>
                                        <p className="image-upload-hint">PNG, JPG, JPEG up to 5MB</p>
                                    </>
                                )}
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    className="image-upload-input"
                                    accept="image/png,image/jpeg,image/jpg"
                                    onChange={(e) => handleImageChange(e.target.files?.[0] || null)}
                                />
                            </div>
                            {errors.image && <span className="form-error" style={{ color: '#e74c3c', fontSize: '0.85rem', marginTop: '0.75rem', display: 'block' }}>{errors.image}</span>}
                        </div>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="blog-editor-sidebar">
                    {/* Publish Panel */}
                    <div className="sidebar-panel">
                        <div className="sidebar-panel-header">
                            <span className="sidebar-panel-title"><i className="fas fa-paper-plane"></i> Publish</span>
                        </div>
                        <div className="sidebar-panel-body">
                            <div className="toggle-wrapper">
                                <span className="toggle-label">Publish immediately</span>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={formData.isPublished}
                                        onChange={(e) => handleChange('isPublished', e.target.checked)}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="editor-form-group">
                                <label className="editor-label">Schedule for later</label>
                                <div className="schedule-datetime">
                                    <input
                                        type="datetime-local"
                                        className="editor-input"
                                        value={formData.publishAt}
                                        onChange={(e) => handleChange('publishAt', e.target.value)}
                                        disabled={formData.isPublished}
                                    />
                                </div>
                            </div>

                            <div className="toggle-wrapper">
                                <span className="toggle-label">Featured post</span>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={formData.isFeatured}
                                        onChange={(e) => handleChange('isFeatured', e.target.checked)}
                                    />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>
                        </div>
                        <div className="editor-actions">
                            <button
                                type="button"
                                className="action-btn action-btn-secondary"
                                onClick={() => handleSubmit(false)}
                                disabled={isSubmitting}
                            >
                                <i className="fas fa-save"></i> Save Draft
                            </button>
                            <button
                                type="button"
                                className="action-btn action-btn-success"
                                onClick={() => handleSubmit(true)}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? (
                                    <><i className="fas fa-spinner fa-spin"></i> Publishing...</>
                                ) : (
                                    <><i className="fas fa-check"></i> Publish</>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Category & Tags */}
                    <div className="sidebar-panel">
                        <div className="sidebar-panel-header">
                            <span className="sidebar-panel-title"><i className="fas fa-folder"></i> Organization</span>
                        </div>
                        <div className="sidebar-panel-body">
                            <div className="editor-form-group">
                                <label className="editor-label">Category</label>
                                {!showNewCategory ? (
                                    <>
                                        <select
                                            className="editor-select"
                                            value={formData.blogCategoryId}
                                            onChange={(e) => handleChange('blogCategoryId', Number(e.target.value))}
                                        >
                                            <option value={0}>-- Select Category --</option>
                                            {categories.map(cat => (
                                                <option key={cat.id} value={cat.id}>{cat.name}</option>
                                            ))}
                                        </select>
                                        <button
                                            type="button"
                                            className="inline-create-btn"
                                            onClick={() => setShowNewCategory(true)}
                                        >
                                            <i className="fas fa-plus"></i> Create New Category
                                        </button>
                                    </>
                                ) : (
                                    <div className="inline-create-form">
                                        <input
                                            type="text"
                                            className="editor-input"
                                            placeholder="New category name..."
                                            value={newCategoryName}
                                            onChange={(e) => setNewCategoryName(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleCreateCategory()}
                                            autoFocus
                                        />
                                        <div className="inline-create-actions">
                                            <button
                                                type="button"
                                                className="inline-action-btn success"
                                                onClick={handleCreateCategory}
                                                disabled={isCreatingCategory || !newCategoryName.trim()}
                                            >
                                                {isCreatingCategory ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-check"></i>}
                                            </button>
                                            <button
                                                type="button"
                                                className="inline-action-btn cancel"
                                                onClick={() => { setShowNewCategory(false); setNewCategoryName(''); }}
                                            >
                                                <i className="fas fa-times"></i>
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="editor-form-group">
                                <label className="editor-label">Tags</label>
                                <div className="tags-input-wrapper">
                                    {formData.tags.map(tag => (
                                        <span key={tag} className="tag-chip">
                                            {tag}
                                            <button type="button" className="tag-remove" onClick={() => removeTag(tag)}>
                                                <i className="fas fa-times"></i>
                                            </button>
                                        </span>
                                    ))}
                                    <input
                                        type="text"
                                        className="tags-input"
                                        placeholder={formData.tags.length === 0 ? "Add tags..." : ""}
                                        value={tagInput}
                                        onChange={(e) => setTagInput(e.target.value)}
                                        onKeyDown={handleTagKeyDown}
                                    />
                                </div>
                            </div>

                            <div className="editor-form-group">
                                <label className="editor-label">Post Series</label>
                                {!showNewSeries ? (
                                    <>
                                        <select
                                            className="editor-select"
                                            value={formData.seriesId}
                                            onChange={(e) => handleChange('seriesId', Number(e.target.value))}
                                        >
                                            <option value={0}>-- Not Part of Series --</option>
                                            {series.map(s => (
                                                <option key={s.id} value={s.id}>{s.title}</option>
                                            ))}
                                        </select>
                                        <button
                                            type="button"
                                            className="inline-create-btn"
                                            onClick={() => setShowNewSeries(true)}
                                        >
                                            <i className="fas fa-plus"></i> Create New Series
                                        </button>
                                    </>
                                ) : (
                                    <div className="inline-create-form">
                                        <input
                                            type="text"
                                            className="editor-input"
                                            placeholder="New series title..."
                                            value={newSeriesTitle}
                                            onChange={(e) => setNewSeriesTitle(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleCreateSeries()}
                                            autoFocus
                                        />
                                        <div className="inline-create-actions">
                                            <button
                                                type="button"
                                                className="inline-action-btn success"
                                                onClick={handleCreateSeries}
                                                disabled={isCreatingSeries || !newSeriesTitle.trim()}
                                            >
                                                {isCreatingSeries ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-check"></i>}
                                            </button>
                                            <button
                                                type="button"
                                                className="inline-action-btn cancel"
                                                onClick={() => { setShowNewSeries(false); setNewSeriesTitle(''); }}
                                            >
                                                <i className="fas fa-times"></i>
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {formData.seriesId > 0 && (
                                <div className="editor-form-group">
                                    <label className="editor-label">Order in Series</label>
                                    <input
                                        type="number"
                                        className="editor-input"
                                        min={0}
                                        value={formData.seriesOrder}
                                        onChange={(e) => handleChange('seriesOrder', Number(e.target.value))}
                                    />
                                </div>
                            )}
                        </div>
                    </div>

                    {/* SEO */}
                    <div className="sidebar-panel">
                        <div className="sidebar-panel-header">
                            <span className="sidebar-panel-title"><i className="fas fa-search"></i> SEO</span>
                        </div>
                        <div className="sidebar-panel-body">
                            <div className="editor-form-group">
                                <label className="editor-label">Meta Description</label>
                                <textarea
                                    className="editor-textarea"
                                    rows={3}
                                    maxLength={300}
                                    placeholder="Brief description for search engines..."
                                    value={formData.metaDescription}
                                    onChange={(e) => handleChange('metaDescription', e.target.value)}
                                />
                                <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.25rem', display: 'block' }}>
                                    {formData.metaDescription.length}/300
                                </span>
                            </div>

                            <div className="seo-preview">
                                <span className="seo-preview-label">Search Preview</span>
                                <div className="seo-preview-title">{formData.title || 'Your Post Title'}</div>
                                <div className="seo-preview-url">/blog/{slug || 'your-post-slug'}</div>
                                <div className="seo-preview-desc">
                                    {formData.metaDescription || formData.content.slice(0, 150) || 'Your post description will appear here...'}
                                    {(formData.metaDescription.length > 150 || formData.content.length > 150) && '...'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Link Modal */}
            {showLinkModal && (
                <div className="editor-modal-overlay" onClick={() => setShowLinkModal(false)}>
                    <div className="editor-modal" onClick={e => e.stopPropagation()}>
                        <div className="editor-modal-header">
                            <h3><i className="fas fa-link"></i> Insert Link</h3>
                            <button type="button" className="modal-close-btn" onClick={() => setShowLinkModal(false)}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>
                        <div className="editor-modal-body">
                            <div className="editor-form-group">
                                <label className="editor-label">Link Text</label>
                                <input
                                    type="text"
                                    className="editor-input"
                                    placeholder="Display text..."
                                    value={linkText}
                                    onChange={(e) => setLinkText(e.target.value)}
                                    autoFocus
                                />
                            </div>
                            <div className="editor-form-group">
                                <label className="editor-label">URL</label>
                                <input
                                    type="url"
                                    className="editor-input"
                                    placeholder="https://..."
                                    value={linkUrl}
                                    onChange={(e) => setLinkUrl(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleInsertLink()}
                                />
                            </div>
                        </div>
                        <div className="editor-modal-footer">
                            <button type="button" className="action-btn action-btn-secondary" onClick={() => setShowLinkModal(false)}>
                                Cancel
                            </button>
                            <button type="button" className="action-btn action-btn-primary" onClick={handleInsertLink} disabled={!linkUrl}>
                                <i className="fas fa-check"></i> Insert Link
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Image Modal */}
            {showImageModal && (
                <div className="editor-modal-overlay" onClick={() => setShowImageModal(false)}>
                    <div className="editor-modal" onClick={e => e.stopPropagation()}>
                        <div className="editor-modal-header">
                            <h3><i className="fas fa-image"></i> Insert Image</h3>
                            <button type="button" className="modal-close-btn" onClick={() => setShowImageModal(false)}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>
                        <div className="editor-modal-body">
                            <div className="editor-form-group">
                                <label className="editor-label">Alt Text</label>
                                <input
                                    type="text"
                                    className="editor-input"
                                    placeholder="Image description..."
                                    value={imageAlt}
                                    onChange={(e) => setImageAlt(e.target.value)}
                                    autoFocus
                                />
                            </div>
                            <div className="editor-form-group">
                                <label className="editor-label">Image URL</label>
                                <input
                                    type="url"
                                    className="editor-input"
                                    placeholder="https://..."
                                    value={imageUrl}
                                    onChange={(e) => setImageUrl(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleInsertImage()}
                                />
                            </div>
                        </div>
                        <div className="editor-modal-footer">
                            <button type="button" className="action-btn action-btn-secondary" onClick={() => setShowImageModal(false)}>
                                Cancel
                            </button>
                            <button type="button" className="action-btn action-btn-primary" onClick={handleInsertImage} disabled={!imageUrl}>
                                <i className="fas fa-check"></i> Insert Image
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {toast && (
                <div className={`editor-toast ${toast.type}`}>
                    <i className={`editor-toast-icon fas fa-${toast.type === 'success' ? 'check-circle' : 'exclamation-circle'}`}></i>
                    <span className="editor-toast-message">{toast.message}</span>
                </div>
            )}
        </div>
    )
}

export default BlogPostEditor
