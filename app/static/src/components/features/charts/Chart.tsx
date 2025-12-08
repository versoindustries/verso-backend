/**
 * Chart Component
 * 
 * A wrapper around Chart.js for rendering charts.
 * Placeholder for Phase 18.2.
 */

import { useEffect, useRef } from 'react'

export interface ChartDataset {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string
    fill?: boolean
    tension?: number
}

export interface ChartProps {
    /** Chart type */
    type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area'
    /** Labels for x-axis */
    labels: string[]
    /** Dataset(s) */
    datasets: ChartDataset[]
    /** Chart title */
    title?: string
    /** Show legend */
    showLegend?: boolean
    /** Height in pixels */
    height?: number
    /** Additional class */
    className?: string
}

export function Chart({
    type,
    labels,
    datasets,
    title,
    showLegend = true,
    height = 300,
    className = '',
}: ChartProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const chartRef = useRef<any>(null)

    useEffect(() => {
        // Dynamic import of Chart.js to avoid SSR issues
        const loadChart = async () => {
            if (!canvasRef.current) return

            const { Chart: ChartJS, registerables } = await import('chart.js')
            ChartJS.register(...registerables)

            // Destroy existing chart
            if (chartRef.current) {
                chartRef.current.destroy()
            }

            const ctx = canvasRef.current.getContext('2d')
            if (!ctx) return

            chartRef.current = new ChartJS(ctx, {
                type: type === 'area' ? 'line' : type,
                data: {
                    labels,
                    datasets: datasets.map(ds => ({
                        ...ds,
                        fill: type === 'area' ? true : ds.fill,
                    })),
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: showLegend,
                            labels: {
                                color: 'rgba(255, 255, 255, 0.7)',
                            },
                        },
                        title: title ? {
                            display: true,
                            text: title,
                            color: '#fff',
                        } : undefined,
                    },
                    scales: type !== 'pie' && type !== 'doughnut' ? {
                        y: {
                            beginAtZero: true,
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        },
                        x: {
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { display: false },
                        },
                    } : undefined,
                },
            })
        }

        loadChart()

        return () => {
            if (chartRef.current) {
                chartRef.current.destroy()
            }
        }
    }, [type, labels, datasets, title, showLegend])

    return (
        <div className={`chart-wrapper ${className}`} style={{ height }}>
            <canvas ref={canvasRef} />
        </div>
    )
}

export default Chart
