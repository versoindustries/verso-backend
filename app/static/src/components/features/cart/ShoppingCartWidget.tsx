import { useState, useEffect, useCallback } from 'react'
import { ShoppingCart, Trash2, Plus, Minus } from 'lucide-react'
import { Button } from '../../ui/button'
import { Sheet } from '../../ui/sheet'
import { useToastApi } from '../../../hooks/useToastApi'

interface CartItem {
    product_id: number
    name: string
    price: number
    quantity: number
    item_total: number
    image_url: string | null
}

interface CartData {
    items: CartItem[]
    subtotal: number
    item_count: number
}

interface CartResponse {
    success?: boolean
    items: CartItem[]
    subtotal: number
    cart_count: number
}

export default function ShoppingCartWidget() {
    const [isOpen, setIsOpen] = useState(false)
    const [cart, setCart] = useState<CartData>({ items: [], subtotal: 0, item_count: 0 })
    const [loading, setLoading] = useState(false)
    const api = useToastApi()

    const fetchCart = useCallback(async () => {
        const response = await api.get<CartData>('/shop/cart/data', { silent: true })
        if (response.ok && response.data) {
            setCart(response.data)
        }
    }, [api])

    useEffect(() => {
        fetchCart()
    }, [fetchCart])

    useEffect(() => {
        if (isOpen) fetchCart()
    }, [isOpen, fetchCart])

    const updateQuantity = async (productId: number, newQty: number) => {
        setLoading(true)
        const response = await api.post<CartResponse>(
            `/shop/cart/update/${productId}`,
            { quantity: newQty },
            { errorMessage: 'Failed to update cart' }
        )
        if (response.ok && response.data?.success) {
            setCart({
                items: response.data.items,
                subtotal: response.data.subtotal,
                item_count: response.data.cart_count
            })
        }
        setLoading(false)
    }

    const removeItem = async (productId: number) => {
        setLoading(true)
        const response = await api.post<CartResponse>(
            `/shop/cart/remove/${productId}`,
            {},
            { errorMessage: 'Failed to remove item' }
        )
        if (response.ok && response.data?.success) {
            setCart({
                items: response.data.items,
                subtotal: response.data.subtotal,
                item_count: response.data.cart_count
            })
        }
        setLoading(false)
    }

    return (
        <>
            <button
                onClick={() => setIsOpen(true)}
                className="relative p-2 text-gray-400 hover:text-white transition-colors"
                aria-label={cart.item_count > 0 ? `Shopping Cart, ${cart.item_count} items` : 'Shopping Cart'}
            >
                <ShoppingCart className="w-6 h-6" />
                {cart.item_count > 0 && (
                    <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-blue-600 rounded-full">
                        {cart.item_count}
                    </span>
                )}
            </button>

            <Sheet isOpen={isOpen} onClose={() => setIsOpen(false)} side="right">
                {cart.items.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <ShoppingCart className="w-12 h-12 mb-4 opacity-20" />
                        <p>Your cart is empty</p>
                        <Button
                            className="mt-4"
                            onClick={() => {
                                setIsOpen(false)
                                window.location.href = '/shop'
                            }}
                        >
                            Start Shopping
                        </Button>
                    </div>
                ) : (
                    <div className="flex flex-col h-full">
                        <div className="flex-1 space-y-4">
                            {cart.items.map(item => (
                                <div key={item.product_id} className="flex gap-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-800/50">
                                    {item.image_url && (
                                        <img src={item.image_url} alt={item.name} className="w-16 h-16 object-cover rounded bg-white" />
                                    )}
                                    <div className="flex-1">
                                        <h4 className="font-medium text-sm">{item.name}</h4>
                                        <p className="text-sm font-semibold mt-1">${item.price.toFixed(2)}</p>

                                        <div className="flex items-center justify-between mt-2">
                                            <div className="flex items-center gap-2">
                                                <button
                                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                                                    onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                                                    disabled={loading}
                                                >
                                                    <Minus className="w-3 h-3" />
                                                </button>
                                                <span className="text-sm w-4 text-center">{item.quantity}</span>
                                                <button
                                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                                                    onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                                                    disabled={loading}
                                                >
                                                    <Plus className="w-3 h-3" />
                                                </button>
                                            </div>
                                            <button
                                                className="text-red-500 hover:text-red-600"
                                                onClick={() => removeItem(item.product_id)}
                                                disabled={loading}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="border-t pt-4 mt-4 dark:border-gray-800">
                            <div className="flex justify-between items-center mb-4">
                                <span className="font-medium">Subtotal</span>
                                <span className="font-bold text-lg">${cart.subtotal.toFixed(2)}</span>
                            </div>
                            <Button
                                className="w-full"
                                onClick={() => window.location.href = '/shop/cart'}
                            >
                                View Full Cart
                            </Button>
                            <Button
                                className="w-full mt-2"
                                variant="ghost" // Changed from outline to ghost to verify type check or just stick to valid ones
                                onClick={() => {
                                    // Assuming backend checkout requires form submission or specific flow
                                    window.location.href = '/shop/cart'
                                }}
                            >
                                Checkout
                            </Button>
                        </div>
                    </div>
                )}
            </Sheet>
        </>
    )
}
