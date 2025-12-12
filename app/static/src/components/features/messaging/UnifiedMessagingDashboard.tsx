/**
 * UnifiedMessagingDashboard Component
 * 
 * Enterprise-level messaging platform with Discord/Slack-style UX.
 * Single-page experience with in-place channel switching, role-based access,
 * and premium glassmorphism design.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
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

interface UnifiedMessagingDashboardProps {
    currentUserId: number
    userRoles?: string[]
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
// Main Component
// =============================================================================

export function UnifiedMessagingDashboard({
    currentUserId,
}: UnifiedMessagingDashboardProps) {
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
        } finally {
            setLoading(false)
        }
    }, [])

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
        } finally {
            setMessagesLoading(false)
        }
    }, [scrollToBottom])

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
            }
        } catch (error) {
            console.error('Send error:', error)
        }
    }

    // Toggle reaction
    const handleReaction = async (messageId: number, emoji: string) => {
        try {
            const response = await api.post<{ success: boolean; reactions: Message['reactions'] }>(
                `/messaging/message/${messageId}/react`,
                { emoji }
            )
            if (response.ok && response.data?.success) {
                setMessages(prev => prev.map(msg =>
                    msg.id === messageId
                        ? { ...msg, reactions: response.data!.reactions }
                        : msg
                ))
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
            const response = await api.post('/messaging/create_channel', formData)
            if (response.ok) {
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
            }
        } catch (error) {
            console.error('Create channel error:', error)
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
                                    onClick={() => setShowSettings(true)}
                                >
                                    <i className="fas fa-cog"></i>
                                </button>
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="chat-container" ref={chatBoxRef}>
                            {messagesLoading ? (
                                <div className="messages-loading">
                                    <i className="fas fa-spinner fa-spin"></i>
                                    <span>Loading messages...</span>
                                </div>
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

                            {/* Danger Zone */}
                            {!selectedChannel.is_direct && (
                                <div className="settings-section danger-zone">
                                    <h5>Danger Zone</h5>
                                    <button
                                        className="btn-delete"
                                        onClick={async () => {
                                            const confirmDelete = window.confirm(
                                                `Are you sure you want to permanently delete #${selectedChannel.name}? This action cannot be undone.`
                                            )
                                            if (confirmDelete) {
                                                try {
                                                    const response = await api.post(
                                                        `/messaging/channel/${selectedChannel.id}/delete`,
                                                        {} // Empty body to ensure proper request format
                                                    )
                                                    if (response.ok) {
                                                        setShowSettings(false)
                                                        setSelectedChannel(null)
                                                        await loadChannels()
                                                    } else {
                                                        alert('Failed to delete channel. You may not have permission.')
                                                    }
                                                } catch (error) {
                                                    console.error('Delete error:', error)
                                                    alert('Failed to delete channel.')
                                                }
                                            }
                                        }}
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
        </div>
    )
}

export default UnifiedMessagingDashboard
