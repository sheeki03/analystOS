/**
 * Authentication API functions
 */

import { api, setAccessToken, ApiClientError } from './client'
import type { LoginRequest, LoginResponse, RefreshResponse, User } from '@/types'

/**
 * Login with username and password
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', credentials)
  setAccessToken(response.access_token)
  return response
}

/**
 * Refresh access token using refresh token cookie
 */
export async function refreshToken(): Promise<RefreshResponse> {
  const response = await api.post<RefreshResponse>('/auth/refresh')
  setAccessToken(response.access_token)
  return response
}

/**
 * Logout - revokes refresh token
 */
export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout')
  } finally {
    setAccessToken(null)
  }
}

/**
 * Logout from all devices
 */
export async function logoutAll(): Promise<{ message: string; tokens_revoked: number }> {
  const response = await api.post<{ message: string; tokens_revoked: number }>('/auth/logout-all')
  setAccessToken(null)
  return response
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<User> {
  return api.get<User>('/auth/me')
}

/**
 * Check if user is authenticated by trying to refresh token
 */
export async function checkAuth(): Promise<User | null> {
  try {
    await refreshToken()
    return await getCurrentUser()
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      setAccessToken(null)
      return null
    }
    throw error
  }
}
