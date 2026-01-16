import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline'
  size?: 'sm' | 'md'
}

function Badge({
  className,
  variant = 'default',
  size = 'md',
  ...props
}: BadgeProps) {
  const variants = {
    default: 'bg-bg-elevated text-text-secondary border-border-default',
    success: 'bg-accent-success/10 text-accent-success border-accent-success/30',
    warning: 'bg-accent-secondary/10 text-accent-secondary border-accent-secondary/30',
    danger: 'bg-accent-danger/10 text-accent-danger border-accent-danger/30',
    info: 'bg-accent-primary/10 text-accent-primary border-accent-primary/30',
    outline: 'bg-transparent text-text-secondary border-border-default',
  }

  const sizes = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-0.5 text-sm',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium font-mono rounded border',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
