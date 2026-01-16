'use client'

import { useState, useRef, useCallback } from 'react'
import { Upload, File, X, AlertCircle, CheckCircle } from 'lucide-react'
import { Button, Badge, Progress } from '@/components/ui'
import { cn } from '@/lib/utils'
import { researchApi } from '@/lib/api'
import type { Job } from '@/types'

interface DocumentUploadProps {
  onJobCreated: (job: Job) => void
}

const ACCEPTED_TYPES = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt',
}

const MAX_SIZE = 50 * 1024 * 1024 // 50MB

export function DocumentUpload({ onJobCreated }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (!Object.keys(ACCEPTED_TYPES).includes(file.type)) {
      return 'Invalid file type. Please upload a PDF, DOCX, or TXT file.'
    }
    if (file.size > MAX_SIZE) {
      return 'File is too large. Maximum size is 50MB.'
    }
    return null
  }

  const handleFile = (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      setFile(null)
      return
    }
    setError(null)
    setFile(file)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFile(droppedFile)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFile(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Simulate progress for UX
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      const job = await researchApi.upload(file)

      clearInterval(progressInterval)
      setUploadProgress(100)

      onJobCreated(job)

      // Reset after short delay
      setTimeout(() => {
        setFile(null)
        setUploadProgress(0)
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const clearFile = () => {
    setFile(null)
    setError(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={cn(
          'relative flex flex-col items-center justify-center p-8',
          'border-2 border-dashed rounded-terminal cursor-pointer',
          'transition-all duration-200',
          isDragging
            ? 'border-accent-primary bg-accent-primary/5'
            : 'border-border-default hover:border-text-muted hover:bg-bg-elevated/50',
          file && 'border-accent-success bg-accent-success/5'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={Object.values(ACCEPTED_TYPES).join(',')}
          onChange={handleInputChange}
          className="hidden"
        />

        {file ? (
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-terminal bg-accent-primary/20 flex items-center justify-center">
              <File className="h-6 w-6 text-accent-primary" />
            </div>
            <div>
              <p className="font-medium text-text-primary">{file.name}</p>
              <p className="text-sm text-text-muted">{formatFileSize(file.size)}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                clearFile()
              }}
              className="p-1 rounded hover:bg-bg-elevated text-text-muted hover:text-text-primary transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 rounded-full bg-bg-elevated flex items-center justify-center mb-4">
              <Upload className="h-6 w-6 text-text-muted" />
            </div>
            <p className="text-text-primary font-medium mb-1">
              Drop your document here or click to browse
            </p>
            <p className="text-sm text-text-muted">
              Supports PDF, DOCX, TXT (max 50MB)
            </p>
          </>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-terminal bg-accent-danger/10 border border-accent-danger/20">
          <AlertCircle className="h-4 w-4 text-accent-danger flex-shrink-0" />
          <p className="text-sm text-accent-danger">{error}</p>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-text-muted">Uploading...</span>
            <span className="text-text-primary font-mono">{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} />
        </div>
      )}

      {/* Upload Button */}
      {file && !isUploading && (
        <Button onClick={handleUpload} className="w-full">
          <Upload className="h-4 w-4 mr-2" />
          Upload & Analyze
        </Button>
      )}

      {/* Success State */}
      {uploadProgress === 100 && (
        <div className="flex items-center gap-2 p-3 rounded-terminal bg-accent-success/10 border border-accent-success/20">
          <CheckCircle className="h-4 w-4 text-accent-success flex-shrink-0" />
          <p className="text-sm text-accent-success">
            Document uploaded! Processing started.
          </p>
        </div>
      )}
    </div>
  )
}
