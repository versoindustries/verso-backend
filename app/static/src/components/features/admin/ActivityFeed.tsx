/**
 * ActivityFeed Component
 * 
 * Displays recent activity from audit logs in a timeline format.
 * Used in the admin dashboard to show recent admin actions.
 */

import { useState, useEffect, useCallback } from 'react'
import {
    Clock, User, FileText, ShoppingCart, Settings, Edit,
    Trash2, UserPlus, RefreshCw, AlertCircle
} from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface ActivityItem {
    id: number
    action: string
    entity_type: string
    entity_id: number | null
    details: Record<string, unknown>
    created_at: string
    user_name?: string
}

export interface ActivityFeedProps {
    /** Maximum items to display */
    limit?: number
    /** Auto-refresh interval in seconds (0 to disable) */
    refreshInterval?: number
    /** Additional class */
    className?: string
}

// =============================================================================
// Icon Mapping
// =============================================================================

function getActionIcon(action: string, entityType: string): React.ReactNode {
    const iconProps = { size: 14 }

    if (action.includes('delete')) return <Trash2 {...iconProps} />
    if (action.includes('create') || action.includes('new')) return <UserPlus {...iconProps} />
    if (action.includes('update') || action.includes('edit')) return <Edit {...iconProps} />

    switch (entityType.toLowerCase()) {
        case 'user': return <User {...iconProps} />
        case 'order': return <ShoppingCart {...iconProps} />
        case 'page': return <FileText {...iconProps} />
        case 'businessconfig': return <Settings {...iconProps} />
        default: return <Clock {...iconProps} />
    }
}

function getActionColor(action: string): string {
    if (action.includes('delete')) return '#e74c3c'
    if (action.includes('create') || action.includes('new')) return '#2ecc71'
    if (action.includes('update') || action.includes('edit')) return '#3498db'
    if (action.includes('login')) return '#9b59b6'
    return '#6366f1'
}

function formatTimeAgo(dateString: string): string {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return 'Just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
    return date.toLocaleDateString()
}

// =============================================================================
// Main Component
// =============================================================================

export function ActivityFeed({
    limit = 10,
    refreshInterval = 60,
    className = '',
}: ActivityFeedProps) {
    const [activities, setActivities] = useState<ActivityItem[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchActivities = useCallback(async () => {
        try {
            const response = await api.get<ActivityItem[]>(`/admin/api/recent-activity?limit=${limit}`)
            setActivities(response.data || [])
            setError(null)
        } catch (err) {
            console.error('Failed to fetch activities:', err)
            setError('Failed to load activity feed')
        } finally {
            setLoading(false)
        }
    }, [limit])

    useEffect(() => {
        fetchActivities()

        if (refreshInterval > 0) {
            const interval = setInterval(fetchActivities, refreshInterval * 1000)
            return () => clearInterval(interval)
        }
    }, [fetchActivities, refreshInterval])

    return (
        <div className={`activity-feed ${className}`}>
            <div className="activity-feed__header">
                <span className="activity-feed__title">
                    <Clock size={16} />
                    Recent Activity
                </span>
                <button
                    className="activity-feed__refresh"
                    onClick={fetchActivities}
                    disabled={loading}
                    title="Refresh"
                >
                    <RefreshCw size={14} className={loading ? 'spinning' : ''} />
                </button>
            </div>

            <div className="activity-feed__list">
                {error && (
                    <div className="activity-feed__error">
                        <AlertCircle size={14} />
                        {error}
                    </div>
                )}

                {!error && activities.length === 0 && !loading && (
                    <div className="activity-feed__empty">
                        No recent activity
                    </div>
                )}

                {activities.map((activity) => (
                    <div key={activity.id} className="activity-feed__item">
                        <div
                            className="activity-feed__icon"
                            style={{ backgroundColor: `${getActionColor(activity.action)}20`, color: getActionColor(activity.action) }}
                        >
                            {getActionIcon(activity.action, activity.entity_type)}
                        </div>
                        <div className="activity-feed__content">
                            <span className="activity-feed__action">
                                {activity.action.replace(/_/g, ' ')}
                                {activity.entity_type && (
                                    <span className="activity-feed__entity">
                                        {` ${activity.entity_type}`}
                                        {activity.entity_id && ` #${activity.entity_id}`}
                                    </span>
                                )}
                            </span>
                            {activity.user_name && (
                                <span className="activity-feed__user">by {activity.user_name}</span>
                            )}
                        </div>
                        <span className="activity-feed__time">
                            {formatTimeAgo(activity.created_at)}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default ActivityFeed
