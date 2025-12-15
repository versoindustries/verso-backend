/**
 * UnifiedMessagingDashboard Component
 * 
 * Enterprise-level messaging platform with Discord/Slack-style UX.
 * Single-page experience with in-place channel switching, role-based access,
 * and premium glassmorphism design.
 * 
 * Features:
 * - Real-time messaging (SSE + polling fallback)
 * - Channel management (create, archive, delete)
 * - Member management for private channels
 * - Role-based access control
 * - Message reactions
 * - File attachments
 * - Confirmation modals for destructive actions
 * - Toast notifications for feedback
 */

import { useState, useEffect, useRef, useCallback, createContext, useContext } from 'react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface Channel {
    id: number
    name: string
    display_name: string
    type: 'public' | 'private' | 'direct'
    category: string
    is_archived: boolean
    is_direct: boolean
    is_restricted: boolean
    allowed_roles: string[]
    description: string | null
    created_by_id: number
    member_count: number
}

interface Message {
    id: number
    user: string
    user_id: number
    content: string
    created_at: string
    attachment?: {
        url: string
        name: string
        is_image: boolean
    }
    reactions: Record<string, { count: number; user_reacted: boolean }>
    message_type?: 'text' | 'command' | 'system' | 'card'
    is_pinned?: boolean
}

interface Role {
    id: number
    name: string
}

interface User {
    id: number
    username: string
    email: string
    initial: string
}

interface Toast {
    id: string
    type: 'success' | 'error' | 'info' | 'warning'
    message: string
}

interface UnifiedMessagingDashboardProps {
    currentUserId: number
    userRoles?: string[]
    initialChannelId?: number
}

// Common emojis for reactions
const EMOJI_OPTIONS = ['👍', '❤️', '😂', '😮', '😢', '🔥', '🎉', '👏']

// Channel categories for grouping
const CHANNEL_CATEGORIES = [
    { id: 'general', name: 'General', icon: 'fa-hashtag' },
    { id: 'support', name: 'Support', icon: 'fa-life-ring' },
    { id: 'project', name: 'Projects', icon: 'fa-folder' },
    { id: 'announcement', name: 'Announcements', icon: 'fa-bullhorn' },
]

// =============================================================================
// Toast Context
// =============================================================================

const ToastContext = createContext<{
    toasts: Toast[]
    addToast: (type: Toast['type'], message: string) => void
    removeToast: (id: string) => void
}>({
    toasts: [],
    addToast: () => { },
    removeToast: () => { },
})

function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([])

    const addToast = useCallback((type: Toast['type'], message: string) => {
        const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        setToasts(prev => [...prev, { id, type, message }])

        // Auto-remove after 5 seconds
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 5000)
    }, [])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
            <ToastContainer />
        </ToastContext.Provider>
    )
}

function ToastContainer() {
    const { toasts, removeToast } = useContext(ToastContext)

    if (toasts.length === 0) return null

    return (
        <div className="toast-container">
            {toasts.map(toast => (
                <div key={toast.id} className={`toast toast-${toast.type}`}>
                    <i className={`fas ${toast.type === 'success' ? 'fa-check-circle' :
                        toast.type === 'error' ? 'fa-exclamation-circle' :
                            toast.type === 'warning' ? 'fa-exclamation-triangle' :
                                'fa-info-circle'
                        }`}></i>
                    <span>{toast.message}</span>
                    <button className="toast-close" onClick={() => removeToast(toast.id)}>
                        <i className="fas fa-times"></i>
                    </button>
                </div>
            ))}
        </div>
    )
}

// =============================================================================
// Confirmation Modal Component
// =============================================================================

interface ConfirmationModalProps {
    isOpen: boolean
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    danger?: boolean
    loading?: boolean
    onConfirm: () => void
    onCancel: () => void
}

function ConfirmationModal({
    isOpen,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    danger = false,
    loading = false,
    onConfirm,
    onCancel,
}: ConfirmationModalProps) {
    if (!isOpen) return null

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content confirmation-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>
                        {danger && <i className="fas fa-exclamation-triangle danger-icon"></i>}
                        {title}
                    </h3>
                    <button className="modal-close" onClick={onCancel} disabled={loading}>
                        <i className="fas fa-times"></i>
                    </button>
                </div>
                <div className="modal-body">
                    <p>{message}</p>
                </div>
                <div className="modal-actions">
                    <button
                        className="btn-cancel"
                        onClick={onCancel}
                        disabled={loading}
                    >
                        {cancelText}
                    </button>
                    <button
                        className={`btn-confirm ${danger ? 'btn-danger' : 'btn-primary'}`}
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? (
                            <><i className="fas fa-spinner fa-spin"></i> Processing...</>
                        ) : (
                            <><i className={`fas ${danger ? 'fa-trash-alt' : 'fa-check'}`}></i> {confirmText}</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}

// =============================================================================
// Skeleton Loaders
// =============================================================================

function MessageSkeleton() {
    return (
        <div className="message-skeleton">
            <div className="skeleton-avatar"></div>
            <div className="skeleton-content">
                <div className="skeleton-line short"></div>
                <div className="skeleton-line"></div>
                <div className="skeleton-line medium"></div>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

function MessagingDashboard({
    currentUserId,
    initialChannelId,
}: UnifiedMessagingDashboardProps) {
    const { addToast } = useContext(ToastContext)

    // State
    const [channels, setChannels] = useState<{
        public: Channel[]
        private: Channel[]
        dm: Channel[]
    }>({ public: [], private: [], dm: [] })
    const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null)
    const [messages, setMessages] = useState<Message[]>([])
    const [messageInput, setMessageInput] = useState('')
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [showSettings, setShowSettings] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [users, setUsers] = useState<User[]>([])
    const [roles, setRoles] = useState<Role[]>([])
    const [canCreate, setCanCreate] = useState(false)
    const [loading, setLoading] = useState(true)
    const [messagesLoading, setMessagesLoading] = useState(false)
    const [showEmojiPicker, setShowEmojiPicker] = useState<number | null>(null)
    const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set())

    // Channel settings state
    const [channelSettings, setChannelSettings] = useState<{
        members: { id: number; username: string }[]
        available_roles: { id: number; name: string }[]
        is_restricted: boolean
        allowed_roles: string[]
    } | null>(null)
    const [settingsLoading, setSettingsLoading] = useState(false)
    const [addMemberSearch, setAddMemberSearch] = useState('')

    // Confirmation modal state
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
    const [showArchiveConfirm, setShowArchiveConfirm] = useState(false)
    const [deleteLoading, setDeleteLoading] = useState(false)
    const [archiveLoading, setArchiveLoading] = useState(false)

    // Channel creation state
    const [newChannel, setNewChannel] = useState({
        name: '',
        type: 'public' as 'public' | 'private',
        category: 'general',
        description: '',
        is_restricted: false,
        allowed_roles: [] as string[]
    })

    // Refs
    const chatBoxRef = useRef<HTMLDivElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const lastIdRef = useRef<number>(0)
    const eventSourceRef = useRef<EventSource | null>(null)
    const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

    // Scroll to bottom of messages
    const scrollToBottom = useCallback(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
        }
    }, [])

    // Load channels
    const loadChannels = useCallback(async () => {
        try {
            const response = await api.get<{
                public: Channel[]
                private: Channel[]
                dm: Channel[]
                can_create: boolean
                roles: Role[]
            }>('/messaging/api/channels')

            if (response.ok && response.data) {
                setChannels({
                    public: response.data.public || [],
                    private: response.data.private || [],
                    dm: response.data.dm || []
                })
                setCanCreate(response.data.can_create)
                setRoles(response.data.roles || [])
            }
        } catch (error) {
            console.error('Failed to load channels:', error)
            addToast('error', 'Failed to load channels')
        } finally {
            setLoading(false)
        }
    }, [addToast])

    // Load users for DM
    const loadUsers = useCallback(async () => {
        try {
            const response = await api.get<{ users: User[] }>('/messaging/api/users')
            if (response.ok && response.data) {
                setUsers(response.data.users || [])
            }
        } catch (error) {
            console.error('Failed to load users:', error)
        }
    }, [])

    // Load messages for a channel
    const loadMessages = useCallback(async (channelId: number) => {
        setMessagesLoading(true)
        try {
            const response = await api.get<Message[]>(`/messaging/channel/${channelId}/poll?last_id=0`)
            if (response.ok && response.data) {
                setMessages(response.data)
                lastIdRef.current = response.data.length > 0
                    ? response.data[response.data.length - 1].id
                    : 0
                setTimeout(scrollToBottom, 100)
            }
        } catch (error) {
            console.error('Failed to load messages:', error)
            addToast('error', 'Failed to load messages')
        } finally {
            setMessagesLoading(false)
        }
    }, [scrollToBottom, addToast])

    // Setup real-time updates for selected channel
    const setupRealTimeUpdates = useCallback((channelId: number) => {
        // Cleanup previous connections
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
        }
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
        }

        // Try SSE first
        const sseUrl = `/messaging/channel/${channelId}/stream?last_id=${lastIdRef.current}`
        const eventSource = new EventSource(sseUrl)
        eventSourceRef.current = eventSource

        eventSource.addEventListener('messages', (event: MessageEvent) => {
            try {
                const newMessages = JSON.parse(event.data) as Message[]
                setMessages(prev => [...prev, ...newMessages])
                if (newMessages.length > 0) {
                    lastIdRef.current = newMessages[newMessages.length - 1].id
                }
                scrollToBottom()
            } catch (e) {
                console.error('SSE parse error:', e)
            }
        })

        eventSource.onerror = () => {
            console.warn('SSE error, falling back to polling')
            eventSource.close()

            // Fallback to polling
            pollIntervalRef.current = setInterval(async () => {
                try {
                    const response = await api.get<Message[]>(
                        `/messaging/channel/${channelId}/poll?last_id=${lastIdRef.current}`
                    )
                    if (response.ok && response.data && response.data.length > 0) {
                        setMessages(prev => [...prev, ...response.data!])
                        lastIdRef.current = response.data[response.data.length - 1].id
                        scrollToBottom()
                    }
                } catch (error) {
                    console.error('Polling error:', error)
                }
            }, 3000)
        }
    }, [scrollToBottom])

    // Select a channel
    const selectChannel = useCallback(async (channel: Channel) => {
        setSelectedChannel(channel)
        setMessages([])
        lastIdRef.current = 0
        setShowSettings(false)
        await loadMessages(channel.id)
        setupRealTimeUpdates(channel.id)
    }, [loadMessages, setupRealTimeUpdates])

    // Send message
    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedChannel || (!messageInput.trim() && !selectedFile)) return

        const formData = new FormData()
        formData.append('content', messageInput)
        if (selectedFile) {
            formData.append('file', selectedFile)
        }

        try {
            const response = await api.post(`/messaging/channel/${selectedChannel.id}/send`, formData)
            if (response.ok) {
                setMessageInput('')
                setSelectedFile(null)
                if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                }
            } else {
                addToast('error', 'Failed to send message')
            }
        } catch (error) {
            console.error('Send error:', error)
            addToast('error', 'Failed to send message')
        }
    }

    // Toggle reaction
    const handleReaction = async (messageId: number, emoji: string) => {
        try {
            const response = await api.post<{ success: boolean; action: string }>(
                `/messaging/message/${messageId}/react`,
                { emoji }
            )
            if (response.ok && response.data?.success) {
                // Reload messages to get updated reactions
                if (selectedChannel) {
                    const msgResponse = await api.get<Message[]>(
                        `/messaging/channel/${selectedChannel.id}/poll?last_id=0`
                    )
                    if (msgResponse.ok && msgResponse.data) {
                        setMessages(msgResponse.data)
                    }
                }
            }
        } catch (error) {
            console.error('Reaction error:', error)
        }
        setShowEmojiPicker(null)
    }

    // Create channel
    const handleCreateChannel = async (e: React.FormEvent) => {
        e.preventDefault()

        const formData = new FormData()
        formData.append('name', newChannel.name)
        formData.append('type', newChannel.type)
        formData.append('category', newChannel.category)
        formData.append('description', newChannel.description)
        if (newChannel.is_restricted) {
            formData.append('is_restricted', '1')
            newChannel.allowed_roles.forEach(role => {
                formData.append('allowed_roles', role)
            })
        }

        try {
            const response = await api.post<{ success: boolean; channel_id: number; message?: string }>(
                '/messaging/create_channel',
                formData
            )
            if (response.ok && response.data?.success) {
                setShowCreateModal(false)
                setNewChannel({
                    name: '',
                    type: 'public',
                    category: 'general',
                    description: '',
                    is_restricted: false,
                    allowed_roles: []
                })
                await loadChannels()
                addToast('success', 'Channel created successfully')
            } else {
                addToast('error', response.data?.message || 'Failed to create channel')
            }
        } catch (error) {
            console.error('Create channel error:', error)
            addToast('error', 'Failed to create channel')
        }
    }

    // Start DM with user
    const startDM = async (userId: number) => {
        window.location.href = `/messaging/dm/${userId}`
    }

    // Toggle category collapse
    const toggleCategory = (category: string) => {
        setCollapsedCategories(prev => {
            const newSet = new Set(prev)
            if (newSet.has(category)) {
                newSet.delete(category)
            } else {
                newSet.add(category)
            }
            return newSet
        })
    }

    // Load channel settings (for settings panel)
    const loadChannelSettings = useCallback(async (channelId: number) => {
        setSettingsLoading(true)
        try {
            const response = await api.get<{
                members: { id: number; username: string }[]
                available_roles: { id: number; name: string }[]
                is_restricted: boolean
                allowed_roles: string[]
            }>(`/messaging/channel/${channelId}/settings`)
            if (response.ok && response.data) {
                setChannelSettings(response.data)
            }
        } catch (error) {
            console.error('Failed to load channel settings:', error)
            addToast('error', 'Failed to load channel settings')
        } finally {
            setSettingsLoading(false)
        }
    }, [addToast])

    // Add member to channel
    const handleAddMember = async (userId: number) => {
        if (!selectedChannel) return
        try {
            const response = await api.post<{ success: boolean; message: string }>(
                `/messaging/channel/${selectedChannel.id}/members/add`,
                { user_id: userId }
            )
            if (response.ok && response.data?.success) {
                await loadChannelSettings(selectedChannel.id)
                await loadChannels()
                setAddMemberSearch('')
                addToast('success', response.data.message)
            } else {
                addToast('error', response.data?.message || 'Failed to add member')
            }
        } catch (error) {
            console.error('Add member error:', error)
            addToast('error', 'Failed to add member')
        }
    }

    // Remove member from channel
    const handleRemoveMember = async (userId: number, username: string) => {
        if (!selectedChannel) return

        try {
            const response = await api.post<{ success: boolean; message: string }>(
                `/messaging/channel/${selectedChannel.id}/members/remove`,
                { user_id: userId }
            )
            if (response.ok && response.data?.success) {
                await loadChannelSettings(selectedChannel.id)
                await loadChannels()
                addToast('success', `${username} removed from channel`)
            } else {
                addToast('error', response.data?.message || 'Failed to remove member')
            }
        } catch (error) {
            console.error('Remove member error:', error)
            addToast('error', 'Failed to remove member')
        }
    }

    // Update channel access roles
    const handleUpdateRoles = async (newRoles: string[], isRestricted: boolean) => {
        if (!selectedChannel) return
        try {
            const response = await api.post<{ success: boolean }>(
                `/messaging/channel/${selectedChannel.id}/settings`,
                { allowed_roles: newRoles, is_restricted: isRestricted }
            )
            if (response.ok && response.data?.success) {
                await loadChannelSettings(selectedChannel.id)
                await loadChannels()
                addToast('success', 'Channel settings updated')
            }
        } catch (error) {
            console.error('Update roles error:', error)
            addToast('error', 'Failed to update settings')
        }
    }

    // Delete channel - now using confirmation modal
    const handleDeleteChannel = async () => {
        if (!selectedChannel) return
        setDeleteLoading(true)

        try {
            const response = await api.delete<{ success: boolean; error?: string; message?: string }>(
                `/messaging/channel/${selectedChannel.id}/delete`
            )

            if (response.ok && response.data?.success) {
                addToast('success', response.data.message || 'Channel deleted successfully')
                setShowDeleteConfirm(false)
                setShowSettings(false)
                setSelectedChannel(null)
                await loadChannels()
            } else {
                addToast('error', response.data?.error || 'Failed to delete channel')
            }
        } catch (error) {
            console.error('Delete error:', error)
            addToast('error', 'Failed to delete channel. Please try again.')
        } finally {
            setDeleteLoading(false)
        }
    }

    // Archive/Unarchive channel
    const handleToggleArchive = async () => {
        if (!selectedChannel) return
        setArchiveLoading(true)

        const endpoint = selectedChannel.is_archived ? 'unarchive' : 'archive'

        try {
            const response = await api.post<{ success: boolean; message?: string; is_archived: boolean }>(
                `/messaging/channel/${selectedChannel.id}/${endpoint}`,
                {}
            )

            if (response.ok && response.data?.success) {
                addToast('success', response.data.message || `Channel ${endpoint}d successfully`)
                setShowArchiveConfirm(false)
                // Update the selected channel's archived status
                setSelectedChannel(prev => prev ? { ...prev, is_archived: response.data!.is_archived } : null)
                await loadChannels()
            } else {
                addToast('error', `Failed to ${endpoint} channel`)
            }
        } catch (error) {
            console.error(`${endpoint} error:`, error)
            addToast('error', `Failed to ${endpoint} channel`)
        } finally {
            setArchiveLoading(false)
        }
    }

    // Open settings panel
    const openSettings = () => {
        if (selectedChannel) {
            loadChannelSettings(selectedChannel.id)
            setShowSettings(true)
        }
    }

    // Filter channels by search
    const filterChannels = (channelList: Channel[]) => {
        if (!searchQuery.trim()) return channelList
        const query = searchQuery.toLowerCase()
        return channelList.filter(c =>
            c.name.toLowerCase().includes(query) ||
            c.display_name.toLowerCase().includes(query)
        )
    }

    // Group public channels by category
    const groupedPublicChannels = CHANNEL_CATEGORIES.map(cat => ({
        ...cat,
        channels: filterChannels(channels.public).filter(c => c.category === cat.id)
    })).filter(cat => cat.channels.length > 0)

    // Initial load
    useEffect(() => {
        loadChannels()
        loadUsers()

        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close()
            }
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current)
            }
        }
    }, [loadChannels, loadUsers])

    // Auto-select initial channel if provided
    useEffect(() => {
        if (initialChannelId && !loading) {
            const allChannels = [...channels.public, ...channels.private, ...channels.dm]
            const channel = allChannels.find(c => c.id === initialChannelId)
            if (channel) {
                selectChannel(channel)
            }
        }
    }, [initialChannelId, loading, channels, selectChannel])

    // ==========================================================================
    // Render
    // ==========================================================================

    if (loading) {
        return (
            <div className="unified-messaging loading">
                <div className="loading-spinner">
                    <i className="fas fa-spinner fa-spin"></i>
                    <span>Loading messaging...</span>
                </div>
            </div>
        )
    }

    return (
        <div className="unified-messaging">
            {/* ============================================================
                SIDEBAR - Channel Navigation
                ============================================================ */}
            <aside className="messaging-sidebar">
                <div className="sidebar-header">
                    <h2><i className="fas fa-comments"></i> Messages</h2>
                    {canCreate && (
                        <button
                            className="btn-icon-circle"
                            onClick={() => setShowCreateModal(true)}
                            title="Create Channel"
                        >
                            <i className="fas fa-plus"></i>
                        </button>
                    )}
                </div>

                <div className="sidebar-search">
                    <i className="fas fa-search search-icon"></i>
                    <input
                        type="text"
                        placeholder="Search channels..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="sidebar-content">
                    {/* Public Channels by Category */}
                    {groupedPublicChannels.map(category => (
                        <div key={category.id} className="channel-category">
                            <div
                                className={`category-header ${collapsedCategories.has(category.id) ? 'collapsed' : ''}`}
                                onClick={() => toggleCategory(category.id)}
                            >
                                <span className="category-title">
                                    <i className={`fas fa-chevron-down`}></i>
                                    <i className={`fas ${category.icon}`}></i>
                                    {category.name}
                                </span>
                                <span className="category-count">{category.channels.length}</span>
                            </div>
                            {!collapsedCategories.has(category.id) && (
                                <ul className="channel-list">
                                    {category.channels.map(channel => (
                                        <li
                                            key={channel.id}
                                            className={`channel-item ${selectedChannel?.id === channel.id ? 'active' : ''}`}
                                        >
                                            <button onClick={() => selectChannel(channel)}>
                                                <span className="channel-icon hash">
                                                    {channel.is_restricted ? (
                                                        <i className="fas fa-shield-alt" title="Role restricted"></i>
                                                    ) : '#'}
                                                </span>
                                                <span className="channel-name">{channel.name}</span>
                                                {channel.is_restricted && (
                                                    <span className="restricted-badge" title={`Roles: ${channel.allowed_roles.join(', ')}`}>
                                                        <i className="fas fa-lock"></i>
                                                    </span>
                                                )}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    ))}

                    {/* Private Channels */}
                    {filterChannels(channels.private).length > 0 && (
                        <div className="channel-category">
                            <div
                                className={`category-header ${collapsedCategories.has('private') ? 'collapsed' : ''}`}
                                onClick={() => toggleCategory('private')}
                            >
                                <span className="category-title">
                                    <i className="fas fa-chevron-down"></i>
                                    <i className="fas fa-lock"></i>
                                    Private
                                </span>
                                <span className="category-count">{filterChannels(channels.private).length}</span>
                            </div>
                            {!collapsedCategories.has('private') && (
                                <ul className="channel-list">
                                    {filterChannels(channels.private).map(channel => (
                                        <li
                                            key={channel.id}
                                            className={`channel-item ${selectedChannel?.id === channel.id ? 'active' : ''}`}
                                        >
                                            <button onClick={() => selectChannel(channel)}>
                                                <span className="channel-icon lock">
                                                    <i className="fas fa-lock"></i>
                                                </span>
                                                <span className="channel-name">{channel.name}</span>
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}

                    {/* Direct Messages */}
                    <div className="channel-category">
                        <div
                            className={`category-header ${collapsedCategories.has('dm') ? 'collapsed' : ''}`}
                            onClick={() => toggleCategory('dm')}
                        >
                            <span className="category-title">
                                <i className="fas fa-chevron-down"></i>
                                <i className="fas fa-user-friends"></i>
                                Direct Messages
                            </span>
                            <span className="category-count">{filterChannels(channels.dm).length}</span>
                        </div>
                        {!collapsedCategories.has('dm') && (
                            <ul className="channel-list dm-list">
                                {filterChannels(channels.dm).map(channel => (
                                    <li
                                        key={channel.id}
                                        className={`channel-item dm-item ${selectedChannel?.id === channel.id ? 'active' : ''}`}
                                    >
                                        <button onClick={() => selectChannel(channel)}>
                                            <div className="dm-avatar">
                                                {channel.display_name[0]?.toUpperCase()}
                                            </div>
                                            <span className="channel-name">{channel.display_name}</span>
                                            <span className="presence-dot online"></span>
                                        </button>
                                    </li>
                                ))}

                                {/* Quick DM Starters */}
                                {users.slice(0, 5).map(user => (
                                    <li key={user.id} className="channel-item dm-item new-dm">
                                        <button onClick={() => startDM(user.id)}>
                                            <div className="dm-avatar muted">{user.initial}</div>
                                            <span className="channel-name">{user.username}</span>
                                            <i className="fas fa-plus new-dm-icon"></i>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            </aside>

            {/* ============================================================
                MAIN CONTENT - Messages
                ============================================================ */}
            <main className="messaging-main">
                {selectedChannel ? (
                    <>
                        {/* Channel Header */}
                        <div className="channel-header">
                            <div className="channel-info">
                                <h3>
                                    {selectedChannel.is_direct ? (
                                        <><i className="fas fa-user"></i> {selectedChannel.display_name}</>
                                    ) : (
                                        <>
                                            <span className="header-hash">#</span> {selectedChannel.name}
                                            {selectedChannel.is_restricted && (
                                                <span className="header-badge restricted">
                                                    <i className="fas fa-shield-alt"></i> Restricted
                                                </span>
                                            )}
                                            {selectedChannel.is_archived && (
                                                <span className="header-badge archived">
                                                    <i className="fas fa-archive"></i> Archived
                                                </span>
                                            )}
                                        </>
                                    )}
                                </h3>
                                {selectedChannel.description && (
                                    <p className="channel-description">{selectedChannel.description}</p>
                                )}
                            </div>
                            <div className="channel-actions">
                                <button className="btn-icon" title="Pinned Messages">
                                    <i className="fas fa-thumbtack"></i>
                                </button>
                                <button className="btn-icon" title="Members">
                                    <i className="fas fa-users"></i>
                                    <span className="member-count">{selectedChannel.member_count}</span>
                                </button>
                                <button
                                    className="btn-icon"
                                    title="Settings"
                                    onClick={openSettings}
                                >
                                    <i className="fas fa-cog"></i>
                                </button>
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="chat-container" ref={chatBoxRef}>
                            {messagesLoading ? (
                                <>
                                    <MessageSkeleton />
                                    <MessageSkeleton />
                                    <MessageSkeleton />
                                </>
                            ) : messages.length === 0 ? (
                                <div className="empty-messages">
                                    <div className="empty-icon">
                                        <i className="fas fa-comments"></i>
                                    </div>
                                    <h4>No messages yet</h4>
                                    <p>Be the first to send a message in this channel!</p>
                                </div>
                            ) : (
                                messages.map(msg => (
                                    <div
                                        key={msg.id}
                                        className={`message ${msg.user_id === currentUserId ? 'me' : ''} ${msg.message_type || 'text'} ${msg.is_pinned ? 'pinned' : ''}`}
                                    >
                                        <div className="message-avatar">
                                            {msg.user[0].toUpperCase()}
                                        </div>
                                        <div className="message-bubble">
                                            {msg.is_pinned && (
                                                <div className="pinned-indicator">
                                                    <i className="fas fa-thumbtack"></i> Pinned
                                                </div>
                                            )}
                                            <div className="message-meta">
                                                <strong>{msg.user}</strong>
                                                <span className="message-time">
                                                    {msg.created_at.split(' ')[1]?.substring(0, 5) || ''}
                                                </span>
                                            </div>
                                            <div
                                                className="message-content"
                                                dangerouslySetInnerHTML={{ __html: msg.content }}
                                            />

                                            {/* Attachment */}
                                            {msg.attachment && (
                                                <div className="message-attachment">
                                                    {msg.attachment.is_image ? (
                                                        <img src={msg.attachment.url} alt={msg.attachment.name} />
                                                    ) : (
                                                        <a href={msg.attachment.url} target="_blank" rel="noreferrer">
                                                            <i className="fas fa-file"></i> {msg.attachment.name}
                                                        </a>
                                                    )}
                                                </div>
                                            )}

                                            {/* Reactions */}
                                            <div className="reactions-container">
                                                {Object.entries(msg.reactions || {}).map(([emoji, data]) => (
                                                    <button
                                                        key={emoji}
                                                        className={`reaction ${data.user_reacted ? 'user-reacted' : ''}`}
                                                        onClick={() => handleReaction(msg.id, emoji)}
                                                    >
                                                        {emoji} <span className="reaction-count">{data.count}</span>
                                                    </button>
                                                ))}
                                                <button
                                                    className="add-reaction-btn"
                                                    onClick={() => setShowEmojiPicker(showEmojiPicker === msg.id ? null : msg.id)}
                                                >
                                                    <i className="far fa-smile"></i>
                                                </button>

                                                {showEmojiPicker === msg.id && (
                                                    <div className="emoji-picker">
                                                        {EMOJI_OPTIONS.map(emoji => (
                                                            <button
                                                                key={emoji}
                                                                onClick={() => handleReaction(msg.id, emoji)}
                                                            >
                                                                {emoji}
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Message Input */}
                        {!selectedChannel.is_archived ? (
                            <div className="message-input-container">
                                <form className="message-input-form" onSubmit={handleSendMessage}>
                                    <button
                                        type="button"
                                        className="btn-attach"
                                        onClick={() => fileInputRef.current?.click()}
                                    >
                                        <i className="fas fa-plus-circle"></i>
                                    </button>
                                    <input
                                        type="text"
                                        value={messageInput}
                                        onChange={(e) => setMessageInput(e.target.value)}
                                        placeholder={`Message #${selectedChannel.name}`}
                                        autoComplete="off"
                                    />
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={(e) => e.target.files?.[0] && setSelectedFile(e.target.files[0])}
                                        style={{ display: 'none' }}
                                    />
                                    <button type="submit" className="btn-send">
                                        <i className="fas fa-paper-plane"></i>
                                    </button>
                                </form>
                                {selectedFile && (
                                    <div className="file-preview">
                                        <i className="fas fa-file"></i>
                                        <span>{selectedFile.name}</span>
                                        <button onClick={() => {
                                            setSelectedFile(null)
                                            if (fileInputRef.current) fileInputRef.current.value = ''
                                        }}>
                                            <i className="fas fa-times"></i>
                                        </button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="archived-notice">
                                <i className="fas fa-archive"></i>
                                <span>This channel is archived. Messages are read-only.</span>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="welcome-state">
                        <div className="welcome-icon">
                            <i className="fas fa-comments"></i>
                        </div>
                        <h2>Welcome to Messaging</h2>
                        <p>Select a channel from the sidebar or start a conversation.</p>
                        <div className="welcome-hints">
                            <div className="hint">
                                <i className="fas fa-slash"></i>
                                <span>Use <code>/help</code> to see available commands</span>
                            </div>
                            <div className="hint">
                                <i className="fas fa-at"></i>
                                <span>Use <code>@username</code> to mention someone</span>
                            </div>
                        </div>
                    </div>
                )}
            </main>

            {/* ============================================================
                CREATE CHANNEL MODAL
                ============================================================ */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content create-channel-modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3><i className="fas fa-plus-circle"></i> Create Channel</h3>
                            <button className="modal-close" onClick={() => setShowCreateModal(false)}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>
                        <form onSubmit={handleCreateChannel}>
                            <div className="form-group">
                                <label>Channel Name</label>
                                <input
                                    type="text"
                                    value={newChannel.name}
                                    onChange={(e) => setNewChannel(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="e.g., general, marketing, support"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label>Type</label>
                                <div className="radio-group">
                                    <label className={`radio-option ${newChannel.type === 'public' ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="type"
                                            value="public"
                                            checked={newChannel.type === 'public'}
                                            onChange={(e) => setNewChannel(prev => ({ ...prev, type: e.target.value as 'public' | 'private' }))}
                                        />
                                        <i className="fas fa-hashtag"></i>
                                        <div>
                                            <strong>Public</strong>
                                            <span>Anyone can see and join</span>
                                        </div>
                                    </label>
                                    <label className={`radio-option ${newChannel.type === 'private' ? 'selected' : ''}`}>
                                        <input
                                            type="radio"
                                            name="type"
                                            value="private"
                                            checked={newChannel.type === 'private'}
                                            onChange={(e) => setNewChannel(prev => ({ ...prev, type: e.target.value as 'public' | 'private' }))}
                                        />
                                        <i className="fas fa-lock"></i>
                                        <div>
                                            <strong>Private</strong>
                                            <span>Only invited members</span>
                                        </div>
                                    </label>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Category</label>
                                <select
                                    value={newChannel.category}
                                    onChange={(e) => setNewChannel(prev => ({ ...prev, category: e.target.value }))}
                                >
                                    {CHANNEL_CATEGORIES.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Description (optional)</label>
                                <input
                                    type="text"
                                    value={newChannel.description}
                                    onChange={(e) => setNewChannel(prev => ({ ...prev, description: e.target.value }))}
                                    placeholder="What's this channel about?"
                                />
                            </div>

                            {/* Role Restriction */}
                            {newChannel.type === 'public' && (
                                <div className="form-group role-restriction">
                                    <label className="checkbox-label">
                                        <input
                                            type="checkbox"
                                            checked={newChannel.is_restricted}
                                            onChange={(e) => setNewChannel(prev => ({
                                                ...prev,
                                                is_restricted: e.target.checked,
                                                allowed_roles: e.target.checked ? prev.allowed_roles : []
                                            }))}
                                        />
                                        <span>Restrict to specific roles</span>
                                    </label>

                                    {newChannel.is_restricted && (
                                        <div className="role-selector">
                                            <p className="hint">Only users with selected roles can see this channel</p>
                                            <div className="role-checkboxes">
                                                {roles.map(role => (
                                                    <label key={role.id} className="role-checkbox">
                                                        <input
                                                            type="checkbox"
                                                            checked={newChannel.allowed_roles.includes(role.name)}
                                                            onChange={(e) => {
                                                                if (e.target.checked) {
                                                                    setNewChannel(prev => ({
                                                                        ...prev,
                                                                        allowed_roles: [...prev.allowed_roles, role.name]
                                                                    }))
                                                                } else {
                                                                    setNewChannel(prev => ({
                                                                        ...prev,
                                                                        allowed_roles: prev.allowed_roles.filter(r => r !== role.name)
                                                                    }))
                                                                }
                                                            }}
                                                        />
                                                        <span className="role-badge">{role.name}</span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="modal-actions">
                                <button type="button" className="btn-cancel" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    <i className="fas fa-plus"></i> Create Channel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ============================================================
                SETTINGS PANEL (Slideout)
                ============================================================ */}
            {showSettings && selectedChannel && (
                <div className="settings-panel-overlay" onClick={() => setShowSettings(false)}>
                    <aside className="settings-panel" onClick={e => e.stopPropagation()}>
                        <div className="settings-header">
                            <h3>Channel Settings</h3>
                            <button className="settings-close" onClick={() => setShowSettings(false)}>
                                <i className="fas fa-times"></i>
                            </button>
                        </div>
                        <div className="settings-content">
                            <div className="settings-section">
                                <h4>{selectedChannel.is_direct ? selectedChannel.display_name : `#${selectedChannel.name}`}</h4>
                                {selectedChannel.description && (
                                    <p className="channel-desc">{selectedChannel.description}</p>
                                )}
                            </div>

                            <div className="settings-section">
                                <h5>Channel Info</h5>
                                <div className="info-row">
                                    <span className="info-label">Type</span>
                                    <span className="info-value">{selectedChannel.type}</span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">Category</span>
                                    <span className="info-value">{selectedChannel.category}</span>
                                </div>
                                <div className="info-row">
                                    <span className="info-label">Members</span>
                                    <span className="info-value">{selectedChannel.member_count}</span>
                                </div>
                                {selectedChannel.is_restricted && (
                                    <div className="info-row">
                                        <span className="info-label">Allowed Roles</span>
                                        <span className="info-value">
                                            {selectedChannel.allowed_roles.join(', ')}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Member Management - Private Channels Only */}
                            {selectedChannel.type === 'private' && (
                                <div className="settings-section">
                                    <h5><i className="fas fa-users"></i> Members</h5>
                                    {settingsLoading ? (
                                        <div className="loading-mini"><i className="fas fa-spinner fa-spin"></i></div>
                                    ) : (
                                        <>
                                            <div className="members-list">
                                                {channelSettings?.members.map(member => (
                                                    <div key={member.id} className="member-item">
                                                        <div className="member-avatar">{member.username[0].toUpperCase()}</div>
                                                        <span className="member-name">{member.username}</span>
                                                        {member.id !== selectedChannel.created_by_id ? (
                                                            <button
                                                                className="btn-remove-member"
                                                                onClick={() => handleRemoveMember(member.id, member.username)}
                                                                title="Remove member"
                                                            >
                                                                <i className="fas fa-times"></i>
                                                            </button>
                                                        ) : (
                                                            <span className="owner-badge">Owner</span>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="add-member-section">
                                                <input
                                                    type="text"
                                                    placeholder="Search users to add..."
                                                    value={addMemberSearch}
                                                    onChange={(e) => setAddMemberSearch(e.target.value)}
                                                    className="add-member-input"
                                                />
                                                {addMemberSearch && (
                                                    <div className="user-search-results">
                                                        {users
                                                            .filter(u =>
                                                                u.username.toLowerCase().includes(addMemberSearch.toLowerCase()) &&
                                                                !channelSettings?.members.some(m => m.id === u.id)
                                                            )
                                                            .slice(0, 5)
                                                            .map(user => (
                                                                <button
                                                                    key={user.id}
                                                                    className="user-result"
                                                                    onClick={() => handleAddMember(user.id)}
                                                                >
                                                                    <div className="user-avatar">{user.initial}</div>
                                                                    <span>{user.username}</span>
                                                                    <i className="fas fa-plus"></i>
                                                                </button>
                                                            ))
                                                        }
                                                    </div>
                                                )}
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}

                            {/* Role-Based Access - All Channels */}
                            {!selectedChannel.is_direct && (
                                <div className="settings-section">
                                    <h5><i className="fas fa-shield-alt"></i> Role-Based Access</h5>
                                    {settingsLoading ? (
                                        <div className="loading-mini"><i className="fas fa-spinner fa-spin"></i></div>
                                    ) : (
                                        <>
                                            <label className="checkbox-label">
                                                <input
                                                    type="checkbox"
                                                    checked={channelSettings?.is_restricted ?? false}
                                                    onChange={(e) => {
                                                        handleUpdateRoles(
                                                            channelSettings?.allowed_roles ?? [],
                                                            e.target.checked
                                                        )
                                                    }}
                                                />
                                                <span>Restrict to specific roles</span>
                                            </label>
                                            {channelSettings?.is_restricted && (
                                                <div className="role-checkboxes">
                                                    {channelSettings.available_roles.map(role => (
                                                        <label key={role.id} className="role-checkbox">
                                                            <input
                                                                type="checkbox"
                                                                checked={channelSettings.allowed_roles.includes(role.name)}
                                                                onChange={(e) => {
                                                                    const newRoles = e.target.checked
                                                                        ? [...channelSettings.allowed_roles, role.name]
                                                                        : channelSettings.allowed_roles.filter(r => r !== role.name)
                                                                    handleUpdateRoles(newRoles, true)
                                                                }}
                                                            />
                                                            <span className="role-badge">{role.name}</span>
                                                        </label>
                                                    ))}
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            )}

                            {/* Archive Section */}
                            {!selectedChannel.is_direct && (
                                <div className="settings-section">
                                    <h5><i className="fas fa-archive"></i> Archive Channel</h5>
                                    <button
                                        className={`btn-archive ${selectedChannel.is_archived ? 'archived' : ''}`}
                                        onClick={() => setShowArchiveConfirm(true)}
                                    >
                                        <i className={`fas ${selectedChannel.is_archived ? 'fa-box-open' : 'fa-archive'}`}></i>
                                        {selectedChannel.is_archived ? 'Unarchive Channel' : 'Archive Channel'}
                                    </button>
                                    <p className="archive-note">
                                        {selectedChannel.is_archived
                                            ? 'Unarchive to enable messaging again.'
                                            : 'Archived channels become read-only.'}
                                    </p>
                                </div>
                            )}

                            {/* Danger Zone */}
                            {!selectedChannel.is_direct && (
                                <div className="settings-section danger-zone">
                                    <h5><i className="fas fa-exclamation-triangle"></i> Danger Zone</h5>
                                    <button
                                        className="btn-delete"
                                        onClick={() => setShowDeleteConfirm(true)}
                                    >
                                        <i className="fas fa-trash-alt"></i>
                                        Delete Channel
                                    </button>
                                    <p className="danger-note">
                                        This will permanently delete all messages and cannot be undone.
                                    </p>
                                </div>
                            )}
                        </div>
                    </aside>
                </div>
            )}

            {/* ============================================================
                CONFIRMATION MODALS
                ============================================================ */}
            <ConfirmationModal
                isOpen={showDeleteConfirm}
                title="Delete Channel"
                message={`Are you sure you want to permanently delete #${selectedChannel?.name}? This will remove all messages and cannot be undone.`}
                confirmText="Delete Channel"
                danger={true}
                loading={deleteLoading}
                onConfirm={handleDeleteChannel}
                onCancel={() => setShowDeleteConfirm(false)}
            />

            <ConfirmationModal
                isOpen={showArchiveConfirm}
                title={selectedChannel?.is_archived ? "Unarchive Channel" : "Archive Channel"}
                message={selectedChannel?.is_archived
                    ? `Are you sure you want to unarchive #${selectedChannel?.name}? Members will be able to send messages again.`
                    : `Are you sure you want to archive #${selectedChannel?.name}? The channel will become read-only.`}
                confirmText={selectedChannel?.is_archived ? "Unarchive" : "Archive"}
                danger={false}
                loading={archiveLoading}
                onConfirm={handleToggleArchive}
                onCancel={() => setShowArchiveConfirm(false)}
            />
        </div>
    )
}

// =============================================================================
// Export with Provider
// =============================================================================

export function UnifiedMessagingDashboard(props: UnifiedMessagingDashboardProps) {
    return (
        <ToastProvider>
            <MessagingDashboard {...props} />
        </ToastProvider>
    )
}

export default UnifiedMessagingDashboard
