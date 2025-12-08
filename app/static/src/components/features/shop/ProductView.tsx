/**
 * ProductView Component
 * 
 * Interactive product view with variant selection, quantity input, and add to cart.
 * Replaces the inline JavaScript in shop/product.html.
 */

import { useState, useEffect } from 'react'
import { Heart, ShoppingCart, Zap, Star, Minus, Plus, Check, AlertTriangle, X } from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

export interface ProductImage {
    id: string
    src: string
    alt?: string
    variantId?: string
    isPrimary?: boolean
}

export interface ProductVariant {
    id: string
    name: string
    sku: string
    price: number
    priceAdjustment: number
    inventoryCount: number
    isActive: boolean
}

export interface ProductViewProps {
    /** Product ID */
    productId: string | number
    /** Product name */
    name: string
    /** Product description */
    description?: string
    /** Base price in cents */
    price: number
    /** Product images */
    images?: ProductImage[]
    /** Product variants */
    variants?: ProductVariant[]
    /** Inventory count */
    inventoryCount: number
    /** Is digital product */
    isDigital?: boolean
    /** Category name */
    category?: string
    /** Is in wishlist */
    inWishlist?: boolean
    /** Add to cart URL */
    addToCartUrl: string
    /** Buy now URL */
    buyNowUrl?: string
    /** Wishlist toggle URL */
    wishlistUrl?: string
    /** Show quantity selector */
    showQuantity?: boolean
    /** Additional class */
    className?: string
}

// =============================================================================
// Main Component
// =============================================================================

export function ProductView({
    productId,
    name,
    description,
    price: basePrice,
    images = [],
    variants = [],
    inventoryCount,
    isDigital = false,
    category,
    inWishlist: initialInWishlist = false,
    addToCartUrl,
    buyNowUrl,
    wishlistUrl,
    showQuantity = true,
    className = '',
}: ProductViewProps) {
    const [mainImage, setMainImage] = useState(images[0]?.src || '')
    const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(
        variants.find(v => v.isActive) || null
    )
    const [quantity, setQuantity] = useState(1)
    const [inWishlist, setInWishlist] = useState(initialInWishlist)
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

    // Calculate current price and inventory
    const currentPrice = selectedVariant
        ? selectedVariant.price
        : basePrice

    const currentInventory = selectedVariant
        ? selectedVariant.inventoryCount
        : inventoryCount

    const currentSku = selectedVariant?.sku || String(productId)

    // Update quantity max when variant changes
    useEffect(() => {
        if (quantity > currentInventory) {
            setQuantity(Math.max(1, currentInventory))
        }
    }, [currentInventory])

    // Select variant
    const handleVariantSelect = (variant: ProductVariant) => {
        setSelectedVariant(variant)

        // Switch to variant image if exists
        const variantImage = images.find(img => img.variantId === variant.id)
        if (variantImage) {
            setMainImage(variantImage.src)
        }
    }

    // Adjust quantity
    const adjustQuantity = (delta: number) => {
        setQuantity(prev => Math.max(1, Math.min(prev + delta, currentInventory || 99)))
    }

    // Add to cart
    const handleAddToCart = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setMessage(null)

        try {
            const response = await api.post(addToCartUrl, {
                quantity,
                variant_id: selectedVariant?.id || '',
            })

            if (response.ok) {
                setMessage({ type: 'success', text: 'Added to cart!' })
                // Dispatch custom event for cart widget to update
                window.dispatchEvent(new CustomEvent('cart:updated'))
            } else {
                setMessage({ type: 'error', text: response.error || 'Failed to add to cart' })
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to add to cart' })
        } finally {
            setLoading(false)
        }
    }

    // Toggle wishlist
    const handleWishlistToggle = async () => {
        if (!wishlistUrl) return

        try {
            const response = await api.post(wishlistUrl)
            if (response.ok) {
                setInWishlist(!inWishlist)
            }
        } catch (err) {
            console.error('Wishlist error:', err)
        }
    }

    // Format price
    const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

    return (
        <div className={`product-view ${className}`}>
            <div className="product-view-grid">
                {/* Image Gallery */}
                <div className="product-images">
                    <div className="product-main-image">
                        {mainImage ? (
                            <img src={mainImage} alt={name} />
                        ) : (
                            <div className="product-no-image">
                                <span>No image</span>
                            </div>
                        )}

                        {/* Wishlist button */}
                        {wishlistUrl && (
                            <button
                                className={`product-wishlist-btn ${inWishlist ? 'active' : ''}`}
                                onClick={handleWishlistToggle}
                                aria-label={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
                            >
                                <Heart />
                            </button>
                        )}
                    </div>

                    {/* Thumbnails */}
                    {images.length > 1 && (
                        <div className="product-thumbnails">
                            {images.map((img, index) => (
                                <button
                                    key={img.id || index}
                                    className={`product-thumbnail ${mainImage === img.src ? 'active' : ''}`}
                                    onClick={() => setMainImage(img.src)}
                                >
                                    <img src={img.src} alt={img.alt || `${name} ${index + 1}`} />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Product Info */}
                <div className="product-info">
                    <h1 className="product-name">{name}</h1>

                    {/* Price */}
                    <div className="product-price">
                        {formatPrice(currentPrice)}
                    </div>

                    {/* Rating placeholder */}
                    <div className="product-rating">
                        {[1, 2, 3, 4, 5].map(star => (
                            <Star
                                key={star}
                                className={`star ${star <= 4 ? 'filled' : ''}`}
                            />
                        ))}
                        <span className="rating-count">(0 reviews)</span>
                    </div>

                    {/* Description */}
                    {description && (
                        <p className="product-description">{description}</p>
                    )}

                    {/* Badges */}
                    <div className="product-badges">
                        {isDigital ? (
                            <span className="product-badge badge-digital">
                                Digital Download
                            </span>
                        ) : (
                            <span className="product-badge badge-physical">
                                Physical Product
                            </span>
                        )}

                        {currentInventory > 10 ? (
                            <span className="product-badge badge-success">
                                <Check className="badge-icon" /> In Stock
                            </span>
                        ) : currentInventory > 0 ? (
                            <span className="product-badge badge-warning">
                                <AlertTriangle className="badge-icon" /> Low Stock ({currentInventory} left)
                            </span>
                        ) : (
                            <span className="product-badge badge-danger">
                                <X className="badge-icon" /> Out of Stock
                            </span>
                        )}
                    </div>

                    {/* Variant Selection */}
                    {variants.length > 0 && (
                        <div className="product-variants">
                            <label className="variants-label">Select Option:</label>
                            <div className="variant-buttons">
                                {variants.filter(v => v.isActive).map(variant => (
                                    <button
                                        key={variant.id}
                                        className={`variant-btn ${selectedVariant?.id === variant.id ? 'active' : ''}`}
                                        onClick={() => handleVariantSelect(variant)}
                                    >
                                        {variant.name}
                                        {variant.priceAdjustment !== 0 && (
                                            <small>
                                                ({variant.priceAdjustment > 0 ? '+' : ''}
                                                {formatPrice(variant.priceAdjustment)})
                                            </small>
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Add to Cart Form */}
                    <form onSubmit={handleAddToCart} className="product-form">
                        {/* Quantity */}
                        {showQuantity && currentInventory > 0 && (
                            <div className="product-quantity">
                                <label className="quantity-label">Quantity:</label>
                                <div className="quantity-input">
                                    <button
                                        type="button"
                                        onClick={() => adjustQuantity(-1)}
                                        disabled={quantity <= 1}
                                    >
                                        <Minus />
                                    </button>
                                    <input
                                        type="number"
                                        value={quantity}
                                        onChange={e => setQuantity(Math.max(1, Math.min(parseInt(e.target.value) || 1, currentInventory)))}
                                        min="1"
                                        max={currentInventory}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => adjustQuantity(1)}
                                        disabled={quantity >= currentInventory}
                                    >
                                        <Plus />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="product-actions">
                            {currentInventory > 0 ? (
                                <>
                                    <button
                                        type="submit"
                                        className="btn-add-to-cart"
                                        disabled={loading}
                                    >
                                        <ShoppingCart />
                                        {loading ? 'Adding...' : 'Add to Cart'}
                                    </button>
                                    {buyNowUrl && (
                                        <a href={buyNowUrl} className="btn-buy-now">
                                            <Zap />
                                            Buy Now
                                        </a>
                                    )}
                                </>
                            ) : (
                                <button className="btn-sold-out" disabled>
                                    <X />
                                    Sold Out
                                </button>
                            )}
                        </div>

                        {/* Message */}
                        {message && (
                            <div className={`product-message ${message.type}`}>
                                {message.text}
                            </div>
                        )}
                    </form>

                    {/* Meta */}
                    <div className="product-meta">
                        <p><strong>SKU:</strong> {currentSku}</p>
                        {category && <p><strong>Category:</strong> {category}</p>}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ProductView
