/**
 * AdminDashboard Component
 * 
 * React version of the admin dashboard with KPI cards, charts, and data tables.
 * This component receives data from the Flask backend via props.
 */

import { useState, useEffect, useCallback } from 'react'
import { DollarSign, UserPlus, CalendarCheck, Users, ArrowUp, ArrowDown } from 'lucide-react'
import api from '../../../api'
import { Spinner } from '../../ui/spinner'

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
}

function KPICard({ title, value, subtitle, icon, iconColor, trend }: KPICardProps) {
    return (
        <div className="kpi-card">
            <div className="kpi-header">
                <span className="kpi-title">{title}</span>
                <span className="kpi-icon" style={{ color: iconColor }}>
                    {icon}
                </span>
            </div>
            <div className="kpi-value">
                {value}
                {trend !== undefined && trend !== 0 && (
                    <span className={`kpi-trend ${trend > 0 ? 'up' : 'down'}`}>
                        {trend > 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                        {Math.abs(trend)}%
                    </span>
                )}
            </div>
            {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
        </div>
    )
}

// =============================================================================
// Funnel Chart Component
// =============================================================================

interface FunnelChartProps {
    stages: FunnelStage[]
}

function FunnelChart({ stages }: FunnelChartProps) {
    const maxCount = Math.max(...stages.map(s => s.count), 1)

    return (
        <div className="funnel-container">
            {stages.map((stage, index) => (
                <div key={index} className="funnel-stage">
                    <span className="funnel-label">{stage.name}</span>
                    <div className="funnel-bar-container">
                        <div
                            className="funnel-bar"
                            style={{
                                width: `${(stage.count / maxCount) * 100}%`,
                                backgroundColor: stage.color,
                            }}
                        >
                            {stage.count}
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
}: AdminDashboardProps) {
    const [kpis] = useState<KPIData | null>(initialKpis || null)
    const [chartData, setChartData] = useState<ChartData | null>(null)
    const [selectedDays, setSelectedDays] = useState(30)
    const [loading, setLoading] = useState(false)
    const [chartRef, setChartRef] = useState<any>(null)

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

    // Chart initialization
    useEffect(() => {
        if (!chartData) return

        const initCharts = async () => {
            const { Chart, registerables } = await import('chart.js')
            Chart.register(...registerables)

            // Revenue Chart
            const revenueCanvas = document.getElementById('revenueChart') as HTMLCanvasElement
            if (revenueCanvas) {
                const ctx = revenueCanvas.getContext('2d')
                if (ctx) {
                    // Destroy existing chart
                    if (chartRef) chartRef.destroy()

                    const newChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: chartData.labels,
                            datasets: [{
                                label: 'Revenue ($)',
                                data: chartData.revenue,
                                borderColor: '#28a745',
                                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                fill: true,
                                tension: 0.4,
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: { color: 'rgba(255,255,255,0.7)' },
                                    grid: { color: 'rgba(255,255,255,0.1)' },
                                },
                                x: {
                                    ticks: { color: 'rgba(255,255,255,0.7)' },
                                    grid: { display: false },
                                },
                            },
                        },
                    })
                    setChartRef(newChart)
                }
            }

            // Leads Chart
            const leadsCanvas = document.getElementById('leadsChart') as HTMLCanvasElement
            if (leadsCanvas) {
                const ctx = leadsCanvas.getContext('2d')
                if (ctx) {
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: chartData.labels,
                            datasets: [{
                                label: 'Leads',
                                data: chartData.leads,
                                backgroundColor: 'rgba(65, 105, 225, 0.6)',
                                borderColor: '#4169e1',
                                borderWidth: 1,
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: { color: 'rgba(255,255,255,0.7)' },
                                    grid: { color: 'rgba(255,255,255,0.1)' },
                                },
                                x: {
                                    ticks: { color: 'rgba(255,255,255,0.7)' },
                                    grid: { display: false },
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
        return <Spinner size="lg" />
    }

    return (
        <div className={`admin-dashboard-react ${className}`}>
            {/* KPI Grid */}
            {kpis && (
                <div className="kpi-grid">
                    <KPICard
                        title="Revenue This Month"
                        value={`$${(kpis.revenue_month / 100).toFixed(2)}`}
                        subtitle={`Today: $${(kpis.revenue_today / 100).toFixed(2)}`}
                        icon={<DollarSign />}
                        iconColor="#28a745"
                        trend={kpis.revenue_trend}
                    />
                    <KPICard
                        title="Leads This Month"
                        value={kpis.leads_month}
                        subtitle={`Today: ${kpis.leads_today} new leads`}
                        icon={<UserPlus />}
                        iconColor="#17a2b8"
                        trend={kpis.leads_trend}
                    />
                    <KPICard
                        title="Appointments Today"
                        value={kpis.appointments_today}
                        subtitle="Scheduled for today"
                        icon={<CalendarCheck />}
                        iconColor="#ffc107"
                    />
                    <KPICard
                        title="Active Users"
                        value={kpis.active_users}
                        subtitle={`of ${kpis.total_users} total (last 24h)`}
                        icon={<Users />}
                        iconColor="#6f42c1"
                    />
                </div>
            )}

            {/* Charts Grid */}
            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-header">
                        <span className="chart-title">Revenue Over Time</span>
                        <div className="chart-controls">
                            {[7, 30, 90].map(days => (
                                <button
                                    key={days}
                                    data-days={days}
                                    className={selectedDays === days ? 'active' : ''}
                                    onClick={() => handleDaysChange(days)}
                                >
                                    {days} Days
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="chart-container">
                        {loading ? <Spinner /> : <canvas id="revenueChart" />}
                    </div>
                </div>

                <div className="chart-card">
                    <div className="chart-header">
                        <span className="chart-title">Lead Pipeline</span>
                    </div>
                    {chartData?.funnel && <FunnelChart stages={chartData.funnel} />}
                </div>
            </div>

            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-header">
                        <span className="chart-title">Leads Over Time</span>
                    </div>
                    <div className="chart-container">
                        {loading ? <Spinner /> : <canvas id="leadsChart" />}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AdminDashboard
