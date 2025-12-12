/**
 * UserManagement Component
 * 
 * Unified enterprise dashboard for user and role management.
 * Features tabbed interface, user profile slideout, location assignment, and inline role assignment.
 */

import { useState, useCallback, useEffect } from 'react'
import {
    Users,
    Shield,
    Search,
    Plus,
    Edit2,
    Trash2,
    X,
    Check,
    Mail,
    Phone,
    Calendar,
    ChevronRight,
    AlertCircle,
    MapPin
} from 'lucide-react'
import api from '../../../api'

// =============================================================================
// Types
// =============================================================================

interface Role {
    id: number
    name: string
}

interface Location {
    id: number
    name: string
    address: string
    user_count: number
    is_primary: boolean
}

interface User {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    phone: string
    roles: Role[]
    role_names: string
    location_id: number | null
    location_name: string
    last_login: string
    is_active: boolean
}

interface RoleWithUsers extends Role {
    user_count: number
    users: { id: number; username: string }[]
}

interface UserManagementProps {
    initialUsers: User[]
    initialRoles: RoleWithUsers[]
    initialLocations: Location[]
    isOwner: boolean
    csrfToken: string
}

type TabType = 'users' | 'roles'

// =============================================================================
// Main Component
// =============================================================================

export default function UserManagement({
    initialUsers,
    initialRoles,
    initialLocations,
    isOwner,
    csrfToken: _csrfToken
}: UserManagementProps) {
    // csrfToken available via _csrfToken if needed for future API calls
    const [activeTab, setActiveTab] = useState<TabType>('users')
    const [users, setUsers] = useState<User[]>(initialUsers)
    const [roles, setRoles] = useState<RoleWithUsers[]>(initialRoles)
    const [locations] = useState<Location[]>(initialLocations)
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedUser, setSelectedUser] = useState<User | null>(null)
    const [isSlideoutOpen, setIsSlideoutOpen] = useState(false)
    const [isSaving, setIsSaving] = useState(false)
    const [newRoleName, setNewRoleName] = useState('')
    const [isCreatingRole, setIsCreatingRole] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Filter users based on search
    const filteredUsers = users.filter(user => {
        const query = searchQuery.toLowerCase()
        return (
            user.username.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query) ||
            user.first_name.toLowerCase().includes(query) ||
            user.last_name.toLowerCase().includes(query) ||
            user.role_names.toLowerCase().includes(query)
        )
    })

    // Filter roles based on search
    const filteredRoles = roles.filter(role =>
        role.name.toLowerCase().includes(searchQuery.toLowerCase())
    )

    // Open user profile slideout
    const openUserProfile = useCallback(async (user: User) => {
        try {
            const response = await api.get(`/admin/api/user/${user.id}`)
            setSelectedUser({ ...user, ...response.data })
            setIsSlideoutOpen(true)
            setError(null)
        } catch {
            setError('Failed to load user details')
        }
    }, [])

    // Close slideout
    const closeSlideout = useCallback(() => {
        setIsSlideoutOpen(false)
        setTimeout(() => setSelectedUser(null), 300)
    }, [])

    // Toggle role for selected user
    const toggleUserRole = useCallback(async (roleId: number) => {
        if (!selectedUser || isSaving) return

        const currentRoleIds = selectedUser.roles.map(r => r.id)
        const newRoleIds = currentRoleIds.includes(roleId)
            ? currentRoleIds.filter(id => id !== roleId)
            : [...currentRoleIds, roleId]

        setIsSaving(true)
        try {
            const response = await api.put(`/admin/api/user/${selectedUser.id}/roles`, {
                role_ids: newRoleIds
            })

            if (response.data.success) {
                // Update selected user
                const updatedRoles = response.data.roles
                setSelectedUser(prev => prev ? {
                    ...prev,
                    roles: updatedRoles,
                    role_names: updatedRoles.map((r: Role) => r.name).join(', ') || 'No roles'
                } : null)

                // Update users list
                setUsers(prev => prev.map(u =>
                    u.id === selectedUser.id
                        ? { ...u, roles: updatedRoles, role_names: updatedRoles.map((r: Role) => r.name).join(', ') || 'No roles' }
                        : u
                ))

                // Update role user counts
                setRoles(prev => prev.map(role => ({
                    ...role,
                    user_count: role.user_count + (
                        newRoleIds.includes(role.id) && !currentRoleIds.includes(role.id) ? 1 :
                            !newRoleIds.includes(role.id) && currentRoleIds.includes(role.id) ? -1 : 0
                    )
                })))
            }
        } catch {
            setError('Failed to update roles')
        } finally {
            setIsSaving(false)
        }
    }, [selectedUser, isSaving])

    // Update user location
    const updateUserLocation = useCallback(async (locationId: number | null) => {
        if (!selectedUser || isSaving) return

        setIsSaving(true)
        try {
            const response = await api.put(`/admin/api/user/${selectedUser.id}/location`, {
                location_id: locationId
            })

            if (response.data.success) {
                const newLocationId = response.data.location_id
                const newLocationName = response.data.location_name

                // Update selected user
                setSelectedUser(prev => prev ? {
                    ...prev,
                    location_id: newLocationId,
                    location_name: newLocationName
                } : null)

                // Update users list
                setUsers(prev => prev.map(u =>
                    u.id === selectedUser.id
                        ? { ...u, location_id: newLocationId, location_name: newLocationName }
                        : u
                ))
            }
        } catch {
            setError('Failed to update location')
        } finally {
            setIsSaving(false)
        }
    }, [selectedUser, isSaving])

    // Create new role
    const createRole = useCallback(async () => {
        if (!newRoleName.trim() || isCreatingRole) return

        setIsCreatingRole(true)
        try {
            const response = await api.post('/admin/api/role', { name: newRoleName.trim() })
            if (response.data.success) {
                setRoles(prev => [...prev, { ...response.data.role, users: [] }])
                setNewRoleName('')
            } else {
                setError(response.data.error || 'Failed to create role')
            }
        } catch {
            setError('Failed to create role')
        } finally {
            setIsCreatingRole(false)
        }
    }, [newRoleName, isCreatingRole])

    // Delete role
    const deleteRole = useCallback(async (roleId: number) => {
        const role = roles.find(r => r.id === roleId)
        if (!role) return

        if (role.user_count > 0) {
            setError(`Cannot delete role - ${role.user_count} user(s) assigned`)
            return
        }

        if (!confirm(`Delete role "${role.name}"?`)) return

        try {
            const response = await api.delete(`/admin/api/role/${roleId}`)
            if (response.data.success) {
                setRoles(prev => prev.filter(r => r.id !== roleId))
            } else {
                setError(response.data.error || 'Failed to delete role')
            }
        } catch {
            setError('Failed to delete role')
        }
    }, [roles])

    // Clear error after 5 seconds
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(null), 5000)
            return () => clearTimeout(timer)
        }
    }, [error])

    // Get user initials for avatar
    const getUserInitials = (user: User) => {
        if (user.first_name && user.last_name) {
            return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
        }
        return user.username.substring(0, 2).toUpperCase()
    }

    return (
        <div className="user-management">
            {/* Error Toast */}
            {error && (
                <div className="um-toast um-toast--error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                    <button onClick={() => setError(null)} className="um-toast-close">
                        <X size={16} />
                    </button>
                </div>
            )}

            {/* Header */}
            <header className="um-header">
                <div className="um-header-content">
                    <h1 className="um-title">
                        <Users className="um-title-icon" />
                        User Management
                    </h1>
                    <p className="um-subtitle">Manage users and roles in one place</p>
                </div>
                <a href="/admin/user/new" className="um-btn um-btn--primary">
                    <Plus size={18} />
                    <span>Create User</span>
                </a>
            </header>

            {/* Tabs */}
            <div className="um-tabs">
                <button
                    className={`um-tab ${activeTab === 'users' ? 'um-tab--active' : ''}`}
                    onClick={() => setActiveTab('users')}
                >
                    <Users size={18} />
                    <span>Users</span>
                    <span className="um-tab-badge">{users.length}</span>
                </button>
                <button
                    className={`um-tab ${activeTab === 'roles' ? 'um-tab--active' : ''}`}
                    onClick={() => setActiveTab('roles')}
                >
                    <Shield size={18} />
                    <span>Roles</span>
                    <span className="um-tab-badge">{roles.length}</span>
                </button>
            </div>

            {/* Search Bar */}
            <div className="um-search">
                <Search className="um-search-icon" size={18} />
                <input
                    type="text"
                    placeholder={activeTab === 'users' ? 'Search users...' : 'Search roles...'}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="um-search-input"
                />
                {searchQuery && (
                    <button onClick={() => setSearchQuery('')} className="um-search-clear">
                        <X size={16} />
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="um-content">
                {activeTab === 'users' ? (
                    <div className="um-users-grid">
                        {filteredUsers.length === 0 ? (
                            <div className="um-empty">
                                <Users size={48} />
                                <p>No users found</p>
                            </div>
                        ) : (
                            filteredUsers.map(user => (
                                <div
                                    key={user.id}
                                    className="um-user-card"
                                    onClick={() => openUserProfile(user)}
                                >
                                    <div className="um-user-avatar">
                                        {getUserInitials(user)}
                                    </div>
                                    <div className="um-user-info">
                                        <h3 className="um-user-name">
                                            {user.first_name && user.last_name
                                                ? `${user.first_name} ${user.last_name}`
                                                : user.username}
                                        </h3>
                                        <p className="um-user-email">{user.email}</p>
                                        <div className="um-user-roles">
                                            {user.roles.slice(0, 3).map(role => (
                                                <span key={role.id} className="um-role-chip">
                                                    {role.name}
                                                </span>
                                            ))}
                                            {user.roles.length > 3 && (
                                                <span className="um-role-chip um-role-chip--more">
                                                    +{user.roles.length - 3}
                                                </span>
                                            )}
                                        </div>
                                        {user.location_name && user.location_name !== 'No location' && (
                                            <div className="um-user-location">
                                                <MapPin size={12} />
                                                <span>{user.location_name}</span>
                                            </div>
                                        )}
                                    </div>
                                    <ChevronRight className="um-user-arrow" size={20} />
                                </div>
                            ))
                        )}
                    </div>
                ) : (
                    <div className="um-roles-section">
                        {/* Create Role Form */}
                        <div className="um-create-role">
                            <input
                                type="text"
                                placeholder="New role name..."
                                value={newRoleName}
                                onChange={(e) => setNewRoleName(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && createRole()}
                                className="um-create-role-input"
                            />
                            <button
                                onClick={createRole}
                                disabled={!newRoleName.trim() || isCreatingRole}
                                className="um-btn um-btn--primary"
                            >
                                {isCreatingRole ? 'Creating...' : 'Create Role'}
                            </button>
                        </div>

                        {/* Roles List */}
                        <div className="um-roles-grid">
                            {filteredRoles.length === 0 ? (
                                <div className="um-empty">
                                    <Shield size={48} />
                                    <p>No roles found</p>
                                </div>
                            ) : (
                                filteredRoles.map(role => (
                                    <div key={role.id} className="um-role-card">
                                        <div className="um-role-header">
                                            <Shield className="um-role-icon" size={24} />
                                            <div className="um-role-info">
                                                <h3 className="um-role-name">{role.name}</h3>
                                                <p className="um-role-count">
                                                    {role.user_count} {role.user_count === 1 ? 'user' : 'users'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="um-role-actions">
                                            <a
                                                href={`/admin/role/${role.id}/edit`}
                                                className="um-action-btn"
                                                title="Edit Role"
                                            >
                                                <Edit2 size={16} />
                                            </a>
                                            <button
                                                onClick={() => deleteRole(role.id)}
                                                className="um-action-btn um-action-btn--danger"
                                                title={role.user_count > 0 ? 'Cannot delete - has users' : 'Delete Role'}
                                                disabled={role.user_count > 0}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* User Profile Slideout */}
            <div className={`um-slideout-overlay ${isSlideoutOpen ? 'um-slideout-overlay--open' : ''}`} onClick={closeSlideout} />
            <div className={`um-slideout ${isSlideoutOpen ? 'um-slideout--open' : ''}`}>
                {selectedUser && (
                    <>
                        <div className="um-slideout-header">
                            <h2>User Profile</h2>
                            <button onClick={closeSlideout} className="um-slideout-close">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="um-slideout-content">
                            {/* User Avatar & Name */}
                            <div className="um-profile-header">
                                <div className="um-profile-avatar">
                                    {getUserInitials(selectedUser)}
                                </div>
                                <div className="um-profile-identity">
                                    <h3 className="um-profile-name">
                                        {selectedUser.first_name && selectedUser.last_name
                                            ? `${selectedUser.first_name} ${selectedUser.last_name}`
                                            : selectedUser.username}
                                    </h3>
                                    <p className="um-profile-username">@{selectedUser.username}</p>
                                </div>
                            </div>

                            {/* Contact Info */}
                            <div className="um-profile-section">
                                <h4 className="um-profile-section-title">Contact Info</h4>
                                <div className="um-profile-field">
                                    <Mail size={16} />
                                    <span>{selectedUser.email}</span>
                                </div>
                                {selectedUser.phone && (
                                    <div className="um-profile-field">
                                        <Phone size={16} />
                                        <span>{selectedUser.phone}</span>
                                    </div>
                                )}
                                <div className="um-profile-field">
                                    <Calendar size={16} />
                                    <span>Last login: {selectedUser.last_login || 'Never'}</span>
                                </div>
                            </div>

                            {/* Location Assignment - Owner/Admin only */}
                            {isOwner && locations.length > 0 && (
                                <div className="um-profile-section">
                                    <h4 className="um-profile-section-title">
                                        <MapPin size={16} />
                                        Location Assignment
                                    </h4>
                                    <select
                                        className="um-location-select"
                                        value={selectedUser.location_id || ''}
                                        onChange={(e) => updateUserLocation(e.target.value ? parseInt(e.target.value) : null)}
                                        disabled={isSaving}
                                    >
                                        <option value="">No location assigned</option>
                                        {locations.map(loc => (
                                            <option key={loc.id} value={loc.id}>
                                                {loc.name} {loc.is_primary && '(Primary)'}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {/* Role Assignment */}
                            <div className="um-profile-section">
                                <h4 className="um-profile-section-title">Assigned Roles</h4>
                                <div className="um-roles-checkboxes">
                                    {roles.map(role => {
                                        const isAssigned = selectedUser.roles.some(r => r.id === role.id)
                                        return (
                                            <label
                                                key={role.id}
                                                className={`um-role-checkbox ${isAssigned ? 'um-role-checkbox--checked' : ''}`}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={isAssigned}
                                                    onChange={() => toggleUserRole(role.id)}
                                                    disabled={isSaving}
                                                />
                                                <span className="um-role-checkbox-box">
                                                    {isAssigned && <Check size={14} />}
                                                </span>
                                                <span className="um-role-checkbox-label">{role.name}</span>
                                            </label>
                                        )
                                    })}
                                </div>
                                {isSaving && <p className="um-saving-indicator">Saving...</p>}
                            </div>

                            {/* Actions */}
                            <div className="um-profile-actions">
                                <a
                                    href={`/admin/user/${selectedUser.id}/edit`}
                                    className="um-btn um-btn--secondary"
                                >
                                    <Edit2 size={16} />
                                    <span>Edit User</span>
                                </a>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
