/**
 * AdminDashboard Component - Modern Futurist Theme
 * 
 * React version of the admin dashboard with premium KPI cards, 
 * animated charts, gradient effects, and enterprise-level design.
 */

import { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react'
import { DollarSign, UserPlus, CalendarCheck, Users, TrendingUp, TrendingDown, Activity, Zap, LayoutDashboard, Calendar, Clock } from 'lucide-react'
import api from '../../../api'
import { Spinner } from '../../ui/spinner'

// Lazy load the appointments dashboard and time cards tab
const UnifiedAppointmentsDashboard = lazy(() => import('./UnifiedAppointmentsDashboard'))
const AdminTimeCardsTab = lazy(() => import('./AdminTimeCardsTab'))

// =============================================================================
// Types
// =============================================================================

interface KPIData {
    revenue_month: number
    revenue_today: number
    revenue_trend: number
    leads_month: number
    leads_today: number
    leads_trend: number
    appointments_today: number
    active_users: number
    total_users: number
}

interface ChartData {
    labels: string[]
    revenue: number[]
    leads: number[]
    funnel: FunnelStage[]
}

interface FunnelStage {
    name: string
    count: number
    color: string
}

export interface AdminDashboardProps {
    /** Initial KPI data from server */
    kpis?: KPIData
    /** Metrics API endpoint */
    metricsUrl?: string
    /** Additional class */
    className?: string
    /** Active tab: 'overview', 'appointments', or 'timecards' */
    activeTab?: 'overview' | 'appointments' | 'timecards'
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
// KPI Card Component - Premium Design
// =============================================================================

interface KPICardProps {
    title: string
    value: string | number
    subtitle?: string
    icon: React.ReactNode
    iconColor: string
    trend?: number
    gradientClass?: string
}

function KPICard({ title, value, subtitle, icon, iconColor, trend, gradientClass = '' }: KPICardProps) {
    // Pulse animation for live data indicator
    const [pulse, setPulse] = useState(true)

    useEffect(() => {
        const interval = setInterval(() => setPulse(p => !p), 2000)
        return () => clearInterval(interval)
    }, [])

    return (
        <div className={`kpi-card ${gradientClass}`}>
            {/* Live data indicator */}
            <div className="kpi-live-indicator" style={{ opacity: pulse ? 1 : 0.5 }}>
                <Activity size={8} />
            </div>

            <div className="kpi-header">
                <span className="kpi-title">{title}</span>
                <div className="kpi-icon" style={{ background: `${iconColor}15`, color: iconColor }}>
                    {icon}
                </div>
            </div>

            <div className="kpi-value">
                {value}
                {trend !== undefined && trend !== 0 && (
                    <span className={`kpi-trend ${trend > 0 ? 'up' : 'down'}`}>
                        {trend > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {Math.abs(trend)}%
                    </span>
                )}
            </div>

            {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
        </div>
    )
}

// =============================================================================
// Funnel Chart Component - Animated Progress Bars
// =============================================================================

interface FunnelChartProps {
    stages: FunnelStage[]
}

function FunnelChart({ stages }: FunnelChartProps) {
    const maxCount = Math.max(...stages.map(s => s.count), 1)
    const [animated, setAnimated] = useState(false)

    useEffect(() => {
        const timer = setTimeout(() => setAnimated(true), 100)
        return () => clearTimeout(timer)
    }, [])

    const stageClasses: Record<string, string> = {
        'New': 'stage-new',
        'Contacted': 'stage-contacted',
        'Qualified': 'stage-qualified',
        'Proposal': 'stage-proposal',
        'Won': 'stage-won'
    }

    return (
        <div className="funnel-container">
            {stages.map((stage, index) => (
                <div key={index} className="funnel-stage">
                    <div className="funnel-stage-header">
                        <span className="funnel-stage-label">{stage.name}</span>
                        <span className="funnel-stage-value">{stage.count}</span>
                    </div>
                    <div className="funnel-bar-bg">
                        <div
                            className={`funnel-bar-fill ${stageClasses[stage.name] || ''}`}
                            style={{
                                width: animated ? `${(stage.count / maxCount) * 100}%` : '0%',
                                backgroundColor: stageClasses[stage.name] ? undefined : stage.color,
                                transitionDelay: `${index * 100}ms`
                            }}
                        >
                            <span className="funnel-bar-percent">
                                {Math.round((stage.count / maxCount) * 100)}%
                            </span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function AdminDashboard({
    kpis: initialKpis,
    metricsUrl = '/admin/dashboard_metrics',
    className = '',
    activeTab: initialTab = 'overview',
}: AdminDashboardProps) {
    const [kpis] = useState<KPIData | null>(initialKpis || null)
    const [chartData, setChartData] = useState<ChartData | null>(null)
    const [selectedDays, setSelectedDays] = useState(30)
    const [loading, setLoading] = useState(false)
    const [activeTab, setActiveTab] = useState<'overview' | 'appointments' | 'timecards'>(initialTab)
    const chartRef = useRef<any>(null)
    const leadsChartRef = useRef<any>(null)

    // Animated values
    const animatedRevenue = useAnimatedCounter(kpis?.revenue_month || 0, 1500)
    const animatedLeads = useAnimatedCounter(kpis?.leads_month || 0, 1200)
    const animatedAppointments = useAnimatedCounter(kpis?.appointments_today || 0, 1000)
    const animatedUsers = useAnimatedCounter(kpis?.active_users || 0, 1100)

    // Load metrics
    const loadMetrics = useCallback(async (days: number) => {
        setLoading(true)
        try {
            const response = await api.get(`${metricsUrl}?days=${days}`)
            if (response.ok && response.data) {
                setChartData(response.data)
            }
        } catch (err) {
            console.error('Error loading metrics:', err)
        } finally {
            setLoading(false)
        }
    }, [metricsUrl])

    // Initial load
    useEffect(() => {
        loadMetrics(selectedDays)
    }, [])

    // Chart initialization with gradient fills
    useEffect(() => {
        if (!chartData) return

        const initCharts = async () => {
            const { Chart, registerables } = await import('chart.js')
            Chart.register(...registerables)

            // Revenue Chart with gradient
            const revenueCanvas = document.getElementById('revenueChart') as HTMLCanvasElement
            if (revenueCanvas) {
                const ctx = revenueCanvas.getContext('2d')
                if (ctx) {
                    // Destroy existing chart
                    if (chartRef.current) chartRef.current.destroy()

                    // Create gradient
                    const gradient = ctx.createLinearGradient(0, 0, 0, 280)
                    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)')
                    gradient.addColorStop(1, 'rgba(16, 185, 129, 0)')

                    chartRef.current = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: chartData.labels,
                            datasets: [{
                                label: 'Revenue ($)',
                                data: chartData.revenue,
                                borderColor: '#10b981',
                                backgroundColor: gradient,
                                fill: true,
                                tension: 0.4,
                                borderWidth: 3,
                                pointBackgroundColor: '#10b981',
                                pointBorderColor: '#fff',
                                pointBorderWidth: 2,
                                pointRadius: 4,
                                pointHoverRadius: 6,
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                intersect: false,
                                mode: 'index',
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 15, 25, 0.95)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1,
                                    titleColor: '#fff',
                                    bodyColor: 'rgba(255, 255, 255, 0.8)',
                                    padding: 12,
                                    cornerRadius: 8,
                                    displayColors: false,
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        color: 'rgba(255,255,255,0.5)',
                                        font: { size: 11 }
                                    },
                                    grid: {
                                        color: 'rgba(255,255,255,0.06)',
                                    },
                                    border: { display: false }
                                },
                                x: {
                                    ticks: {
                                        color: 'rgba(255,255,255,0.5)',
                                        font: { size: 11 }
                                    },
                                    grid: { display: false },
                                    border: { display: false }
                                },
                            },
                        },
                    })
                }
            }

            // Leads Chart with gradient bars
            const leadsCanvas = document.getElementById('leadsChart') as HTMLCanvasElement
            if (leadsCanvas) {
                const ctx = leadsCanvas.getContext('2d')
                if (ctx) {
                    if (leadsChartRef.current) leadsChartRef.current.destroy()

                    const gradient = ctx.createLinearGradient(0, 0, 0, 280)
                    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)')
                    gradient.addColorStop(1, 'rgba(139, 92, 246, 0.4)')

                    leadsChartRef.current = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: chartData.labels,
                            datasets: [{
                                label: 'Leads',
                                data: chartData.leads,
                                backgroundColor: gradient,
                                borderColor: 'rgba(99, 102, 241, 0.8)',
                                borderWidth: 0,
                                borderRadius: 6,
                                borderSkipped: false,
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 15, 25, 0.95)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1,
                                    titleColor: '#fff',
                                    bodyColor: 'rgba(255, 255, 255, 0.8)',
                                    padding: 12,
                                    cornerRadius: 8,
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        color: 'rgba(255,255,255,0.5)',
                                        font: { size: 11 }
                                    },
                                    grid: {
                                        color: 'rgba(255,255,255,0.06)',
                                    },
                                    border: { display: false }
                                },
                                x: {
                                    ticks: {
                                        color: 'rgba(255,255,255,0.5)',
                                        font: { size: 11 }
                                    },
                                    grid: { display: false },
                                    border: { display: false }
                                },
                            },
                        },
                    })
                }
            }
        }

        initCharts()
    }, [chartData])

    const handleDaysChange = (days: number) => {
        setSelectedDays(days)
        loadMetrics(days)
    }

    if (!kpis && loading) {
        return (
            <div className="dashboard-loading">
                <Spinner size="lg" />
                <span>Loading dashboard...</span>
            </div>
        )
    }

    return (
        <div className={`admin-dashboard-react ${className}`}>
            {/* Tab Navigation */}
            <div className="dashboard-tabs">
                <button
                    className={`dashboard-tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    <LayoutDashboard size={18} />
                    Overview
                </button>
                <button
                    className={`dashboard-tab ${activeTab === 'appointments' ? 'active' : ''}`}
                    onClick={() => setActiveTab('appointments')}
                >
                    <Calendar size={18} />
                    Appointments
                </button>
                <button
                    className={`dashboard-tab ${activeTab === 'timecards' ? 'active' : ''}`}
                    onClick={() => setActiveTab('timecards')}
                >
                    <Clock size={18} />
                    Time Cards
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'appointments' ? (
                <Suspense fallback={<div className="dashboard-loading"><Spinner size="lg" /><span>Loading appointments...</span></div>}>
                    <UnifiedAppointmentsDashboard />
                </Suspense>
            ) : activeTab === 'timecards' ? (
                <Suspense fallback={<div className="dashboard-loading"><Spinner size="lg" /><span>Loading time cards...</span></div>}>
                    <AdminTimeCardsTab />
                </Suspense>
            ) : (
                <>
                    {/* KPI Grid */}
                    {kpis && (
                        <div className="kpi-grid">
                            <KPICard
                                title="Revenue This Month"
                                value={`$${(animatedRevenue / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                                subtitle={`Today: $${(kpis.revenue_today / 100).toFixed(2)}`}
                                icon={<DollarSign size={24} />}
                                iconColor="#10b981"
                                trend={kpis.revenue_trend}
                            />
                            <KPICard
                                title="Leads This Month"
                                value={animatedLeads}
                                subtitle={`Today: ${kpis.leads_today} new leads`}
                                icon={<UserPlus size={24} />}
                                iconColor="#22d3ee"
                                trend={kpis.leads_trend}
                            />
                            <KPICard
                                title="Appointments Today"
                                value={animatedAppointments}
                                subtitle="Scheduled for today"
                                icon={<CalendarCheck size={24} />}
                                iconColor="#f59e0b"
                            />
                            <KPICard
                                title="Active Users"
                                value={animatedUsers}
                                subtitle={`of ${kpis.total_users} total (last 24h)`}
                                icon={<Users size={24} />}
                                iconColor="#a855f7"
                            />
                        </div>
                    )}

                    {/* Charts Grid */}
                    <div className="charts-grid">
                        <div className="chart-card">
                            <div className="chart-header">
                                <span className="chart-title">
                                    <Zap size={16} className="chart-icon chart-icon--success" />
                                    Revenue Over Time
                                </span>
                                <div className="chart-controls">
                                    {[7, 30, 90].map(days => (
                                        <button
                                            key={days}
                                            className={selectedDays === days ? 'active' : ''}
                                            onClick={() => handleDaysChange(days)}
                                        >
                                            {days}D
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="chart-container">
                                {loading ? (
                                    <div className="chart-loading"><Spinner /></div>
                                ) : (
                                    <canvas id="revenueChart" />
                                )}
                            </div>
                        </div>

                        <div className="chart-card">
                            <div className="chart-header">
                                <span className="chart-title">
                                    <Activity size={16} className="chart-icon chart-icon--primary" />
                                    Lead Pipeline
                                </span>
                            </div>
                            {chartData?.funnel && <FunnelChart stages={chartData.funnel} />}
                        </div>
                    </div>

                    <div className="charts-grid">
                        <div className="chart-card" style={{ gridColumn: 'span 2' }}>
                            <div className="chart-header">
                                <span className="chart-title">
                                    <UserPlus size={16} className="chart-icon chart-icon--accent" />
                                    Leads Over Time
                                </span>
                            </div>
                            <div className="chart-container">
                                {loading ? (
                                    <div className="chart-loading"><Spinner /></div>
                                ) : (
                                    <canvas id="leadsChart" />
                                )}
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default AdminDashboard
