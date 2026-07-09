import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn('animate-shimmer rounded bg-zinc-800', className)}
      aria-hidden="true"
    />
  )
}

function SkeletonText({ className }: SkeletonProps) {
  return <Skeleton className={cn('h-4 w-full', className)} />
}

function SkeletonTitle({ className }: SkeletonProps) {
  return <Skeleton className={cn('h-6 w-3/4', className)} />
}

function SkeletonAvatar({ className }: SkeletonProps) {
  return <Skeleton className={cn('h-10 w-10 rounded-full', className)} />
}

function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div className={cn('p-4 space-y-3', className)}>
      <SkeletonTitle />
      <SkeletonText />
      <SkeletonText className="w-2/3" />
    </div>
  )
}

export { Skeleton, SkeletonText, SkeletonTitle, SkeletonAvatar, SkeletonCard }
