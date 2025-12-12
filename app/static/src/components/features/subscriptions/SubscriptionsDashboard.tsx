/**
 * SubscriptionsDashboard Component - Enterprise Level Design
 * 
 * React version of the subscriptions page with premium glassmorphism design,
 * animated KPI cards, and responsive subscription management.
 */

import { useState, useEffect, useRef } from 'react'
import {
    CreditCard, RefreshCw, ExternalLink, Store,
    AlertTriangle, CheckCircle, Clock, XCircle
} from 'lucide-react'
import { Spinner } from '../../ui/spinner'

// =============================================================================
// Types
// =============================================================================

interface Subscription {
    id: number
    product_name: string
    product_description: string
    status: string
    cancel_at_period_end: boolean
    current_period_end: string | null
    created_at: string | null
}

interface Stats {
    active: number
    trialing: number
    past_due: number
    canceled: number
}

interface SubscriptionsDashboardProps {
    apiUrl?: string
    portalUrl?: string
    shopUrl?: string
    className?: string
}

// =============================================================================
// Animated Counter Hook
// =============================================================================

function useAnimatedCounter(endValue: number, duration: number = 1000) {
    const [value, setValue] = useState(0)
    const prevValue = useRef(0)

    useEffect(() => {
        const startValue = prevValue.current
        const startTime = performance.now()

        const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime
            const progress = Math.min(elapsed / duration, 1)
            const easeOut = 1 - Math.pow(1 - progress, 3)
            const current = startValue + (endValue - startValue) * easeOut
            setValue(Math.round(current))

            if (progress < 1) {
                requestAnimationFrame(animate)
            } else {
                prevValue.current = endValue
            }
        }

        requestAnimationFrame(animate)
    }, [endValue, duration])

    return value
}

// =============================================================================
// KPI Card Component
// =============================================================================

interface KPICardProps {
    title: string
    value: number
    icon: React.ReactNode
    iconColor: string
    accentGradient: string
    delay?: number
}

function KPICard({ title, value, icon, iconColor, accentGradient, delay = 0 }: KPICardProps) {
    const [visible, setVisible] = useState(false)
    const animatedValue = useAnimatedCounter(value, 1200)

    useEffect(() => {
        const timer = setTimeout(() => setVisible(true), delay * 100)
        return () => clearTimeout(timer)
    }, [delay])

    return (
        <div
            className={`subs-kpi-card ${visible ? 'visible' : ''}`}
            style={{ '--accent-gradient': accentGradient } as React.CSSProperties}
        >
            <div className="subs-kpi-header">
                <span className="subs-kpi-title">{title}</span>
                <div className="subs-kpi-icon" style={{ background: `${iconColor}15`, color: iconColor }}>
                    {icon}
                </div>
            </div>
            <div className="subs-kpi-value">{animatedValue}</div>
        </div>
    )
}

// =============================================================================
// Subscription Card Component
// =============================================================================

interface SubscriptionCardProps {
    subscription: Subscription
    onCancel: (id: number) => void
    canceling: number | null
}

function SubscriptionCard({ subscription, onCancel, canceling }: SubscriptionCardProps) {
    const getStatusConfig = (status: string, cancelAtPeriodEnd: boolean) => {
        if (cancelAtPeriodEnd) {
            return { label: 'Canceling', className: 'warning', icon: <Clock size={14} /> }
        }
        switch (status) {
            case 'active':
                return { label: 'Active', className: 'success', icon: <CheckCircle size={14} /> }
            case 'trialing':
                return { label: 'Trialing', className: 'info', icon: <Clock size={14} /> }
            case 'past_due':
                return { label: 'Past Due', className: 'danger', icon: <AlertTriangle size={14} /> }
            case 'canceled':
                return { label: 'Canceled', className: 'muted', icon: <XCircle size={14} /> }
            default:
                return { label: status, className: 'muted', icon: null }
        }
    }

    const statusConfig = getStatusConfig(subscription.status, subscription.cancel_at_period_end)

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return 'N/A'
        try {
            return new Date(dateStr).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric'
            })
        } catch {
            return 'N/A'
        }
    }

    const handleCancel = () => {
        if (confirm('Cancel this subscription? You will keep access until the end of your billing period.')) {
            onCancel(subscription.id)
        }
    }

    return (
        <div className="subs-card">
            <div className="subs-card-header">
                <div className="subs-card-title">
                    <CreditCard size={20} />
                    <h3>{subscription.product_name}</h3>
                </div>
                <span className={`subs-status-badge ${statusConfig.className}`}>
                    {statusConfig.icon}
                    {statusConfig.label}
                </span>
            </div>

            {subscription.product_description && (
                <p className="subs-card-description">{subscription.product_description}</p>
            )}

            <div className="subs-card-details">
                {subscription.current_period_end && (
                    <div className="subs-detail-item">
                        <span className="subs-detail-label">
                            {subscription.cancel_at_period_end ? 'Access until' : 'Next billing'}
                        </span>
                        <span className="subs-detail-value">
                            {formatDate(subscription.current_period_end)}
                        </span>
                    </div>
                )}
                <div className="subs-detail-item">
                    <span className="subs-detail-label">Subscribed</span>
                    <span className="subs-detail-value">{formatDate(subscription.created_at)}</span>
                </div>
            </div>

            <div className="subs-card-footer">
                {subscription.status === 'active' && !subscription.cancel_at_period_end ? (
                    <button
                        className="subs-btn subs-btn-cancel"
                        onClick={handleCancel}
                        disabled={canceling === subscription.id}
                    >
                        {canceling === subscription.id ? (
                            <>
                                <Spinner size="sm" />
                                Canceling...
                            </>
                        ) : (
                            'Cancel Subscription'
                        )}
                    </button>
                ) : subscription.cancel_at_period_end ? (
                    <span className="subs-cancel-notice">
                        <Clock size={14} />
                        Will cancel at period end
                    </span>
                ) : (
                    <span className="subs-status-notice">{statusConfig.label}</span>
                )}
            </div>
        </div>
    )
}

// =============================================================================
// Empty State Component
// =============================================================================

function EmptyState({ shopUrl }: { shopUrl: string }) {
    return (
        <div className="subs-empty-state">
            <div className="subs-empty-icon">
                <CreditCard size={64} />
            </div>
            <h2>No Active Subscriptions</h2>
            <p>You don't have any subscriptions yet. Browse our products to find subscription plans that suit your needs.</p>
            <a href={shopUrl} className="subs-btn subs-btn-primary">
                <Store size={18} />
                Browse Products
            </a>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function SubscriptionsDashboard({
    apiUrl = '/account/subscriptions/api',
    portalUrl = '/account/subscriptions/portal',
    shopUrl = '/shop',
    className = ''
}: SubscriptionsDashboardProps) {
    const [loading, setLoading] = useState(true)
    const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
    const [stats, setStats] = useState<Stats>({ active: 0, trialing: 0, past_due: 0, canceled: 0 })
    const [csrfToken, setCsrfToken] = useState('')
    const [canceling, setCanceling] = useState<number | null>(null)
    const [error, setError] = useState<string | null>(null)

    const fetchSubscriptions = async () => {
        try {
            const response = await fetch(apiUrl)
            if (!response.ok) throw new Error('Failed to load subscriptions')
            const data = await response.json()
            setSubscriptions(data.subscriptions || [])
            setStats(data.stats || { active: 0, trialing: 0, past_due: 0, canceled: 0 })
            setCsrfToken(data.csrf_token || '')
        } catch (err) {
            setError('Failed to load subscriptions. Please refresh the page.')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchSubscriptions()
    }, [apiUrl])

    const handleCancel = async (subscriptionId: number) => {
        setCanceling(subscriptionId)
        try {
            const formData = new FormData()
            formData.append('csrf_token', csrfToken)

            const response = await fetch(`/account/subscriptions/${subscriptionId}/cancel`, {
                method: 'POST',
                body: formData
            })

            if (response.redirected) {
                // Refresh data after redirect
                await fetchSubscriptions()
            } else if (!response.ok) {
                throw new Error('Failed to cancel subscription')
            } else {
                await fetchSubscriptions()
            }
        } catch (err) {
            setError('Failed to cancel subscription. Please try again.')
            console.error(err)
        } finally {
            setCanceling(null)
        }
    }

    if (loading) {
        return (
            <div className="subs-dashboard-loading">
                <Spinner size="lg" />
                <span>Loading your subscriptions...</span>
            </div>
        )
    }

    if (error) {
        return (
            <div className="subs-dashboard-error">
                <AlertTriangle size={48} />
                <p>{error}</p>
                <button onClick={() => { setError(null); setLoading(true); fetchSubscriptions() }} className="subs-btn subs-btn-primary">
                    <RefreshCw size={18} />
                    Retry
                </button>
            </div>
        )
    }

    const hasSubscriptions = subscriptions.length > 0

    return (
        <div className={`subs-dashboard ${className}`}>
            {/* Header */}
            <div className="subs-header">
                <div className="subs-header-content">
                    <h1>My Subscriptions</h1>
                    <p>Manage your recurring billing and subscription plans</p>
                </div>
                <div className="subs-header-actions">
                    {hasSubscriptions && (
                        <a href={portalUrl} className="subs-btn subs-btn-primary">
                            <ExternalLink size={18} />
                            Manage in Stripe
                        </a>
                    )}
                    <a href={shopUrl} className="subs-btn subs-btn-secondary">
                        <Store size={18} />
                        Browse Products
                    </a>
                </div>
            </div>

            {hasSubscriptions ? (
                <>
                    {/* KPI Grid */}
                    <div className="subs-kpi-grid">
                        <KPICard
                            title="Active"
                            value={stats.active}
                            icon={<CheckCircle size={24} />}
                            iconColor="#10b981"
                            accentGradient="linear-gradient(90deg, #10b981 0%, #059669 100%)"
                            delay={0}
                        />
                        <KPICard
                            title="Trialing"
                            value={stats.trialing}
                            icon={<Clock size={24} />}
                            iconColor="#22d3ee"
                            accentGradient="linear-gradient(90deg, #22d3ee 0%, #06b6d4 100%)"
                            delay={1}
                        />
                        <KPICard
                            title="Past Due"
                            value={stats.past_due}
                            icon={<AlertTriangle size={24} />}
                            iconColor="#f59e0b"
                            accentGradient="linear-gradient(90deg, #f59e0b 0%, #d97706 100%)"
                            delay={2}
                        />
                        <KPICard
                            title="Canceled"
                            value={stats.canceled}
                            icon={<XCircle size={24} />}
                            iconColor="#6b7280"
                            accentGradient="linear-gradient(90deg, #6b7280 0%, #4b5563 100%)"
                            delay={3}
                        />
                    </div>

                    {/* Subscriptions Grid */}
                    <div className="subs-grid">
                        {subscriptions.map(subscription => (
                            <SubscriptionCard
                                key={subscription.id}
                                subscription={subscription}
                                onCancel={handleCancel}
                                canceling={canceling}
                            />
                        ))}
                    </div>
                </>
            ) : (
                <EmptyState shopUrl={shopUrl} />
            )}
        </div>
    )
}

export default SubscriptionsDashboard
