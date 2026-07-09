'use client'

import { useState, useEffect } from 'react'
import { PageContainer, PageHeader, PageSection, Grid } from '@/components/layout'
import {
  WorkflowCard,
  QueueList,
  StatusIndicator,
  HistoryList,
} from '@/components/automation'
import { Button, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui'
import { RefreshCw, Play, Clock, CheckCircle, ListTodo, History } from 'lucide-react'
import { automationApi } from '@/lib/api'
import type { AutomationStatus, QueueItem, AutomationHistory } from '@/types'

export default function AutomationPage() {
  const [status, setStatus] = useState<AutomationStatus | null>(null)
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [history, setHistory] = useState<AutomationHistory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'queue' | 'history'>('overview')

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      setIsLoading(true)
      const [statusData, queueData, historyData] = await Promise.all([
        automationApi.getStatus(),
        automationApi.getQueue(),
        automationApi.getHistory(),
      ])
      setStatus(statusData)
      setQueue(queueData)
      setHistory(historyData)
    } catch (error) {
      console.error('Failed to load automation data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await loadData()
    setIsRefreshing(false)
  }

  const handleTrigger = async (itemId: string) => {
    try {
      await automationApi.trigger(itemId)
      // Reload queue
      const queueData = await automationApi.getQueue()
      setQueue(queueData)
    } catch (error) {
      console.error('Failed to trigger automation:', error)
    }
  }

  const completedCount = history.filter((h) => h.status === 'completed').length
  const failedCount = history.filter((h) => h.status === 'failed').length

  return (
    <PageContainer>
      <PageHeader
        title="Notion Automation"
        description="Automate your Notion workflows and track processing status"
        actions={
          <div className="flex items-center gap-3">
            {status && (
              <Badge variant={status.is_running ? 'success' : 'secondary'}>
                {status.is_running ? 'Running' : 'Idle'}
              </Badge>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`}
              />
              Refresh
            </Button>
          </div>
        }
      />

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatusCard
          title="Status"
          value={status?.is_running ? 'Active' : 'Idle'}
          icon={<StatusIndicator status={status?.is_running ? 'running' : 'idle'} />}
          variant={status?.is_running ? 'success' : 'default'}
        />
        <StatusCard
          title="Queue"
          value={queue.length.toString()}
          icon={<ListTodo className="h-5 w-5" />}
          variant={queue.length > 0 ? 'warning' : 'default'}
        />
        <StatusCard
          title="Completed"
          value={completedCount.toString()}
          icon={<CheckCircle className="h-5 w-5" />}
          variant="success"
        />
        <StatusCard
          title="Last Run"
          value={status?.last_run ? formatRelativeTime(status.last_run) : 'Never'}
          icon={<Clock className="h-5 w-5" />}
        />
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList className="mb-6">
          <TabsTrigger value="overview">
            <Play className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="queue">
            <ListTodo className="h-4 w-4 mr-2" />
            Queue
            {queue.length > 0 && (
              <Badge variant="warning" className="ml-2">
                {queue.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history">
            <History className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Grid cols={2} gap="lg">
            <PageSection title="Workflows" description="Available automation workflows">
              <div className="space-y-4">
                <WorkflowCard
                  title="Process New Items"
                  description="Automatically process new items added to your Notion database"
                  status={status?.is_running ? 'running' : 'idle'}
                  lastRun={status?.last_run}
                  onTrigger={() => handleTrigger('process_new')}
                />
                <WorkflowCard
                  title="Sync Updates"
                  description="Sync changes between your Notion databases"
                  status="idle"
                  onTrigger={() => handleTrigger('sync_updates')}
                />
                <WorkflowCard
                  title="Generate Summaries"
                  description="Create AI-powered summaries for your documents"
                  status="idle"
                  onTrigger={() => handleTrigger('generate_summaries')}
                />
              </div>
            </PageSection>

            <PageSection title="Recent Activity" description="Latest automation runs">
              <HistoryList history={history.slice(0, 5)} compact />
            </PageSection>
          </Grid>
        </TabsContent>

        <TabsContent value="queue">
          <PageSection
            title="Processing Queue"
            description="Items waiting to be processed"
          >
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-16 rounded-terminal bg-bg-elevated animate-pulse"
                  />
                ))}
              </div>
            ) : queue.length === 0 ? (
              <div className="text-center py-12">
                <ListTodo className="h-12 w-12 text-text-muted mx-auto mb-4" />
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  Queue is empty
                </h3>
                <p className="text-text-muted">
                  All items have been processed. New items will appear here automatically.
                </p>
              </div>
            ) : (
              <QueueList queue={queue} onTrigger={handleTrigger} />
            )}
          </PageSection>
        </TabsContent>

        <TabsContent value="history">
          <PageSection
            title="Automation History"
            description="Complete history of automation runs"
          >
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-16 rounded-terminal bg-bg-elevated animate-pulse"
                  />
                ))}
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-12">
                <History className="h-12 w-12 text-text-muted mx-auto mb-4" />
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  No history yet
                </h3>
                <p className="text-text-muted">
                  Run an automation to start tracking history.
                </p>
              </div>
            ) : (
              <HistoryList history={history} />
            )}
          </PageSection>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}

interface StatusCardProps {
  title: string
  value: string
  icon: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

function StatusCard({ title, value, icon, variant = 'default' }: StatusCardProps) {
  const variantClasses = {
    default: 'text-text-muted',
    success: 'text-accent-success',
    warning: 'text-accent-secondary',
    danger: 'text-accent-danger',
  }

  return (
    <div className="p-4 rounded-terminal bg-bg-surface border border-border-default">
      <div className="flex items-center justify-between">
        <span className="text-sm text-text-muted">{title}</span>
        <span className={variantClasses[variant]}>{icon}</span>
      </div>
      <p className="mt-2 text-2xl font-mono font-semibold text-text-primary">{value}</p>
    </div>
  )
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  return `${Math.floor(diffInSeconds / 86400)}d ago`
}
