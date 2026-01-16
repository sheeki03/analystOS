'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-react'
import { useAuth } from '@/contexts/auth-context'
import { Button, Input } from '@/components/ui'
import { cn } from '@/lib/utils'

export default function LoginPage() {
  const router = useRouter()
  const { user, login, isLoading: authLoading } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Redirect if already logged in
  useEffect(() => {
    if (user && !authLoading) {
      router.replace('/research')
    }
  }, [user, authLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login({ username, password })
      router.push('/research')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid credentials')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-primary">
        <div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex bg-bg-primary">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:flex-1 flex-col justify-between p-12 bg-bg-surface border-r border-border-default">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-primary/20 flex items-center justify-center">
              <span className="text-accent-primary font-mono font-bold text-xl">A</span>
            </div>
            <span className="font-mono font-semibold text-xl text-text-primary tracking-tight">
              analyst<span className="text-accent-primary">OS</span>
            </span>
          </div>
          <p className="mt-6 text-text-muted max-w-md">
            Premium research terminal for AI-powered analysis, crypto insights, and workflow automation.
          </p>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <FeatureCard
              title="AI Research"
              description="Deep document analysis with entity extraction"
            />
            <FeatureCard
              title="Crypto Intel"
              description="Real-time market data and AI insights"
            />
            <FeatureCard
              title="Automation"
              description="Notion workflow automation"
            />
            <FeatureCard
              title="Reports"
              description="Generate comprehensive research reports"
            />
          </div>
        </div>

        <p className="text-text-muted text-xs">
          &copy; {new Date().getFullYear()} analystOS. All rights reserved.
        </p>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-accent-primary/20 flex items-center justify-center">
                <span className="text-accent-primary font-mono font-bold text-xl">A</span>
              </div>
              <span className="font-mono font-semibold text-xl text-text-primary tracking-tight">
                analyst<span className="text-accent-primary">OS</span>
              </span>
            </div>
          </div>

          <div className="space-y-2 mb-8">
            <h1 className="text-2xl font-semibold font-mono text-text-primary">
              Welcome back
            </h1>
            <p className="text-text-muted">
              Sign in to access your research terminal
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-terminal bg-accent-danger/10 border border-accent-danger/20">
                <AlertCircle className="h-4 w-4 text-accent-danger flex-shrink-0" />
                <p className="text-sm text-accent-danger">{error}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-text-secondary mb-1.5">
                  Username
                </label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                  autoComplete="username"
                  autoFocus
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    autoComplete="current-password"
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting || !username || !password}
            >
              {isSubmitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-8 pt-8 border-t border-border-default">
            <p className="text-xs text-text-muted text-center">
              By signing in, you agree to our Terms of Service and Privacy Policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="p-4 rounded-terminal bg-bg-elevated border border-border-default">
      <h3 className="font-mono font-medium text-text-primary text-sm">{title}</h3>
      <p className="text-xs text-text-muted mt-1">{description}</p>
    </div>
  )
}
