/**
 * CRM Analytics Panel
 * 
 * Displays conversion funnel, source attribution, and pipeline overview
 * with animated charts and glassmorphism styling.
 */

import { useMemo } from 'react'
import {
    TrendingUp,
    PieChart,
    BarChart2,
    ArrowRight
} from 'lucide-react'

interface FunnelItem {
    stage: string
    color: string
    count: number
    probability: number
}

interface SourceItem {
    source: string
    count: number
    percentage: number
}

interface KPIData {
    totalLeads: number
    newThisWeek: number
    wonThisMonth: number
    conversionRate: number
    trends: {
        totalLeads: number
        newThisWeek: number
        wonThisMonth: number
        conversionRate: number
    }
}

interface CRMAnalyticsProps {
    funnelData: FunnelItem[]
    sourceData: SourceItem[]
    kpiData: KPIData
}

export default function CRMAnalytics({
    funnelData,
    sourceData
}: CRMAnalyticsProps) {
    // Calculate max count for funnel bar widths
    const maxCount = useMemo(() => {
        return Math.max(...funnelData.map(item => item.count), 1)
    }, [funnelData])

    // Calculate weighted pipeline value
    const pipelineValue = useMemo(() => {
        return funnelData.reduce((sum, item) => {
            return sum + (item.count * item.probability / 100)
        }, 0).toFixed(1)
    }, [funnelData])

    return (
        <div className="crm-analytics-grid">
            {/* Conversion Funnel */}
            <div className="crm-chart-card">
                <div className="crm-chart-header">
                    <h3 className="crm-chart-title">
                        <TrendingUp size={18} style={{ marginRight: '0.5rem', color: '#28a745' }} />
                        Conversion Funnel
                    </h3>
                </div>
                <div className="crm-chart-body">
                    {funnelData.length > 0 ? (
                        funnelData.map((item, index) => {
                            const widthPercent = (item.count / maxCount) * 100
                            return (
                                <div key={index} className="crm-funnel-stage">
                                    <div className="crm-funnel-header">
                                        <span className="crm-funnel-label">
                                            <span
                                                style={{
                                                    display: 'inline-block',
                                                    width: '10px',
                                                    height: '10px',
                                                    borderRadius: '2px',
                                                    backgroundColor: item.color,
                                                    marginRight: '0.5rem'
                                                }}
                                            />
                                            {item.stage}
                                        </span>
                                        <span className="crm-funnel-value">{item.count}</span>
                                    </div>
                                    <div className="crm-funnel-bar-bg">
                                        <div
                                            className="crm-funnel-bar"
                                            style={{
                                                width: `${widthPercent}%`,
                                                background: `linear-gradient(90deg, ${item.color} 0%, ${item.color}cc 100%)`
                                            }}
                                        >
                                            {item.probability}%
                                        </div>
                                    </div>
                                </div>
                            )
                        })
                    ) : (
                        <div className="crm-empty-state">
                            <p>No funnel data available</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Source Attribution */}
            <div className="crm-chart-card">
                <div className="crm-chart-header">
                    <h3 className="crm-chart-title">
                        <PieChart size={18} style={{ marginRight: '0.5rem', color: '#4169e1' }} />
                        Lead Sources
                    </h3>
                </div>
                <div className="crm-chart-body">
                    {sourceData.length > 0 ? (
                        <table className="crm-source-table">
                            <thead>
                                <tr>
                                    <th>Source</th>
                                    <th style={{ textAlign: 'right' }}>Count</th>
                                    <th style={{ textAlign: 'right' }}>Share</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sourceData.map((item, index) => (
                                    <tr key={index}>
                                        <td>
                                            <span className="crm-source-badge">
                                                {item.source || 'Unknown'}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'right' }}>{item.count}</td>
                                        <td style={{ textAlign: 'right' }}>{item.percentage.toFixed(1)}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="crm-empty-state">
                            <p>No source data available</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Pipeline Overview */}
            <div className="crm-chart-card" style={{ gridColumn: '1 / -1' }}>
                <div className="crm-chart-header">
                    <h3 className="crm-chart-title">
                        <BarChart2 size={18} style={{ marginRight: '0.5rem', color: '#ffc107' }} />
                        Pipeline Overview
                    </h3>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.9rem',
                        color: 'rgba(255,255,255,0.7)'
                    }}>
                        <span>Weighted Pipeline:</span>
                        <strong style={{ color: '#28a745', fontSize: '1.1rem' }}>
                            {pipelineValue} leads
                        </strong>
                    </div>
                </div>
                <div className="crm-chart-body">
                    <table className="crm-source-table">
                        <thead>
                            <tr>
                                <th>Stage</th>
                                <th style={{ textAlign: 'center' }}>Lead Count</th>
                                <th style={{ textAlign: 'center' }}>Probability</th>
                                <th style={{ textAlign: 'center' }}>Weighted Value</th>
                                <th style={{ textAlign: 'center' }}>Flow</th>
                            </tr>
                        </thead>
                        <tbody>
                            {funnelData.map((item, index) => (
                                <tr key={index}>
                                    <td>
                                        <span
                                            style={{
                                                display: 'inline-block',
                                                padding: '0.25rem 0.75rem',
                                                borderRadius: '4px',
                                                backgroundColor: item.color,
                                                color: '#fff',
                                                fontSize: '0.85rem',
                                                fontWeight: 600
                                            }}
                                        >
                                            {item.stage}
                                        </span>
                                    </td>
                                    <td style={{ textAlign: 'center', fontWeight: 600 }}>
                                        {item.count}
                                    </td>
                                    <td style={{ textAlign: 'center' }}>
                                        {item.probability}%
                                    </td>
                                    <td style={{ textAlign: 'center', color: '#28a745', fontWeight: 600 }}>
                                        {(item.count * item.probability / 100).toFixed(1)}
                                    </td>
                                    <td style={{ textAlign: 'center' }}>
                                        {index < funnelData.length - 1 && (
                                            <ArrowRight size={16} style={{ opacity: 0.4 }} />
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
