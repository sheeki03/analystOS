'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { User, LogOut, Settings, ChevronDown, Bell } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/auth-context'

interface HeaderProps {
  title?: string
  subtitle?: string
  actions?: React.ReactNode
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Get page title from pathname
  const getPageTitle = () => {
    if (title) return title
    const segments = pathname.split('/').filter(Boolean)
    const lastSegment = segments[segments.length - 1] || 'Dashboard'
    return lastSegment.charAt(0).toUpperCase() + lastSegment.slice(1)
  }

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsUserMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header className="h-16 bg-bg-surface border-b border-border-default flex items-center justify-between px-6">
      {/* Left: Title */}
      <div>
        <h1 className="text-lg font-semibold font-mono text-text-primary">
          {getPageTitle()}
        </h1>
        {subtitle && (
          <p className="text-sm text-text-muted">{subtitle}</p>
        )}
      </div>

      {/* Right: Actions & User Menu */}
      <div className="flex items-center gap-4">
        {actions}

        {/* Notifications */}
        <button
          className={cn(
            'relative p-2 rounded-terminal',
            'text-text-muted hover:text-text-primary hover:bg-bg-elevated',
            'transition-colors duration-200'
          )}
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {/* Notification dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent-primary rounded-full" />
        </button>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-terminal',
              'text-text-secondary hover:text-text-primary hover:bg-bg-elevated',
              'transition-colors duration-200'
            )}
            aria-expanded={isUserMenuOpen}
            aria-haspopup="true"
          >
            <div className="w-8 h-8 rounded-full bg-accent-primary/20 flex items-center justify-center">
              <span className="text-accent-primary font-mono font-medium text-sm">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </span>
            </div>
            <span className="text-sm font-medium hidden sm:block">
              {user?.username || 'User'}
            </span>
            <ChevronDown
              className={cn(
                'h-4 w-4 transition-transform duration-200',
                isUserMenuOpen && 'rotate-180'
              )}
            />
          </button>

          {/* Dropdown Menu */}
          {isUserMenuOpen && (
            <div
              className={cn(
                'absolute right-0 mt-2 w-56',
                'bg-bg-elevated border border-border-default rounded-terminal shadow-elevated',
                'py-1 z-dropdown animate-slide-in-up'
              )}
            >
              {/* User Info */}
              <div className="px-4 py-3 border-b border-border-default">
                <p className="text-sm font-medium text-text-primary">
                  {user?.username || 'User'}
                </p>
                <p className="text-xs text-text-muted truncate">
                  {user?.email || 'user@example.com'}
                </p>
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <Link
                  href="/settings"
                  className={cn(
                    'flex items-center gap-3 px-4 py-2',
                    'text-sm text-text-secondary hover:text-text-primary hover:bg-bg-primary',
                    'transition-colors duration-150'
                  )}
                  onClick={() => setIsUserMenuOpen(false)}
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>
                <Link
                  href="/settings"
                  className={cn(
                    'flex items-center gap-3 px-4 py-2',
                    'text-sm text-text-secondary hover:text-text-primary hover:bg-bg-primary',
                    'transition-colors duration-150'
                  )}
                  onClick={() => setIsUserMenuOpen(false)}
                >
                  <User className="h-4 w-4" />
                  Profile
                </Link>
              </div>

              {/* Logout */}
              <div className="border-t border-border-default py-1">
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false)
                    logout()
                  }}
                  className={cn(
                    'flex items-center gap-3 w-full px-4 py-2',
                    'text-sm text-accent-danger hover:bg-accent-danger/10',
                    'transition-colors duration-150'
                  )}
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
