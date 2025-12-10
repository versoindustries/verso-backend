/**
 * CRM Dashboard - Unified Enterprise Dashboard
 * 
 * Consolidates Kanban board, Analytics, Pipeline Settings, and Email Templates
 * into a single tabbed interface with premium glassmorphism design.
 */

import { useState } from 'react'
import {
    LayoutGrid,
    BarChart3,
    Settings,
    Mail,
    Users,
    TrendingUp,
    TrendingDown,
    Target,
    Award,
    Plus,
    Search,
    Filter
} from 'lucide-react'
import KanbanBoard from './KanbanBoard'
import CRMAnalytics from './CRMAnalytics'
import PipelineSettings from './PipelineSettings'
import EmailTemplates from './EmailTemplates'

// Types
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

interface Stage {
    id: number
    name: string
    color: string
    order: number
    probability: number
    isWonStage: boolean
    isLostStage: boolean
    pipelineName: string
}

interface Lead {
    id: number
    type: 'contact' | 'appointment'
    name: string
    email: string
    phone: string
    date: string
    source: string
    score: number
}

interface Column {
    stage: { name: string; color: string }
    leads: Lead[]
}

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

interface EmailTemplate {
    id: number
    name: string
    type: string
    subject: string
    body: string
    isActive: boolean
}

interface CRMDashboardProps {
    columns: Record<string, Column>
    updateStatusUrl: string
    leadDetailUrl: string
    stages: Stage[]
    pipelineName: string
    kpiData: KPIData
    funnelData: FunnelItem[]
    sourceData: SourceItem[]
    templates: EmailTemplate[]
    csrfToken: string
}

type TabId = 'board' | 'analytics' | 'settings' | 'templates'

interface Tab {
    id: TabId
    label: string
    icon: React.ReactNode
    badge?: number
}

export default function CRMDashboard({
    columns,
    updateStatusUrl,
    leadDetailUrl,
    stages,
    pipelineName,
    kpiData,
    funnelData,
    sourceData,
    templates,
    csrfToken
}: CRMDashboardProps) {
    const [activeTab, setActiveTab] = useState<TabId>('board')
    const [searchQuery, setSearchQuery] = useState('')
    const [isLoading] = useState(false)

    // Calculate total leads for badge
    const totalLeads = Object.values(columns).reduce(
        (sum, col) => sum + col.leads.length,
        0
    )

    const tabs: Tab[] = [
        {
            id: 'board',
            label: 'Lead Board',
            icon: <LayoutGrid size={18} />,
            badge: totalLeads
        },
        {
            id: 'analytics',
            label: 'Analytics',
            icon: <BarChart3 size={18} />
        },
        {
            id: 'settings',
            label: 'Pipeline',
            icon: <Settings size={18} />,
            badge: stages.length
        },
        {
            id: 'templates',
            label: 'Templates',
            icon: <Mail size={18} />,
            badge: templates.length
        }
    ]

    // KPI Cards data
    const kpiCards = [
        {
            label: 'Total Leads',
            value: kpiData.totalLeads,
            trend: kpiData.trends.totalLeads,
            icon: <Users size={24} />
        },
        {
            label: 'New This Week',
            value: kpiData.newThisWeek,
            trend: kpiData.trends.newThisWeek,
            icon: <TrendingUp size={24} />
        },
        {
            label: 'Won This Month',
            value: kpiData.wonThisMonth,
            trend: kpiData.trends.wonThisMonth,
            icon: <Award size={24} />
        },
        {
            label: 'Conversion Rate',
            value: `${kpiData.conversionRate}%`,
            trend: kpiData.trends.conversionRate,
            icon: <Target size={24} />
        }
    ]

    const renderTrend = (trend: number) => {
        if (trend === 0) return null
        const isUp = trend > 0
        return (
            <span className={`crm-kpi-trend ${isUp ? 'up' : 'down'}`}>
                {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {Math.abs(trend)}%
            </span>
        )
    }

    const renderContent = () => {
        if (isLoading) {
            return (
                <div className="crm-loading">
                    <div className="crm-loading-spinner" />
                    <span>Loading...</span>
                </div>
            )
        }

        switch (activeTab) {
            case 'board':
                return (
                    <KanbanBoard
                        columns={columns}
                        updateStatusUrl={updateStatusUrl}
                        leadDetailUrl={leadDetailUrl}
                    />
                )
            case 'analytics':
                return (
                    <CRMAnalytics
                        funnelData={funnelData}
                        sourceData={sourceData}
                        kpiData={kpiData}
                    />
                )
            case 'settings':
                return (
                    <PipelineSettings
                        stages={stages}
                        pipelineName={pipelineName}
                        csrfToken={csrfToken}
                    />
                )
            case 'templates':
                return (
                    <EmailTemplates
                        templates={templates}
                        csrfToken={csrfToken}
                    />
                )
            default:
                return null
        }
    }

    const getPanelTitle = () => {
        switch (activeTab) {
            case 'board':
                return 'Lead Pipeline'
            case 'analytics':
                return 'Performance Analytics'
            case 'settings':
                return 'Pipeline Configuration'
            case 'templates':
                return 'Email Templates'
            default:
                return ''
        }
    }

    const renderPanelActions = () => {
        switch (activeTab) {
            case 'board':
                return (
                    <>
                        <div className="crm-search-box" style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            background: 'rgba(0,0,0,0.2)',
                            padding: '0.5rem 0.75rem',
                            borderRadius: '8px'
                        }}>
                            <Search size={16} style={{ opacity: 0.5 }} />
                            <input
                                type="text"
                                placeholder="Search leads..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: '#fff',
                                    fontSize: '0.85rem',
                                    outline: 'none',
                                    width: '150px'
                                }}
                            />
                        </div>
                        <button className="crm-btn-icon" title="Filter">
                            <Filter size={18} />
                        </button>
                    </>
                )
            case 'settings':
                return (
                    <button className="crm-btn crm-btn-primary">
                        <Plus size={16} />
                        Add Stage
                    </button>
                )
            case 'templates':
                return (
                    <button className="crm-btn crm-btn-primary">
                        <Plus size={16} />
                        New Template
                    </button>
                )
            default:
                return null
        }
    }

    return (
        <div className="crm-dashboard">
            {/* Tab Navigation */}
            <nav className="crm-tabs" role="tablist">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        role="tab"
                        aria-selected={activeTab === tab.id}
                        className={`crm-tab ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <span className="crm-tab-icon">{tab.icon}</span>
                        <span>{tab.label}</span>
                        {tab.badge !== undefined && tab.badge > 0 && (
                            <span className="crm-tab-badge">{tab.badge}</span>
                        )}
                    </button>
                ))}
            </nav>

            {/* KPI Strip - Only show on board and analytics tabs */}
            {(activeTab === 'board' || activeTab === 'analytics') && (
                <div className="crm-kpi-strip">
                    {kpiCards.map((kpi, index) => (
                        <div key={index} className="crm-kpi-card">
                            <div className="crm-kpi-label">{kpi.label}</div>
                            <div className="crm-kpi-value">
                                {kpi.value}
                                {renderTrend(kpi.trend)}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Main Content Panel */}
            <div className="crm-content-panel">
                <div className="crm-panel-header">
                    <h2 className="crm-panel-title">{getPanelTitle()}</h2>
                    <div className="crm-panel-actions">
                        {renderPanelActions()}
                    </div>
                </div>
                <div className="crm-panel-body">
                    {renderContent()}
                </div>
            </div>
        </div>
    )
}
