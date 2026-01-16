'use client'

import { cn } from '@/lib/utils'

type Status = 'idle' | 'running' | 'completed' | 'failed' | 'pending'

interface StatusIndicatorProps {
  status: Status
  size?: 'sm' | 'md' | 'lg'
  showPulse?: boolean
}

const STATUS_COLORS: Record<Status, string> = {
  idle: 'bg-text-muted',
  running: 'bg-accent-secondary',
  completed: 'bg-accent-success',
  failed: 'bg-accent-danger',
  pending: 'bg-text-muted',
}

const STATUS_GLOW: Record<Status, string> = {
  idle: '',
  running: 'shadow-[0_0_8px_2px_rgba(245,158,11,0.4)]',
  completed: 'shadow-[0_0_8px_2px_rgba(34,197,94,0.4)]',
  failed: 'shadow-[0_0_8px_2px_rgba(239,68,68,0.4)]',
  pending: '',
}

export function StatusIndicator({
  status,
  size = 'md',
  showPulse = true,
}: StatusIndicatorProps) {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  }

  return (
    <div className="relative flex items-center justify-center">
      <span
        className={cn(
          'rounded-full',
          sizeClasses[size],
          STATUS_COLORS[status],
          STATUS_GLOW[status],
          status === 'running' && showPulse && 'animate-pulse'
        )}
      />
      {status === 'running' && showPulse && (
        <span
          className={cn(
            'absolute rounded-full animate-ping opacity-75',
            sizeClasses[size],
            STATUS_COLORS[status]
          )}
        />
      )}
    </div>
  )
}
