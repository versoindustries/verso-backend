import * as React from "react"

interface SheetProps {
    isOpen: boolean
    onClose: () => void
    children: React.ReactNode
    side?: "left" | "right"
    className?: string
    width?: string
}

export function Sheet({ isOpen, onClose, children, side = "right", className = "", width = "500px" }: SheetProps) {
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
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 1000,
                display: 'flex',
            }}
        >
            {/* Backdrop */}
            <div
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.6)',
                    backdropFilter: 'blur(4px)',
                }}
                onClick={onClose}
                aria-hidden="true"
            />
            {/* Sheet Panel */}
            <div
                className={className}
                style={{
                    position: 'relative',
                    zIndex: 1001,
                    display: 'flex',
                    flexDirection: 'column',
                    width: '100%',
                    maxWidth: width,
                    height: '100%',
                    marginLeft: side === 'right' ? 'auto' : undefined,
                    marginRight: side === 'left' ? 'auto' : undefined,
                    background: 'rgba(31, 31, 31, 0.98)',
                    backdropFilter: 'blur(20px)',
                    borderLeft: side === 'right' ? '1px solid rgba(65, 105, 225, 0.2)' : undefined,
                    borderRight: side === 'left' ? '1px solid rgba(65, 105, 225, 0.2)' : undefined,
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                    animation: 'sheetSlideIn 0.3s ease-out',
                }}
            >
                <style>{`
                    @keyframes sheetSlideIn {
                        from {
                            opacity: 0;
                            transform: translateX(${side === 'right' ? '100%' : '-100%'});
                        }
                        to {
                            opacity: 1;
                            transform: translateX(0);
                        }
                    }
                `}</style>
                <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
                    {children}
                </div>
            </div>
        </div>
    )
}
