/**
 * MessagingChannel Component
 * 
 * Real-time messaging channel with reactions, file attachments,
 * and read receipts. Replaces inline JS from messaging/channel.html.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import api from '../../../api'
import { DataCard } from './DataCard'

// =============================================================================
// Types
// =============================================================================

interface MessageCard {
    type: string
    id?: number
    title?: string
    [key: string]: unknown
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
    // Enterprise messaging fields
    message_type?: 'text' | 'command' | 'system' | 'card'
    card?: MessageCard | null
    is_pinned?: boolean
    extra_data?: Record<string, unknown> | null
}


interface Member {
    id: number
    username: string
}

interface ChannelInfo {
    id: number
    name: string
    type: 'public' | 'private' | 'direct'
    is_archived: boolean
    is_direct: boolean
    display_name: string
}

interface MessagingChannelProps {
    /** Current channel info */
    channel: ChannelInfo
    /** Initial messages */
    initialMessages: Message[]
    /** Current user ID */
    currentUserId: number
    /** Is muted */
    isMuted: boolean
    /** Can manage members (private channels only) */
    canManageMembers: boolean
    /** Can archive channel */
    canArchive: boolean
    /** Users who have seen the latest message */
    seenUsers?: Member[]
    /** Polling URL for new messages (fallback) */
    pollUrl: string
    /** SSE stream URL for real-time messages */
    streamUrl?: string
    /** Send message URL */
    sendUrl: string
    /** React to message URL pattern */
    reactUrlPattern: string
    /** Manage members URL */
    manageMembersUrl?: string
    /** Toggle mute URL */
    toggleMuteUrl: string
    /** Archive/unarchive URL */
    archiveUrl?: string
}

// Common emojis for reactions
const EMOJI_OPTIONS = ['👍', '❤️', '😂', '😮', '😢', '🔥', '🎉', '👏']

// =============================================================================
// Main Component
// =============================================================================

export function MessagingChannel({
    channel,
    initialMessages,
    currentUserId,
    isMuted: initialMuted,
    canManageMembers,
    seenUsers = [],
    pollUrl,
    streamUrl,
    sendUrl,
    reactUrlPattern,
    manageMembersUrl,
    toggleMuteUrl,
}: MessagingChannelProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages)
    const [messageInput, setMessageInput] = useState('')
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [isMuted, setIsMuted] = useState(initialMuted)
    const [showEmojiPicker, setShowEmojiPicker] = useState<number | null>(null)
    const [useSSE, setUseSSE] = useState(!!streamUrl)

    const chatBoxRef = useRef<HTMLDivElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const lastIdRef = useRef<number>(
        initialMessages.length > 0 ? initialMessages[initialMessages.length - 1].id : 0
    )

    // Scroll to bottom
    const scrollToBottom = useCallback(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
        }
    }, [])

    // Real-time messaging: Try SSE first, fall back to polling
    useEffect(() => {
        let eventSource: EventSource | null = null
        let pollInterval: ReturnType<typeof setInterval> | null = null

        const handleNewMessages = (newMessages: Message[]) => {
            setMessages(prev => [...prev, ...newMessages])
            if (newMessages.length > 0) {
                lastIdRef.current = newMessages[newMessages.length - 1].id
            }
            scrollToBottom()
        }

        // Try SSE if available
        if (useSSE && streamUrl) {
            const sseUrl = `${streamUrl}?last_id=${lastIdRef.current}`
            eventSource = new EventSource(sseUrl)

            eventSource.addEventListener('messages', (event: MessageEvent) => {
                try {
                    const newMessages = JSON.parse(event.data) as Message[]
                    handleNewMessages(newMessages)
                } catch (e) {
                    console.error('SSE parse error:', e)
                }
            })

            eventSource.addEventListener('connected', () => {
                console.log('SSE connected to channel')
            })

            eventSource.onerror = () => {
                console.warn('SSE error, falling back to polling')
                eventSource?.close()
                setUseSSE(false)
            }
        } else {
            // Polling fallback
            pollInterval = setInterval(async () => {
                try {
                    const response = await api.get<Message[]>(`${pollUrl}?last_id=${lastIdRef.current}`)
                    if (response.ok && response.data && response.data.length > 0) {
                        handleNewMessages(response.data)
                    }
                } catch (error) {
                    console.error('Polling error:', error)
                }
            }, 3000)
        }

        return () => {
            eventSource?.close()
            if (pollInterval) clearInterval(pollInterval)
        }
    }, [pollUrl, streamUrl, scrollToBottom, useSSE])

    // Initial scroll to bottom
    useEffect(() => {
        scrollToBottom()
    }, [scrollToBottom])

    // Send message
    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!messageInput.trim() && !selectedFile) return

        const formData = new FormData()
        formData.append('content', messageInput)
        if (selectedFile) {
            formData.append('file', selectedFile)
        }

        try {
            const response = await api.post(sendUrl, formData)
            if (response.ok) {
                setMessageInput('')
                setSelectedFile(null)
                if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                }
            } else {
                alert('Failed to send message')
            }
        } catch (error) {
            console.error('Send error:', error)
            alert('Failed to send message')
        }
    }

    // Toggle reaction
    const handleReaction = async (messageId: number, emoji: string) => {
        try {
            const url = reactUrlPattern.replace('{id}', String(messageId))
            const response = await api.post<{ success: boolean; reactions: Message['reactions'] }>(
                url,
                { emoji }
            )

            if (response.ok && response.data?.success) {
                // Update message reactions locally
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

    // Toggle mute
    const handleToggleMute = async () => {
        try {
            const response = await api.post(toggleMuteUrl, {})
            if (response.ok) {
                setIsMuted(!isMuted)
            }
        } catch (error) {
            console.error('Mute toggle error:', error)
        }
    }

    // File selection
    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0])
        }
    }

    return (
        <div className="messaging-channel">
            {/* Channel Header */}
            <div className="channel-header">
                <h3>
                    {channel.is_direct ? (
                        <><i className="fas fa-user"></i> {channel.display_name}</>
                    ) : (
                        <><i className="fas fa-hashtag"></i> {channel.name}</>
                    )}
                    {channel.is_archived && (
                        <span className="channel-status">Archived</span>
                    )}
                </h3>
                <div className="channel-actions">
                    {canManageMembers && manageMembersUrl && (
                        <a href={manageMembersUrl} className="btn-icon" title="Manage Members">
                            <i className="fas fa-users-cog"></i>
                        </a>
                    )}
                    <button
                        type="button"
                        className="btn-icon"
                        onClick={handleToggleMute}
                        title="Toggle Notifications"
                    >
                        <i className={`fas fa-bell${isMuted ? '-slash' : ''}`}></i>
                    </button>
                </div>
            </div>

            {/* Messages */}
            <div className="chat-container" ref={chatBoxRef}>
                {messages.map(msg => (
                    <div
                        key={msg.id}
                        className={`message ${msg.user_id === currentUserId ? 'me' : ''} ${msg.message_type || 'text'} ${msg.is_pinned ? 'pinned' : ''}`}
                        data-id={msg.id}
                    >
                        <div className="message-avatar">
                            {msg.user[0].toUpperCase()}
                        </div>
                        <div className="message-bubble">
                            {/* Pinned Indicator */}
                            {msg.is_pinned && (
                                <div className="pinned-indicator">
                                    <i className="fas fa-thumbtack"></i> Pinned
                                </div>
                            )}
                            <div className="message-meta">
                                <strong>{msg.user}</strong> • {msg.created_at.split(' ')[1]?.substring(0, 5) || ''}
                            </div>
                            <div
                                className="message-content"
                                dangerouslySetInnerHTML={{ __html: msg.content }}
                            />

                            {/* Data Card for slash command results */}
                            {msg.card && (
                                <DataCard card={msg.card as unknown as Parameters<typeof DataCard>[0]['card']} />
                            )}

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
                                    <span
                                        key={emoji}
                                        className={`reaction ${data.user_reacted ? 'user-reacted' : ''}`}
                                        onClick={() => handleReaction(msg.id, emoji)}
                                    >
                                        {emoji} <span className="reaction-count">{data.count}</span>
                                    </span>
                                ))}
                                <button
                                    className="add-reaction-btn"
                                    onClick={() => setShowEmojiPicker(showEmojiPicker === msg.id ? null : msg.id)}
                                >
                                    <i className="far fa-smile"></i>
                                </button>

                                {/* Emoji Picker */}
                                {showEmojiPicker === msg.id && (
                                    <div className="emoji-picker show">
                                        {EMOJI_OPTIONS.map(emoji => (
                                            <button
                                                key={emoji}
                                                type="button"
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
                ))}
            </div>

            {/* Read Receipts */}
            {seenUsers.length > 0 && (
                <div className="read-receipts">
                    {seenUsers.map(member => (
                        <div
                            key={member.id}
                            className="read-receipt-avatar"
                            title={member.username}
                        >
                            {member.username[0].toUpperCase()}
                        </div>
                    ))}
                    <span className="read-receipt-label">Seen</span>
                </div>
            )}

            {/* Message Input */}
            <div className="message-input-container">
                <form className="message-input-form" onSubmit={handleSendMessage}>
                    <input
                        type="text"
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        placeholder="Type a message... Use @username to mention"
                        autoComplete="off"
                    />
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                    />
                    <button
                        type="button"
                        className="btn btn-outline-secondary"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <i className="fas fa-paperclip"></i>
                    </button>
                    <button type="submit" className="btn btn-primary">
                        <i className="fas fa-paper-plane"></i>
                    </button>
                </form>
                {selectedFile && (
                    <div className="file-name-display">
                        Attached: {selectedFile.name}
                        <button
                            type="button"
                            className="btn-remove-file"
                            onClick={() => {
                                setSelectedFile(null)
                                if (fileInputRef.current) fileInputRef.current.value = ''
                            }}
                        >
                            ×
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

export default MessagingChannel
