/**
 * CartPage Component
 * 
 * Interactive shopping cart with quantity controls, real-time totals,
 * and HTMX-compatible actions.
 */

import { useState, useEffect } from 'react'
import { ShoppingCart, Trash2, Plus, Minus, ArrowLeft, ShoppingBag } from 'lucide-react'
import { useToastApi } from '../../../hooks/useToastApi'

// =============================================================================
// Types
// =============================================================================

export interface CartItem {
    productId: string | number
    name: string
    price: number
    quantity: number
    maxQuantity: number
    imageUrl?: string
    productUrl: string
    isDigital: boolean
    itemTotal: number
}

export interface CartPageProps {
    /** Cart items */
    items: CartItem[]
    /** Subtotal in cents */
    subtotal: number
    /** Update quantity URL pattern - use {productId} as placeholder */
    updateQuantityUrlPattern: string
    /** Remove item URL pattern - use {productId} as placeholder */
    removeItemUrlPattern: string
    /** Checkout URL */
    checkoutUrl: string
    /** Clear cart URL */
    clearCartUrl: string
    /** Continue shopping URL */
    shopUrl: string
    /** CSRF token */
    csrfToken: string
}

// =============================================================================
// Helper Functions
// =============================================================================

const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

// =============================================================================
// Cart Item Component
// =============================================================================

interface CartItemRowProps {
    item: CartItem
    onQuantityChange: (productId: string | number, newQuantity: number) => void
    onRemove: (productId: string | number) => void
    isLoading: boolean
}

function CartItemRow({ item, onQuantityChange, onRemove, isLoading }: CartItemRowProps) {
    const handleDecrease = () => {
        if (item.quantity > 1) {
            onQuantityChange(item.productId, item.quantity - 1)
        }
    }

    const handleIncrease = () => {
        if (item.quantity < item.maxQuantity) {
            onQuantityChange(item.productId, item.quantity + 1)
        }
    }

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value) || 1
        const clampedValue = Math.max(1, Math.min(value, item.maxQuantity))
        onQuantityChange(item.productId, clampedValue)
    }

    return (
        <div className="cart-item" id={`cart-item-${item.productId}`}>
            <div className="cart-item-image">
                {item.imageUrl ? (
                    <img src={item.imageUrl} alt={item.name} />
                ) : (
                    <div className="placeholder-image">
                        <ShoppingBag />
                    </div>
                )}
            </div>

            <div className="cart-item-details">
                <h3>
                    <a href={item.productUrl}>{item.name}</a>
                </h3>
                <p className="item-price">{formatPrice(item.price)}</p>
                {item.isDigital && (
                    <span className="badge badge-digital">Digital Product</span>
                )}
            </div>

            <div className="cart-item-quantity">
                <button
                    type="button"
                    className="qty-btn qty-minus"
                    onClick={handleDecrease}
                    disabled={isLoading || item.quantity <= 1}
                    aria-label="Decrease quantity"
                >
                    <Minus size={14} />
                </button>
                <input
                    type="number"
                    value={item.quantity}
                    onChange={handleInputChange}
                    min={1}
                    max={item.maxQuantity}
                    className="qty-input"
                    disabled={isLoading}
                />
                <button
                    type="button"
                    className="qty-btn qty-plus"
                    onClick={handleIncrease}
                    disabled={isLoading || item.quantity >= item.maxQuantity}
                    aria-label="Increase quantity"
                >
                    <Plus size={14} />
                </button>
            </div>

            <div className="cart-item-total">
                <strong>{formatPrice(item.itemTotal)}</strong>
            </div>

            <div className="cart-item-remove">
                <button
                    type="button"
                    className="btn-remove"
                    onClick={() => onRemove(item.productId)}
                    disabled={isLoading}
                    title="Remove item"
                    aria-label="Remove item"
                >
                    <Trash2 size={18} />
                </button>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function CartPage({
    items: initialItems,
    subtotal: initialSubtotal,
    updateQuantityUrlPattern,
    removeItemUrlPattern,
    checkoutUrl,
    clearCartUrl,
    shopUrl,
    csrfToken,
}: CartPageProps) {
    const [items, setItems] = useState<CartItem[]>(initialItems)
    const [subtotal, setSubtotal] = useState(initialSubtotal)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const api = useToastApi()

    // Recalculate subtotal when items change
    useEffect(() => {
        const newSubtotal = items.reduce((sum, item) => sum + item.itemTotal, 0)
        setSubtotal(newSubtotal)
    }, [items])

    // Update quantity
    const handleQuantityChange = async (productId: string | number, newQuantity: number) => {
        setIsLoading(true)
        setError(null)

        // Optimistic update
        setItems(prevItems =>
            prevItems.map(item =>
                item.productId === productId
                    ? { ...item, quantity: newQuantity, itemTotal: item.price * newQuantity }
                    : item
            )
        )

        try {
            const url = updateQuantityUrlPattern.replace('{productId}', String(productId))
            const response = await api.post(url, { quantity: newQuantity }, {
                errorMessage: 'Failed to update quantity'
            })

            if (!response.ok) {
                throw new Error(response.error || 'Failed to update quantity')
            }

            // Dispatch event for cart widget
            window.dispatchEvent(new CustomEvent('cart:updated'))
        } catch (err) {
            // Revert on error
            setItems(initialItems)
            setError(err instanceof Error ? err.message : 'Failed to update quantity')
        } finally {
            setIsLoading(false)
        }
    }

    // Remove item
    const handleRemove = async (productId: string | number) => {
        setIsLoading(true)
        setError(null)

        // Optimistic update
        const previousItems = [...items]
        setItems(prevItems => prevItems.filter(item => item.productId !== productId))

        try {
            const url = removeItemUrlPattern.replace('{productId}', String(productId))
            const response = await api.post(url, {}, {
                errorMessage: 'Failed to remove item'
            })

            if (!response.ok) {
                throw new Error(response.error || 'Failed to remove item')
            }

            // Dispatch event for cart widget
            window.dispatchEvent(new CustomEvent('cart:updated'))
        } catch (err) {
            // Revert on error
            setItems(previousItems)
            setError(err instanceof Error ? err.message : 'Failed to remove item')
        } finally {
            setIsLoading(false)
        }
    }

    // Clear cart
    const handleClearCart = async () => {
        if (!confirm('Are you sure you want to clear your cart?')) return

        setIsLoading(true)
        setError(null)

        try {
            const response = await api.post(clearCartUrl, {}, {
                errorMessage: 'Failed to clear cart'
            })

            if (!response.ok) {
                throw new Error(response.error || 'Failed to clear cart')
            }

            setItems([])
            window.dispatchEvent(new CustomEvent('cart:updated'))
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to clear cart')
        } finally {
            setIsLoading(false)
        }
    }

    // Checkout handler (submits traditional form)
    const handleCheckout = () => {
        // Create and submit form for checkout
        const form = document.createElement('form')
        form.method = 'POST'
        form.action = checkoutUrl

        const csrfInput = document.createElement('input')
        csrfInput.type = 'hidden'
        csrfInput.name = 'csrf_token'
        csrfInput.value = csrfToken
        form.appendChild(csrfInput)

        document.body.appendChild(form)
        form.submit()
    }

    // Empty cart state
    if (items.length === 0) {
        return (
            <div className="cart-page">
                <div className="container">
                    <h1>Shopping Cart</h1>
                    <div className="cart-empty">
                        <ShoppingCart size={64} />
                        <h2>Your cart is empty</h2>
                        <p>Looks like you haven't added anything to your cart yet.</p>
                        <a href={shopUrl} className="btn btn-primary">
                            Continue Shopping
                        </a>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="cart-page">
            <div className="container">
                <h1>Shopping Cart</h1>

                {error && (
                    <div className="cart-error">
                        {error}
                    </div>
                )}

                <div className="cart-content">
                    <div className="cart-items">
                        {items.map(item => (
                            <CartItemRow
                                key={item.productId}
                                item={item}
                                onQuantityChange={handleQuantityChange}
                                onRemove={handleRemove}
                                isLoading={isLoading}
                            />
                        ))}
                    </div>

                    <div className="cart-summary">
                        <div className="summary-card">
                            <h3>Order Summary</h3>
                            <div className="summary-row">
                                <span>Subtotal</span>
                                <span>{formatPrice(subtotal)}</span>
                            </div>
                            <div className="summary-row">
                                <span>Shipping</span>
                                <span>Calculated at checkout</span>
                            </div>
                            <hr />
                            <div className="summary-row total-row">
                                <strong>Total</strong>
                                <strong>{formatPrice(subtotal)}</strong>
                            </div>

                            <button
                                type="button"
                                className="btn btn-primary btn-checkout"
                                onClick={handleCheckout}
                                disabled={isLoading}
                            >
                                Proceed to Checkout
                            </button>

                            <button
                                type="button"
                                className="btn btn-outline btn-clear"
                                onClick={handleClearCart}
                                disabled={isLoading}
                            >
                                Clear Cart
                            </button>
                        </div>
                    </div>
                </div>

                <div className="cart-back">
                    <a href={shopUrl} className="back-link">
                        <ArrowLeft size={16} />
                        Continue Shopping
                    </a>
                </div>
            </div>
        </div>
    )
}

export default CartPage
