'use client'

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { useRouter, usePathname } from 'next/navigation'
import type { User, LoginRequest } from '@/types'
import {
  login as apiLogin,
  logout as apiLogout,
  logoutAll as apiLogoutAll,
  checkAuth,
  setAccessToken,
} from '@/lib/api'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  logoutAll: () => Promise<void>
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Public routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/']

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  const isAuthenticated = user !== null

  /**
   * Check authentication on mount and route changes
   * This prevents spurious logouts on page reload
   */
  const refreshAuth = useCallback(async () => {
    try {
      const currentUser = await checkAuth()
      setUser(currentUser)
    } catch (error) {
      console.error('Auth check failed:', error)
      setUser(null)
      setAccessToken(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Login handler
   */
  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true)
    try {
      await apiLogin(credentials)
      await refreshAuth()
      router.push('/research')
    } catch (error) {
      setIsLoading(false)
      throw error
    }
  }, [refreshAuth, router])

  /**
   * Logout handler
   */
  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await apiLogout()
    } finally {
      setUser(null)
      setIsLoading(false)
      router.push('/login')
    }
  }, [router])

  /**
   * Logout from all devices
   */
  const logoutAll = useCallback(async () => {
    setIsLoading(true)
    try {
      await apiLogoutAll()
    } finally {
      setUser(null)
      setIsLoading(false)
      router.push('/login')
    }
  }, [router])

  /**
   * Initial auth check on mount
   */
  useEffect(() => {
    refreshAuth()
  }, [refreshAuth])

  /**
   * Redirect unauthenticated users away from protected routes
   */
  useEffect(() => {
    if (!isLoading && !isAuthenticated && !PUBLIC_ROUTES.includes(pathname)) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, pathname, router])

  /**
   * Redirect authenticated users away from login page
   */
  useEffect(() => {
    if (!isLoading && isAuthenticated && pathname === '/login') {
      router.push('/research')
    }
  }, [isLoading, isAuthenticated, pathname, router])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    logoutAll,
    refreshAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to access auth context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/**
 * Hook to require authentication
 * Returns null while loading, redirects if not authenticated
 */
export function useRequireAuth(): User | null {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) return null
  return user
}
