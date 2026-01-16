'use client'

import { useState } from 'react'
import { Play, Clock, FileText, ExternalLink, Loader2 } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { StatusIndicator } from './status-indicator'
import { cn } from '@/lib/utils'
import { formatRelativeTime } from '@/lib/utils/formatters'
import type { QueueItem } from '@/types'

interface QueueListProps {
  queue: QueueItem[]
  onTrigger: (itemId: string) => void
}

export function QueueList({ queue, onTrigger }: QueueListProps) {
  return (
    <div className="space-y-3">
      {queue.map((item) => (
        <QueueItemCard key={item.item_id} item={item} onTrigger={() => onTrigger(item.item_id)} />
      ))}
    </div>
  )
}

interface QueueItemCardProps {
  item: QueueItem
  onTrigger: () => void
}

function QueueItemCard({ item, onTrigger }: QueueItemCardProps) {
  const [isTriggering, setIsTriggering] = useState(false)

  const handleTrigger = async () => {
    setIsTriggering(true)
    try {
      await onTrigger()
    } finally {
      setTimeout(() => setIsTriggering(false), 1000)
    }
  }

  const statusMap: Record<QueueItem['status'], string> = {
    pending: 'Pending',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
  }

  const badgeVariant: Record<QueueItem['status'], 'secondary' | 'warning' | 'success' | 'danger'> = {
    pending: 'secondary',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }

  return (
    <div
      className={cn(
        'flex items-center justify-between p-4 rounded-terminal border',
        item.status === 'processing'
          ? 'border-accent-secondary bg-accent-secondary/5'
          : 'border-border-default hover:border-text-muted',
        'transition-all'
      )}
    >
      <div className="flex items-center gap-4">
        <StatusIndicator
          status={
            item.status === 'processing'
              ? 'running'
              : item.status === 'completed'
              ? 'completed'
              : item.status === 'failed'
              ? 'failed'
              : 'pending'
          }
          size="md"
        />

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-terminal bg-bg-elevated flex items-center justify-center">
            <FileText className="h-5 w-5 text-text-muted" />
          </div>
          <div>
            <h4 className="font-medium text-text-primary">{item.title}</h4>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-text-muted">
                Added {formatRelativeTime(item.created_at)}
              </span>
              {item.source_url && (
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-accent-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  View in Notion
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Badge variant={badgeVariant[item.status] ?? 'secondary'}>{statusMap[item.status] ?? 'Pending'}</Badge>

        {(item.status === 'pending' || item.status === 'failed') && (
          <Button
            size="sm"
            variant="secondary"
            onClick={handleTrigger}
            disabled={isTriggering}
          >
            {isTriggering ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Play className="h-4 w-4 mr-1" />
                Process
              </>
            )}
          </Button>
        )}

        {item.status === 'processing' && (
          <div className="flex items-center gap-2 text-accent-secondary">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Processing...</span>
          </div>
        )}
      </div>
    </div>
  )
}
