/**
 * DataManagement Component
 * 
 * Enterprise-grade data management dashboard with tabbed interface,
 * refined proportions, and world-class UX matching other admin components.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
    Database, Download, Upload, Shield, Clock,
    HardDrive, Users, Calendar, ShoppingCart, FileText,
    AlertTriangle, Check, X, RefreshCw, Activity
} from 'lucide-react'
import { useToast } from '../../ui/toast'
import { Tabs } from '../../ui/tabs'
import { Card } from '../../ui/card'
import { Button } from '../../ui/button'
import { Input } from '../../ui/input'
import { Badge } from '../../ui/badge'
import { Spinner } from '../../ui/spinner'
import { Modal, useModal } from '../../ui/modal'

interface DataManagementProps {
    csrfToken: string
    backupUrl: string
    importUrl: string
    gdprExportUrl: string
    statsUrl?: string
}

interface DatabaseStats {
    totalUsers: number
    totalAppointments: number
    totalOrders: number
    totalProducts: number
    lastBackup: string | null
    databaseSize: string
}

interface RecentActivity {
    id: number
    action: string
    timestamp: string
    details: string
}

export default function DataManagement({
    csrfToken,
    backupUrl,
    importUrl,
    gdprExportUrl,
    statsUrl
}: DataManagementProps) {
    const toast = useToast()
    const [stats, setStats] = useState<DatabaseStats | null>(null)
    const [activities, setActivities] = useState<RecentActivity[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [isDownloading, setIsDownloading] = useState(false)
    const [isImporting, setIsImporting] = useState(false)
    const [isExporting, setIsExporting] = useState(false)
    const [gdprEmail, setGdprEmail] = useState('')
    const [dragActive, setDragActive] = useState(false)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const { isOpen: showImportModal, openModal, closeModal } = useModal()
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Fetch database stats on mount
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch(statsUrl || '/admin/api/data-stats')
                if (response.ok) {
                    const data = await response.json()
                    setStats(data.stats)
                    setActivities(data.activities || [])
                }
            } catch (err) {
                console.error('Failed to fetch stats:', err)
            } finally {
                setIsLoading(false)
            }
        }
        fetchStats()
    }, [statsUrl])

    // Handle backup download
    const handleBackup = useCallback(async () => {
        setIsDownloading(true)
        try {
            window.location.href = backupUrl
            toast.success('Your backup download will begin shortly.')
        } catch {
            toast.error('Could not create backup. Please try again.')
        } finally {
            setTimeout(() => setIsDownloading(false), 2000)
        }
    }, [backupUrl, toast])

    // Handle drag events
    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }, [])

    // Handle drop
    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0]
            if (file.name.endsWith('.zip')) {
                setSelectedFile(file)
            } else {
                toast.error('Please upload a .zip backup file.')
            }
        }
    }, [toast])

    // Handle file select
    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0]
            if (file.name.endsWith('.zip')) {
                setSelectedFile(file)
            } else {
                toast.error('Please upload a .zip backup file.')
            }
        }
    }, [toast])

    // Handle import confirmation
    const handleImport = useCallback(async () => {
        if (!selectedFile) return

        setIsImporting(true)
        closeModal()

        const formData = new FormData()
        formData.append('backup_file', selectedFile)
        formData.append('csrf_token', csrfToken)

        try {
            const response = await fetch(importUrl, {
                method: 'POST',
                body: formData
            })

            if (response.ok || response.redirected) {
                toast.success('Data has been restored from backup.')
                setTimeout(() => window.location.reload(), 2000)
            } else {
                throw new Error('Import failed')
            }
        } catch {
            toast.error('Could not restore data. Please check the file and try again.')
        } finally {
            setIsImporting(false)
            setSelectedFile(null)
        }
    }, [selectedFile, csrfToken, importUrl, toast, closeModal])

    // Handle GDPR export
    const handleGdprExport = useCallback(async (e: React.FormEvent) => {
        e.preventDefault()
        if (!gdprEmail) return

        setIsExporting(true)

        const formData = new FormData()
        formData.append('email', gdprEmail)
        formData.append('csrf_token', csrfToken)

        try {
            const response = await fetch(gdprExportUrl, {
                method: 'POST',
                body: formData
            })

            if (response.ok) {
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `gdpr_export_${gdprEmail}.json`
                document.body.appendChild(a)
                a.click()
                window.URL.revokeObjectURL(url)
                a.remove()

                toast.success(`Personal data for ${gdprEmail} has been exported.`)
                setGdprEmail('')
            } else {
                throw new Error('Export failed')
            }
        } catch {
            toast.error('Could not export user data. Please verify the email and try again.')
        } finally {
            setIsExporting(false)
        }
    }, [gdprEmail, csrfToken, gdprExportUrl, toast])

    // Build tabs with content
    const tabs = [
        {
            id: 'overview',
            label: 'Overview',
            icon: <Database size={16} />,
            content: <OverviewPanel activities={activities} />
        },
        {
            id: 'backup',
            label: 'Backup & Export',
            icon: <Download size={16} />,
            content: (
                <BackupPanel
                    isDownloading={isDownloading}
                    onBackup={handleBackup}
                    lastBackup={stats?.lastBackup}
                />
            )
        },
        {
            id: 'import',
            label: 'Import & Restore',
            icon: <Upload size={16} />,
            content: (
                <ImportPanel
                    dragActive={dragActive}
                    selectedFile={selectedFile}
                    isImporting={isImporting}
                    onDrag={handleDrag}
                    onDrop={handleDrop}
                    onFileSelect={handleFileSelect}
                    onClearFile={() => setSelectedFile(null)}
                    onImport={openModal}
                    fileInputRef={fileInputRef}
                />
            )
        },
        {
            id: 'gdpr',
            label: 'GDPR Compliance',
            icon: <Shield size={16} />,
            content: (
                <GdprPanel
                    email={gdprEmail}
                    setEmail={setGdprEmail}
                    isExporting={isExporting}
                    onExport={handleGdprExport}
                />
            )
        },
    ]

    return (
        <div className="data-mgmt">
            {/* Header */}
            <div className="data-mgmt__header">
                <div className="data-mgmt__header-content">
                    <h1 className="data-mgmt__title">Data Management</h1>
                    <p className="data-mgmt__subtitle">
                        Backup, restore, and manage system data with enterprise-grade security
                    </p>
                </div>
                <div className="data-mgmt__header-actions">
                    <Button
                        variant={isDownloading ? 'secondary' : 'primary'}
                        onClick={handleBackup}
                        disabled={isDownloading}
                    >
                        {isDownloading ? <Spinner size="sm" /> : <Download size={16} />}
                        {isDownloading ? 'Preparing...' : 'Quick Backup'}
                    </Button>
                </div>
            </div>

            {/* Stats Row */}
            <div className="data-mgmt__stats">
                <Card className="data-mgmt__stat-card">
                    <div className="data-mgmt__stat-icon data-mgmt__stat-icon--users">
                        <Users size={18} />
                    </div>
                    <div className="data-mgmt__stat-content">
                        <span className="data-mgmt__stat-value">
                            {isLoading ? '—' : stats?.totalUsers || 0}
                        </span>
                        <span className="data-mgmt__stat-label">Users</span>
                    </div>
                </Card>
                <Card className="data-mgmt__stat-card">
                    <div className="data-mgmt__stat-icon data-mgmt__stat-icon--calendar">
                        <Calendar size={18} />
                    </div>
                    <div className="data-mgmt__stat-content">
                        <span className="data-mgmt__stat-value">
                            {isLoading ? '—' : stats?.totalAppointments || 0}
                        </span>
                        <span className="data-mgmt__stat-label">Appointments</span>
                    </div>
                </Card>
                <Card className="data-mgmt__stat-card">
                    <div className="data-mgmt__stat-icon data-mgmt__stat-icon--orders">
                        <ShoppingCart size={18} />
                    </div>
                    <div className="data-mgmt__stat-content">
                        <span className="data-mgmt__stat-value">
                            {isLoading ? '—' : stats?.totalOrders || 0}
                        </span>
                        <span className="data-mgmt__stat-label">Orders</span>
                    </div>
                </Card>
                <Card className="data-mgmt__stat-card">
                    <div className="data-mgmt__stat-icon data-mgmt__stat-icon--storage">
                        <HardDrive size={18} />
                    </div>
                    <div className="data-mgmt__stat-content">
                        <span className="data-mgmt__stat-value">
                            {isLoading ? '—' : stats?.databaseSize || 'N/A'}
                        </span>
                        <span className="data-mgmt__stat-label">Database</span>
                    </div>
                </Card>
                {stats?.lastBackup && (
                    <Card className="data-mgmt__stat-card">
                        <div className="data-mgmt__stat-icon data-mgmt__stat-icon--backup">
                            <Clock size={18} />
                        </div>
                        <div className="data-mgmt__stat-content">
                            <span className="data-mgmt__stat-value data-mgmt__stat-value--small">
                                {stats.lastBackup}
                            </span>
                            <span className="data-mgmt__stat-label">Last Backup</span>
                        </div>
                    </Card>
                )}
            </div>

            {/* Tabbed Content */}
            <div className="data-mgmt__tabs-wrapper">
                <Tabs
                    tabs={tabs}
                    className="data-mgmt__tabs"
                />
            </div>

            {/* Import Confirmation Modal */}
            <Modal
                open={showImportModal}
                onClose={closeModal}
                title="Confirm Data Import"
            >
                <div className="data-mgmt__modal-content">
                    <div className="data-mgmt__modal-warning">
                        <AlertTriangle size={20} />
                        <div>
                            <strong>Warning</strong>
                            <p>This will import data from <code>{selectedFile?.name}</code></p>
                        </div>
                    </div>
                    <ul className="data-mgmt__modal-list">
                        <li>Existing records with matching IDs may be overwritten</li>
                        <li>System settings and configurations may be modified</li>
                        <li>This action cannot be easily undone</li>
                    </ul>
                    <div className="data-mgmt__modal-actions">
                        <Button variant="secondary" onClick={closeModal}>
                            Cancel
                        </Button>
                        <Button
                            className="data-mgmt__btn-danger"
                            onClick={handleImport}
                        >
                            <Check size={16} /> Confirm Import
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    )
}

// =============================================================================
// Sub-Panels
// =============================================================================

function OverviewPanel({ activities }: { activities: RecentActivity[] }) {
    return (
        <div className="data-mgmt__overview">
            <div className="data-mgmt__overview-grid">
                {/* Quick Actions */}
                <Card className="data-mgmt__card">
                    <h3 className="data-mgmt__card-title">
                        <Database size={18} /> Quick Actions
                    </h3>
                    <div className="data-mgmt__quick-actions">
                        <a href="/admin/backup/download" className="data-mgmt__action-item">
                            <Download size={16} />
                            <span>Download Full Backup</span>
                        </a>
                        <button
                            className="data-mgmt__action-item"
                            onClick={() => {
                                const importTab = document.querySelector('[id="tab-import"]') as HTMLButtonElement
                                importTab?.click()
                            }}
                        >
                            <Upload size={16} />
                            <span>Import Data</span>
                        </button>
                        <button
                            className="data-mgmt__action-item"
                            onClick={() => {
                                const gdprTab = document.querySelector('[id="tab-gdpr"]') as HTMLButtonElement
                                gdprTab?.click()
                            }}
                        >
                            <Shield size={16} />
                            <span>GDPR Export</span>
                        </button>
                    </div>
                </Card>

                {/* System Status */}
                <Card className="data-mgmt__card">
                    <h3 className="data-mgmt__card-title">
                        <Activity size={18} /> System Status
                    </h3>
                    <div className="data-mgmt__status-list">
                        <div className="data-mgmt__status-item">
                            <span className="data-mgmt__status-dot data-mgmt__status-dot--success" />
                            <span>Database connection healthy</span>
                        </div>
                        <div className="data-mgmt__status-item">
                            <span className="data-mgmt__status-dot data-mgmt__status-dot--success" />
                            <span>Backup system operational</span>
                        </div>
                        <div className="data-mgmt__status-item">
                            <span className="data-mgmt__status-dot data-mgmt__status-dot--success" />
                            <span>GDPR compliance tools ready</span>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Recent Activity */}
            {activities.length > 0 && (
                <Card className="data-mgmt__card data-mgmt__card--full">
                    <h3 className="data-mgmt__card-title">
                        <RefreshCw size={18} /> Recent Activity
                    </h3>
                    <div className="data-mgmt__activity-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Action</th>
                                    <th>Details</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {activities.map((activity) => (
                                    <tr key={activity.id}>
                                        <td>
                                            <Badge variant="secondary">{activity.action}</Badge>
                                        </td>
                                        <td>{activity.details || '—'}</td>
                                        <td className="data-mgmt__activity-time">{activity.timestamp}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}
        </div>
    )
}

function BackupPanel({
    isDownloading,
    onBackup,
    lastBackup
}: {
    isDownloading: boolean
    onBackup: () => void
    lastBackup?: string | null
}) {
    return (
        <div className="data-mgmt__section">
            <Card className="data-mgmt__card data-mgmt__card--lg">
                <div className="data-mgmt__section-header">
                    <Download size={20} />
                    <div>
                        <h3>Full System Backup</h3>
                        <p>Download a complete backup of your database</p>
                    </div>
                </div>

                <div className="data-mgmt__section-body">
                    <div className="data-mgmt__info-box">
                        <FileText size={16} />
                        <div>
                            <strong>What's included:</strong>
                            <ul>
                                <li>All users, roles, and permissions</li>
                                <li>Appointments and booking data</li>
                                <li>Orders and transaction history</li>
                                <li>Content pages and blog posts</li>
                                <li>System settings and configurations</li>
                            </ul>
                        </div>
                    </div>

                    {lastBackup && (
                        <div className="data-mgmt__last-backup">
                            <Clock size={14} />
                            <span>Last backup: <strong>{lastBackup}</strong></span>
                        </div>
                    )}

                    <Button
                        size="lg"
                        onClick={onBackup}
                        disabled={isDownloading}
                        className="data-mgmt__backup-btn"
                    >
                        {isDownloading ? (
                            <><Spinner size="sm" /> Preparing Download...</>
                        ) : (
                            <><Download size={18} /> Download Full Backup</>
                        )}
                    </Button>
                </div>
            </Card>
        </div>
    )
}

function ImportPanel({
    dragActive,
    selectedFile,
    isImporting,
    onDrag,
    onDrop,
    onFileSelect,
    onClearFile,
    onImport,
    fileInputRef
}: {
    dragActive: boolean
    selectedFile: File | null
    isImporting: boolean
    onDrag: (e: React.DragEvent) => void
    onDrop: (e: React.DragEvent) => void
    onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
    onClearFile: () => void
    onImport: () => void
    fileInputRef: React.RefObject<HTMLInputElement>
}) {
    return (
        <div className="data-mgmt__section">
            <Card className="data-mgmt__card data-mgmt__card--lg">
                <div className="data-mgmt__section-header">
                    <Upload size={20} />
                    <div>
                        <h3>Import & Restore Data</h3>
                        <p>Restore from a previous backup file</p>
                    </div>
                </div>

                <div className="data-mgmt__section-body">
                    <div className="data-mgmt__warning-box">
                        <AlertTriangle size={16} />
                        <div>
                            <strong>Caution:</strong> Importing data may overwrite existing records
                            if they share the same IDs. Always create a backup before importing.
                        </div>
                    </div>

                    <div
                        className={`data-mgmt__dropzone ${dragActive ? 'data-mgmt__dropzone--active' : ''} ${selectedFile ? 'data-mgmt__dropzone--has-file' : ''}`}
                        onDragEnter={onDrag}
                        onDragLeave={onDrag}
                        onDragOver={onDrag}
                        onDrop={onDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".zip"
                            onChange={onFileSelect}
                            style={{ display: 'none' }}
                        />
                        {selectedFile ? (
                            <div className="data-mgmt__dropzone-file">
                                <FileText size={24} />
                                <div className="data-mgmt__dropzone-file-info">
                                    <span className="data-mgmt__dropzone-filename">{selectedFile.name}</span>
                                    <span className="data-mgmt__dropzone-size">
                                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                    </span>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => { e.stopPropagation(); onClearFile(); }}
                                >
                                    <X size={16} />
                                </Button>
                            </div>
                        ) : (
                            <>
                                <Upload size={32} className="data-mgmt__dropzone-icon" />
                                <p className="data-mgmt__dropzone-text">
                                    Drag & drop your backup file here, or <span>browse</span>
                                </p>
                                <p className="data-mgmt__dropzone-hint">Accepts .zip files only</p>
                            </>
                        )}
                    </div>

                    <Button
                        size="lg"
                        className="data-mgmt__btn-danger data-mgmt__import-btn"
                        onClick={onImport}
                        disabled={!selectedFile || isImporting}
                    >
                        {isImporting ? (
                            <><Spinner size="sm" /> Importing...</>
                        ) : (
                            <><Upload size={18} /> Import Data</>
                        )}
                    </Button>
                </div>
            </Card>
        </div>
    )
}

function GdprPanel({
    email,
    setEmail,
    isExporting,
    onExport
}: {
    email: string
    setEmail: (email: string) => void
    isExporting: boolean
    onExport: (e: React.FormEvent) => void
}) {
    return (
        <div className="data-mgmt__section">
            <Card className="data-mgmt__card data-mgmt__card--lg">
                <div className="data-mgmt__section-header">
                    <Shield size={20} />
                    <div>
                        <h3>GDPR Personal Data Export</h3>
                        <p>Export all personal data for a specific user</p>
                    </div>
                </div>

                <div className="data-mgmt__section-body">
                    <div className="data-mgmt__info-box">
                        <FileText size={16} />
                        <div>
                            <strong>Export includes:</strong>
                            <ul>
                                <li>User profile information</li>
                                <li>Order and transaction history</li>
                                <li>Appointment records</li>
                                <li>Contact form submissions</li>
                            </ul>
                        </div>
                    </div>

                    <form onSubmit={onExport} className="data-mgmt__gdpr-form">
                        <div className="data-mgmt__form-group">
                            <label htmlFor="gdpr-email">User Email Address</label>
                            <Input
                                id="gdpr-email"
                                type="email"
                                placeholder="user@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <Button
                            type="submit"
                            size="lg"
                            disabled={!email || isExporting}
                        >
                            {isExporting ? (
                                <><Spinner size="sm" /> Exporting...</>
                            ) : (
                                <><Download size={18} /> Export Personal Data</>
                            )}
                        </Button>
                    </form>
                </div>
            </Card>
        </div>
    )
}
