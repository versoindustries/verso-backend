import { useState, useEffect, useRef, useCallback } from 'react'
import { Bell, CheckCheck } from 'lucide-react'
import { Button } from '../../ui/button'
import { Card } from '../../ui/card'
import { useToastApi } from '../../../hooks/useToastApi'

interface Notification {
    id: number
    title: string
    created_at: string
    is_read: boolean
}

interface PollResponse {
    unread_count?: number
    notifications?: Notification[]
}

export default function NotificationBell({ initialCount = 0 }: { initialCount?: number }) {
    const [unreadCount, setUnreadCount] = useState(initialCount)
    const [notifications, setNotifications] = useState<Notification[]>([])
    const [isOpen, setIsOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const dropdownRef = useRef<HTMLDivElement>(null)
    const api = useToastApi()

    const fetchNotifications = useCallback(async () => {
        const response = await api.get<PollResponse>('/notifications/poll', { silent: true })
        if (response.ok && response.data) {
            if (response.data.unread_count !== undefined) {
                setUnreadCount(response.data.unread_count)
            }
            if (response.data.notifications) {
                setNotifications(response.data.notifications)
            }
        }
    }, [api])

    useEffect(() => {
        // Poll for notifications
        const interval = setInterval(fetchNotifications, 30000)
        return () => clearInterval(interval)
    }, [fetchNotifications])

    useEffect(() => {
        if (isOpen) {
            setLoading(true)
            fetchNotifications().finally(() => setLoading(false))
        }
    }, [isOpen, fetchNotifications])

    // Click outside listener
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [])

    const markAllRead = async () => {
        const response = await api.post('/notifications/read-all', {}, {
            errorMessage: 'Failed to mark notifications as read'
        })
        if (response.ok) {
            setUnreadCount(0)
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
        }
    }

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                className="relative p-2 text-gray-400 hover:text-white transition-colors"
                onClick={() => setIsOpen(!isOpen)}
                aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : 'Notifications'}
            >
                <Bell className="w-6 h-6" />
                {unreadCount > 0 && (
                    <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 transform translate-x-1/4 -translate-y-1/4 bg-red-600 rounded-full">
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                )}
            </button>

            {isOpen && (
                <Card className="absolute right-0 mt-2 w-80 z-50 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-xl border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
                        <h4 className="font-semibold">Notifications</h4>
                        <a href="/notifications" className="text-xs text-blue-500 hover:underline">See All</a>
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                        {loading ? (
                            <div className="p-4 text-center text-sm text-gray-500">Loading...</div>
                        ) : notifications.length === 0 ? (
                            <div className="p-4 text-center text-sm text-gray-500">No new notifications</div>
                        ) : (
                            <ul className="divide-y dark:divide-gray-700">
                                {notifications.map(n => (
                                    <li key={n.id} className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-750 ${!n.is_read ? 'bg-blue-50 dark:bg-blue-900/10' : ''}`}>
                                        <a href={`/notifications/${n.id}/read`} className="block">
                                            <p className="text-sm font-medium">{n.title}</p>
                                            <p className="text-xs text-gray-500 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    <div className="p-2 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                        <Button variant="ghost" size="sm" className="w-full text-xs" onClick={markAllRead}>
                            <CheckCheck className="w-3 h-3 mr-2" />
                            Mark all as read
                        </Button>
                    </div>
                </Card>
            )}
        </div>
    )
}
