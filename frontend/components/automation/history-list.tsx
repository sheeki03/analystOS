'use client'

import { CheckCircle, XCircle, Clock, FileText, ExternalLink } from 'lucide-react'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import { formatDate, formatRelativeTime } from '@/lib/utils/formatters'
import type { AutomationHistory } from '@/types'

interface HistoryListProps {
  history: AutomationHistory[]
  compact?: boolean
}

export function HistoryList({ history, compact }: HistoryListProps) {
  if (compact) {
    return (
      <div className="space-y-2">
        {history.map((item) => (
          <CompactHistoryItem key={item.id} item={item} />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {history.map((item) => (
        <HistoryItem key={item.id} item={item} />
      ))}
    </div>
  )
}

interface HistoryItemProps {
  item: AutomationHistory
}

function HistoryItem({ item }: HistoryItemProps) {
  const isSuccess = item.status === 'completed'
  const isFailed = item.status === 'failed'

  return (
    <div
      className={cn(
        'p-4 rounded-terminal border',
        'border-border-default hover:border-text-muted transition-colors'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              'w-10 h-10 rounded-terminal flex items-center justify-center',
              isSuccess
                ? 'bg-accent-success/10'
                : isFailed
                ? 'bg-accent-danger/10'
                : 'bg-bg-elevated'
            )}
          >
            {isSuccess ? (
              <CheckCircle className="h-5 w-5 text-accent-success" />
            ) : isFailed ? (
              <XCircle className="h-5 w-5 text-accent-danger" />
            ) : (
              <Clock className="h-5 w-5 text-text-muted" />
            )}
          </div>

          <div>
            <h4 className="font-medium text-text-primary">{item.title}</h4>
            <p className="text-sm text-text-muted mt-0.5">{item.workflow_name}</p>
            {item.error_message && (
              <p className="text-sm text-accent-danger mt-2">
                Error: {item.error_message}
              </p>
            )}
          </div>
        </div>

        <Badge variant={isSuccess ? 'success' : isFailed ? 'danger' : 'secondary'}>
          {item.status}
        </Badge>
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-default">
        <div className="flex items-center gap-4 text-xs text-text-muted">
          <span>Started: {formatDate(item.started_at)}</span>
          {item.completed_at && (
            <span>
              Duration:{' '}
              {formatDuration(
                new Date(item.completed_at).getTime() -
                  new Date(item.started_at).getTime()
              )}
            </span>
          )}
        </div>

        {item.output_url && (
          <a
            href={item.output_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-accent-primary hover:underline"
          >
            View Output
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  )
}

function CompactHistoryItem({ item }: HistoryItemProps) {
  const isSuccess = item.status === 'completed'
  const isFailed = item.status === 'failed'

  return (
    <div className="flex items-center justify-between p-3 rounded-terminal border border-border-default">
      <div className="flex items-center gap-3">
        {isSuccess ? (
          <CheckCircle className="h-4 w-4 text-accent-success" />
        ) : isFailed ? (
          <XCircle className="h-4 w-4 text-accent-danger" />
        ) : (
          <Clock className="h-4 w-4 text-text-muted" />
        )}

        <div>
          <p className="text-sm font-medium text-text-primary">{item.title}</p>
          <p className="text-xs text-text-muted">
            {formatRelativeTime(item.started_at)}
          </p>
        </div>
      </div>

      <Badge
        variant={isSuccess ? 'success' : isFailed ? 'danger' : 'secondary'}
        className="text-xs"
      >
        {item.status}
      </Badge>
    </div>
  )
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}
