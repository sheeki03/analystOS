'use client'

import { useState } from 'react'
import { Play, Clock, CheckCircle, AlertCircle, Loader2, MoreVertical } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { StatusIndicator } from './status-indicator'
import { cn } from '@/lib/utils'
import { formatRelativeTime } from '@/lib/utils/formatters'

interface WorkflowCardProps {
  title: string
  description: string
  status: 'idle' | 'running' | 'completed' | 'failed'
  lastRun?: string
  onTrigger: () => void
}

export function WorkflowCard({
  title,
  description,
  status,
  lastRun,
  onTrigger,
}: WorkflowCardProps) {
  const [isTriggering, setIsTriggering] = useState(false)

  const handleTrigger = async () => {
    setIsTriggering(true)
    try {
      await onTrigger()
    } finally {
      setTimeout(() => setIsTriggering(false), 1000)
    }
  }

  const statusConfig = {
    idle: {
      badge: 'secondary' as const,
      label: 'Idle',
      icon: <Clock className="h-4 w-4" />,
    },
    running: {
      badge: 'warning' as const,
      label: 'Running',
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
    },
    completed: {
      badge: 'success' as const,
      label: 'Completed',
      icon: <CheckCircle className="h-4 w-4" />,
    },
    failed: {
      badge: 'danger' as const,
      label: 'Failed',
      icon: <AlertCircle className="h-4 w-4" />,
    },
  }

  const config = statusConfig[status]

  return (
    <div
      className={cn(
        'p-4 rounded-terminal border transition-all',
        status === 'running'
          ? 'border-accent-secondary bg-accent-secondary/5'
          : 'border-border-default hover:border-text-muted'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <StatusIndicator status={status} size="lg" />
          <div>
            <h3 className="font-medium text-text-primary">{title}</h3>
            <p className="text-sm text-text-muted mt-1">{description}</p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          className="p-1"
          aria-label="More options"
        >
          <MoreVertical className="h-4 w-4 text-text-muted" />
        </Button>
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border-default">
        <div className="flex items-center gap-3">
          <Badge variant={config.badge}>
            {config.icon}
            <span className="ml-1">{config.label}</span>
          </Badge>
          {lastRun && (
            <span className="text-xs text-text-muted">
              Last run: {formatRelativeTime(lastRun)}
            </span>
          )}
        </div>

        <Button
          size="sm"
          onClick={handleTrigger}
          disabled={status === 'running' || isTriggering}
        >
          {isTriggering || status === 'running' ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Run Now
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
