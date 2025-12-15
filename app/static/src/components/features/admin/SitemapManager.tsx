/**
 * SitemapManager Component
 * 
 * Admin component for managing sitemap generation:
 * - View URL counts by type (pages, posts, products, categories)
 * - Generate/regenerate sitemap
 * - Submit to search engines
 * - Preview sitemap URLs
 */

import { useState, useEffect, useCallback } from 'react'
import {
    Globe, FileText, ShoppingBag, FolderOpen, RefreshCw,
    Send, Eye, EyeOff, CheckCircle, XCircle, Clock, Loader2,
    ExternalLink, FileCode
} from 'lucide-react'
import api from '../../../api'
import { useToast } from '../../ui/toast'
import './SitemapManager.css'

// =============================================================================
// Types
// =============================================================================

interface SitemapStats {
    pages: number
    posts: number
    products: number
    categories: number
    static_routes: number
    total: number
    file_exists: boolean
    file_size: number | null
    last_modified: string | null
}

interface SitemapUrl {
    loc: string
    lastmod: string | null
    priority: string | null
    changefreq: string | null
}

interface SubmitResult {
    success: boolean
    status_code?: number
    error?: string
}

interface SitemapManagerProps {
    statsUrl?: string
    previewUrl?: string
    generateUrl?: string
    submitUrl?: string
    className?: string
}

// =============================================================================
// Stat Card Component
// =============================================================================

interface StatCardProps {
    title: string
    value: number
    icon: React.ReactNode
    color: string
}

function StatCard({ title, value, icon, color }: StatCardProps) {
    return (
        <div className="sitemap-stat-card">
            <div className="stat-icon" style={{ background: color }}>
                {icon}
            </div>
            <div className="stat-content">
                <span className="stat-value">{value}</span>
                <span className="stat-label">{title}</span>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function SitemapManager({
    statsUrl = '/admin/api/sitemap/stats',
    previewUrl = '/admin/api/sitemap/preview',
    generateUrl = '/admin/generate-sitemap',
    submitUrl = '/admin/api/sitemap/submit',
    className = ''
}: SitemapManagerProps) {
    const [stats, setStats] = useState<SitemapStats | null>(null)
    const [urls, setUrls] = useState<SitemapUrl[]>([])
    const [showPreview, setShowPreview] = useState(false)
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [previewLoading, setPreviewLoading] = useState(false)
    const [submitResults, setSubmitResults] = useState<{ google: SubmitResult | null, bing: SubmitResult | null } | null>(null)

    const toast = useToast()

    // Fetch sitemap stats
    const fetchStats = useCallback(async () => {
        try {
            const response = await api.get(statsUrl)
            setStats(response.data)
        } catch (error) {
            console.error('Error fetching sitemap stats:', error)
            toast.error('Failed to load sitemap stats')
        } finally {
            setLoading(false)
        }
    }, [statsUrl, toast])

    useEffect(() => {
        fetchStats()
    }, [fetchStats])

    // Generate sitemap
    const handleGenerate = async () => {
        setGenerating(true)
        try {
            const response = await api.post(generateUrl, {}, {
                headers: { 'Accept': 'application/json' }
            })

            if (response.data.success) {
                toast.success('Sitemap generated successfully!')
                fetchStats() // Refresh stats
            } else {
                toast.error(response.data.error || 'Failed to generate sitemap')
            }
        } catch (error: any) {
            console.error('Error generating sitemap:', error)
            toast.error(error.response?.data?.error || 'Failed to generate sitemap')
        } finally {
            setGenerating(false)
        }
    }

    // Submit to search engines
    const handleSubmit = async () => {
        setSubmitting(true)
        setSubmitResults(null)
        try {
            const response = await api.post(submitUrl)

            if (response.data.success) {
                setSubmitResults(response.data.results)
                const googleSuccess = response.data.results.google?.success
                const bingSuccess = response.data.results.bing?.success

                if (googleSuccess && bingSuccess) {
                    toast.success('Sitemap submitted to Google and Bing!')
                } else if (googleSuccess || bingSuccess) {
                    toast.warning('Sitemap submitted (some engines may have failed)')
                } else {
                    toast.error('Failed to submit to search engines')
                }
            } else {
                toast.error(response.data.error || 'Failed to submit sitemap')
            }
        } catch (error: any) {
            console.error('Error submitting sitemap:', error)
            toast.error(error.response?.data?.error || 'Failed to submit sitemap')
        } finally {
            setSubmitting(false)
        }
    }

    // Load preview URLs
    const handleTogglePreview = async () => {
        if (!showPreview && urls.length === 0) {
            setPreviewLoading(true)
            try {
                const response = await api.get(previewUrl)
                setUrls(response.data.urls)
            } catch (error) {
                console.error('Error loading sitemap preview:', error)
                toast.error('Failed to load sitemap preview')
            } finally {
                setPreviewLoading(false)
            }
        }
        setShowPreview(!showPreview)
    }

    // Format file size
    const formatFileSize = (bytes: number | null) => {
        if (!bytes) return 'N/A'
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
    }

    // Format date
    const formatDate = (isoString: string | null) => {
        if (!isoString) return 'Never'
        const date = new Date(isoString)
        return date.toLocaleString()
    }

    if (loading) {
        return (
            <div className={`sitemap-manager ${className}`}>
                <div className="sitemap-loading">
                    <Loader2 className="spin" size={24} />
                    <span>Loading sitemap stats...</span>
                </div>
            </div>
        )
    }

    return (
        <div className={`sitemap-manager ${className}`}>
            {/* Header */}
            <div className="sitemap-header">
                <div className="sitemap-title">
                    <FileCode size={24} />
                    <h3>Sitemap Manager</h3>
                </div>
                <div className="sitemap-actions">
                    <button
                        className="sitemap-btn secondary"
                        onClick={handleTogglePreview}
                        disabled={previewLoading}
                    >
                        {previewLoading ? (
                            <Loader2 className="spin" size={16} />
                        ) : showPreview ? (
                            <EyeOff size={16} />
                        ) : (
                            <Eye size={16} />
                        )}
                        {showPreview ? 'Hide Preview' : 'Preview URLs'}
                    </button>
                    <button
                        className="sitemap-btn primary"
                        onClick={handleGenerate}
                        disabled={generating}
                    >
                        {generating ? (
                            <Loader2 className="spin" size={16} />
                        ) : (
                            <RefreshCw size={16} />
                        )}
                        {generating ? 'Generating...' : 'Regenerate'}
                    </button>
                    <button
                        className="sitemap-btn accent"
                        onClick={handleSubmit}
                        disabled={submitting || !stats?.file_exists}
                        title={!stats?.file_exists ? 'Generate sitemap first' : 'Submit to Google and Bing'}
                    >
                        {submitting ? (
                            <Loader2 className="spin" size={16} />
                        ) : (
                            <Send size={16} />
                        )}
                        {submitting ? 'Submitting...' : 'Submit to Engines'}
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="sitemap-stats-grid">
                    <StatCard
                        title="Pages"
                        value={stats.pages}
                        icon={<FileText size={20} />}
                        color="linear-gradient(135deg, #6366f1, #8b5cf6)"
                    />
                    <StatCard
                        title="Blog Posts"
                        value={stats.posts}
                        icon={<Globe size={20} />}
                        color="linear-gradient(135deg, #10b981, #059669)"
                    />
                    <StatCard
                        title="Products"
                        value={stats.products}
                        icon={<ShoppingBag size={20} />}
                        color="linear-gradient(135deg, #f59e0b, #d97706)"
                    />
                    <StatCard
                        title="Categories"
                        value={stats.categories}
                        icon={<FolderOpen size={20} />}
                        color="linear-gradient(135deg, #ec4899, #db2777)"
                    />
                </div>
            )}

            {/* File Info */}
            {stats && (
                <div className="sitemap-file-info">
                    <div className="file-info-item">
                        <Clock size={16} />
                        <span>Last Generated: {formatDate(stats.last_modified)}</span>
                    </div>
                    <div className="file-info-item">
                        <FileCode size={16} />
                        <span>Size: {formatFileSize(stats.file_size)}</span>
                    </div>
                    <div className="file-info-item">
                        <Globe size={16} />
                        <span>Total URLs: {stats.total}</span>
                    </div>
                    {stats.file_exists && (
                        <a href="/sitemap.xml" target="_blank" rel="noopener noreferrer" className="file-info-link">
                            <ExternalLink size={16} />
                            <span>View sitemap.xml</span>
                        </a>
                    )}
                </div>
            )}

            {/* Submit Results */}
            {submitResults && (
                <div className="sitemap-submit-results">
                    <div className={`submit-result ${submitResults.google?.success ? 'success' : 'error'}`}>
                        {submitResults.google?.success ? <CheckCircle size={16} /> : <XCircle size={16} />}
                        <span>Google: {submitResults.google?.success ? 'Submitted' : 'Failed'}</span>
                    </div>
                    <div className={`submit-result ${submitResults.bing?.success ? 'success' : 'error'}`}>
                        {submitResults.bing?.success ? <CheckCircle size={16} /> : <XCircle size={16} />}
                        <span>Bing: {submitResults.bing?.success ? 'Submitted' : 'Failed'}</span>
                    </div>
                </div>
            )}

            {/* URL Preview */}
            {showPreview && (
                <div className="sitemap-preview">
                    <div className="preview-header">
                        <h4>Sitemap URLs ({urls.length})</h4>
                    </div>
                    <div className="preview-list">
                        {urls.map((url, index) => (
                            <div key={index} className="preview-item">
                                <a href={url.loc} target="_blank" rel="noopener noreferrer">
                                    {url.loc}
                                </a>
                                <div className="preview-meta">
                                    {url.priority && <span className="meta-badge">Priority: {url.priority}</span>}
                                    {url.changefreq && <span className="meta-badge">{url.changefreq}</span>}
                                    {url.lastmod && <span className="meta-date">Updated: {url.lastmod}</span>}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default SitemapManager
