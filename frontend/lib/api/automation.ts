/**
 * Automation API functions
 */

import { api } from './client'
import type { NotionStatus, QueueItem, HistoryItem, WorkflowConfig } from '@/types'

/**
 * Get Notion connection status
 */
export async function getNotionStatus(): Promise<NotionStatus> {
  return api.get<NotionStatus>('/automation/status')
}

/**
 * Get research queue
 */
export async function getQueue(
  limit = 20
): Promise<{ items: QueueItem[]; total: number }> {
  return api.get<{ items: QueueItem[]; total: number }>('/automation/queue', {
    limit: String(limit),
  })
}

/**
 * Trigger research for a queue item
 */
export async function triggerResearch(
  itemId: string
): Promise<{ job_id: string; item_id: string; message: string }> {
  return api.post<{ job_id: string; item_id: string; message: string }>(
    `/automation/trigger/${itemId}`
  )
}

/**
 * Get recent completion history
 */
export async function getHistory(
  limit = 20
): Promise<{ items: HistoryItem[]; total: number }> {
  return api.get<{ items: HistoryItem[]; total: number }>('/automation/history', {
    limit: String(limit),
  })
}

/**
 * Get workflow configuration
 */
export async function getWorkflowConfig(): Promise<WorkflowConfig> {
  return api.get<WorkflowConfig>('/automation/config')
}

/**
 * Update workflow configuration
 */
export async function updateWorkflowConfig(
  config: WorkflowConfig
): Promise<WorkflowConfig> {
  return api.put<WorkflowConfig>('/automation/config', config)
}

/**
 * Force sync with Notion
 */
export async function forceSync(): Promise<{ message: string; next_auto_sync_in_seconds: number }> {
  return api.post<{ message: string; next_auto_sync_in_seconds: number }>('/automation/sync')
}
