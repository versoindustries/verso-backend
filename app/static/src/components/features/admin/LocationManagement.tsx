import React, { useState, useMemo, useCallback } from 'react';

interface Location {
    id: number;
    name: string;
    address: string | null;
    userCount: number;
    createdAt: string;
}

interface LocationManagementProps {
    initialLocations: Location[];
    csrfToken: string;
}

export const LocationManagement: React.FC<LocationManagementProps> = ({
    initialLocations,
    csrfToken,
}) => {
    const [locations, setLocations] = useState<Location[]>(initialLocations);
    const [searchQuery, setSearchQuery] = useState('');
    const [isSlideoutOpen, setIsSlideoutOpen] = useState(false);
    const [editingLocation, setEditingLocation] = useState<Location | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<Location | null>(null);
    const [formName, setFormName] = useState('');
    const [formAddress, setFormAddress] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

    // Computed stats
    const stats = useMemo(() => {
        const totalLocations = locations.length;
        const totalUsers = locations.reduce((sum, loc) => sum + loc.userCount, 0);
        const mostActive = locations.reduce(
            (max, loc) => (loc.userCount > (max?.userCount || 0) ? loc : max),
            null as Location | null
        );
        return { totalLocations, totalUsers, mostActive };
    }, [locations]);

    // Filtered locations
    const filteredLocations = useMemo(() => {
        if (!searchQuery.trim()) return locations;
        const query = searchQuery.toLowerCase();
        return locations.filter(
            (loc) =>
                loc.name.toLowerCase().includes(query) ||
                (loc.address && loc.address.toLowerCase().includes(query))
        );
    }, [locations, searchQuery]);

    const showToast = useCallback((message: string, type: 'success' | 'error') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    }, []);

    const openAddForm = () => {
        setEditingLocation(null);
        setFormName('');
        setFormAddress('');
        setIsSlideoutOpen(true);
    };

    const openEditForm = (location: Location) => {
        setEditingLocation(location);
        setFormName(location.name);
        setFormAddress(location.address || '');
        setIsSlideoutOpen(true);
    };

    const closeSlideout = () => {
        setIsSlideoutOpen(false);
        setEditingLocation(null);
        setFormName('');
        setFormAddress('');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formName.trim()) return;

        setIsSubmitting(true);

        try {
            const url = editingLocation
                ? `/admin/api/locations/${editingLocation.id}`
                : '/admin/api/locations';
            const method = editingLocation ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    name: formName.trim(),
                    address: formAddress.trim() || null,
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to save location');
            }

            const data = await response.json();

            if (editingLocation) {
                setLocations((prev) =>
                    prev.map((loc) => (loc.id === data.location.id ? data.location : loc))
                );
                showToast('Location updated successfully', 'success');
            } else {
                setLocations((prev) => [...prev, data.location]);
                showToast('Location created successfully', 'success');
            }

            closeSlideout();
        } catch (error) {
            showToast(error instanceof Error ? error.message : 'An error occurred', 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!deleteTarget) return;

        setIsSubmitting(true);

        try {
            const response = await fetch(`/admin/api/locations/${deleteTarget.id}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to delete location');
            }

            setLocations((prev) => prev.filter((loc) => loc.id !== deleteTarget.id));
            showToast('Location deleted successfully', 'success');
            setDeleteTarget(null);
        } catch (error) {
            showToast(error instanceof Error ? error.message : 'An error occurred', 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
            });
        } catch {
            return dateStr;
        }
    };

    return (
        <div className="location-management">
            {/* Header */}
            <header className="lm-header">
                <div className="lm-header-content">
                    <h1 className="lm-title">
                        <i className="fas fa-map-marker-alt"></i>
                        Location Management
                    </h1>
                    <p className="lm-subtitle">
                        Manage your business locations and track user assignments
                    </p>
                </div>
                <div className="lm-actions">
                    <button className="lm-btn-add" onClick={openAddForm}>
                        <i className="fas fa-plus"></i>
                        Add Location
                    </button>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="lm-stats">
                <div className="lm-stat-card">
                    <div className="lm-stat-icon">
                        <i className="fas fa-building"></i>
                    </div>
                    <div className="lm-stat-value">{stats.totalLocations}</div>
                    <div className="lm-stat-label">Total Locations</div>
                </div>
                <div className="lm-stat-card">
                    <div className="lm-stat-icon">
                        <i className="fas fa-users"></i>
                    </div>
                    <div className="lm-stat-value">{stats.totalUsers}</div>
                    <div className="lm-stat-label">Total Users</div>
                </div>
                <div className="lm-stat-card">
                    <div className="lm-stat-icon">
                        <i className="fas fa-star"></i>
                    </div>
                    <div className="lm-stat-value">
                        {stats.mostActive?.name || 'N/A'}
                    </div>
                    <div className="lm-stat-label">Most Active Location</div>
                </div>
            </div>

            {/* Search Bar */}
            <div className="lm-search-bar">
                <div className="lm-search-input">
                    <i className="fas fa-search"></i>
                    <input
                        type="text"
                        placeholder="Search locations by name or address..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* Location Cards Grid */}
            {filteredLocations.length > 0 ? (
                <div className="lm-grid">
                    {filteredLocations.map((location, index) => (
                        <div
                            className="lm-card"
                            key={location.id}
                            style={{ animationDelay: `${index * 0.05}s` }}
                        >
                            <div className="lm-card-header">
                                <div className="lm-card-icon">
                                    <i className="fas fa-map-marker-alt"></i>
                                </div>
                                <div className="lm-card-actions">
                                    <button
                                        className="lm-card-btn"
                                        onClick={() => openEditForm(location)}
                                        title="Edit location"
                                    >
                                        <i className="fas fa-edit"></i>
                                    </button>
                                    <button
                                        className="lm-card-btn delete"
                                        onClick={() => setDeleteTarget(location)}
                                        title="Delete location"
                                    >
                                        <i className="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                            <div className="lm-card-body">
                                <h3 className="lm-card-name">{location.name}</h3>
                                <p className="lm-card-address">
                                    <i className="fas fa-location-dot"></i>
                                    {location.address || 'No address specified'}
                                </p>
                            </div>
                            <div className="lm-card-footer">
                                <span className="lm-card-users">
                                    <i className="fas fa-user"></i>
                                    {location.userCount} {location.userCount === 1 ? 'user' : 'users'}
                                </span>
                                <span className="lm-card-date">
                                    Created {formatDate(location.createdAt)}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="lm-empty">
                    <div className="lm-empty-icon">
                        <i className="fas fa-map-marker-alt"></i>
                    </div>
                    {searchQuery ? (
                        <>
                            <h3>No locations found</h3>
                            <p>Try adjusting your search query</p>
                        </>
                    ) : (
                        <>
                            <h3>No locations yet</h3>
                            <p>Add your first location to get started</p>
                        </>
                    )}
                </div>
            )}

            {/* Add/Edit Slideout */}
            <div className={`lm-slideout-overlay ${isSlideoutOpen ? 'open' : ''}`}>
                <div className="lm-slideout">
                    <div className="lm-slideout-header">
                        <h2 className="lm-slideout-title">
                            <i className="fas fa-map-marker-alt"></i>
                            {editingLocation ? 'Edit Location' : 'Add New Location'}
                        </h2>
                        <button className="lm-slideout-close" onClick={closeSlideout}>
                            <i className="fas fa-times"></i>
                        </button>
                    </div>
                    <form onSubmit={handleSubmit}>
                        <div className="lm-slideout-body">
                            <div className="lm-form-group">
                                <label className="lm-form-label">Location Name *</label>
                                <input
                                    type="text"
                                    className="lm-form-input"
                                    placeholder="Enter location name"
                                    value={formName}
                                    onChange={(e) => setFormName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="lm-form-group">
                                <label className="lm-form-label">Address</label>
                                <input
                                    type="text"
                                    className="lm-form-input"
                                    placeholder="Enter street address"
                                    value={formAddress}
                                    onChange={(e) => setFormAddress(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="lm-slideout-footer">
                            <button
                                type="button"
                                className="lm-btn-cancel"
                                onClick={closeSlideout}
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="lm-btn-save"
                                disabled={isSubmitting || !formName.trim()}
                            >
                                {isSubmitting ? 'Saving...' : editingLocation ? 'Update' : 'Create'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            <div className={`lm-modal-overlay ${deleteTarget ? 'open' : ''}`}>
                <div className="lm-modal">
                    <div className="lm-modal-header">
                        <h3 className="lm-modal-title">
                            <i className="fas fa-exclamation-triangle"></i>
                            Delete Location
                        </h3>
                    </div>
                    <div className="lm-modal-body">
                        <p>
                            Are you sure you want to delete <strong>{deleteTarget?.name}</strong>?
                            This action cannot be undone.
                        </p>
                    </div>
                    <div className="lm-modal-footer">
                        <button
                            className="lm-btn-cancel"
                            onClick={() => setDeleteTarget(null)}
                            disabled={isSubmitting}
                        >
                            Cancel
                        </button>
                        <button
                            className="lm-btn-delete"
                            onClick={handleDelete}
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Deleting...' : 'Delete'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Toast Notification */}
            {toast && (
                <div className={`lm-toast ${toast.type}`}>
                    <i className={`fas fa-${toast.type === 'success' ? 'check-circle' : 'exclamation-circle'}`}></i>
                    {toast.message}
                </div>
            )}
        </div>
    );
};

export default LocationManagement;
