/**
 * UnifiedShopDashboard - Enterprise Shop Management
 * 
 * Unified dashboard for managing products and orders with
 * premium glassmorphism design and modern UX patterns.
 */

import React, { useState, useEffect } from 'react'
import {
    ShoppingCart,
    Package,
    DollarSign,

    AlertTriangle,
    Plus,
    Search,

    Grid,
    List,
    Edit,
    Trash2,
    Eye,
    X,
    Upload,
    ChevronLeft,
    ChevronRight,
    Truck,
    RefreshCw,
    BarChart2,
    Clock,
    CheckCircle,

} from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface Product {
    id: number
    name: string
    description: string
    price: number
    price_display: string
    inventory_count: number
    is_digital: boolean
    category_id: number | null
    image_url: string | null
    variants_count: number
    created_at: string | null
    updated_at: string | null
}

interface Order {
    id: number
    status: string
    total: number
    total_display: string
    email: string
    customer_name: string
    items_count: number
    shipping_address: string | null
    tracking_number: string | null
    carrier: string | null
    created_at: string | null
    shipped_at: string | null
    delivered_at: string | null
}

interface ShopStats {
    products: {
        total: number
        digital: number
        physical: number
        low_stock: number
    }
    orders: {
        total: number
        today: number
        month: number
    }
    revenue: {
        month: number
        month_display: string
        today: number
        today_display: string
    }
    recent_orders: Array<{
        id: number
        status: string
        total: string
        date: string
        email: string
    }>
    low_stock_alerts: Array<{
        id: number
        name: string
        inventory: number
    }>
}

interface Category {
    id: number
    name: string
    slug: string | null
}

interface UnifiedShopDashboardProps {
    initialTab?: 'overview' | 'products' | 'orders'
}

// =============================================================================
// Status Badge Component
// =============================================================================

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const statusConfig: Record<string, { color: string; bg: string }> = {
        pending: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' },
        paid: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' },
        processing: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)' },
        shipped: { color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)' },
        delivered: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)' },
        cancelled: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' },
        refunded: { color: '#6b7280', bg: 'rgba(107, 114, 128, 0.15)' },
    }

    const config = statusConfig[status] || { color: '#6b7280', bg: 'rgba(107, 114, 128, 0.15)' }

    return (
        <span
            className="shop-status-badge"
            style={{
                color: config.color,
                backgroundColor: config.bg,
                border: `1px solid ${config.color}30`
            }}
        >
            {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
    )
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

const KPICard: React.FC<KPICardProps> = ({ title, value, subtitle, icon, iconColor, trend }) => (
    <div className="shop-kpi-card">
        <div className="shop-kpi-header">
            <span className="shop-kpi-title">{title}</span>
            <div className="shop-kpi-icon" style={{ color: iconColor }}>
                {icon}
            </div>
        </div>
        <div className="shop-kpi-value">
            {value}
            {trend !== undefined && (
                <span className={`shop-kpi-trend ${trend >= 0 ? 'up' : 'down'}`}>
                    {trend >= 0 ? '+' : ''}{trend}%
                </span>
            )}
        </div>
        {subtitle && <div className="shop-kpi-subtitle">{subtitle}</div>}
    </div>
)

// =============================================================================
// Product Card Component
// =============================================================================

interface ProductCardProps {
    product: Product
    viewMode: 'grid' | 'list'
    onEdit: (product: Product) => void
    onDelete: (productId: number) => void
}

const ProductCard: React.FC<ProductCardProps> = ({ product, viewMode, onEdit, onDelete }) => {
    const isLowStock = !product.is_digital && product.inventory_count <= 5

    if (viewMode === 'list') {
        return (
            <div className="shop-product-row">
                <div className="shop-product-image-small">
                    {product.image_url ? (
                        <img src={product.image_url} alt={product.name} />
                    ) : (
                        <Package size={24} />
                    )}
                </div>
                <div className="shop-product-info">
                    <h4>{product.name}</h4>
                    <span className={`shop-product-type ${product.is_digital ? 'digital' : 'physical'}`}>
                        {product.is_digital ? 'Digital' : 'Physical'}
                    </span>
                </div>
                <div className="shop-product-price">{product.price_display}</div>
                <div className={`shop-product-inventory ${isLowStock ? 'low' : ''}`}>
                    {product.is_digital ? '∞' : product.inventory_count}
                    {isLowStock && <AlertTriangle size={14} />}
                </div>
                <div className="shop-product-actions">
                    <button className="shop-btn-icon" onClick={() => onEdit(product)} title="Edit">
                        <Edit size={16} />
                    </button>
                    <button className="shop-btn-icon danger" onClick={() => onDelete(product.id)} title="Delete">
                        <Trash2 size={16} />
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="shop-product-card">
            <div className="shop-product-image">
                {product.image_url ? (
                    <img src={product.image_url} alt={product.name} />
                ) : (
                    <div className="shop-product-placeholder">
                        <Package size={48} />
                    </div>
                )}
                {isLowStock && (
                    <div className="shop-product-alert">
                        <AlertTriangle size={14} /> Low Stock
                    </div>
                )}
            </div>
            <div className="shop-product-body">
                <h4>{product.name}</h4>
                <div className="shop-product-meta">
                    <span className={`shop-product-type ${product.is_digital ? 'digital' : 'physical'}`}>
                        {product.is_digital ? 'Digital' : 'Physical'}
                    </span>
                    {product.variants_count > 0 && (
                        <span className="shop-product-variants">{product.variants_count} variants</span>
                    )}
                </div>
                <div className="shop-product-footer">
                    <span className="shop-product-price">{product.price_display}</span>
                    <span className={`shop-product-stock ${isLowStock ? 'low' : ''}`}>
                        {product.is_digital ? '∞' : `${product.inventory_count} in stock`}
                    </span>
                </div>
            </div>
            <div className="shop-product-overlay">
                <button className="shop-btn-sm" onClick={() => onEdit(product)}>
                    <Edit size={14} /> Edit
                </button>
                <button className="shop-btn-sm danger" onClick={() => onDelete(product.id)}>
                    <Trash2 size={14} /> Delete
                </button>
            </div>
        </div>
    )
}

// =============================================================================
// Order Row Component
// =============================================================================

interface OrderRowProps {
    order: Order
    onView: (order: Order) => void
    onUpdateStatus: (orderId: number, status: string) => void
}

const OrderRow: React.FC<OrderRowProps> = ({ order, onView, onUpdateStatus }) => {
    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '—'
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    }

    return (
        <div className="shop-order-row">
            <div className="shop-order-id">
                <span className="shop-order-num">#{order.id}</span>
                <span className="shop-order-date">{formatDate(order.created_at)}</span>
            </div>
            <div className="shop-order-customer">
                <span className="shop-customer-name">{order.customer_name}</span>
                <span className="shop-customer-email">{order.email}</span>
            </div>
            <div className="shop-order-items">{order.items_count} item(s)</div>
            <div className="shop-order-total">{order.total_display}</div>
            <div className="shop-order-status">
                <StatusBadge status={order.status} />
            </div>
            <div className="shop-order-actions">
                <button className="shop-btn-icon" onClick={() => onView(order)} title="View Details">
                    <Eye size={16} />
                </button>
                {order.status === 'paid' && (
                    <button
                        className="shop-btn-icon primary"
                        onClick={() => onUpdateStatus(order.id, 'shipped')}
                        title="Mark Shipped"
                    >
                        <Truck size={16} />
                    </button>
                )}
            </div>
        </div>
    )
}

// =============================================================================
// Product Editor Slideout
// =============================================================================

interface ProductEditorProps {
    product: Product | null
    isOpen: boolean
    onClose: () => void
    onSave: (data: Partial<Product>) => void
    categories: Category[]
}

const ProductEditor: React.FC<ProductEditorProps> = ({ product, isOpen, onClose, onSave, categories }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        price: '',
        inventory_count: 0,
        is_digital: false,
        category_id: null as number | null,
    })
    const [imageFile, setImageFile] = useState<File | null>(null)
    const [imagePreview, setImagePreview] = useState<string | null>(null)
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        if (product) {
            setFormData({
                name: product.name,
                description: product.description || '',
                price: (product.price / 100).toFixed(2),
                inventory_count: product.inventory_count,
                is_digital: product.is_digital,
                category_id: product.category_id,
            })
            setImagePreview(product.image_url)
        } else {
            setFormData({
                name: '',
                description: '',
                price: '',
                inventory_count: 0,
                is_digital: false,
                category_id: null,
            })
            setImagePreview(null)
        }
        setImageFile(null)
    }, [product, isOpen])

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            setImageFile(file)
            const reader = new FileReader()
            reader.onload = () => setImagePreview(reader.result as string)
            reader.readAsDataURL(file)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setSaving(true)

        try {
            const productData = {
                ...formData,
                price: parseFloat(formData.price),
            }
            await onSave(productData)

            // Upload image if changed
            if (imageFile && product?.id) {
                const formDataObj = new FormData()
                formDataObj.append('image', imageFile)
                await fetch(`/admin/shop/api/products/${product.id}/image`, {
                    method: 'POST',
                    body: formDataObj,
                    credentials: 'include',
                })
            }

            onClose()
        } catch (err) {
            console.error('Save error:', err)
        } finally {
            setSaving(false)
        }
    }

    if (!isOpen) return null

    return (
        <div className="shop-slideout-overlay" onClick={onClose}>
            <div className="shop-slideout" onClick={e => e.stopPropagation()}>
                <div className="shop-slideout-header">
                    <h2>{product ? 'Edit Product' : 'New Product'}</h2>
                    <button className="shop-slideout-close" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="shop-slideout-body">
                    <div className="shop-form-group">
                        <label>Product Image</label>
                        <div className="shop-image-upload">
                            {imagePreview ? (
                                <img src={imagePreview} alt="Preview" />
                            ) : (
                                <div className="shop-image-placeholder">
                                    <Upload size={32} />
                                    <span>Upload Image</span>
                                </div>
                            )}
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                            />
                        </div>
                    </div>

                    <div className="shop-form-group">
                        <label>Product Name *</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                            required
                            placeholder="Enter product name"
                        />
                    </div>

                    <div className="shop-form-group">
                        <label>Description</label>
                        <textarea
                            value={formData.description}
                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                            rows={4}
                            placeholder="Product description..."
                        />
                    </div>

                    <div className="shop-form-row">
                        <div className="shop-form-group">
                            <label>Price ($) *</label>
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={formData.price}
                                onChange={e => setFormData({ ...formData, price: e.target.value })}
                                required
                                placeholder="0.00"
                            />
                        </div>
                        <div className="shop-form-group">
                            <label>Inventory</label>
                            <input
                                type="number"
                                min="0"
                                value={formData.inventory_count}
                                onChange={e => setFormData({ ...formData, inventory_count: parseInt(e.target.value) || 0 })}
                                disabled={formData.is_digital}
                            />
                        </div>
                    </div>

                    <div className="shop-form-group">
                        <label>Category</label>
                        <select
                            value={formData.category_id || ''}
                            onChange={e => setFormData({ ...formData, category_id: e.target.value ? parseInt(e.target.value) : null })}
                        >
                            <option value="">No Category</option>
                            {categories.map(cat => (
                                <option key={cat.id} value={cat.id}>{cat.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="shop-form-group">
                        <label className="shop-checkbox">
                            <input
                                type="checkbox"
                                checked={formData.is_digital}
                                onChange={e => setFormData({ ...formData, is_digital: e.target.checked })}
                            />
                            <span>Digital Product (no inventory tracking)</span>
                        </label>
                    </div>

                    <div className="shop-slideout-footer">
                        <button type="button" className="shop-btn secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="shop-btn primary" disabled={saving}>
                            {saving ? 'Saving...' : (product ? 'Update Product' : 'Create Product')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// =============================================================================
// Order Detail Slideout
// =============================================================================

interface OrderDetailProps {
    orderId: number | null
    isOpen: boolean
    onClose: () => void
    onStatusChange: (orderId: number, status: string) => void
    onRefund: (orderId: number) => void
}

const OrderDetail: React.FC<OrderDetailProps> = ({ orderId, isOpen, onClose, onStatusChange, onRefund }) => {
    const [order, setOrder] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [shipForm, setShipForm] = useState({ tracking_number: '', carrier: '' })
    const [showShipForm, setShowShipForm] = useState(false)

    useEffect(() => {
        if (orderId && isOpen) {
            loadOrder()
        }
    }, [orderId, isOpen])

    const loadOrder = async () => {
        if (!orderId) return
        setLoading(true)
        try {
            const response = await api.get(`/admin/shop/api/orders/${orderId}`)
            if (response.ok && response.data) {
                setOrder(response.data)
            }
        } catch (err) {
            console.error('Failed to load order:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleShip = async () => {
        if (!orderId) return
        try {
            await api.post(`/admin/shop/api/orders/${orderId}/ship`, shipForm)
            await loadOrder()
            setShowShipForm(false)
            onStatusChange(orderId, 'shipped')
        } catch (err) {
            console.error('Failed to ship order:', err)
        }
    }

    if (!isOpen) return null

    return (
        <div className="shop-slideout-overlay" onClick={onClose}>
            <div className="shop-slideout wide" onClick={e => e.stopPropagation()}>
                <div className="shop-slideout-header">
                    <h2>Order #{orderId}</h2>
                    <button className="shop-slideout-close" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>
                <div className="shop-slideout-body">
                    {loading ? (
                        <div className="shop-loading">Loading order details...</div>
                    ) : order ? (
                        <>
                            {/* Order Timeline */}
                            <div className="shop-order-timeline">
                                <div className={`shop-timeline-step ${order.created_at ? 'completed' : ''}`}>
                                    <Clock size={16} />
                                    <span>Created</span>
                                    {order.created_at && <small>{new Date(order.created_at).toLocaleDateString()}</small>}
                                </div>
                                <div className={`shop-timeline-step ${order.status !== 'pending' ? 'completed' : ''}`}>
                                    <CheckCircle size={16} />
                                    <span>Paid</span>
                                </div>
                                <div className={`shop-timeline-step ${order.shipped_at ? 'completed' : ''}`}>
                                    <Truck size={16} />
                                    <span>Shipped</span>
                                    {order.shipped_at && <small>{new Date(order.shipped_at).toLocaleDateString()}</small>}
                                </div>
                                <div className={`shop-timeline-step ${order.delivered_at ? 'completed' : ''}`}>
                                    <Package size={16} />
                                    <span>Delivered</span>
                                    {order.delivered_at && <small>{new Date(order.delivered_at).toLocaleDateString()}</small>}
                                </div>
                            </div>

                            {/* Status & Actions */}
                            <div className="shop-order-section">
                                <div className="shop-order-status-bar">
                                    <StatusBadge status={order.status} />
                                    <div className="shop-order-quick-actions">
                                        {(order.status === 'paid' || order.status === 'processing') && (
                                            <button className="shop-btn-sm primary" onClick={() => setShowShipForm(true)}>
                                                <Truck size={14} /> Ship Order
                                            </button>
                                        )}
                                        {order.status === 'paid' && order.stripe_payment_intent_id && (
                                            <button
                                                className="shop-btn-sm danger"
                                                onClick={() => {
                                                    if (confirm('Are you sure you want to refund this order?')) {
                                                        onRefund(order.id)
                                                    }
                                                }}
                                            >
                                                <RefreshCw size={14} /> Refund
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {showShipForm && (
                                    <div className="shop-ship-form">
                                        <div className="shop-form-row">
                                            <div className="shop-form-group">
                                                <label>Tracking Number</label>
                                                <input
                                                    type="text"
                                                    value={shipForm.tracking_number}
                                                    onChange={e => setShipForm({ ...shipForm, tracking_number: e.target.value })}
                                                    placeholder="Enter tracking number"
                                                />
                                            </div>
                                            <div className="shop-form-group">
                                                <label>Carrier</label>
                                                <select
                                                    value={shipForm.carrier}
                                                    onChange={e => setShipForm({ ...shipForm, carrier: e.target.value })}
                                                >
                                                    <option value="">Select carrier</option>
                                                    <option value="usps">USPS</option>
                                                    <option value="ups">UPS</option>
                                                    <option value="fedex">FedEx</option>
                                                    <option value="dhl">DHL</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="shop-form-actions">
                                            <button type="button" className="shop-btn secondary" onClick={() => setShowShipForm(false)}>
                                                Cancel
                                            </button>
                                            <button type="button" className="shop-btn primary" onClick={handleShip}>
                                                Mark as Shipped
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Customer Info */}
                            <div className="shop-order-section">
                                <h3>Customer</h3>
                                <div className="shop-info-grid">
                                    <div className="shop-info-item">
                                        <label>Email</label>
                                        <span>{order.email || 'N/A'}</span>
                                    </div>
                                    {order.customer && (
                                        <>
                                            <div className="shop-info-item">
                                                <label>Name</label>
                                                <span>{order.customer.name}</span>
                                            </div>
                                            {order.customer.phone && (
                                                <div className="shop-info-item">
                                                    <label>Phone</label>
                                                    <span>{order.customer.phone}</span>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Shipping Address */}
                            {order.shipping_address && (
                                <div className="shop-order-section">
                                    <h3>Shipping Address</h3>
                                    <p className="shop-address">{order.shipping_address}</p>
                                    {order.tracking_number && (
                                        <div className="shop-tracking">
                                            <strong>Tracking:</strong> {order.tracking_number} ({order.carrier?.toUpperCase()})
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Order Items */}
                            <div className="shop-order-section">
                                <h3>Items</h3>
                                <div className="shop-items-list">
                                    {order.items?.map((item: any) => (
                                        <div key={item.id} className="shop-item-row">
                                            <div className="shop-item-image">
                                                {item.image_url ? (
                                                    <img src={item.image_url} alt={item.product_name} />
                                                ) : (
                                                    <Package size={24} />
                                                )}
                                            </div>
                                            <div className="shop-item-info">
                                                <span className="shop-item-name">{item.product_name}</span>
                                                <span className="shop-item-type">
                                                    {item.is_digital ? 'Digital' : 'Physical'}
                                                </span>
                                            </div>
                                            <div className="shop-item-qty">×{item.quantity}</div>
                                            <div className="shop-item-price">{item.total_display}</div>
                                        </div>
                                    ))}
                                </div>
                                <div className="shop-order-total-row">
                                    <span>Total</span>
                                    <strong>{order.total_display}</strong>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="shop-error">Failed to load order</div>
                    )}
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

const UnifiedShopDashboard: React.FC<UnifiedShopDashboardProps> = ({
    initialTab = 'overview'
}) => {
    // State
    const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'orders'>(initialTab)
    const [stats, setStats] = useState<ShopStats | null>(null)
    const [products, setProducts] = useState<Product[]>([])
    const [orders, setOrders] = useState<Order[]>([])
    const [categories, setCategories] = useState<Category[]>([])
    const [loading, setLoading] = useState(true)

    // Products state
    const [productSearch, setProductSearch] = useState('')
    const [productFilter, setProductFilter] = useState('')
    const [productViewMode, setProductViewMode] = useState<'grid' | 'list'>('grid')
    const [productPage, setProductPage] = useState(1)
    const [productPagination, setProductPagination] = useState({ pages: 1, total: 0 })

    // Orders state
    const [orderSearch, setOrderSearch] = useState('')
    const [orderStatus, setOrderStatus] = useState('')
    const [orderPage, setOrderPage] = useState(1)
    const [orderPagination, setOrderPagination] = useState({ pages: 1, total: 0 })
    const [statusCounts, setStatusCounts] = useState<Record<string, number>>({})

    // Editor state
    const [editingProduct, setEditingProduct] = useState<Product | null>(null)
    const [showProductEditor, setShowProductEditor] = useState(false)
    const [viewingOrderId, setViewingOrderId] = useState<number | null>(null)
    const [showOrderDetail, setShowOrderDetail] = useState(false)

    // Load data
    useEffect(() => {
        loadStats()
        loadCategories()
    }, [])

    useEffect(() => {
        if (activeTab === 'products') {
            loadProducts()
        }
    }, [activeTab, productSearch, productFilter, productPage])

    useEffect(() => {
        if (activeTab === 'orders') {
            loadOrders()
        }
    }, [activeTab, orderSearch, orderStatus, orderPage])

    const loadStats = async () => {
        try {
            const response = await api.get('/admin/shop/api/stats')
            if (response.ok && response.data) {
                setStats(response.data)
            }
        } catch (err) {
            console.error('Failed to load stats:', err)
        } finally {
            setLoading(false)
        }
    }

    const loadCategories = async () => {
        try {
            const response = await api.get('/admin/shop/api/categories')
            if (response.ok && response.data) {
                setCategories(response.data.categories || [])
            }
        } catch (err) {
            console.error('Failed to load categories:', err)
        }
    }

    const loadProducts = async () => {
        try {
            const params = new URLSearchParams({
                page: productPage.toString(),
                per_page: '12',
            })
            if (productSearch) params.append('search', productSearch)
            if (productFilter === 'digital') params.append('type', 'digital')
            if (productFilter === 'physical') params.append('type', 'physical')
            if (productFilter === 'low_stock') params.append('low_stock', 'true')

            const response = await api.get(`/admin/shop/api/products?${params}`)
            if (response.ok && response.data) {
                setProducts(response.data.products || [])
                setProductPagination({ pages: response.data.pagination?.pages || 1, total: response.data.pagination?.total || 0 })
            }
        } catch (err) {
            console.error('Failed to load products:', err)
        }
    }

    const loadOrders = async () => {
        try {
            const params = new URLSearchParams({
                page: orderPage.toString(),
                per_page: '20',
            })
            if (orderSearch) params.append('search', orderSearch)
            if (orderStatus) params.append('status', orderStatus)

            const response = await api.get(`/admin/shop/api/orders?${params}`)
            if (response.ok && response.data) {
                setOrders(response.data.orders || [])
                setOrderPagination({ pages: response.data.pagination?.pages || 1, total: response.data.pagination?.total || 0 })
                setStatusCounts(response.data.status_counts || {})
            }
        } catch (err) {
            console.error('Failed to load orders:', err)
        }
    }

    const handleCreateProduct = () => {
        setEditingProduct(null)
        setShowProductEditor(true)
    }

    const handleEditProduct = (product: Product) => {
        setEditingProduct(product)
        setShowProductEditor(true)
    }

    const handleDeleteProduct = async (productId: number) => {
        if (!confirm('Are you sure you want to delete this product?')) return
        try {
            await api.delete(`/admin/shop/api/products/${productId}`)
            loadProducts()
            loadStats()
        } catch (err) {
            console.error('Failed to delete product:', err)
        }
    }

    const handleSaveProduct = async (data: Partial<Product>) => {
        try {
            if (editingProduct) {
                await api.put(`/admin/shop/api/products/${editingProduct.id}`, data)
            } else {
                await api.post('/admin/shop/api/products', data)
            }
            loadProducts()
            loadStats()
        } catch (err) {
            console.error('Failed to save product:', err)
            throw err
        }
    }

    const handleViewOrder = (order: Order) => {
        setViewingOrderId(order.id)
        setShowOrderDetail(true)
    }

    const handleUpdateOrderStatus = async (orderId: number, status: string) => {
        try {
            await api.post(`/admin/shop/api/orders/${orderId}/status`, { status })
            loadOrders()
            loadStats()
        } catch (err) {
            console.error('Failed to update order status:', err)
        }
    }

    const handleRefundOrder = async (orderId: number) => {
        try {
            await api.post(`/admin/shop/api/orders/${orderId}/refund`, {})
            loadOrders()
            loadStats()
            setShowOrderDetail(false)
        } catch (err) {
            console.error('Failed to refund order:', err)
        }
    }

    // Render
    return (
        <div className="unified-shop-dashboard">
            {/* Tab Navigation */}
            <div className="shop-tabs">
                <button
                    className={`shop-tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    <BarChart2 size={18} /> Overview
                </button>
                <button
                    className={`shop-tab ${activeTab === 'products' ? 'active' : ''}`}
                    onClick={() => setActiveTab('products')}
                >
                    <Package size={18} /> Products
                </button>
                <button
                    className={`shop-tab ${activeTab === 'orders' ? 'active' : ''}`}
                    onClick={() => setActiveTab('orders')}
                >
                    <ShoppingCart size={18} /> Orders
                </button>
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <div className="shop-overview">
                    {loading ? (
                        <div className="shop-loading">Loading dashboard...</div>
                    ) : stats ? (
                        <>
                            {/* KPI Grid */}
                            <div className="shop-kpi-grid">
                                <KPICard
                                    title="Revenue (Month)"
                                    value={stats.revenue.month_display}
                                    subtitle={`Today: ${stats.revenue.today_display}`}
                                    icon={<DollarSign size={24} />}
                                    iconColor="#10b981"
                                />
                                <KPICard
                                    title="Orders"
                                    value={stats.orders.month}
                                    subtitle={`Today: ${stats.orders.today}`}
                                    icon={<ShoppingCart size={24} />}
                                    iconColor="#3b82f6"
                                />
                                <KPICard
                                    title="Products"
                                    value={stats.products.total}
                                    subtitle={`${stats.products.digital} digital, ${stats.products.physical} physical`}
                                    icon={<Package size={24} />}
                                    iconColor="#8b5cf6"
                                />
                                <KPICard
                                    title="Low Stock"
                                    value={stats.products.low_stock}
                                    subtitle="Products need restock"
                                    icon={<AlertTriangle size={24} />}
                                    iconColor={stats.products.low_stock > 0 ? '#f59e0b' : '#6b7280'}
                                />
                            </div>

                            {/* Quick Panels */}
                            <div className="shop-panels-grid">
                                {/* Recent Orders */}
                                <div className="shop-panel">
                                    <div className="shop-panel-header">
                                        <h3>Recent Orders</h3>
                                        <button className="shop-link" onClick={() => setActiveTab('orders')}>
                                            View All →
                                        </button>
                                    </div>
                                    <div className="shop-panel-body">
                                        {stats.recent_orders.length > 0 ? (
                                            stats.recent_orders.map(order => (
                                                <div key={order.id} className="shop-recent-order">
                                                    <div className="shop-recent-order-info">
                                                        <span className="shop-recent-order-id">#{order.id}</span>
                                                        <span className="shop-recent-order-date">{order.date}</span>
                                                    </div>
                                                    <StatusBadge status={order.status} />
                                                    <span className="shop-recent-order-total">{order.total}</span>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="shop-empty">No recent orders</p>
                                        )}
                                    </div>
                                </div>

                                {/* Low Stock Alerts */}
                                <div className="shop-panel">
                                    <div className="shop-panel-header">
                                        <h3>Low Stock Alerts</h3>
                                        <button className="shop-link" onClick={() => {
                                            setProductFilter('low_stock')
                                            setActiveTab('products')
                                        }}>
                                            View All →
                                        </button>
                                    </div>
                                    <div className="shop-panel-body">
                                        {stats.low_stock_alerts.length > 0 ? (
                                            stats.low_stock_alerts.map(product => (
                                                <div key={product.id} className="shop-low-stock-item">
                                                    <span className="shop-low-stock-name">{product.name}</span>
                                                    <span className="shop-low-stock-count">{product.inventory} left</span>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="shop-empty">All products stocked</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="shop-error">Failed to load dashboard</div>
                    )}
                </div>
            )}

            {/* Products Tab */}
            {activeTab === 'products' && (
                <div className="shop-products">
                    {/* Header */}
                    <div className="shop-section-header">
                        <div className="shop-search-bar">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Search products..."
                                value={productSearch}
                                onChange={e => {
                                    setProductSearch(e.target.value)
                                    setProductPage(1)
                                }}
                            />
                        </div>
                        <div className="shop-filters">
                            <select
                                value={productFilter}
                                onChange={e => {
                                    setProductFilter(e.target.value)
                                    setProductPage(1)
                                }}
                            >
                                <option value="">All Products</option>
                                <option value="digital">Digital</option>
                                <option value="physical">Physical</option>
                                <option value="low_stock">Low Stock</option>
                            </select>
                            <div className="shop-view-toggle">
                                <button
                                    className={productViewMode === 'grid' ? 'active' : ''}
                                    onClick={() => setProductViewMode('grid')}
                                >
                                    <Grid size={18} />
                                </button>
                                <button
                                    className={productViewMode === 'list' ? 'active' : ''}
                                    onClick={() => setProductViewMode('list')}
                                >
                                    <List size={18} />
                                </button>
                            </div>
                        </div>
                        <button className="shop-btn primary" onClick={handleCreateProduct}>
                            <Plus size={18} /> New Product
                        </button>
                    </div>

                    {/* Products Grid/List */}
                    <div className={`shop-products-container ${productViewMode}`}>
                        {products.length > 0 ? (
                            products.map(product => (
                                <ProductCard
                                    key={product.id}
                                    product={product}
                                    viewMode={productViewMode}
                                    onEdit={handleEditProduct}
                                    onDelete={handleDeleteProduct}
                                />
                            ))
                        ) : (
                            <div className="shop-empty-state">
                                <Package size={48} />
                                <h3>No products found</h3>
                                <p>Create your first product to get started</p>
                                <button className="shop-btn primary" onClick={handleCreateProduct}>
                                    <Plus size={18} /> Create Product
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Pagination */}
                    {productPagination.pages > 1 && (
                        <div className="shop-pagination">
                            <button
                                disabled={productPage === 1}
                                onClick={() => setProductPage(p => p - 1)}
                            >
                                <ChevronLeft size={18} /> Previous
                            </button>
                            <span>Page {productPage} of {productPagination.pages}</span>
                            <button
                                disabled={productPage === productPagination.pages}
                                onClick={() => setProductPage(p => p + 1)}
                            >
                                Next <ChevronRight size={18} />
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Orders Tab */}
            {activeTab === 'orders' && (
                <div className="shop-orders">
                    {/* Header */}
                    <div className="shop-section-header">
                        <div className="shop-search-bar">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Search by email..."
                                value={orderSearch}
                                onChange={e => {
                                    setOrderSearch(e.target.value)
                                    setOrderPage(1)
                                }}
                            />
                        </div>
                        <div className="shop-status-filters">
                            <button
                                className={`shop-status-chip ${orderStatus === '' ? 'active' : ''}`}
                                onClick={() => { setOrderStatus(''); setOrderPage(1) }}
                            >
                                All ({statusCounts.all || 0})
                            </button>
                            <button
                                className={`shop-status-chip ${orderStatus === 'pending' ? 'active' : ''}`}
                                onClick={() => { setOrderStatus('pending'); setOrderPage(1) }}
                            >
                                Pending ({statusCounts.pending || 0})
                            </button>
                            <button
                                className={`shop-status-chip ${orderStatus === 'paid' ? 'active' : ''}`}
                                onClick={() => { setOrderStatus('paid'); setOrderPage(1) }}
                            >
                                Paid ({statusCounts.paid || 0})
                            </button>
                            <button
                                className={`shop-status-chip ${orderStatus === 'shipped' ? 'active' : ''}`}
                                onClick={() => { setOrderStatus('shipped'); setOrderPage(1) }}
                            >
                                Shipped ({statusCounts.shipped || 0})
                            </button>
                            <button
                                className={`shop-status-chip ${orderStatus === 'delivered' ? 'active' : ''}`}
                                onClick={() => { setOrderStatus('delivered'); setOrderPage(1) }}
                            >
                                Delivered ({statusCounts.delivered || 0})
                            </button>
                        </div>
                    </div>

                    {/* Orders Table */}
                    <div className="shop-orders-table">
                        <div className="shop-orders-header">
                            <div>Order</div>
                            <div>Customer</div>
                            <div>Items</div>
                            <div>Total</div>
                            <div>Status</div>
                            <div>Actions</div>
                        </div>
                        {orders.length > 0 ? (
                            orders.map(order => (
                                <OrderRow
                                    key={order.id}
                                    order={order}
                                    onView={handleViewOrder}
                                    onUpdateStatus={handleUpdateOrderStatus}
                                />
                            ))
                        ) : (
                            <div className="shop-empty-state">
                                <ShoppingCart size={48} />
                                <h3>No orders found</h3>
                                <p>Orders will appear here when customers make purchases</p>
                            </div>
                        )}
                    </div>

                    {/* Pagination */}
                    {orderPagination.pages > 1 && (
                        <div className="shop-pagination">
                            <button
                                disabled={orderPage === 1}
                                onClick={() => setOrderPage(p => p - 1)}
                            >
                                <ChevronLeft size={18} /> Previous
                            </button>
                            <span>Page {orderPage} of {orderPagination.pages}</span>
                            <button
                                disabled={orderPage === orderPagination.pages}
                                onClick={() => setOrderPage(p => p + 1)}
                            >
                                Next <ChevronRight size={18} />
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Product Editor Slideout */}
            <ProductEditor
                product={editingProduct}
                isOpen={showProductEditor}
                onClose={() => setShowProductEditor(false)}
                onSave={handleSaveProduct}
                categories={categories}
            />

            {/* Order Detail Slideout */}
            <OrderDetail
                orderId={viewingOrderId}
                isOpen={showOrderDetail}
                onClose={() => setShowOrderDetail(false)}
                onStatusChange={handleUpdateOrderStatus}
                onRefund={handleRefundOrder}
            />
        </div>
    )
}

export default UnifiedShopDashboard
