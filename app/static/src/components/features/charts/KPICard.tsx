/**
 * KPICard Component
 * 
 * A card for displaying key performance indicators.
 * Placeholder for Phase 18.2.
 */

import { ReactNode } from 'react'
import { ArrowUp, ArrowDown, Minus } from 'lucide-react'

export interface KPICardProps {
    /** KPI title */
    title: string
    /** KPI value */
    value: string | number
    /** Subtitle/description */
    subtitle?: string
    /** Icon component */
    icon?: ReactNode
    /** Icon color */
    iconColor?: string
    /** Trend percentage (positive = up, negative = down) */
    trend?: number
    /** Trend label */
    trendLabel?: string
    /** Additional class */
    className?: string
}

export function KPICard({
    title,
    value,
    subtitle,
    icon,
    iconColor = '#4169e1',
    trend,
    trendLabel,
    className = '',
}: KPICardProps) {
    const getTrendIcon = () => {
        if (!trend || trend === 0) return <Minus className="w-3 h-3" />
        return trend > 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
    }

    const getTrendClass = () => {
        if (!trend || trend === 0) return 'kpi-trend-neutral'
        return trend > 0 ? 'kpi-trend-up' : 'kpi-trend-down'
    }

    return (
        <div className={`kpi-card ${className}`}>
            <div className="kpi-header">
                <span className="kpi-title">{title}</span>
                {icon && (
                    <span className="kpi-icon" style={{ color: iconColor }}>
                        {icon}
                    </span>
                )}
            </div>

            <div className="kpi-value">
                {value}
                {trend !== undefined && (
                    <span className={`kpi-trend ${getTrendClass()}`}>
                        {getTrendIcon()}
                        {Math.abs(trend)}%
                    </span>
                )}
            </div>

            {(subtitle || trendLabel) && (
                <div className="kpi-subtitle">
                    {subtitle || trendLabel}
                </div>
            )}
        </div>
    )
}

export default KPICard
