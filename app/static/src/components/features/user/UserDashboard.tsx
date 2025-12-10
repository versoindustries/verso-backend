/**
 * UserDashboard Component - Enterprise Level Design
 * 
 * React version of the user dashboard with premium KPI cards, 
 * animated effects, and glassmorphism design matching admin dashboard.
 * E-commerce features conditionally displayed based on ecommerceEnabled prop.
 */

import { useState, useEffect, useRef } from 'react'
import {
    ShoppingBag, Download, Calendar, CreditCard,
    Receipt, DownloadCloud, Store, CalendarPlus,
    Bell, ChevronRight, TrendingUp, TrendingDown,
    User, Settings, Activity, Package, Clock
} from 'lucide-react'
import { Spinner } from '../../ui/spinner'

// =============================================================================
// Types
// =============================================================================

interface Order {
    id: number
    total_amount: number
    status: string
    created_at: string
}

interface AppointmentData {
    id: number
    service_name: string
    preferred_date_time: string
    status: string
}

interface DownloadTokenData {
    id: number
    product_name: string
    download_count: number
    max_downloads: number
    is_valid: boolean
    download_url: string
}

interface NotificationData {
    id: number
    title: string
    created_at: string
    is_read: boolean
}

interface Stats {
    total_orders: number
    total_downloads: number
    upcoming_appointments: number
    active_subscriptions: number
    orders_trend?: number
    downloads_trend?: number
}

export interface UserDashboardProps {
    userName: string
    stats: Stats
    recentOrders: Order[]
    upcomingAppointments: AppointmentData[]
    downloadTokens: DownloadTokenData[]
    notifications: NotificationData[]
    ecommerceEnabled: boolean
    accountUrl?: string
    settingsUrl?: string
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

            // Ease out cubic
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
    value: string | number
    subtitle?: string
    icon: React.ReactNode
    iconColor: string
    trend?: number
    delay?: number
}

function KPICard({ title, value, subtitle, icon, iconColor, trend, delay = 0 }: KPICardProps) {
    const [visible, setVisible] = useState(false)

    useEffect(() => {
        const timer = setTimeout(() => setVisible(true), delay * 100)
        return () => clearTimeout(timer)
    }, [delay])

    return (
        <div className={`user-kpi-card ${visible ? 'visible' : ''}`} style={{ animationDelay: `${delay * 0.1}s` }}>
            <div className="user-kpi-header">
                <span className="user-kpi-title">{title}</span>
                <div className="user-kpi-icon" style={{ background: `${iconColor}15`, color: iconColor }}>
                    {icon}
                </div>
            </div>

            <div className="user-kpi-value">
                {value}
                {trend !== undefined && trend !== 0 && (
                    <span className={`user-kpi-trend ${trend > 0 ? 'up' : 'down'}`}>
                        {trend > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {Math.abs(trend)}%
                    </span>
                )}
            </div>

            {subtitle && <div className="user-kpi-subtitle">{subtitle}</div>}
        </div>
    )
}

// =============================================================================
// Activity Card Component
// =============================================================================

interface ActivityCardProps {
    title: string
    icon: React.ReactNode
    viewAllUrl: string
    emptyMessage: string
    children: React.ReactNode
    isEmpty: boolean
}

function ActivityCard({ title, icon, viewAllUrl, emptyMessage, children, isEmpty }: ActivityCardProps) {
    return (
        <div className="user-activity-card">
            <div className="user-activity-header">
                <h3>
                    {icon}
                    {title}
                </h3>
                <a href={viewAllUrl}>View All <ChevronRight size={14} /></a>
            </div>
            <div className="user-activity-body">
                {isEmpty ? (
                    <div className="user-empty-state">
                        {icon}
                        <p>{emptyMessage}</p>
                    </div>
                ) : (
                    children
                )}
            </div>
        </div>
    )
}

// =============================================================================
// Quick Action Button Component
// =============================================================================

interface QuickActionProps {
    icon: React.ReactNode
    label: string
    href: string
}

function QuickAction({ icon, label, href }: QuickActionProps) {
    return (
        <a href={href} className="user-quick-action">
            {icon}
            <span>{label}</span>
        </a>
    )
}

// =============================================================================
// Status Pill Component
// =============================================================================

function StatusPill({ status, isLink, href }: { status: string; isLink?: boolean; href?: string }) {
    const statusClass = status.toLowerCase()

    if (isLink && href) {
        return (
            <a href={href} className={`user-status-pill ${statusClass}`}>
                {status}
            </a>
        )
    }

    return <span className={`user-status-pill ${statusClass}`}>{status}</span>
}

// =============================================================================
// Main Component
// =============================================================================

export function UserDashboard({
    userName,
    stats,
    recentOrders,
    upcomingAppointments,
    downloadTokens,
    notifications,
    ecommerceEnabled,
    accountUrl = '/my-account',
    settingsUrl = '/settings',
    className = '',
}: UserDashboardProps) {
    const [loading, setLoading] = useState(true)

    // Animated values
    const animatedOrders = useAnimatedCounter(stats.total_orders, 1200)
    const animatedDownloads = useAnimatedCounter(stats.total_downloads, 1000)
    const animatedAppointments = useAnimatedCounter(stats.upcoming_appointments, 1100)
    const animatedSubscriptions = useAnimatedCounter(stats.active_subscriptions, 1300)

    useEffect(() => {
        // Simulate initial load
        const timer = setTimeout(() => setLoading(false), 300)
        return () => clearTimeout(timer)
    }, [])

    if (loading) {
        return (
            <div className="user-dashboard-loading">
                <Spinner size="lg" />
                <span>Loading your dashboard...</span>
            </div>
        )
    }

    // Build KPI cards based on ecommerce setting
    const kpiCards = []
    let kpiIndex = 0

    if (ecommerceEnabled) {
        kpiCards.push(
            <KPICard
                key="orders"
                title="Total Orders"
                value={animatedOrders}
                subtitle="Lifetime orders"
                icon={<ShoppingBag size={24} />}
                iconColor="#10b981"
                trend={stats.orders_trend}
                delay={kpiIndex++}
            />
        )
    }

    kpiCards.push(
        <KPICard
            key="downloads"
            title="Downloads"
            value={animatedDownloads}
            subtitle="Digital products"
            icon={<Download size={24} />}
            iconColor="#22d3ee"
            trend={stats.downloads_trend}
            delay={kpiIndex++}
        />
    )

    kpiCards.push(
        <KPICard
            key="appointments"
            title="Upcoming Appointments"
            value={animatedAppointments}
            subtitle="Scheduled"
            icon={<Calendar size={24} />}
            iconColor="#f59e0b"
            delay={kpiIndex++}
        />
    )

    if (ecommerceEnabled) {
        kpiCards.push(
            <KPICard
                key="subscriptions"
                title="Active Subscriptions"
                value={animatedSubscriptions}
                subtitle="Recurring plans"
                icon={<CreditCard size={24} />}
                iconColor="#a855f7"
                delay={kpiIndex++}
            />
        )
    }

    return (
        <div className={`user-dashboard ${className}`}>
            {/* Welcome Banner */}
            <div className="user-welcome-banner">
                <div className="user-welcome-content">
                    <div className="user-welcome-text">
                        <h1>Welcome back, {userName}!</h1>
                        <p>Here's an overview of your account activity.</p>
                    </div>
                    <div className="user-welcome-actions">
                        <a href={accountUrl} className="user-welcome-btn">
                            <User size={18} />
                            My Account
                        </a>
                        <a href={settingsUrl} className="user-welcome-btn secondary">
                            <Settings size={18} />
                            Settings
                        </a>
                    </div>
                </div>
                <div className="user-welcome-decoration">
                    <Activity size={120} />
                </div>
            </div>

            {/* KPI Grid */}
            <div className={`user-kpi-grid cols-${kpiCards.length}`}>
                {kpiCards}
            </div>

            {/* Quick Actions */}
            <div className="user-quick-actions">
                {ecommerceEnabled && (
                    <QuickAction
                        icon={<Receipt size={20} />}
                        label="View Order History"
                        href={`${accountUrl}?tab=orders`}
                    />
                )}
                <QuickAction
                    icon={<DownloadCloud size={20} />}
                    label="My Downloads"
                    href="/downloads"
                />
                {ecommerceEnabled && (
                    <QuickAction
                        icon={<Store size={20} />}
                        label="Browse Shop"
                        href="/shop"
                    />
                )}
                <QuickAction
                    icon={<CalendarPlus size={20} />}
                    label="Book Appointment"
                    href="/booking"
                />
                {ecommerceEnabled && (
                    <QuickAction
                        icon={<CreditCard size={20} />}
                        label="Manage Subscriptions"
                        href="/subscriptions"
                    />
                )}
            </div>

            {/* Activity Grid */}
            <div className="user-activity-grid">
                {/* Recent Orders - Only if ecommerce enabled */}
                {ecommerceEnabled && (
                    <ActivityCard
                        title="Recent Orders"
                        icon={<ShoppingBag size={18} />}
                        viewAllUrl={`${accountUrl}?tab=orders`}
                        emptyMessage="No orders yet"
                        isEmpty={recentOrders.length === 0}
                    >
                        <ul className="user-activity-list">
                            {recentOrders.map(order => (
                                <li key={order.id} className="user-activity-item">
                                    <div className="user-activity-info">
                                        <div className="user-activity-title">
                                            <Package size={14} />
                                            Order #{order.id}
                                        </div>
                                        <div className="user-activity-meta">
                                            ${(order.total_amount / 100).toFixed(2)} • {formatDate(order.created_at)}
                                        </div>
                                    </div>
                                    <StatusPill status={order.status} />
                                </li>
                            ))}
                        </ul>
                    </ActivityCard>
                )}

                {/* Upcoming Appointments */}
                <ActivityCard
                    title="Upcoming Appointments"
                    icon={<Calendar size={18} />}
                    viewAllUrl={`${accountUrl}?tab=appointments`}
                    emptyMessage="No upcoming appointments"
                    isEmpty={upcomingAppointments.length === 0}
                >
                    <ul className="user-activity-list">
                        {upcomingAppointments.map(appt => (
                            <li key={appt.id} className="user-activity-item">
                                <div className="user-activity-info">
                                    <div className="user-activity-title">
                                        <Clock size={14} />
                                        {appt.service_name || 'Appointment'}
                                    </div>
                                    <div className="user-activity-meta">
                                        {formatDateTime(appt.preferred_date_time)}
                                    </div>
                                </div>
                                <StatusPill status="Scheduled" />
                            </li>
                        ))}
                    </ul>
                </ActivityCard>

                {/* Digital Downloads */}
                <ActivityCard
                    title="Recent Downloads"
                    icon={<Download size={18} />}
                    viewAllUrl="/downloads"
                    emptyMessage="No downloads yet"
                    isEmpty={downloadTokens.length === 0}
                >
                    <ul className="user-activity-list">
                        {downloadTokens.map(token => (
                            <li key={token.id} className="user-activity-item">
                                <div className="user-activity-info">
                                    <div className="user-activity-title">
                                        <DownloadCloud size={14} />
                                        {token.product_name || 'Digital Product'}
                                    </div>
                                    <div className="user-activity-meta">
                                        {token.download_count}/{token.max_downloads} downloads
                                    </div>
                                </div>
                                {token.is_valid ? (
                                    <StatusPill status="Download" isLink href={token.download_url} />
                                ) : (
                                    <StatusPill status="Expired" />
                                )}
                            </li>
                        ))}
                    </ul>
                </ActivityCard>

                {/* Notifications */}
                <ActivityCard
                    title="Notifications"
                    icon={<Bell size={18} />}
                    viewAllUrl="/notifications"
                    emptyMessage="No new notifications"
                    isEmpty={notifications.length === 0}
                >
                    <ul className="user-activity-list">
                        {notifications.slice(0, 5).map(notif => (
                            <li key={notif.id} className={`user-activity-item ${!notif.is_read ? 'unread' : ''}`}>
                                <div className="user-activity-info">
                                    <div className="user-activity-title">
                                        <Bell size={14} />
                                        {notif.title}
                                    </div>
                                    <div className="user-activity-meta">
                                        {formatDateTime(notif.created_at)}
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                </ActivityCard>
            </div>
        </div>
    )
}

// =============================================================================
// Utility Functions
// =============================================================================

function formatDate(dateStr: string): string {
    if (!dateStr) return 'N/A'
    try {
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
        return 'N/A'
    }
}

function formatDateTime(dateStr: string): string {
    if (!dateStr) return 'TBD'
    try {
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        })
    } catch {
        return 'TBD'
    }
}

export default UserDashboard
