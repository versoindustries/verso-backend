/**
 * AnalyticsDashboard Component
 * 
 * React component for the analytics dashboard that replaces inline Chart.js.
 * Displays KPI metrics and interactive charts for traffic, sources, and devices.
 */

import { useState, useEffect, useCallback } from 'react'
import { Eye, Users, LogOut, Clock, TrendingUp } from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface MetricsData {
    page_views: number
    unique_sessions: number
    bounce_rate: number
    avg_session_duration: number
}

interface ChartDataset {
    labels: string[]
    page_views?: number[]
    sessions?: number[]
    values?: number[]
}

interface AnalyticsDashboardProps {
    /** Initial metrics data from server */
    metrics: MetricsData
    /** Number of days for the current view */
    days?: number
    /** API URLs for fetching chart data */
    trafficUrl: string
    sourcesUrl: string
    devicesUrl: string
    /** Additional className */
    className?: string
}

// =============================================================================
// KPI Card Component
// =============================================================================

function AnalyticsKPICard({
    title,
    value,
    icon: Icon,
    color = 'primary',
}: {
    title: string
    value: string | number
    icon: React.ElementType
    color?: 'primary' | 'success' | 'warning' | 'info'
}) {
    const colorClasses = {
        primary: 'analytics-kpi-primary',
        success: 'analytics-kpi-success',
        warning: 'analytics-kpi-warning',
        info: 'analytics-kpi-info',
    }

    return (
        <div className={`analytics-kpi-card ${colorClasses[color]}`}>
            <div className="analytics-kpi-content">
                <div className="analytics-kpi-text">
                    <span className="analytics-kpi-title">{title}</span>
                    <span className="analytics-kpi-value">{value}</span>
                </div>
                <div className="analytics-kpi-icon">
                    <Icon size={32} />
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function AnalyticsDashboard({
    metrics,
    // days param available for future use
    trafficUrl,
    sourcesUrl,
    devicesUrl,
    className = '',
}: AnalyticsDashboardProps) {
    const [trafficData, setTrafficData] = useState<ChartDataset | null>(null)
    const [sourcesData, setSourcesData] = useState<ChartDataset | null>(null)
    const [devicesData, setDevicesData] = useState<ChartDataset | null>(null)
    const [loading, setLoading] = useState(true)
    const [chartInstance, setChartInstance] = useState<any>(null)

    // Format duration
    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}m ${secs}s`
    }

    // Format number with commas
    const formatNumber = (num: number) => {
        return num.toLocaleString()
    }

    // Load all chart data
    const loadChartData = useCallback(async () => {
        setLoading(true)
        try {
            const [trafficRes, sourcesRes, devicesRes] = await Promise.all([
                api.get(trafficUrl),
                api.get(sourcesUrl),
                api.get(devicesUrl),
            ])

            if (trafficRes.ok && trafficRes.data) {
                setTrafficData(trafficRes.data)
            }
            if (sourcesRes.ok && sourcesRes.data) {
                setSourcesData(sourcesRes.data)
            }
            if (devicesRes.ok && devicesRes.data) {
                setDevicesData(devicesRes.data)
            }
        } catch (err) {
            console.error('Error loading analytics data:', err)
        } finally {
            setLoading(false)
        }
    }, [trafficUrl, sourcesUrl, devicesUrl])

    // Initial load
    useEffect(() => {
        loadChartData()
    }, [loadChartData])

    // Initialize charts when data is available
    useEffect(() => {
        if (!trafficData || !sourcesData || !devicesData) return

        const initCharts = async () => {
            const { Chart, registerables } = await import('chart.js')
            Chart.register(...registerables)

            // Traffic Chart
            const trafficCanvas = document.getElementById('analyticsTrafficChart') as HTMLCanvasElement
            if (trafficCanvas) {
                if (chartInstance) {
                    chartInstance.destroy()
                }
                const newChart = new Chart(trafficCanvas, {
                    type: 'line',
                    data: {
                        labels: trafficData.labels,
                        datasets: [
                            {
                                label: 'Page Views',
                                data: trafficData.page_views || [],
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                                fill: true,
                                tension: 0.3,
                            },
                            {
                                label: 'Sessions',
                                data: trafficData.sessions || [],
                                borderColor: 'rgb(54, 162, 235)',
                                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                                fill: true,
                                tension: 0.3,
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true },
                        },
                        plugins: {
                            legend: {
                                labels: { color: 'rgba(255, 255, 255, 0.7)' },
                            },
                        },
                    },
                })
                setChartInstance(newChart)
            }

            // Sources Chart
            const sourcesCanvas = document.getElementById('analyticsSourcesChart') as HTMLCanvasElement
            if (sourcesCanvas) {
                new Chart(sourcesCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: sourcesData.labels,
                        datasets: [
                            {
                                data: sourcesData.values || [],
                                backgroundColor: [
                                    '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
                                    '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf',
                                ],
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { color: 'rgba(255, 255, 255, 0.7)' },
                            },
                        },
                    },
                })
            }

            // Devices Chart
            const devicesCanvas = document.getElementById('analyticsDevicesChart') as HTMLCanvasElement
            if (devicesCanvas) {
                new Chart(devicesCanvas, {
                    type: 'pie',
                    data: {
                        labels: devicesData.labels,
                        datasets: [
                            {
                                data: devicesData.values || [],
                                backgroundColor: ['#4e73df', '#1cc88a', '#f6c23e'],
                            },
                        ],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { color: 'rgba(255, 255, 255, 0.7)' },
                            },
                        },
                    },
                })
            }
        }

        initCharts()
    }, [trafficData, sourcesData, devicesData])

    return (
        <div className={`analytics-dashboard ${className}`}>
            {/* KPI Cards */}
            <div className="analytics-kpi-grid">
                <AnalyticsKPICard
                    title="Page Views"
                    value={formatNumber(metrics.page_views)}
                    icon={Eye}
                    color="primary"
                />
                <AnalyticsKPICard
                    title="Unique Sessions"
                    value={formatNumber(metrics.unique_sessions)}
                    icon={Users}
                    color="success"
                />
                <AnalyticsKPICard
                    title="Bounce Rate"
                    value={`${metrics.bounce_rate}%`}
                    icon={LogOut}
                    color="warning"
                />
                <AnalyticsKPICard
                    title="Avg. Duration"
                    value={formatDuration(metrics.avg_session_duration)}
                    icon={Clock}
                    color="info"
                />
            </div>

            {/* Charts Row */}
            <div className="analytics-charts-row">
                {/* Traffic Chart */}
                <div className="analytics-chart-card analytics-chart-large">
                    <div className="analytics-chart-header">
                        <span className="analytics-chart-title">
                            <TrendingUp size={18} className="me-2" />
                            Traffic Trend
                        </span>
                    </div>
                    <div className="analytics-chart-body">
                        {loading ? (
                            <div className="analytics-chart-loading">Loading chart...</div>
                        ) : (
                            <canvas id="analyticsTrafficChart"></canvas>
                        )}
                    </div>
                </div>

                {/* Sources Chart */}
                <div className="analytics-chart-card analytics-chart-small">
                    <div className="analytics-chart-header">
                        <span className="analytics-chart-title">Traffic Sources</span>
                    </div>
                    <div className="analytics-chart-body">
                        {loading ? (
                            <div className="analytics-chart-loading">Loading...</div>
                        ) : (
                            <canvas id="analyticsSourcesChart"></canvas>
                        )}
                    </div>
                </div>
            </div>

            {/* Devices Chart (rendered separately since it's in a different row in the original) */}
            <div className="analytics-devices-section">
                <div className="analytics-chart-card analytics-chart-devices">
                    <div className="analytics-chart-header">
                        <span className="analytics-chart-title">Devices</span>
                    </div>
                    <div className="analytics-chart-body">
                        {loading ? (
                            <div className="analytics-chart-loading">Loading...</div>
                        ) : (
                            <canvas id="analyticsDevicesChart"></canvas>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AnalyticsDashboard
