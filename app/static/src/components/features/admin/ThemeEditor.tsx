/**
 * ThemeEditor Component
 * 
 * Interactive theme editor with color pickers, typography controls,
 * and live preview functionality.
 */

import { useState, useEffect, useRef, CSSProperties } from 'react'
import { Palette, Type, BarChart3, Image, RefreshCw, Save, Trash2 } from 'lucide-react'

// =============================================================================
// Types
// =============================================================================

export interface ThemeConfig {
    primaryColor: string
    secondaryColor: string
    accentColor: string
    fontFamily: string
    borderRadius: number
    ga4TrackingId?: string
}

export interface FontChoice {
    value: string
    label: string
}

export interface ThemeEditorProps {
    /** Current theme configuration */
    currentTheme: ThemeConfig
    /** Available font choices */
    fontChoices: FontChoice[]
    /** Form action URL */
    formActionUrl: string
    /** Logo upload URL */
    logoUploadUrl: string
    /** Logo remove URL */
    logoRemoveUrl: string
    /** Preview URL */
    previewUrl: string
    /** Dashboard URL for back button */
    dashboardUrl: string
    /** Current logo URL (if exists) */
    currentLogoUrl?: string
    /** CSRF token */
    csrfToken: string
}

// =============================================================================
// Sub-components
// =============================================================================

interface ColorPickerRowProps {
    id: string
    label: string
    value: string
    onChange: (value: string) => void
}

function ColorPickerRow({ id, label, value, onChange }: ColorPickerRowProps) {
    const [colorValue, setColorValue] = useState(value)
    const [textValue, setTextValue] = useState(value)

    useEffect(() => {
        setColorValue(value)
        setTextValue(value)
    }, [value])

    const handleColorChange = (newColor: string) => {
        setColorValue(newColor)
        setTextValue(newColor)
        onChange(newColor)
    }

    const handleTextChange = (newText: string) => {
        setTextValue(newText)
        if (/^#[0-9A-Fa-f]{6}$/.test(newText)) {
            setColorValue(newText)
            onChange(newText)
        }
    }

    return (
        <div className="form-group">
            <label htmlFor={id}>{label}</label>
            <div className="color-picker-row">
                <input
                    type="color"
                    id={id}
                    name={id}
                    value={colorValue}
                    onChange={e => handleColorChange(e.target.value)}
                />
                <input
                    type="text"
                    id={`${id}_text`}
                    value={textValue}
                    onChange={e => handleTextChange(e.target.value)}
                    placeholder="#4169e1"
                    pattern="^#[0-9A-Fa-f]{6}$"
                />
            </div>
        </div>
    )
}

// =============================================================================
// Live Preview Component
// =============================================================================

interface LivePreviewProps {
    primaryColor: string
    secondaryColor: string
    accentColor: string
    borderRadius: number
    fontFamily: string
}

function LivePreview({ primaryColor, secondaryColor, accentColor, borderRadius, fontFamily }: LivePreviewProps) {
    const previewStyles: CSSProperties = {
        '--preview-primary': primaryColor,
        '--preview-secondary': secondaryColor,
        '--preview-accent': accentColor,
        '--preview-radius': `${borderRadius}px`,
        fontFamily: fontFamily,
    } as CSSProperties

    return (
        <div className="live-preview-sample" style={previewStyles}>
            <div
                className="preview-card"
                style={{
                    background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`,
                    borderRadius: `${borderRadius}px`,
                }}
            >
                <h3 style={{ margin: '0 0 0.5rem 0' }}>Sample Card</h3>
                <p style={{ margin: 0, opacity: 0.9 }}>This is how your brand colors will look.</p>
            </div>

            <div style={{ marginBottom: '1rem' }}>
                <a
                    href="#"
                    className="preview-btn"
                    style={{ background: primaryColor, borderRadius: `${borderRadius}px` }}
                    onClick={e => e.preventDefault()}
                >
                    Primary Button
                </a>
                <a
                    href="#"
                    className="preview-btn secondary"
                    style={{ background: secondaryColor, borderRadius: `${borderRadius}px` }}
                    onClick={e => e.preventDefault()}
                >
                    Secondary
                </a>
                <a
                    href="#"
                    className="preview-btn accent"
                    style={{ background: accentColor, borderRadius: `${borderRadius}px` }}
                    onClick={e => e.preventDefault()}
                >
                    Accent
                </a>
            </div>

            <div style={{
                background: 'rgba(255,255,255,0.1)',
                padding: '1rem',
                borderRadius: `${borderRadius}px`
            }}>
                <p style={{ margin: 0, color: 'rgba(255,255,255,0.8)' }}>
                    Sample text content with the selected font family.
                </p>
            </div>
        </div>
    )
}

// =============================================================================
// Main Component
// =============================================================================

export function ThemeEditor({
    currentTheme,
    fontChoices,
    formActionUrl,
    logoUploadUrl,
    logoRemoveUrl,
    previewUrl,
    dashboardUrl,
    currentLogoUrl,
    csrfToken,
}: ThemeEditorProps) {
    // State for form values
    const [primaryColor, setPrimaryColor] = useState(currentTheme.primaryColor)
    const [secondaryColor, setSecondaryColor] = useState(currentTheme.secondaryColor)
    const [accentColor, setAccentColor] = useState(currentTheme.accentColor)
    const [fontFamily, setFontFamily] = useState(currentTheme.fontFamily)
    const [borderRadius, setBorderRadius] = useState(currentTheme.borderRadius)
    const [ga4TrackingId, setGa4TrackingId] = useState(currentTheme.ga4TrackingId || '')

    // State for iframe preview
    const [showIframe, setShowIframe] = useState(false)
    const iframeRef = useRef<HTMLIFrameElement>(null)

    // Update iframe preview
    const updateIframePreview = () => {
        if (iframeRef.current && showIframe) {
            const params = new URLSearchParams({
                primary_color: primaryColor,
                secondary_color: secondaryColor,
                accent_color: accentColor,
                border_radius: String(borderRadius),
                font_family: fontFamily,
            })
            iframeRef.current.src = `${previewUrl}?${params.toString()}`
        }
    }

    useEffect(() => {
        updateIframePreview()
    }, [primaryColor, secondaryColor, accentColor, borderRadius, fontFamily, showIframe])

    return (
        <div className="theme-editor">
            <h1><Palette className="inline-icon" /> Theme Editor</h1>

            <div className="editor-layout">
                {/* Settings Panel */}
                <div className="editor-panel">
                    <form action={formActionUrl} method="POST">
                        <input type="hidden" name="csrf_token" value={csrfToken} />

                        {/* Colors Section */}
                        <div className="panel-section">
                            <h3><Palette className="inline-icon" /> Colors</h3>

                            <ColorPickerRow
                                id="primary_color"
                                label="Primary Color"
                                value={primaryColor}
                                onChange={setPrimaryColor}
                            />

                            <ColorPickerRow
                                id="secondary_color"
                                label="Secondary Color"
                                value={secondaryColor}
                                onChange={setSecondaryColor}
                            />

                            <ColorPickerRow
                                id="accent_color"
                                label="Accent Color"
                                value={accentColor}
                                onChange={setAccentColor}
                            />
                        </div>

                        {/* Typography Section */}
                        <div className="panel-section">
                            <h3><Type className="inline-icon" /> Typography</h3>

                            <div className="form-group">
                                <label htmlFor="font_family">Font Family</label>
                                <select
                                    id="font_family"
                                    name="font_family"
                                    value={fontFamily}
                                    onChange={e => setFontFamily(e.target.value)}
                                >
                                    {fontChoices.map(choice => (
                                        <option key={choice.value} value={choice.value}>
                                            {choice.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="border_radius">Border Radius (px)</label>
                                <input
                                    type="number"
                                    id="border_radius"
                                    name="border_radius"
                                    value={borderRadius}
                                    onChange={e => setBorderRadius(Number(e.target.value))}
                                    min={0}
                                    max={50}
                                />
                            </div>
                        </div>

                        {/* Analytics Section */}
                        <div className="panel-section">
                            <h3><BarChart3 className="inline-icon" /> Analytics</h3>

                            <div className="form-group">
                                <label htmlFor="ga4_tracking_id">Google Analytics 4 ID</label>
                                <input
                                    type="text"
                                    id="ga4_tracking_id"
                                    name="ga4_tracking_id"
                                    value={ga4TrackingId}
                                    onChange={e => setGa4TrackingId(e.target.value)}
                                    placeholder="G-XXXXXXXXXX"
                                />
                                <small className="form-hint">Leave empty to disable</small>
                            </div>
                        </div>

                        <button type="submit" className="btn-save">
                            <Save className="inline-icon" /> Save Theme
                        </button>
                    </form>

                    {/* Logo Upload */}
                    <div className="panel-section logo-section">
                        <h3><Image className="inline-icon" /> Logo</h3>

                        {currentLogoUrl && (
                            <>
                                <div className="current-logo">
                                    <img src={currentLogoUrl} alt="Current Logo" />
                                </div>
                                <form action={logoRemoveUrl} method="POST" style={{ marginBottom: '1rem' }}>
                                    <input type="hidden" name="csrf_token" value={csrfToken} />
                                    <button type="submit" className="btn-danger">
                                        <Trash2 className="inline-icon" /> Remove Logo
                                    </button>
                                </form>
                            </>
                        )}

                        <form
                            action={logoUploadUrl}
                            method="POST"
                            encType="multipart/form-data"
                            className="logo-upload-form"
                        >
                            <input type="hidden" name="csrf_token" value={csrfToken} />
                            <input type="file" name="logo" accept="image/*" required />
                            <button type="submit" className="btn-secondary">
                                Upload Logo
                            </button>
                        </form>
                    </div>
                </div>

                {/* Preview Panel */}
                <div className="preview-panel">
                    <div className="preview-header">
                        <h3>Live Preview</h3>
                        <div className="preview-controls">
                            <button
                                type="button"
                                onClick={() => setShowIframe(!showIframe)}
                                className={showIframe ? 'active' : ''}
                            >
                                {showIframe ? 'Inline' : 'Full Page'}
                            </button>
                            {showIframe && (
                                <button type="button" onClick={updateIframePreview}>
                                    <RefreshCw className="inline-icon" /> Refresh
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Inline Preview */}
                    {!showIframe && (
                        <LivePreview
                            primaryColor={primaryColor}
                            secondaryColor={secondaryColor}
                            accentColor={accentColor}
                            borderRadius={borderRadius}
                            fontFamily={fontFamily}
                        />
                    )}

                    {/* Iframe Preview */}
                    {showIframe && (
                        <div className="preview-frame-container">
                            <iframe
                                ref={iframeRef}
                                className="preview-frame"
                                title="Theme Preview"
                            />
                        </div>
                    )}
                </div>
            </div>

            <div style={{ marginTop: '2rem' }}>
                <a href={dashboardUrl} className="quick-action-btn">
                    ← Back to Dashboard
                </a>
            </div>
        </div>
    )
}

export default ThemeEditor
