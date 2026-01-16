'use client'

import { useState } from 'react'
import {
  X,
  Download,
  Share2,
  Copy,
  Check,
  FileText,
  Calendar,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import { researchApi } from '@/lib/api'
import type { Report } from '@/types'
import { formatDate, formatRelativeTime } from '@/lib/utils/formatters'

interface ReportViewerProps {
  report: Report
  onClose: () => void
}

export function ReportViewer({ report, onClose }: ReportViewerProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState<string[]>(['summary'])

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const blob = await researchApi.downloadReport(report.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${report.title.replace(/\s+/g, '_')}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(report.content || '')
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Copy failed:', error)
    }
  }

  const toggleSection = (section: string) => {
    setExpandedSections((prev) =>
      prev.includes(section)
        ? prev.filter((s) => s !== section)
        : [...prev, section]
    )
  }

  // Parse sections from content if structured
  const sections = parseSections(report.content || '')

  return (
    <div className="bg-bg-surface border border-border-default rounded-terminal">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-border-default">
        <div className="flex-1 min-w-0 pr-4">
          <h2 className="text-lg font-semibold font-mono text-text-primary truncate">
            {report.title}
          </h2>
          <div className="flex items-center gap-4 mt-2 text-sm text-text-muted">
            <span className="flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              {formatDate(report.created_at)}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {formatRelativeTime(report.created_at)}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {copied ? (
              <Check className="h-4 w-4 text-accent-success" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            disabled={isDownloading}
          >
            <Download className={cn('h-4 w-4', isDownloading && 'animate-bounce')} />
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Metadata */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border-default bg-bg-elevated/50">
        <Badge variant="secondary">{report.type}</Badge>
        {report.source_type && (
          <Badge variant="muted">{report.source_type}</Badge>
        )}
        {report.model && <Badge variant="muted">{report.model}</Badge>}
      </div>

      {/* Content */}
      <div className="p-4 max-h-[60vh] overflow-y-auto scrollbar-hide">
        {sections.length > 0 ? (
          <div className="space-y-4">
            {sections.map((section, index) => (
              <CollapsibleSection
                key={index}
                title={section.title}
                content={section.content}
                isExpanded={expandedSections.includes(section.title)}
                onToggle={() => toggleSection(section.title)}
              />
            ))}
          </div>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <div
              className="text-text-secondary leading-relaxed whitespace-pre-wrap"
              dangerouslySetInnerHTML={{
                __html: formatContent(report.content || ''),
              }}
            />
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between p-4 border-t border-border-default bg-bg-elevated/50">
        <p className="text-xs text-text-muted">
          Report ID: <span className="font-mono">{report.id}</span>
        </p>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Button size="sm" onClick={handleDownload} disabled={isDownloading}>
            <Download className="h-4 w-4 mr-2" />
            Download PDF
          </Button>
        </div>
      </div>
    </div>
  )
}

interface CollapsibleSectionProps {
  title: string
  content: string
  isExpanded: boolean
  onToggle: () => void
}

function CollapsibleSection({
  title,
  content,
  isExpanded,
  onToggle,
}: CollapsibleSectionProps) {
  return (
    <div className="border border-border-default rounded-terminal overflow-hidden">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full p-3 bg-bg-elevated hover:bg-bg-elevated/80 transition-colors"
      >
        <span className="font-medium text-text-primary">{title}</span>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-text-muted" />
        ) : (
          <ChevronDown className="h-4 w-4 text-text-muted" />
        )}
      </button>
      {isExpanded && (
        <div className="p-4 border-t border-border-default">
          <div
            className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: formatContent(content) }}
          />
        </div>
      )}
    </div>
  )
}

// Helper to parse markdown-like sections
function parseSections(content: string): { title: string; content: string }[] {
  const sections: { title: string; content: string }[] = []
  const lines = content.split('\n')
  let currentSection: { title: string; content: string } | null = null

  for (const line of lines) {
    const headerMatch = line.match(/^#{1,3}\s+(.+)$/)
    if (headerMatch) {
      if (currentSection) {
        sections.push(currentSection)
      }
      currentSection = { title: headerMatch[1], content: '' }
    } else if (currentSection) {
      currentSection.content += line + '\n'
    }
  }

  if (currentSection) {
    sections.push(currentSection)
  }

  return sections.map((s) => ({
    ...s,
    content: s.content.trim(),
  }))
}

// Format content for display
function formatContent(content: string): string {
  return content
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-text-primary">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="px-1 py-0.5 bg-bg-elevated rounded text-accent-primary font-mono text-xs">$1</code>')
    .replace(/\n/g, '<br />')
}
