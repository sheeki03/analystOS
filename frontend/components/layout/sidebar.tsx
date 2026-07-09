'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FlaskConical,
  Coins,
  Workflow,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string | number
}

const navigation: NavItem[] = [
  { name: 'Research', href: '/research', icon: FlaskConical },
  { name: 'Crypto', href: '/crypto', icon: Coins },
  { name: 'Automation', href: '/automation', icon: Workflow },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-sticky h-screen',
        'bg-bg-surface border-r border-border-default',
        'flex flex-col',
        'transition-all duration-300 ease-in-out',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border-default">
        {!isCollapsed && (
          <Link href="/research" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-accent-primary/20 flex items-center justify-center">
              <span className="text-accent-primary font-mono font-bold text-lg">A</span>
            </div>
            <span className="font-mono font-semibold text-text-primary tracking-tight">
              analyst<span className="text-accent-primary">OS</span>
            </span>
          </Link>
        )}
        {isCollapsed && (
          <div className="w-full flex justify-center">
            <div className="w-8 h-8 rounded bg-accent-primary/20 flex items-center justify-center">
              <span className="text-accent-primary font-mono font-bold text-lg">A</span>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-hide">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-terminal',
                'transition-all duration-200 group',
                isActive
                  ? 'bg-accent-primary/10 text-accent-primary'
                  : 'text-text-muted hover:bg-bg-elevated hover:text-text-primary',
                isCollapsed && 'justify-center px-2'
              )}
              title={isCollapsed ? item.name : undefined}
            >
              <Icon
                className={cn(
                  'h-5 w-5 flex-shrink-0',
                  isActive && 'text-accent-primary'
                )}
              />
              {!isCollapsed && (
                <>
                  <span className="text-sm font-medium">{item.name}</span>
                  {item.badge && (
                    <span className="ml-auto text-xs bg-accent-primary/20 text-accent-primary px-1.5 py-0.5 rounded">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-border-default">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            'flex items-center gap-3 w-full px-3 py-2 rounded-terminal',
            'text-text-muted hover:bg-bg-elevated hover:text-text-primary',
            'transition-colors duration-200',
            isCollapsed && 'justify-center px-2'
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <>
              <ChevronLeft className="h-5 w-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>

        {!isCollapsed && (
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              'flex items-center gap-3 px-3 py-2 mt-1 rounded-terminal',
              'text-text-muted hover:bg-bg-elevated hover:text-text-primary',
              'transition-colors duration-200'
            )}
          >
            <HelpCircle className="h-5 w-5" />
            <span className="text-sm">Help & Docs</span>
          </a>
        )}
      </div>
    </aside>
  )
}

export function SidebarSpacer() {
  return <div className="w-64 flex-shrink-0 transition-all duration-300" />
}
