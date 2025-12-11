/**
 * BlogManagement React Component
 * 
 * Enterprise-level blog management dashboard with:
 * - KPI cards displaying post statistics
 * - Quick filter tabs (All, Published, Drafts, Scheduled)
 * - Search functionality
 * - Delete confirmation modal
 */

import { useState, useCallback, useMemo, useEffect } from 'react'

export interface BlogKPI {
    total: number
    published: number
    drafts: number
    scheduled: number
}

export interface BlogManagementProps {
    /** KPI data for the dashboard cards */
    kpis: BlogKPI
    /** Initial filter state */
    initialFilter?: 'all' | 'published' | 'drafts' | 'scheduled'
    /** URL for creating new post */
    newPostUrl: string
    /** Callback when filter changes */
    onFilterChange?: (filter: string) => void
    /** CSRF token for delete forms */
    csrfToken: string
}

export function BlogManagement({
    kpis,
    initialFilter = 'all',
    newPostUrl: _newPostUrl,
    onFilterChange,
    csrfToken: _csrfToken
}: BlogManagementProps) {
    // Acknowledge props used for external integration
    void _newPostUrl
    void _csrfToken
    const [activeFilter, setActiveFilter] = useState(initialFilter)
    const [searchQuery, setSearchQuery] = useState('')
    const [deleteModal, setDeleteModal] = useState<{ show: boolean; postId: number | null; postTitle: string }>({
        show: false,
        postId: null,
        postTitle: ''
    })

    // Handle filter change
    const handleFilterChange = useCallback((filter: typeof activeFilter) => {
        setActiveFilter(filter)
        onFilterChange?.(filter)

        // Filter the AdminDataTable by triggering a custom event
        const event = new CustomEvent('blog-filter-change', { detail: { filter } })
        document.dispatchEvent(event)
    }, [onFilterChange])

    // Handle search
    const handleSearch = useCallback((query: string) => {
        setSearchQuery(query)

        // Trigger search event for AdminDataTable
        const event = new CustomEvent('blog-search', { detail: { query } })
        document.dispatchEvent(event)
    }, [])

    // Show delete confirmation modal - exposed via window for AdminDataTable usage
    useEffect(() => {
        const handleShowDeleteModal = (e: CustomEvent<{ postId: number; postTitle: string }>) => {
            setDeleteModal({ show: true, postId: e.detail.postId, postTitle: e.detail.postTitle })
        }
        document.addEventListener('blog-show-delete-modal', handleShowDeleteModal as EventListener)
        return () => {
            document.removeEventListener('blog-show-delete-modal', handleShowDeleteModal as EventListener)
        }
    }, [])

    // Hide delete confirmation modal
    const hideDeleteModal = useCallback(() => {
        setDeleteModal({ show: false, postId: null, postTitle: '' })
    }, [])

    // Confirm delete
    const confirmDelete = useCallback(() => {
        if (deleteModal.postId) {
            const form = document.querySelector(`form[data-delete-post-id="${deleteModal.postId}"]`) as HTMLFormElement
            if (form) {
                form.submit()
            }
        }
        hideDeleteModal()
    }, [deleteModal.postId, hideDeleteModal])

    // KPI cards data
    const kpiCards = useMemo(() => [
        {
            title: 'Total Posts',
            value: kpis.total,
            icon: 'fas fa-file-alt',
            subtitle: 'All blog posts'
        },
        {
            title: 'Published',
            value: kpis.published,
            icon: 'fas fa-check-circle',
            subtitle: 'Live on your site'
        },
        {
            title: 'Drafts',
            value: kpis.drafts,
            icon: 'fas fa-edit',
            subtitle: 'Work in progress'
        },
        {
            title: 'Scheduled',
            value: kpis.scheduled,
            icon: 'fas fa-clock',
            subtitle: 'Queued to publish'
        }
    ], [kpis])

    // Filter tabs
    const filterTabs = useMemo(() => [
        { key: 'all', label: 'All', count: kpis.total },
        { key: 'published', label: 'Published', count: kpis.published },
        { key: 'drafts', label: 'Drafts', count: kpis.drafts },
        { key: 'scheduled', label: 'Scheduled', count: kpis.scheduled }
    ], [kpis])

    return (
        <>
            {/* KPI Grid */}
            <div className="blog-kpi-grid">
                {kpiCards.map((card, index) => (
                    <div key={index} className="blog-kpi-card">
                        <div className="blog-kpi-header">
                            <span className="blog-kpi-title">{card.title}</span>
                            <div className="blog-kpi-icon">
                                <i className={card.icon}></i>
                            </div>
                        </div>
                        <div className="blog-kpi-value">{card.value}</div>
                        <div className="blog-kpi-subtitle">{card.subtitle}</div>
                    </div>
                ))}
            </div>

            {/* Filter Bar */}
            <div className="blog-filter-bar">
                <div className="blog-filter-tabs">
                    {filterTabs.map((tab) => (
                        <button
                            key={tab.key}
                            className={`blog-filter-tab ${activeFilter === tab.key ? 'active' : ''}`}
                            onClick={() => handleFilterChange(tab.key as typeof activeFilter)}
                        >
                            {tab.label}
                            <span className="badge">{tab.count}</span>
                        </button>
                    ))}
                </div>

                <div className="blog-search-wrapper">
                    <i className="fas fa-search blog-search-icon"></i>
                    <input
                        type="text"
                        className="blog-search-input"
                        placeholder="Search posts..."
                        value={searchQuery}
                        onChange={(e) => handleSearch(e.target.value)}
                    />
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            {deleteModal.show && (
                <div className="blog-delete-modal-backdrop" onClick={hideDeleteModal}>
                    <div className="blog-delete-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="blog-delete-modal-icon">
                            <i className="fas fa-trash-alt"></i>
                        </div>
                        <h4>Delete Post?</h4>
                        <p>
                            Are you sure you want to delete "<strong>{deleteModal.postTitle}</strong>"?
                            This action cannot be undone.
                        </p>
                        <div className="blog-delete-modal-actions">
                            <button className="btn btn-secondary" onClick={hideDeleteModal}>
                                Cancel
                            </button>
                            <button className="btn btn-danger" onClick={confirmDelete}>
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

// Expose delete modal trigger globally for use by AdminDataTable action buttons
if (typeof window !== 'undefined') {
    (window as any).showBlogDeleteModal = (postId: number, postTitle: string) => {
        const event = new CustomEvent('blog-show-delete-modal', { detail: { postId, postTitle } })
        document.dispatchEvent(event)
    }
}

export default BlogManagement
