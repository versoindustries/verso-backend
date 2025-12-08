/**
 * FileUpload Component
 * 
 * A file upload component with drag-and-drop support.
 * Placeholder for Phase 18.2.
 */

import { useRef, useState, ChangeEvent, DragEvent } from 'react'
import { Upload, X, File } from 'lucide-react'
import { Button } from '../../ui/button'

export interface FileUploadProps {
    /** Field name */
    name: string
    /** Accepted file types */
    accept?: string
    /** Multiple files */
    multiple?: boolean
    /** Maximum file size in bytes */
    maxSize?: number
    /** Change callback */
    onChange?: (files: File[]) => void
    /** Error message */
    error?: string
    /** Additional class */
    className?: string
}

export function FileUpload({
    name,
    accept,
    multiple = false,
    maxSize,
    onChange,
    error,
    className = '',
}: FileUploadProps) {
    const inputRef = useRef<HTMLInputElement>(null)
    const [files, setFiles] = useState<File[]>([])
    const [isDragging, setIsDragging] = useState(false)

    const handleFiles = (newFiles: FileList | null) => {
        if (!newFiles) return

        const fileArray = Array.from(newFiles)
        const validFiles = maxSize
            ? fileArray.filter(f => f.size <= maxSize)
            : fileArray

        const updatedFiles = multiple ? [...files, ...validFiles] : validFiles.slice(0, 1)
        setFiles(updatedFiles)
        onChange?.(updatedFiles)
    }

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files)
    }

    const handleDragOver = (e: DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = () => {
        setIsDragging(false)
    }

    const handleDrop = (e: DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
    }

    const removeFile = (index: number) => {
        const updatedFiles = files.filter((_, i) => i !== index)
        setFiles(updatedFiles)
        onChange?.(updatedFiles)
    }

    return (
        <div className={`file-upload ${className}`}>
            <div
                className={`file-upload-dropzone ${isDragging ? 'file-upload-dragging' : ''} ${error ? 'file-upload-error' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
            >
                <Upload className="file-upload-icon" />
                <p className="file-upload-text">
                    Drag and drop files here, or click to browse
                </p>
                {accept && (
                    <p className="file-upload-hint">
                        Accepted: {accept}
                    </p>
                )}
                <input
                    ref={inputRef}
                    type="file"
                    name={name}
                    accept={accept}
                    multiple={multiple}
                    onChange={handleChange}
                    className="file-upload-input"
                />
            </div>

            {files.length > 0 && (
                <ul className="file-upload-list">
                    {files.map((file, index) => (
                        <li key={index} className="file-upload-item">
                            <File className="file-upload-item-icon" />
                            <span className="file-upload-item-name">{file.name}</span>
                            <span className="file-upload-item-size">
                                {(file.size / 1024).toFixed(1)} KB
                            </span>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    removeFile(index)
                                }}
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </li>
                    ))}
                </ul>
            )}

            {error && (
                <p className="file-upload-error-message" role="alert">
                    {error}
                </p>
            )}
        </div>
    )
}

export default FileUpload
