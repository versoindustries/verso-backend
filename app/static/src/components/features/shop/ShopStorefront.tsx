/**
 * ShopStorefront - Enterprise E-commerce Storefront
 * 
 * Premium React storefront component with glassmorphism design,
 * real-time filtering, category navigation, and cart integration.
 */

import React, { useState, useEffect } from 'react'
import {
    Search,
    Grid,
    List,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    ShoppingCart,
    Heart,
    Tag,
    Package,
    Star,
    Sparkles,
    ArrowUp,
    X,
    SlidersHorizontal
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
    category_name: string | null
    image_url: string | null
    rating: number
    reviews_count: number
    is_new: boolean
    is_featured: boolean
    in_wishlist: boolean
}

interface Category {
    id: number
    name: string
    slug: string
    product_count: number
}

interface ShopStorefrontProps {
    /** Initial products from server */
    initialProducts?: Product[]
    /** Initial categories from server */
    initialCategories?: Category[]
    /** Add to cart URL template */
    addToCartUrlTemplate?: string
    /** Product URL template */
    productUrlTemplate?: string
    /** Wishlist URL template */
    wishlistUrlTemplate?: string
    /** Show hero section */
    showHero?: boolean
    /** Hero title */
    heroTitle?: string
    /** Hero subtitle */
    heroSubtitle?: string
}

// =============================================================================
// ProductCard Component
// =============================================================================

interface ProductCardProps {
    product: Product
    viewMode: 'grid' | 'list'
    productUrl: string
    addToCartUrl: string
    wishlistUrl?: string
    onAddToCart: (productId: number) => void
    onToggleWishlist: (productId: number) => void
}

const ProductCard: React.FC<ProductCardProps> = ({
    product,
    viewMode,
    productUrl,
    onAddToCart,
    onToggleWishlist
}) => {
    const [inWishlist, setInWishlist] = useState(product.in_wishlist)
    const [addingToCart, setAddingToCart] = useState(false)

    const handleAddToCart = async (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setAddingToCart(true)
        try {
            await onAddToCart(product.id)
        } finally {
            setAddingToCart(false)
        }
    }

    const handleWishlistToggle = async (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setInWishlist(!inWishlist)
        onToggleWishlist(product.id)
    }

    const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

    if (viewMode === 'list') {
        return (
            <div className="shop-product-row">
                <a href={productUrl} className="shop-product-row-image">
                    {product.image_url ? (
                        <img src={product.image_url} alt={product.name} />
                    ) : (
                        <div className="shop-product-placeholder">
                            <Package size={32} />
                        </div>
                    )}
                </a>
                <div className="shop-product-row-info">
                    <a href={productUrl} className="shop-product-row-name">{product.name}</a>
                    <p className="shop-product-row-desc">{product.description?.substring(0, 100)}...</p>
                    <div className="shop-product-row-meta">
                        {product.category_name && (
                            <span className="shop-product-category">{product.category_name}</span>
                        )}
                        {product.is_digital ? (
                            <span className="shop-badge digital">Digital</span>
                        ) : (
                            <span className="shop-badge physical">Physical</span>
                        )}
                        {product.is_new && <span className="shop-badge new">New</span>}
                    </div>
                </div>
                <div className="shop-product-row-rating">
                    {[1, 2, 3, 4, 5].map(star => (
                        <Star
                            key={star}
                            size={14}
                            className={star <= Math.round(product.rating) ? 'filled' : ''}
                        />
                    ))}
                    <span>({product.reviews_count})</span>
                </div>
                <div className="shop-product-row-price">
                    {product.price_display || formatPrice(product.price)}
                </div>
                <div className="shop-product-row-actions">
                    <button
                        className={`shop-wishlist-btn ${inWishlist ? 'active' : ''}`}
                        onClick={handleWishlistToggle}
                        aria-label="Add to wishlist"
                    >
                        <Heart size={18} />
                    </button>
                    <button
                        className="shop-add-cart-btn"
                        onClick={handleAddToCart}
                        disabled={addingToCart || product.inventory_count === 0}
                    >
                        <ShoppingCart size={18} />
                        {addingToCart ? 'Adding...' : 'Add'}
                    </button>
                </div>
            </div>
        )
    }

    // Grid view
    return (
        <div className="shop-product-card">
            {/* Badges */}
            <div className="shop-product-badges">
                {product.is_new && <span className="shop-badge new"><Sparkles size={12} /> New</span>}
                {product.is_featured && <span className="shop-badge featured"><Star size={12} /> Featured</span>}
            </div>

            {/* Wishlist button */}
            <button
                className={`shop-product-wishlist ${inWishlist ? 'active' : ''}`}
                onClick={handleWishlistToggle}
                aria-label={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
            >
                <Heart size={20} />
            </button>

            {/* Image */}
            <a href={productUrl} className="shop-product-image">
                {product.image_url ? (
                    <img src={product.image_url} alt={product.name} loading="lazy" />
                ) : (
                    <div className="shop-product-placeholder">
                        <Package size={48} />
                    </div>
                )}

                {/* Quick action overlay */}
                <div className="shop-product-overlay">
                    <button
                        className="shop-quick-add"
                        onClick={handleAddToCart}
                        disabled={addingToCart || product.inventory_count === 0}
                    >
                        <ShoppingCart size={18} />
                        {product.inventory_count === 0 ? 'Sold Out' : (addingToCart ? 'Adding...' : 'Add to Cart')}
                    </button>
                </div>
            </a>

            {/* Content */}
            <div className="shop-product-content">
                {product.category_name && (
                    <span className="shop-product-category">{product.category_name}</span>
                )}

                <a href={productUrl} className="shop-product-name">{product.name}</a>

                {/* Rating */}
                <div className="shop-product-rating">
                    {[1, 2, 3, 4, 5].map(star => (
                        <Star
                            key={star}
                            size={14}
                            className={star <= Math.round(product.rating) ? 'filled' : ''}
                        />
                    ))}
                    {product.reviews_count > 0 && (
                        <span className="shop-rating-count">({product.reviews_count})</span>
                    )}
                </div>

                {/* Price & Stock */}
                <div className="shop-product-footer">
                    <span className="shop-product-price">
                        {product.price_display || formatPrice(product.price)}
                    </span>
                    {!product.is_digital && (
                        <span className={`shop-product-stock ${product.inventory_count < 10 ? 'low' : ''}`}>
                            {product.inventory_count === 0 ? (
                                'Out of Stock'
                            ) : product.inventory_count < 10 ? (
                                `Only ${product.inventory_count} left`
                            ) : (
                                'In Stock'
                            )}
                        </span>
                    )}
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// CategorySidebar Component
// =============================================================================

interface CategorySidebarProps {
    categories: Category[]
    selectedCategory: number | null
    onSelectCategory: (categoryId: number | null) => void
    totalProducts: number
}

const CategorySidebar: React.FC<CategorySidebarProps> = ({
    categories,
    selectedCategory,
    onSelectCategory,
    totalProducts
}) => {
    return (
        <aside className="shop-sidebar">
            <div className="shop-sidebar-section">
                <h3 className="shop-sidebar-title">
                    <Tag size={18} /> Categories
                </h3>
                <ul className="shop-category-list">
                    <li>
                        <button
                            className={`shop-category-item ${selectedCategory === null ? 'active' : ''}`}
                            onClick={() => onSelectCategory(null)}
                        >
                            <span>All Products</span>
                            <span className="shop-category-count">{totalProducts}</span>
                        </button>
                    </li>
                    {categories.map(category => (
                        <li key={category.id}>
                            <button
                                className={`shop-category-item ${selectedCategory === category.id ? 'active' : ''}`}
                                onClick={() => onSelectCategory(category.id)}
                            >
                                <span>{category.name}</span>
                                <span className="shop-category-count">{category.product_count}</span>
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
        </aside>
    )
}

// =============================================================================
// Main ShopStorefront Component
// =============================================================================

export const ShopStorefront: React.FC<ShopStorefrontProps> = ({
    initialProducts = [],
    initialCategories = [],
    addToCartUrlTemplate = '/shop/cart/add/{id}',
    productUrlTemplate = '/shop/{id}',
    wishlistUrlTemplate = '/ecommerce/wishlist/add/{id}',
    showHero = true,
    heroTitle = 'Discover Our Collection',
    heroSubtitle = 'Premium products crafted for excellence'
}) => {
    // State
    const [products, setProducts] = useState<Product[]>(initialProducts)
    const [categories, setCategories] = useState<Category[]>(initialCategories)
    const [loading, setLoading] = useState(!initialProducts.length)
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
    const [sortBy, setSortBy] = useState<string>('newest')
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [showFilters, setShowFilters] = useState(false)
    const [priceRange] = useState<[number, number]>([0, 100000])
    const [showBackToTop, setShowBackToTop] = useState(false)

    // Load products
    useEffect(() => {
        loadProducts()
    }, [searchQuery, selectedCategory, sortBy, page])

    // Load categories on mount
    useEffect(() => {
        if (!initialCategories.length) {
            loadCategories()
        }
    }, [])

    // Scroll to top button visibility
    useEffect(() => {
        const handleScroll = () => {
            setShowBackToTop(window.scrollY > 400)
        }
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    const loadProducts = async () => {
        setLoading(true)
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                per_page: '12',
                sort: sortBy
            })
            if (searchQuery) params.append('search', searchQuery)
            if (selectedCategory) params.append('category', selectedCategory.toString())
            if (priceRange[0] > 0) params.append('min_price', priceRange[0].toString())
            if (priceRange[1] < 100000) params.append('max_price', priceRange[1].toString())

            const response = await api.get(`/shop/api/products?${params}`)
            if (response.ok && response.data) {
                setProducts(response.data.products || [])
                setTotalPages(response.data.pagination?.pages || 1)
            }
        } catch (err) {
            console.error('Failed to load products:', err)
        } finally {
            setLoading(false)
        }
    }

    const loadCategories = async () => {
        try {
            const response = await api.get('/shop/api/categories')
            if (response.ok && response.data) {
                setCategories(response.data.categories || [])
            }
        } catch (err) {
            console.error('Failed to load categories:', err)
        }
    }

    const handleAddToCart = async (productId: number) => {
        try {
            const url = addToCartUrlTemplate.replace('{id}', productId.toString())
            const response = await api.post(url, { quantity: 1 })
            if (response.ok) {
                // Dispatch cart update event
                window.dispatchEvent(new CustomEvent('cart:updated'))
                // Show toast notification
                window.dispatchEvent(new CustomEvent('toast', {
                    detail: { message: 'Added to cart!', type: 'success' }
                }))
            }
        } catch (err) {
            console.error('Failed to add to cart:', err)
        }
    }

    const handleToggleWishlist = async (productId: number) => {
        try {
            const url = wishlistUrlTemplate.replace('{id}', productId.toString())
            await api.post(url)
        } catch (err) {
            console.error('Failed to toggle wishlist:', err)
        }
    }

    const getProductUrl = (productId: number) => {
        return productUrlTemplate.replace('{id}', productId.toString())
    }

    const getAddToCartUrl = (productId: number) => {
        return addToCartUrlTemplate.replace('{id}', productId.toString())
    }

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        setPage(1)
        loadProducts()
    }

    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const totalProducts = products.length

    return (
        <div className="shop-storefront">
            {/* Hero Section */}
            {showHero && (
                <section className="shop-hero">
                    <div className="shop-hero-content">
                        <h1 className="shop-hero-title">{heroTitle}</h1>
                        <p className="shop-hero-subtitle">{heroSubtitle}</p>
                        <form onSubmit={handleSearch} className="shop-hero-search">
                            <Search size={20} />
                            <input
                                type="text"
                                placeholder="Search products..."
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                            />
                            <button type="submit">Search</button>
                        </form>
                    </div>
                    <div className="shop-hero-overlay"></div>
                </section>
            )}

            {/* Main Content */}
            <div className="shop-main">
                {/* Sidebar - Desktop */}
                <CategorySidebar
                    categories={categories}
                    selectedCategory={selectedCategory}
                    onSelectCategory={(id) => {
                        setSelectedCategory(id)
                        setPage(1)
                    }}
                    totalProducts={totalProducts}
                />

                {/* Products Section */}
                <section className="shop-products-section">
                    {/* Toolbar */}
                    <div className="shop-toolbar">
                        <div className="shop-toolbar-left">
                            <button
                                className="shop-filter-toggle"
                                onClick={() => setShowFilters(!showFilters)}
                            >
                                <SlidersHorizontal size={18} />
                                Filters
                            </button>
                            <span className="shop-results-count">
                                {totalProducts} {totalProducts === 1 ? 'product' : 'products'}
                            </span>
                        </div>

                        <div className="shop-toolbar-right">
                            {/* Sort */}
                            <div className="shop-sort">
                                <label>Sort by:</label>
                                <select
                                    value={sortBy}
                                    onChange={e => {
                                        setSortBy(e.target.value)
                                        setPage(1)
                                    }}
                                >
                                    <option value="newest">Newest</option>
                                    <option value="price_low">Price: Low to High</option>
                                    <option value="price_high">Price: High to Low</option>
                                    <option value="popular">Most Popular</option>
                                    <option value="rating">Highest Rated</option>
                                </select>
                                <ChevronDown size={16} />
                            </div>

                            {/* View Toggle */}
                            <div className="shop-view-toggle">
                                <button
                                    className={viewMode === 'grid' ? 'active' : ''}
                                    onClick={() => setViewMode('grid')}
                                    aria-label="Grid view"
                                >
                                    <Grid size={18} />
                                </button>
                                <button
                                    className={viewMode === 'list' ? 'active' : ''}
                                    onClick={() => setViewMode('list')}
                                    aria-label="List view"
                                >
                                    <List size={18} />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Active Filters */}
                    {(searchQuery || selectedCategory) && (
                        <div className="shop-active-filters">
                            {searchQuery && (
                                <span className="shop-filter-tag">
                                    Search: "{searchQuery}"
                                    <button onClick={() => setSearchQuery('')}><X size={14} /></button>
                                </span>
                            )}
                            {selectedCategory && (
                                <span className="shop-filter-tag">
                                    Category: {categories.find(c => c.id === selectedCategory)?.name}
                                    <button onClick={() => setSelectedCategory(null)}><X size={14} /></button>
                                </span>
                            )}
                            <button
                                className="shop-clear-filters"
                                onClick={() => {
                                    setSearchQuery('')
                                    setSelectedCategory(null)
                                }}
                            >
                                Clear All
                            </button>
                        </div>
                    )}

                    {/* Products Grid/List */}
                    {loading ? (
                        <div className="shop-loading">
                            <div className="shop-spinner"></div>
                            <span>Loading products...</span>
                        </div>
                    ) : products.length > 0 ? (
                        <div className={`shop-products-grid ${viewMode}`}>
                            {products.map(product => (
                                <ProductCard
                                    key={product.id}
                                    product={product}
                                    viewMode={viewMode}
                                    productUrl={getProductUrl(product.id)}
                                    addToCartUrl={getAddToCartUrl(product.id)}
                                    onAddToCart={handleAddToCart}
                                    onToggleWishlist={handleToggleWishlist}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="shop-empty-state">
                            <Package size={64} />
                            <h3>No Products Found</h3>
                            <p>Try adjusting your search or filters</p>
                            {(searchQuery || selectedCategory) && (
                                <button
                                    className="shop-btn primary"
                                    onClick={() => {
                                        setSearchQuery('')
                                        setSelectedCategory(null)
                                    }}
                                >
                                    Clear Filters
                                </button>
                            )}
                        </div>
                    )}

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="shop-pagination">
                            <button
                                className="shop-page-btn"
                                disabled={page === 1}
                                onClick={() => setPage(p => p - 1)}
                            >
                                <ChevronLeft size={18} /> Previous
                            </button>

                            <div className="shop-page-numbers">
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    let pageNum: number
                                    if (totalPages <= 5) {
                                        pageNum = i + 1
                                    } else if (page <= 3) {
                                        pageNum = i + 1
                                    } else if (page >= totalPages - 2) {
                                        pageNum = totalPages - 4 + i
                                    } else {
                                        pageNum = page - 2 + i
                                    }
                                    return (
                                        <button
                                            key={pageNum}
                                            className={`shop-page-num ${page === pageNum ? 'active' : ''}`}
                                            onClick={() => setPage(pageNum)}
                                        >
                                            {pageNum}
                                        </button>
                                    )
                                })}
                            </div>

                            <button
                                className="shop-page-btn"
                                disabled={page === totalPages}
                                onClick={() => setPage(p => p + 1)}
                            >
                                Next <ChevronRight size={18} />
                            </button>
                        </div>
                    )}
                </section>
            </div>

            {/* Back to Top */}
            {showBackToTop && (
                <button className="shop-back-to-top" onClick={scrollToTop}>
                    <ArrowUp size={20} />
                </button>
            )}
        </div>
    )
}

export default ShopStorefront
