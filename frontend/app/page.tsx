'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Spinner } from '@/components/ui'

export default function HomePage() {
  const router = useRouter()
  const { user, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        router.replace('/research')
      } else {
        router.replace('/login')
      }
    }
  }, [user, isLoading, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-lg bg-accent-primary/20 flex items-center justify-center">
          <span className="text-accent-primary font-mono font-bold text-2xl">A</span>
        </div>
        <Spinner size="lg" />
        <p className="text-text-muted text-sm font-mono">Initializing...</p>
      </div>
    </div>
  )
}
