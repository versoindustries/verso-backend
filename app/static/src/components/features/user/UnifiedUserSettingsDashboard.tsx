/**
 * UnifiedUserSettingsDashboard - Enterprise User Settings React Island
 * 
 * Consolidated dashboard for all user account settings:
 * - Profile & Security
 * - Preferences (email, push, SMS, privacy, theme)
 * - Notification Settings
 * - Saved Items / Wishlist
 * - Orders History
 * - Appointments
 * - Subscriptions
 * - Digital Downloads
 * 
 * Features world-class glassmorphism design with micro-animations.
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
    User, Settings, Bell, Heart, ShoppingBag, Calendar, RefreshCw, Download,
    Lock, Mail, MapPin, Globe, Moon, Eye, EyeOff, Save, Trash2,
    AlertCircle, CheckCircle, ChevronRight, Shield, Sparkles, Package,
    Clock, CreditCard
} from 'lucide-react'
import api from '../../../api'
import './user-settings-dashboard.css'

// =============================================================================
// Types
// =============================================================================

interface Profile {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    bio: string
    location: string
    phone: string
}

interface Preferences {
    email_marketing: boolean
    email_order_updates: boolean
    email_appointment_reminders: boolean
    email_digest_weekly: boolean
    email_newsletter: boolean
    push_enabled: boolean
    sms_enabled: boolean
    show_activity_status: boolean
    show_profile_publicly: boolean
    theme: string
    language: string
}

interface NotificationPreferences {
    email_digest_enabled: boolean
    email_digest_frequency: string
    muted_types: string[]
}

interface NotificationType {
    value: string
    label: string
}

interface SavedItem {
    id: number
    item_type: string
    item_id: number
    notes: string
    created_at: string
    item: {
        id: number
        name?: string
        title?: string
        price?: number
        image?: string
        excerpt?: string
    }
}

interface Order {
    id: number
    total_amount: number
    status: string
    created_at: string
    items_count: number
}

interface Appointment {
    id: number
    service_name: string
    preferred_date_time: string
    status: string
    notes: string
}

interface Subscription {
    id: number
    plan_name: string
    status: string
    current_period_end: string
    cancel_at_period_end: boolean
}

interface DigitalDownload {
    id: number
    product_name: string
    download_count: number
    max_downloads: number
    is_valid: boolean
    download_url: string
}

interface Stats {
    total_orders: number
    pending_orders: number
    total_downloads: number
    upcoming_appointments: number
    active_subscriptions: number
    saved_items: number
}

interface SettingsData {
    profile: Profile
    preferences: Preferences
    notification_preferences: NotificationPreferences
    notification_types: NotificationType[]
    saved_items: SavedItem[]
    orders: Order[]
    appointments: Appointment[]
    subscriptions: Subscription[]
    downloads: DigitalDownload[]
    stats: Stats
}

interface UnifiedUserSettingsDashboardProps {
    initialTab?: string
    csrfToken?: string
    apiBaseUrl?: string
}

type TabId = 'profile' | 'preferences' | 'notifications' | 'saved' | 'orders' | 'appointments' | 'subscriptions' | 'downloads'

interface Tab {
    id: TabId
    label: string
    icon: React.ReactNode
    badge?: number
}

// =============================================================================
// Toast Component
// =============================================================================

interface Toast {
    id: number
    message: string
    type: 'success' | 'error' | 'info'
}

const ToastContainer: React.FC<{ toasts: Toast[], onDismiss: (id: number) => void }> = ({ toasts, onDismiss }) => (
    <div className="usd-toast-container">
        {toasts.map(toast => (
            <div key={toast.id} className={`usd-toast usd-toast-${toast.type}`}>
                {toast.type === 'success' && <CheckCircle size={18} />}
                {toast.type === 'error' && <AlertCircle size={18} />}
                <span>{toast.message}</span>
                <button onClick={() => onDismiss(toast.id)}>&times;</button>
            </div>
        ))}
    </div>
)

// =============================================================================
// Toggle Switch Component
// =============================================================================

const ToggleSwitch: React.FC<{
    checked: boolean
    onChange: (checked: boolean) => void
    label: string
    description?: string
}> = ({ checked, onChange, label, description }) => (
    <label className="usd-toggle-row">
        <div className="usd-toggle-info">
            <span className="usd-toggle-label">{label}</span>
            {description && <span className="usd-toggle-desc">{description}</span>}
        </div>
        <div className={`usd-toggle ${checked ? 'usd-toggle-on' : ''}`} onClick={() => onChange(!checked)}>
            <div className="usd-toggle-handle" />
        </div>
    </label>
)

// =============================================================================
// Status Badge Component
// =============================================================================

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const statusColors: Record<string, string> = {
        active: 'success',
        trialing: 'warning',
        paid: 'success',
        delivered: 'success',
        completed: 'success',
        pending: 'warning',
        processing: 'warning',
        shipped: 'info',
        cancelled: 'danger',
        canceled: 'danger',
        past_due: 'danger',
        failed: 'danger',
        upcoming: 'info',
        past: 'muted'
    }
    const colorClass = statusColors[status.toLowerCase()] || 'muted'

    return (
        <span className={`usd-status-badge usd-status-${colorClass}`}>
            {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
        </span>
    )
}

// =============================================================================
// Main Component
// =============================================================================

const UnifiedUserSettingsDashboard: React.FC<UnifiedUserSettingsDashboardProps> = ({
    initialTab = 'profile',
    apiBaseUrl = '/api/user'
}) => {
    const [activeTab, setActiveTab] = useState<TabId>(initialTab as TabId)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [data, setData] = useState<SettingsData | null>(null)
    const [toasts, setToasts] = useState<Toast[]>([])

    // Form states
    const [profile, setProfile] = useState<Profile | null>(null)
    const [preferences, setPreferences] = useState<Preferences | null>(null)
    const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences | null>(null)

    // Password change
    const [passwords, setPasswords] = useState({
        current_password: '',
        new_password: '',
        confirm_password: ''
    })
    const [showPasswords, setShowPasswords] = useState({
        current: false,
        new: false,
        confirm: false
    })

    // Toast helper
    const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
        const id = Date.now()
        setToasts(prev => [...prev, { id, message, type }])
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
    }, [])

    const dismissToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    // Fetch data
    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            console.log('[UnifiedUserSettingsDashboard] Fetching from:', `${apiBaseUrl}/settings-data`)
            const response = await api.get<SettingsData & { success: boolean }>(`${apiBaseUrl}/settings-data`)
            console.log('[UnifiedUserSettingsDashboard] Response:', {
                ok: response.ok,
                status: response.status,
                error: response.error,
                hasData: !!response.data,
                success: response.data?.success,
                dataType: typeof response.data
            })
            if (response.ok && response.data?.success) {
                setData(response.data)
                setProfile(response.data.profile)
                setPreferences(response.data.preferences)
                setNotifPrefs(response.data.notification_preferences)
                console.log('[UnifiedUserSettingsDashboard] Data loaded successfully')
            } else {
                console.error('[UnifiedUserSettingsDashboard] Failed to load settings:', response)
                addToast('Failed to load settings', 'error')
            }
        } catch (error) {
            console.error('[UnifiedUserSettingsDashboard] Exception during fetch:', error)
            addToast('Failed to load settings', 'error')
        } finally {
            setLoading(false)
        }
    }, [apiBaseUrl, addToast])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    // Save profile
    const saveProfile = async () => {
        if (!profile) return
        setSaving(true)
        try {
            const response = await api.post<{ success: boolean; message?: string }>(`${apiBaseUrl}/profile`, profile)
            if (response.ok && response.data?.success) {
                addToast('Profile updated successfully', 'success')
            } else {
                addToast(response.data?.message || 'Failed to update profile', 'error')
            }
        } catch (error) {
            addToast('Failed to update profile', 'error')
        } finally {
            setSaving(false)
        }
    }

    // Save password
    const savePassword = async () => {
        if (!passwords.current_password || !passwords.new_password) {
            addToast('Please fill in all password fields', 'error')
            return
        }
        if (passwords.new_password !== passwords.confirm_password) {
            addToast('New passwords do not match', 'error')
            return
        }
        if (passwords.new_password.length < 8) {
            addToast('Password must be at least 8 characters', 'error')
            return
        }

        setSaving(true)
        try {
            const response = await api.post<{ success: boolean; message?: string }>(`${apiBaseUrl}/password`, passwords)
            if (response.ok && response.data?.success) {
                addToast('Password changed successfully', 'success')
                setPasswords({ current_password: '', new_password: '', confirm_password: '' })
            } else {
                addToast(response.data?.message || 'Failed to change password', 'error')
            }
        } catch (error) {
            addToast('Failed to change password', 'error')
        } finally {
            setSaving(false)
        }
    }

    // Save preferences
    const savePreferences = async () => {
        if (!preferences) return
        setSaving(true)
        try {
            const response = await api.post<{ success: boolean; message?: string }>(`${apiBaseUrl}/preferences`, preferences)
            if (response.ok && response.data?.success) {
                addToast('Preferences saved successfully', 'success')
            } else {
                addToast(response.data?.message || 'Failed to save preferences', 'error')
            }
        } catch (error) {
            addToast('Failed to save preferences', 'error')
        } finally {
            setSaving(false)
        }
    }

    // Save notification preferences
    const saveNotificationPrefs = async () => {
        if (!notifPrefs) return
        setSaving(true)
        try {
            const response = await api.post<{ success: boolean; message?: string }>(`${apiBaseUrl}/notification-preferences`, notifPrefs)
            if (response.ok && response.data?.success) {
                addToast('Notification settings saved', 'success')
            } else {
                addToast(response.data?.message || 'Failed to save notification settings', 'error')
            }
        } catch (error) {
            addToast('Failed to save notification settings', 'error')
        } finally {
            setSaving(false)
        }
    }

    // Remove saved item
    const removeSavedItem = async (itemId: number) => {
        try {
            const response = await api.delete<{ success: boolean }>(`${apiBaseUrl}/saved-items/${itemId}`)
            if (response.ok && response.data?.success) {
                setData(prev => prev ? {
                    ...prev,
                    saved_items: prev.saved_items.filter(i => i.id !== itemId)
                } : null)
                addToast('Item removed from saved', 'success')
            }
        } catch (error) {
            addToast('Failed to remove item', 'error')
        }
    }

    // Toggle muted notification type
    const toggleMutedType = (type: string) => {
        if (!notifPrefs) return
        const muted = notifPrefs.muted_types || []
        if (muted.includes(type)) {
            setNotifPrefs({ ...notifPrefs, muted_types: muted.filter(t => t !== type) })
        } else {
            setNotifPrefs({ ...notifPrefs, muted_types: [...muted, type] })
        }
    }

    // Tab definitions with badges
    const tabs: Tab[] = [
        { id: 'profile', label: 'Profile & Security', icon: <User size={18} /> },
        { id: 'preferences', label: 'Preferences', icon: <Settings size={18} /> },
        { id: 'notifications', label: 'Notifications', icon: <Bell size={18} /> },
        { id: 'saved', label: 'Saved Items', icon: <Heart size={18} />, badge: data?.stats.saved_items },
        { id: 'orders', label: 'Orders', icon: <ShoppingBag size={18} />, badge: data?.stats.total_orders },
        { id: 'appointments', label: 'Appointments', icon: <Calendar size={18} />, badge: data?.stats.upcoming_appointments },
        { id: 'subscriptions', label: 'Subscriptions', icon: <RefreshCw size={18} />, badge: data?.stats.active_subscriptions },
        { id: 'downloads', label: 'Downloads', icon: <Download size={18} />, badge: data?.stats.total_downloads },
    ]

    // Format currency
    const formatCurrency = (cents: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(cents / 100)
    }

    // Format date
    const formatDate = (dateStr: string) => {
        if (!dateStr) return 'N/A'
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        })
    }

    const formatDateTime = (dateStr: string) => {
        if (!dateStr) return 'N/A'
        return new Date(dateStr).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        })
    }

    if (loading) {
        return (
            <div className="usd-container">
                <div className="usd-loading">
                    <div className="usd-spinner" />
                    <p>Loading your settings...</p>
                </div>
            </div>
        )
    }

    // Error state if data failed to load
    if (!data) {
        return (
            <div className="usd-container">
                <ToastContainer toasts={toasts} onDismiss={dismissToast} />
                <div className="usd-empty" style={{ marginTop: '4rem' }}>
                    <AlertCircle size={48} />
                    <h4>Unable to Load Settings</h4>
                    <p>There was a problem loading your account settings. Please try refreshing the page.</p>
                    <button className="usd-btn usd-btn-primary" onClick={fetchData} style={{ marginTop: '1.5rem' }}>
                        <RefreshCw size={16} /> Try Again
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="usd-container">
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            {/* Header */}
            <header className="usd-header">
                <div className="usd-header-content">
                    <div className="usd-header-icon">
                        <Sparkles size={28} />
                    </div>
                    <div>
                        <h1 className="usd-header-title">Account Settings</h1>
                        <p className="usd-header-subtitle">Manage your profile, preferences, and account data</p>
                    </div>
                </div>
            </header>

            {/* Tab Navigation */}
            <nav className="usd-tabs">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`usd-tab ${activeTab === tab.id ? 'usd-tab-active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        {tab.icon}
                        <span>{tab.label}</span>
                        {tab.badge !== undefined && tab.badge > 0 && (
                            <span className="usd-tab-badge">{tab.badge}</span>
                        )}
                    </button>
                ))}
            </nav>

            {/* Content Area */}
            <div className="usd-content">

                {/* Profile & Security Tab */}
                {activeTab === 'profile' && !profile && (
                    <div className="usd-empty">
                        <div className="usd-spinner" />
                        <p>Loading profile data...</p>
                    </div>
                )}
                {activeTab === 'profile' && profile && (
                    <div className="usd-panel-grid">
                        {/* Profile Info */}
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <User size={20} />
                                <h3>Profile Information</h3>
                            </div>
                            <div className="usd-panel-body">
                                <div className="usd-form-row">
                                    <div className="usd-form-group">
                                        <label>First Name</label>
                                        <input
                                            type="text"
                                            value={profile.first_name}
                                            onChange={e => setProfile({ ...profile, first_name: e.target.value })}
                                            placeholder="First name"
                                        />
                                    </div>
                                    <div className="usd-form-group">
                                        <label>Last Name</label>
                                        <input
                                            type="text"
                                            value={profile.last_name}
                                            onChange={e => setProfile({ ...profile, last_name: e.target.value })}
                                            placeholder="Last name"
                                        />
                                    </div>
                                </div>
                                <div className="usd-form-group">
                                    <label>Username</label>
                                    <input
                                        type="text"
                                        value={profile.username}
                                        onChange={e => setProfile({ ...profile, username: e.target.value })}
                                        placeholder="Username"
                                    />
                                </div>
                                <div className="usd-form-group">
                                    <label><Mail size={14} /> Email</label>
                                    <input
                                        type="email"
                                        value={profile.email}
                                        onChange={e => setProfile({ ...profile, email: e.target.value })}
                                        placeholder="Email address"
                                    />
                                </div>
                                <div className="usd-form-group">
                                    <label><MapPin size={14} /> Location</label>
                                    <input
                                        type="text"
                                        value={profile.location}
                                        onChange={e => setProfile({ ...profile, location: e.target.value })}
                                        placeholder="City, State"
                                    />
                                </div>
                                <div className="usd-form-group">
                                    <label>Bio</label>
                                    <textarea
                                        value={profile.bio}
                                        onChange={e => setProfile({ ...profile, bio: e.target.value })}
                                        placeholder="Tell us about yourself..."
                                        rows={3}
                                    />
                                </div>
                                <button className="usd-btn usd-btn-primary" onClick={saveProfile} disabled={saving}>
                                    <Save size={16} />
                                    {saving ? 'Saving...' : 'Save Profile'}
                                </button>
                            </div>
                        </div>

                        {/* Security */}
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Lock size={20} />
                                <h3>Change Password</h3>
                            </div>
                            <div className="usd-panel-body">
                                <div className="usd-form-group">
                                    <label>Current Password</label>
                                    <div className="usd-input-with-icon">
                                        <input
                                            type={showPasswords.current ? 'text' : 'password'}
                                            value={passwords.current_password}
                                            onChange={e => setPasswords({ ...passwords, current_password: e.target.value })}
                                            placeholder="Current password"
                                        />
                                        <button
                                            type="button"
                                            className="usd-input-icon-btn"
                                            onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                                        >
                                            {showPasswords.current ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>
                                </div>
                                <div className="usd-form-group">
                                    <label>New Password</label>
                                    <div className="usd-input-with-icon">
                                        <input
                                            type={showPasswords.new ? 'text' : 'password'}
                                            value={passwords.new_password}
                                            onChange={e => setPasswords({ ...passwords, new_password: e.target.value })}
                                            placeholder="New password (min 8 characters)"
                                        />
                                        <button
                                            type="button"
                                            className="usd-input-icon-btn"
                                            onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                                        >
                                            {showPasswords.new ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>
                                </div>
                                <div className="usd-form-group">
                                    <label>Confirm New Password</label>
                                    <div className="usd-input-with-icon">
                                        <input
                                            type={showPasswords.confirm ? 'text' : 'password'}
                                            value={passwords.confirm_password}
                                            onChange={e => setPasswords({ ...passwords, confirm_password: e.target.value })}
                                            placeholder="Confirm new password"
                                        />
                                        <button
                                            type="button"
                                            className="usd-input-icon-btn"
                                            onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                                        >
                                            {showPasswords.confirm ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>
                                </div>
                                <button className="usd-btn usd-btn-primary" onClick={savePassword} disabled={saving}>
                                    <Shield size={16} />
                                    {saving ? 'Updating...' : 'Update Password'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Preferences Tab */}
                {activeTab === 'preferences' && !preferences && (
                    <div className="usd-empty">
                        <div className="usd-spinner" />
                        <p>Loading preferences...</p>
                    </div>
                )}
                {activeTab === 'preferences' && preferences && (
                    <div className="usd-panel-grid">
                        {/* Email Notifications */}
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Mail size={20} />
                                <h3>Email Notifications</h3>
                            </div>
                            <div className="usd-panel-body usd-toggle-list">
                                <ToggleSwitch
                                    checked={preferences.email_order_updates}
                                    onChange={v => setPreferences({ ...preferences, email_order_updates: v })}
                                    label="Order Updates"
                                    description="Receive updates about your orders and shipments"
                                />
                                <ToggleSwitch
                                    checked={preferences.email_appointment_reminders}
                                    onChange={v => setPreferences({ ...preferences, email_appointment_reminders: v })}
                                    label="Appointment Reminders"
                                    description="Get reminded before scheduled appointments"
                                />
                                <ToggleSwitch
                                    checked={preferences.email_newsletter}
                                    onChange={v => setPreferences({ ...preferences, email_newsletter: v })}
                                    label="Newsletter"
                                    description="Stay updated with our latest news"
                                />
                                <ToggleSwitch
                                    checked={preferences.email_marketing}
                                    onChange={v => setPreferences({ ...preferences, email_marketing: v })}
                                    label="Marketing & Promotions"
                                    description="Receive exclusive offers and deals"
                                />
                                <ToggleSwitch
                                    checked={preferences.email_digest_weekly}
                                    onChange={v => setPreferences({ ...preferences, email_digest_weekly: v })}
                                    label="Weekly Digest"
                                    description="Weekly summary of your account activity"
                                />
                            </div>
                        </div>

                        {/* Other Notifications */}
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Bell size={20} />
                                <h3>Other Notifications</h3>
                            </div>
                            <div className="usd-panel-body usd-toggle-list">
                                <ToggleSwitch
                                    checked={preferences.push_enabled}
                                    onChange={v => setPreferences({ ...preferences, push_enabled: v })}
                                    label="Push Notifications"
                                    description="Receive browser push notifications"
                                />
                                <ToggleSwitch
                                    checked={preferences.sms_enabled}
                                    onChange={v => setPreferences({ ...preferences, sms_enabled: v })}
                                    label="SMS Notifications"
                                    description="Receive text message notifications"
                                />
                            </div>
                        </div>

                        {/* Privacy */}
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Shield size={20} />
                                <h3>Privacy Settings</h3>
                            </div>
                            <div className="usd-panel-body usd-toggle-list">
                                <ToggleSwitch
                                    checked={preferences.show_activity_status}
                                    onChange={v => setPreferences({ ...preferences, show_activity_status: v })}
                                    label="Show Activity Status"
                                    description="Let others see when you're online"
                                />
                                <ToggleSwitch
                                    checked={preferences.show_profile_publicly}
                                    onChange={v => setPreferences({ ...preferences, show_profile_publicly: v })}
                                    label="Public Profile"
                                    description="Make your profile visible to others"
                                />
                            </div>
                        </div>

                        {/* Display */}
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Globe size={20} />
                                <h3>Display Settings</h3>
                            </div>
                            <div className="usd-panel-body">
                                <div className="usd-form-row">
                                    <div className="usd-form-group">
                                        <label><Moon size={14} /> Theme</label>
                                        <select
                                            value={preferences.theme}
                                            onChange={e => setPreferences({ ...preferences, theme: e.target.value })}
                                        >
                                            <option value="dark">Dark</option>
                                            <option value="light">Light</option>
                                            <option value="auto">System Default</option>
                                        </select>
                                    </div>
                                    <div className="usd-form-group">
                                        <label><Globe size={14} /> Language</label>
                                        <select
                                            value={preferences.language}
                                            onChange={e => setPreferences({ ...preferences, language: e.target.value })}
                                        >
                                            <option value="en">English</option>
                                            <option value="es">Español</option>
                                            <option value="fr">Français</option>
                                            <option value="de">Deutsch</option>
                                        </select>
                                    </div>
                                </div>
                                <button className="usd-btn usd-btn-primary" onClick={savePreferences} disabled={saving}>
                                    <Save size={16} />
                                    {saving ? 'Saving...' : 'Save Preferences'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Notifications Tab */}
                {activeTab === 'notifications' && (!notifPrefs || !data) && (
                    <div className="usd-empty">
                        <div className="usd-spinner" />
                        <p>Loading notification settings...</p>
                    </div>
                )}
                {activeTab === 'notifications' && notifPrefs && data && (
                    <div className="usd-panel-single">
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Bell size={20} />
                                <h3>Notification Preferences</h3>
                            </div>
                            <div className="usd-panel-body">
                                {/* Email Digest */}
                                <div className="usd-section">
                                    <h4><Mail size={16} /> Email Digest</h4>
                                    <ToggleSwitch
                                        checked={notifPrefs.email_digest_enabled}
                                        onChange={v => setNotifPrefs({ ...notifPrefs, email_digest_enabled: v })}
                                        label="Send Email Digests"
                                        description="Receive email digests of unread notifications"
                                    />
                                    <div className="usd-form-group" style={{ marginTop: '1rem' }}>
                                        <label>Digest Frequency</label>
                                        <select
                                            value={notifPrefs.email_digest_frequency}
                                            onChange={e => setNotifPrefs({ ...notifPrefs, email_digest_frequency: e.target.value })}
                                        >
                                            <option value="daily">Daily</option>
                                            <option value="weekly">Weekly</option>
                                            <option value="never">Never</option>
                                        </select>
                                    </div>
                                </div>

                                {/* Muted Types */}
                                <div className="usd-section">
                                    <h4><Bell size={16} /> Muted Notification Types</h4>
                                    <p className="usd-section-desc">Select notification types to mute. You won't receive these notifications.</p>
                                    <div className="usd-muted-types">
                                        {data.notification_types.map(type => (
                                            <label key={type.value} className="usd-muted-type">
                                                <span>{type.label}</span>
                                                <div
                                                    className={`usd-toggle ${notifPrefs.muted_types?.includes(type.value) ? 'usd-toggle-on' : ''}`}
                                                    onClick={() => toggleMutedType(type.value)}
                                                >
                                                    <div className="usd-toggle-handle" />
                                                </div>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <button className="usd-btn usd-btn-primary" onClick={saveNotificationPrefs} disabled={saving}>
                                    <Save size={16} />
                                    {saving ? 'Saving...' : 'Save Notification Settings'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Saved Items Tab */}
                {activeTab === 'saved' && data && (
                    <div className="usd-panel-single">
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Heart size={20} />
                                <h3>Saved Items</h3>
                            </div>
                            <div className="usd-panel-body">
                                {data.saved_items.length === 0 ? (
                                    <div className="usd-empty">
                                        <Heart size={48} />
                                        <h4>No saved items yet</h4>
                                        <p>Items you save will appear here. Start browsing to save your favorites!</p>
                                    </div>
                                ) : (
                                    <div className="usd-saved-grid">
                                        {data.saved_items.map(item => (
                                            <div key={item.id} className="usd-saved-card">
                                                {item.item_type === 'product' && item.item && (
                                                    <>
                                                        <div className="usd-saved-image">
                                                            {item.item.image ? (
                                                                <img src={`/static/uploads/${item.item.image}`} alt={item.item.name} />
                                                            ) : (
                                                                <Package size={32} />
                                                            )}
                                                        </div>
                                                        <div className="usd-saved-info">
                                                            <span className="usd-saved-type">Product</span>
                                                            <h4>{item.item.name}</h4>
                                                            <span className="usd-saved-price">{formatCurrency((item.item.price || 0) * 100)}</span>
                                                        </div>
                                                    </>
                                                )}
                                                {item.item_type === 'post' && item.item && (
                                                    <div className="usd-saved-info">
                                                        <span className="usd-saved-type">Article</span>
                                                        <h4>{item.item.title}</h4>
                                                        <p>{item.item.excerpt}</p>
                                                    </div>
                                                )}
                                                <div className="usd-saved-actions">
                                                    <a href={item.item_type === 'product' ? `/shop/product/${item.item_id}` : `/blog/${item.item_id}`} className="usd-btn usd-btn-sm">
                                                        View <ChevronRight size={14} />
                                                    </a>
                                                    <button className="usd-btn usd-btn-sm usd-btn-danger" onClick={() => removeSavedItem(item.id)}>
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                                <div className="usd-saved-date">Saved {formatDate(item.created_at)}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Orders Tab */}
                {activeTab === 'orders' && data && (
                    <div className="usd-panel-single">
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <ShoppingBag size={20} />
                                <h3>Order History</h3>
                            </div>
                            <div className="usd-panel-body">
                                {data.orders.length === 0 ? (
                                    <div className="usd-empty">
                                        <ShoppingBag size={48} />
                                        <h4>No orders yet</h4>
                                        <p>Your order history will appear here.</p>
                                    </div>
                                ) : (
                                    <table className="usd-table">
                                        <thead>
                                            <tr>
                                                <th>Order #</th>
                                                <th>Date</th>
                                                <th>Items</th>
                                                <th>Total</th>
                                                <th>Status</th>
                                                <th></th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.orders.map(order => (
                                                <tr key={order.id}>
                                                    <td className="usd-order-id">#{order.id}</td>
                                                    <td>{formatDate(order.created_at)}</td>
                                                    <td>{order.items_count} item{order.items_count !== 1 ? 's' : ''}</td>
                                                    <td className="usd-order-total">{formatCurrency(order.total_amount)}</td>
                                                    <td><StatusBadge status={order.status} /></td>
                                                    <td>
                                                        <a href={`/my-account/orders/${order.id}`} className="usd-btn usd-btn-sm">
                                                            View <ChevronRight size={14} />
                                                        </a>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Appointments Tab */}
                {activeTab === 'appointments' && data && (
                    <div className="usd-panel-single">
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Calendar size={20} />
                                <h3>Appointments</h3>
                            </div>
                            <div className="usd-panel-body">
                                {data.appointments.length === 0 ? (
                                    <div className="usd-empty">
                                        <Calendar size={48} />
                                        <h4>No appointments</h4>
                                        <p>You don't have any appointments yet.</p>
                                    </div>
                                ) : (
                                    <div className="usd-appointments-list">
                                        {data.appointments.map(appt => (
                                            <div key={appt.id} className="usd-appointment-card">
                                                <div className="usd-apt-icon">
                                                    <Clock size={20} />
                                                </div>
                                                <div className="usd-apt-info">
                                                    <h4>{appt.service_name}</h4>
                                                    <span className="usd-apt-time">{formatDateTime(appt.preferred_date_time)}</span>
                                                    {appt.notes && <p className="usd-apt-notes">{appt.notes}</p>}
                                                </div>
                                                <StatusBadge status={appt.status} />
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Subscriptions Tab */}
                {activeTab === 'subscriptions' && data && (
                    <div className="usd-panel-single">
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <RefreshCw size={20} />
                                <h3>Subscriptions</h3>
                            </div>
                            <div className="usd-panel-body">
                                {data.subscriptions.length === 0 ? (
                                    <div className="usd-empty">
                                        <RefreshCw size={48} />
                                        <h4>No active subscriptions</h4>
                                        <p>You don't have any subscriptions yet.</p>
                                    </div>
                                ) : (
                                    <div className="usd-subscriptions-list">
                                        {data.subscriptions.map(sub => (
                                            <div key={sub.id} className="usd-subscription-card">
                                                <div className="usd-sub-icon">
                                                    <CreditCard size={20} />
                                                </div>
                                                <div className="usd-sub-info">
                                                    <h4>{sub.plan_name}</h4>
                                                    <span className="usd-sub-renew">
                                                        {sub.cancel_at_period_end ? 'Cancels' : 'Renews'} {formatDate(sub.current_period_end)}
                                                    </span>
                                                </div>
                                                <StatusBadge status={sub.status} />
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Downloads Tab */}
                {activeTab === 'downloads' && data && (
                    <div className="usd-panel-single">
                        <div className="usd-panel">
                            <div className="usd-panel-header">
                                <Download size={20} />
                                <h3>Digital Downloads</h3>
                            </div>
                            <div className="usd-panel-body">
                                {data.downloads.length === 0 ? (
                                    <div className="usd-empty">
                                        <Download size={48} />
                                        <h4>No downloads available</h4>
                                        <p>Your digital purchases will appear here.</p>
                                    </div>
                                ) : (
                                    <div className="usd-downloads-list">
                                        {data.downloads.map(dl => (
                                            <div key={dl.id} className="usd-download-card">
                                                <div className="usd-dl-icon">
                                                    <Package size={20} />
                                                </div>
                                                <div className="usd-dl-info">
                                                    <h4>{dl.product_name}</h4>
                                                    <span className="usd-dl-count">
                                                        {dl.download_count} / {dl.max_downloads} downloads used
                                                    </span>
                                                </div>
                                                {dl.is_valid ? (
                                                    <a href={dl.download_url} className="usd-btn usd-btn-primary">
                                                        <Download size={14} /> Download
                                                    </a>
                                                ) : (
                                                    <span className="usd-dl-expired">Expired</span>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    )
}

export default UnifiedUserSettingsDashboard
