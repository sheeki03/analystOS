'use client'

import { useState } from 'react'
import { Link, Globe, AlertCircle, Loader2 } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { researchApi } from '@/lib/api'
import type { Job } from '@/types'

interface UrlInputProps {
  onJobCreated: (job: Job) => void
}

export function UrlInput({ onJobCreated }: UrlInputProps) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const trimmedUrl = url.trim()
    if (!trimmedUrl) {
      setError('Please enter a URL')
      return
    }

    // Add protocol if missing
    const normalizedUrl = trimmedUrl.startsWith('http')
      ? trimmedUrl
      : `https://${trimmedUrl}`

    if (!validateUrl(normalizedUrl)) {
      setError('Please enter a valid URL')
      return
    }

    setIsSubmitting(true)

    try {
      const job = await researchApi.scrape(normalizedUrl)
      onJobCreated(job)
      setUrl('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze URL')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
          <Globe className="h-4 w-4" />
        </div>
        <Input
          type="text"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value)
            setError(null)
          }}
          placeholder="https://example.com/article"
          className="pl-10"
          disabled={isSubmitting}
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-terminal bg-accent-danger/10 border border-accent-danger/20">
          <AlertCircle className="h-4 w-4 text-accent-danger flex-shrink-0" />
          <p className="text-sm text-accent-danger">{error}</p>
        </div>
      )}

      <Button type="submit" className="w-full" disabled={isSubmitting || !url.trim()}>
        {isSubmitting ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Link className="h-4 w-4 mr-2" />
            Analyze URL
          </>
        )}
      </Button>

      <p className="text-xs text-text-muted">
        Enter a URL to extract and analyze its content. Works best with articles,
        documentation, and research papers.
      </p>
    </form>
  )
}
