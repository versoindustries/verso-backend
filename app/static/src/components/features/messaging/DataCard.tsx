/**
 * DataCard Component
 * 
 * Renders data cards from slash command results (orders, leads, appointments, etc.)
 */

import { useMemo } from 'react'

// =============================================================================
// Types
// =============================================================================

interface OrderCard {
    type: 'order'
    id: number
    title: string
    status: string
    total: string
    customer: string
    items: string[]
    created_at: string | null
    url: string
}

interface LeadCard {
    type: 'lead'
    id: number
    title: string
    email: string | null
    phone: string | null
    status: string
    message: string
    created_at: string | null
    url: string | null
}

interface AppointmentCard {
    type: 'appointment'
    id: number
    title: string
    service: string
    estimator: string
    status: string
    date: string | null
    time: string | null
    customer_name: string | null
    customer_email: string | null
    url: string
}

interface ProductCard {
    type: 'product'
    id: number
    title: string
    sku: string | null
    price: string
    inventory: number
    is_active: boolean
    description: string
    url: string
}

interface TicketCard {
    type: 'ticket'
    id: number
    title: string
    status: string
    priority: string
    customer_email: string
    created_at: string | null
    url: string
}

interface SearchResultsCard {
    type: 'search_results'
    query: string
    results: Array<{
        type: string
        id: number
        name: string
        email: string
        source: string
    }>
}

type DataCardData = OrderCard | LeadCard | AppointmentCard | ProductCard | TicketCard | SearchResultsCard

interface DataCardProps {
    card: DataCardData
}

// =============================================================================
// Status Badge Component
// =============================================================================

function StatusBadge({ status }: { status: string }) {
    const colorClass = useMemo(() => {
        const s = status.toLowerCase()
        if (s.includes('complete') || s.includes('approved') || s.includes('paid') || s.includes('active')) {
            return 'badge-success'
        }
        if (s.includes('pending') || s.includes('processing') || s.includes('scheduled')) {
            return 'badge-warning'
        }
        if (s.includes('cancel') || s.includes('reject') || s.includes('failed')) {
            return 'badge-danger'
        }
        return 'badge-secondary'
    }, [status])

    return <span className={`data-card-badge ${colorClass}`}>{status}</span>
}

// =============================================================================
// Individual Card Components
// =============================================================================

function OrderCardView({ card }: { card: OrderCard }) {
    return (
        <div className="data-card data-card-order">
            <div className="data-card-header">
                <i className="fas fa-box"></i>
                <span className="data-card-title">{card.title}</span>
                <StatusBadge status={card.status} />
            </div>
            <div className="data-card-body">
                <div className="data-card-row">
                    <span className="data-card-label">Total:</span>
                    <span className="data-card-value data-card-price">{card.total}</span>
                </div>
                <div className="data-card-row">
                    <span className="data-card-label">Customer:</span>
                    <span className="data-card-value">{card.customer}</span>
                </div>
                {card.items.length > 0 && (
                    <div className="data-card-items">
                        <span className="data-card-label">Items:</span>
                        <ul>
                            {card.items.map((item, idx) => (
                                <li key={idx}>{item}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
            <div className="data-card-footer">
                {card.created_at && <span className="data-card-date">{card.created_at}</span>}
                <a href={card.url} className="data-card-link" target="_blank" rel="noreferrer">
                    View Order <i className="fas fa-external-link-alt"></i>
                </a>
            </div>
        </div>
    )
}

function LeadCardView({ card }: { card: LeadCard }) {
    return (
        <div className="data-card data-card-lead">
            <div className="data-card-header">
                <i className="fas fa-user"></i>
                <span className="data-card-title">{card.title}</span>
                <StatusBadge status={card.status} />
            </div>
            <div className="data-card-body">
                {card.email && (
                    <div className="data-card-row">
                        <span className="data-card-label">Email:</span>
                        <span className="data-card-value">{card.email}</span>
                    </div>
                )}
                {card.phone && (
                    <div className="data-card-row">
                        <span className="data-card-label">Phone:</span>
                        <span className="data-card-value">{card.phone}</span>
                    </div>
                )}
                {card.message && (
                    <div className="data-card-message">
                        <p>{card.message}</p>
                    </div>
                )}
            </div>
            <div className="data-card-footer">
                {card.created_at && <span className="data-card-date">{card.created_at}</span>}
                {card.url && (
                    <a href={card.url} className="data-card-link" target="_blank" rel="noreferrer">
                        View Lead <i className="fas fa-external-link-alt"></i>
                    </a>
                )}
            </div>
        </div>
    )
}

function AppointmentCardView({ card }: { card: AppointmentCard }) {
    return (
        <div className="data-card data-card-appointment">
            <div className="data-card-header">
                <i className="fas fa-calendar"></i>
                <span className="data-card-title">{card.title}</span>
                <StatusBadge status={card.status} />
            </div>
            <div className="data-card-body">
                <div className="data-card-row">
                    <span className="data-card-label">Service:</span>
                    <span className="data-card-value">{card.service}</span>
                </div>
                <div className="data-card-row">
                    <span className="data-card-label">Assigned to:</span>
                    <span className="data-card-value">{card.estimator}</span>
                </div>
                {(card.date || card.time) && (
                    <div className="data-card-row">
                        <span className="data-card-label">When:</span>
                        <span className="data-card-value">
                            {card.date} {card.time && `at ${card.time}`}
                        </span>
                    </div>
                )}
                {card.customer_name && (
                    <div className="data-card-row">
                        <span className="data-card-label">Customer:</span>
                        <span className="data-card-value">{card.customer_name}</span>
                    </div>
                )}
            </div>
            <div className="data-card-footer">
                <a href={card.url} className="data-card-link" target="_blank" rel="noreferrer">
                    View Appointments <i className="fas fa-external-link-alt"></i>
                </a>
            </div>
        </div>
    )
}

function ProductCardView({ card }: { card: ProductCard }) {
    return (
        <div className="data-card data-card-product">
            <div className="data-card-header">
                <i className="fas fa-tag"></i>
                <span className="data-card-title">{card.title}</span>
                {!card.is_active && <span className="data-card-badge badge-secondary">Inactive</span>}
            </div>
            <div className="data-card-body">
                <div className="data-card-row">
                    <span className="data-card-label">Price:</span>
                    <span className="data-card-value data-card-price">{card.price}</span>
                </div>
                {card.sku && (
                    <div className="data-card-row">
                        <span className="data-card-label">SKU:</span>
                        <span className="data-card-value">{card.sku}</span>
                    </div>
                )}
                <div className="data-card-row">
                    <span className="data-card-label">Inventory:</span>
                    <span className={`data-card-value ${card.inventory <= 0 ? 'text-danger' : ''}`}>
                        {card.inventory > 0 ? `${card.inventory} in stock` : 'Out of stock'}
                    </span>
                </div>
                {card.description && (
                    <div className="data-card-description">
                        <p>{card.description}</p>
                    </div>
                )}
            </div>
            <div className="data-card-footer">
                <a href={card.url} className="data-card-link" target="_blank" rel="noreferrer">
                    View Product <i className="fas fa-external-link-alt"></i>
                </a>
            </div>
        </div>
    )
}

function TicketCardView({ card }: { card: TicketCard }) {
    return (
        <div className="data-card data-card-ticket">
            <div className="data-card-header">
                <i className="fas fa-ticket-alt"></i>
                <span className="data-card-title">{card.title}</span>
                <StatusBadge status={card.status} />
            </div>
            <div className="data-card-body">
                <div className="data-card-row">
                    <span className="data-card-label">Priority:</span>
                    <span className="data-card-value">{card.priority}</span>
                </div>
                <div className="data-card-row">
                    <span className="data-card-label">Customer:</span>
                    <span className="data-card-value">{card.customer_email}</span>
                </div>
            </div>
            <div className="data-card-footer">
                {card.created_at && <span className="data-card-date">{card.created_at}</span>}
                <a href={card.url} className="data-card-link" target="_blank" rel="noreferrer">
                    View Ticket <i className="fas fa-external-link-alt"></i>
                </a>
            </div>
        </div>
    )
}

function SearchResultsCardView({ card }: { card: SearchResultsCard }) {
    return (
        <div className="data-card data-card-search">
            <div className="data-card-header">
                <i className="fas fa-search"></i>
                <span className="data-card-title">Search Results</span>
                <span className="data-card-badge badge-info">{card.results.length} found</span>
            </div>
            <div className="data-card-body">
                <p className="data-card-query">Query: "{card.query}"</p>
                <ul className="data-card-results">
                    {card.results.slice(0, 5).map((result, idx) => (
                        <li key={idx}>
                            <span className="result-source">[{result.source}]</span>{' '}
                            <span className="result-name">{result.name}</span>{' '}
                            <span className="result-email">{result.email}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    )
}

// =============================================================================
// Main DataCard Component
// =============================================================================

export function DataCard({ card }: DataCardProps) {
    if (!card || !card.type) return null

    switch (card.type) {
        case 'order':
            return <OrderCardView card={card} />
        case 'lead':
            return <LeadCardView card={card} />
        case 'appointment':
            return <AppointmentCardView card={card} />
        case 'product':
            return <ProductCardView card={card} />
        case 'ticket':
            return <TicketCardView card={card} />
        case 'search_results':
            return <SearchResultsCardView card={card} />
        default:
            return null
    }
}

export default DataCard
