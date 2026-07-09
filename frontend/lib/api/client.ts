/**
 * API Client
 *
 * Handles all API requests with:
 * - Automatic token refresh
 * - Proper cookie handling for auth endpoints
 * - Error handling
 *
 * Cookie Rules:
 * - /auth/* endpoints use credentials: 'include' for cookies
 * - Other endpoints use Authorization: Bearer header
 */

import type { ApiError } from '@/types'

// API base URL
// In development, we proxy through Next.js (/api/*)
// In production, we call the API directly
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api'

// Token storage (in-memory for security)
let accessToken: string | null = null

/**
 * Set the access token (called after login/refresh)
 */
export function setAccessToken(token: string | null) {
  accessToken = token
}

/**
 * Get the current access token
 */
export function getAccessToken(): string | null {
  return accessToken
}

/**
 * Check if an endpoint needs cookie-based auth
 * Only login/refresh/logout use cookies; /auth/me uses Bearer token
 */
function isAuthCookieEndpoint(url: string): boolean {
  return (
    url.includes('/auth/login') ||
    url.includes('/auth/refresh') ||
    url.includes('/auth/logout')
  )
}

/**
 * Build request options based on endpoint type
 */
function buildRequestOptions(
  url: string,
  options: RequestInit = {}
): RequestInit {
  const headers = new Headers(options.headers)

  // Cookie-based auth endpoints (login/refresh/logout)
  if (isAuthCookieEndpoint(url)) {
    return {
      ...options,
      credentials: 'include',
      headers,
    }
  }

  // Other endpoints use Bearer token
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  return {
    ...options,
    headers,
  }
}

/**
 * API Error class
 */
export class ApiClientError extends Error {
  status: number
  data?: ApiError

  constructor(message: string, status: number, data?: ApiError) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.data = data
  }
}

/**
 * Main fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const requestOptions = buildRequestOptions(url, options)

  const response = await fetch(url, requestOptions)

  // Handle non-JSON responses (like file downloads)
  const contentType = response.headers.get('content-type')
  if (contentType && !contentType.includes('application/json')) {
    if (!response.ok) {
      throw new ApiClientError(
        `Request failed: ${response.statusText}`,
        response.status
      )
    }
    return response as unknown as T
  }

  // Parse JSON response
  let data: T | ApiError
  try {
    data = await response.json()
  } catch {
    if (!response.ok) {
      throw new ApiClientError(
        `Request failed: ${response.statusText}`,
        response.status
      )
    }
    return {} as T
  }

  if (!response.ok) {
    const error = data as ApiError
    throw new ApiClientError(
      error.detail || `Request failed: ${response.statusText}`,
      response.status,
      error
    )
  }

  return data as T
}

/**
 * API client methods
 */
export const api = {
  /**
   * GET request
   */
  get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = params
      ? `${endpoint}?${new URLSearchParams(params).toString()}`
      : endpoint
    return fetchApi<T>(url, { method: 'GET' })
  },

  /**
   * POST request with JSON body
   */
  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return fetchApi<T>(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
  },

  /**
   * POST request with FormData (for file uploads)
   */
  postForm<T>(endpoint: string, formData: FormData): Promise<T> {
    return fetchApi<T>(endpoint, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type - browser will set it with boundary
    })
  },

  /**
   * PUT request with JSON body
   */
  put<T>(endpoint: string, body?: unknown): Promise<T> {
    return fetchApi<T>(endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
  },

  /**
   * DELETE request
   */
  delete<T>(endpoint: string): Promise<T> {
    return fetchApi<T>(endpoint, { method: 'DELETE' })
  },
}

export default api
