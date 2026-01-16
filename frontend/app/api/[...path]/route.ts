import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

/**
 * API Proxy Route Handler
 *
 * Proxies requests from /api/* to the FastAPI backend
 * This is only used in development - in production, requests go directly to the backend
 */
async function proxyRequest(request: NextRequest, params: { path: string[] }) {
  const path = params.path.join('/')
  const url = new URL(path, BACKEND_URL)

  // Forward query parameters
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.append(key, value)
  })

  // Prepare headers
  const headers = new Headers()

  // Forward relevant headers
  const forwardHeaders = [
    'content-type',
    'authorization',
    'cookie',
    'x-request-id',
  ]

  forwardHeaders.forEach((header) => {
    const value = request.headers.get(header)
    if (value) {
      headers.set(header, value)
    }
  })

  try {
    // Get request body for non-GET requests
    let body: BodyInit | null = null
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      const contentType = request.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        // Handle empty body case
        const text = await request.text()
        if (text) {
          try {
            body = text
          } catch {
            body = null
          }
        }
      } else if (contentType?.includes('multipart/form-data')) {
        // For file uploads, pass through the FormData
        body = await request.formData()
        // Remove content-type header to let fetch set it with boundary
        headers.delete('content-type')
      } else {
        const text = await request.text()
        body = text || null
      }
    }

    // Make the proxied request
    const response = await fetch(url.toString(), {
      method: request.method,
      headers,
      body,
      credentials: 'include',
    })

    // Create response with forwarded headers
    const responseHeaders = new Headers()

    // Forward response headers
    const responseForwardHeaders = [
      'content-type',
      'set-cookie',
      'cache-control',
      'x-request-id',
    ]

    responseForwardHeaders.forEach((header) => {
      const value = response.headers.get(header)
      if (value) {
        responseHeaders.set(header, value)
      }
    })

    // Handle different response types
    const contentType = response.headers.get('content-type')
    let responseBody: string | Blob

    if (contentType?.includes('application/json')) {
      responseBody = await response.text()
    } else if (contentType?.includes('application/pdf') || contentType?.includes('application/octet-stream')) {
      responseBody = await response.blob()
    } else {
      responseBody = await response.text()
    }

    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    })
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json(
      { detail: 'Failed to connect to backend server' },
      { status: 503 }
    )
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params)
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params)
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params)
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params)
}
