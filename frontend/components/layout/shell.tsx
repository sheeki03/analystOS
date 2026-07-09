'use client'

import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Sidebar } from './sidebar'
import { Header } from './header'

interface ShellProps {
  children: ReactNode
  title?: string
  subtitle?: string
  actions?: ReactNode
  fullWidth?: boolean
}

export function Shell({
  children,
  title,
  subtitle,
  actions,
  fullWidth = false,
}: ShellProps) {
  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="pl-64 transition-all duration-300">
        {/* Header */}
        <Header title={title} subtitle={subtitle} actions={actions} />

        {/* Page content */}
        <main
          className={cn(
            'min-h-[calc(100vh-4rem)]',
            !fullWidth && 'p-6'
          )}
        >
          {children}
        </main>
      </div>
    </div>
  )
}

interface PageContainerProps {
  children: ReactNode
  className?: string
}

export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div className={cn('max-w-7xl mx-auto', className)}>
      {children}
    </div>
  )
}

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-semibold font-mono text-text-primary tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-text-muted">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  )
}

interface PageSectionProps {
  children: ReactNode
  title?: string
  description?: string
  className?: string
}

export function PageSection({
  children,
  title,
  description,
  className,
}: PageSectionProps) {
  return (
    <section className={cn('mb-8', className)}>
      {(title || description) && (
        <div className="mb-4">
          {title && (
            <h2 className="text-lg font-semibold font-mono text-text-primary">
              {title}
            </h2>
          )}
          {description && (
            <p className="mt-0.5 text-sm text-text-muted">{description}</p>
          )}
        </div>
      )}
      {children}
    </section>
  )
}

interface GridProps {
  children: ReactNode
  cols?: 1 | 2 | 3 | 4
  gap?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Grid({ children, cols = 3, gap = 'md', className }: GridProps) {
  const colsClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  }

  const gapClass = {
    sm: 'gap-3',
    md: 'gap-4',
    lg: 'gap-6',
  }

  return (
    <div className={cn('grid', colsClass[cols], gapClass[gap], className)}>
      {children}
    </div>
  )
}
