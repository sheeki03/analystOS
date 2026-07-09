'use client'

import { FileText, Calendar, Clock, ChevronRight, Download } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { cn } from '@/lib/utils'
import { researchApi } from '@/lib/api'
import type { Report } from '@/types'
import { formatDate, formatRelativeTime } from '@/lib/utils/formatters'

interface ReportCardProps {
  report: Report
  onClick: () => void
}

export function ReportCard({ report, onClick }: ReportCardProps) {
  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation()
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
    }
  }

  const typeColors: Record<string, string> = {
    upload: 'bg-blue-400/10 text-blue-400',
    scrape: 'bg-green-400/10 text-green-400',
    generate: 'bg-purple-400/10 text-purple-400',
  }

  return (
    <div
      onClick={onClick}
      className={cn(
        'group relative p-4 rounded-terminal',
        'bg-bg-surface border border-border-default',
        'hover:border-text-muted hover:bg-bg-elevated/50',
        'transition-all duration-200 cursor-pointer',
        'hover:shadow-elevated'
      )}
    >
      {/* Icon & Type Badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-terminal bg-accent-primary/10 flex items-center justify-center">
          <FileText className="h-5 w-5 text-accent-primary" />
        </div>
        <Badge className={cn(typeColors[report.type] || 'bg-bg-elevated text-text-muted')}>
          {report.type}
        </Badge>
      </div>

      {/* Title */}
      <h3 className="font-medium text-text-primary mb-1 line-clamp-2 group-hover:text-accent-primary transition-colors">
        {report.title}
      </h3>

      {/* Preview */}
      {report.content && (
        <p className="text-sm text-text-muted line-clamp-2 mb-3">
          {report.content.substring(0, 150)}...
        </p>
      )}

      {/* Metadata */}
      <div className="flex items-center gap-3 text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          {formatDate(report.created_at)}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatRelativeTime(report.created_at)}
        </span>
      </div>

      {/* Hover Actions */}
      <div
        className={cn(
          'absolute inset-x-0 bottom-0 p-4 pt-8',
          'bg-gradient-to-t from-bg-surface via-bg-surface/95 to-transparent',
          'opacity-0 group-hover:opacity-100 transition-opacity duration-200',
          'flex items-center justify-between'
        )}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDownload}
          className="text-text-muted hover:text-text-primary"
        >
          <Download className="h-4 w-4 mr-1" />
          Download
        </Button>
        <span className="flex items-center gap-1 text-sm text-accent-primary">
          View
          <ChevronRight className="h-4 w-4" />
        </span>
      </div>

      {/* Source indicator */}
      {report.source_type && (
        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
          <Badge variant="muted" className="text-xs">
            {report.source_type}
          </Badge>
        </div>
      )}
    </div>
  )
}
