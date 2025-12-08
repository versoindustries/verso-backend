/**
 * BlogPostUtils Component
 * 
 * Lightweight utility component for blog post pages.
 * Handles:
 * - Hero content fade-in animation
 * - Code block copy buttons
 * - Notification dismiss functionality
 */

import { useEffect } from 'react'

export interface BlogPostUtilsProps {
    /** Enable hero animation */
    heroAnimation?: boolean
    /** Enable code copy buttons */
    codeCopy?: boolean
    /** Enable notification dismiss */
    notificationDismiss?: boolean
}

export function BlogPostUtils({
    heroAnimation = true,
    codeCopy = true,
    notificationDismiss = true,
}: BlogPostUtilsProps) {
    useEffect(() => {
        // Hero fade-in animation
        if (heroAnimation) {
            const heroContent = document.querySelector('.hero-content') as HTMLElement
            if (heroContent) {
                heroContent.style.opacity = '0'
                heroContent.style.transition = 'opacity 1s ease'
                setTimeout(() => {
                    heroContent.style.opacity = '1'
                }, 100)
            }
        }

        // Code copy buttons
        if (codeCopy) {
            document.querySelectorAll('pre').forEach((pre) => {
                const code = pre.querySelector('code')
                if (code && !pre.querySelector('.copy-button')) {
                    const button = document.createElement('button')
                    button.className = 'copy-button'
                    button.innerHTML = '<i class="fas fa-copy"></i>'
                    button.setAttribute('aria-label', 'Copy code')
                    button.setAttribute('type', 'button')
                    pre.style.position = 'relative'
                    pre.appendChild(button)

                    button.addEventListener('click', () => {
                        navigator.clipboard.writeText(code.textContent || '').then(() => {
                            button.innerHTML = '<i class="fas fa-check"></i>'
                            setTimeout(() => {
                                button.innerHTML = '<i class="fas fa-copy"></i>'
                            }, 2000)
                        }).catch(() => {
                            // Fallback for older browsers
                            const textArea = document.createElement('textarea')
                            textArea.value = code.textContent || ''
                            document.body.appendChild(textArea)
                            textArea.select()
                            document.execCommand('copy')
                            document.body.removeChild(textArea)
                            button.innerHTML = '<i class="fas fa-check"></i>'
                            setTimeout(() => {
                                button.innerHTML = '<i class="fas fa-copy"></i>'
                            }, 2000)
                        })
                    })
                }
            })
        }

        // Notification dismiss
        if (notificationDismiss) {
            document.querySelectorAll('.notification-close').forEach(button => {
                button.addEventListener('click', () => {
                    const notification = button.parentElement
                    if (notification) {
                        notification.style.display = 'none'
                    }
                })
            })
        }
    }, [heroAnimation, codeCopy, notificationDismiss])

    // This component only runs side effects, doesn't render anything
    return null
}

export default BlogPostUtils
