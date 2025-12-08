import * as React from "react"
import { X } from "lucide-react"

interface SheetProps {
    isOpen: boolean
    onClose: () => void
    children: React.ReactNode
    side?: "left" | "right"
}

export function Sheet({ isOpen, onClose, children, side = "right" }: SheetProps) {
    React.useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose()
        }
        if (isOpen) {
            document.addEventListener("keydown", handleEscape)
            document.body.style.overflow = "hidden"
        }
        return () => {
            document.removeEventListener("keydown", handleEscape)
            document.body.style.overflow = "unset"
        }
    }, [isOpen, onClose])

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex">
            <div
                className="fixed inset-0 bg-black/50 transition-opacity"
                onClick={onClose}
                aria-hidden="true"
            />
            <div
                className={`relative z-50 flex flex-col w-full max-w-md bg-white dark:bg-gray-900 shadow-xl transition-transform duration-300 ease-in-out ${side === 'right' ? 'ml-auto h-full' : 'mr-auto h-full'
                    }`}
            >
                <div className="flex items-center justify-between p-4 border-b dark:border-gray-800">
                    <h2 className="text-lg font-semibold">Shopping Cart</h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-4">
                    {children}
                </div>
            </div>
        </div>
    )
}
