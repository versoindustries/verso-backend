/**
 * ImageGallery Component
 * 
 * A responsive image gallery with lazy loading and lightbox support.
 * Replaces jQuery lightbox functionality.
 */

import { useState, useEffect, useRef } from 'react'
import { X, ChevronLeft, ChevronRight, ZoomIn } from 'lucide-react'

export interface GalleryImage {
    src: string
    alt?: string
    thumbnail?: string
}

export interface ImageGalleryProps {
    /** Array of images */
    images: GalleryImage[]
    /** Columns in the grid */
    columns?: number
    /** Gap between items (pixels) */
    gap?: number
    /** Enable lightbox */
    lightbox?: boolean
    /** Lazy load images */
    lazyLoad?: boolean
    /** Load more callback */
    onLoadMore?: () => void
    /** Has more images */
    hasMore?: boolean
    /** Loading state */
    loading?: boolean
    /** Additional class */
    className?: string
}

export function ImageGallery({
    images,
    columns = 4,
    gap = 16,
    lightbox = true,
    lazyLoad = true,
    onLoadMore,
    hasMore = false,
    loading = false,
    className = '',
}: ImageGalleryProps) {
    const [lightboxOpen, setLightboxOpen] = useState(false)
    const [currentIndex, setCurrentIndex] = useState(0)
    const observerRef = useRef<IntersectionObserver | null>(null)

    // Lazy loading observer
    useEffect(() => {
        if (!lazyLoad) return

        observerRef.current = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const img = entry.target as HTMLImageElement
                        if (img.dataset.src) {
                            img.src = img.dataset.src
                            img.removeAttribute('data-src')
                            img.classList.add('loaded')
                            observerRef.current?.unobserve(img)
                        }
                    }
                })
            },
            { rootMargin: '100px' }
        )

        return () => observerRef.current?.disconnect()
    }, [lazyLoad])

    const openLightbox = (index: number) => {
        if (lightbox) {
            setCurrentIndex(index)
            setLightboxOpen(true)
            document.body.style.overflow = 'hidden'
        }
    }

    const closeLightbox = () => {
        setLightboxOpen(false)
        document.body.style.overflow = ''
    }

    const goToNext = () => {
        setCurrentIndex((prev) => (prev + 1) % images.length)
    }

    const goToPrev = () => {
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length)
    }

    // Keyboard navigation
    useEffect(() => {
        if (!lightboxOpen) return

        const handleKeyDown = (e: KeyboardEvent) => {
            switch (e.key) {
                case 'Escape':
                    closeLightbox()
                    break
                case 'ArrowRight':
                    goToNext()
                    break
                case 'ArrowLeft':
                    goToPrev()
                    break
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [lightboxOpen])

    return (
        <>
            <div
                className={`image-gallery ${className}`}
                style={{
                    display: 'grid',
                    gridTemplateColumns: `repeat(${columns}, 1fr)`,
                    gap: `${gap}px`,
                }}
            >
                {images.map((image, index) => (
                    <div
                        key={index}
                        className="gallery-item"
                        onClick={() => openLightbox(index)}
                    >
                        <img
                            ref={(el) => {
                                if (el && lazyLoad && observerRef.current) {
                                    observerRef.current.observe(el)
                                }
                            }}
                            src={lazyLoad ? undefined : (image.thumbnail || image.src)}
                            data-src={lazyLoad ? (image.thumbnail || image.src) : undefined}
                            alt={image.alt || `Gallery image ${index + 1}`}
                            className={`gallery-image ${lazyLoad ? 'lazy' : ''}`}
                            loading="lazy"
                        />
                        {lightbox && (
                            <div className="gallery-overlay">
                                <ZoomIn className="gallery-zoom-icon" />
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {hasMore && onLoadMore && (
                <div className="gallery-load-more">
                    <button
                        onClick={onLoadMore}
                        disabled={loading}
                        className="gallery-load-more-btn"
                    >
                        {loading ? 'Loading...' : 'Load More'}
                    </button>
                </div>
            )}

            {lightboxOpen && (
                <div className="gallery-lightbox" onClick={closeLightbox}>
                    <button
                        className="lightbox-close"
                        onClick={closeLightbox}
                        aria-label="Close lightbox"
                    >
                        <X />
                    </button>

                    <button
                        className="lightbox-nav lightbox-prev"
                        onClick={(e) => {
                            e.stopPropagation()
                            goToPrev()
                        }}
                        aria-label="Previous image"
                    >
                        <ChevronLeft />
                    </button>

                    <div
                        className="lightbox-content"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <img
                            src={images[currentIndex]?.src}
                            alt={images[currentIndex]?.alt || 'Gallery image'}
                            className="lightbox-image"
                        />
                        <div className="lightbox-counter">
                            {currentIndex + 1} / {images.length}
                        </div>
                    </div>

                    <button
                        className="lightbox-nav lightbox-next"
                        onClick={(e) => {
                            e.stopPropagation()
                            goToNext()
                        }}
                        aria-label="Next image"
                    >
                        <ChevronRight />
                    </button>
                </div>
            )}
        </>
    )
}

export default ImageGallery
