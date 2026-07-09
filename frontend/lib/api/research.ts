/**
 * Research API functions
 */

import { api } from './client'
import type {
  Job,
  UploadResponse,
  ScrapeRequest,
  ScrapeResponse,
  GenerateRequest,
  GenerateResponse,
  ReportSummary,
  ReportDetail,
  PaginatedResponse,
} from '@/types'

/**
 * Upload documents for processing
 */
export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  return api.postForm<UploadResponse>('/research/upload', formData)
}

/**
 * Scrape URLs for content
 */
export async function scrapeUrls(request: ScrapeRequest): Promise<ScrapeResponse> {
  return api.post<ScrapeResponse>('/research/scrape', request)
}

/**
 * Generate a research report
 */
export async function generateReport(request: GenerateRequest): Promise<GenerateResponse> {
  return api.post<GenerateResponse>('/research/generate', request)
}

/**
 * Extract entities from sources
 */
export async function extractEntities(sources: string[]): Promise<{ job_id: string }> {
  return api.post<{ job_id: string }>('/research/extract-entities', { sources })
}

/**
 * Get job status
 */
export async function getJob(jobId: string): Promise<Job> {
  return api.get<Job>(`/research/jobs/${jobId}`)
}

/**
 * Poll job status until complete or failed
 */
export async function pollJob(
  jobId: string,
  onProgress?: (job: Job) => void,
  intervalMs = 2000
): Promise<Job> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const job = await getJob(jobId)
        onProgress?.(job)

        if (job.status === 'completed') {
          resolve(job)
        } else if (job.status === 'failed') {
          reject(new Error(job.error || 'Job failed'))
        } else {
          setTimeout(poll, intervalMs)
        }
      } catch (error) {
        reject(error)
      }
    }
    poll()
  })
}

/**
 * List user's reports
 */
export async function listReports(
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<ReportSummary>> {
  const response = await api.get<{
    reports: ReportSummary[]
    total: number
    page: number
    page_size: number
  }>('/research/reports', {
    page: String(page),
    page_size: String(pageSize),
  })
  return {
    items: response.reports,
    total: response.total,
    page: response.page,
    page_size: response.page_size,
  }
}

/**
 * Get report details
 */
export async function getReport(reportId: string): Promise<ReportDetail> {
  return api.get<ReportDetail>(`/research/reports/${reportId}`)
}

/**
 * Download report file
 */
export async function downloadReport(reportId: string): Promise<Blob> {
  const response = await api.get<Response>(`/research/reports/${reportId}/download`)
  return response.blob()
}
