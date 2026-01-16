'use client'

import { useState, useEffect } from 'react'
import { PageContainer, PageHeader, PageSection, Grid } from '@/components/layout'
import {
  DocumentUpload,
  UrlInput,
  ModelSelector,
  ReportViewer,
  EntityPanel,
  ChatPanel,
  ReportCard,
} from '@/components/research'
import { Button, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui'
import { Plus, FileText, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { researchApi } from '@/lib/api'
import type { Report, Job } from '@/types'

export default function ResearchPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [activeJobs, setActiveJobs] = useState<Job[]>([])
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [activeTab, setActiveTab] = useState<'new' | 'reports'>('new')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      setIsLoading(true)
      const data = await researchApi.getReports()
      setReports(data)
    } catch (error) {
      console.error('Failed to load reports:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleJobCreated = (job: Job) => {
    setActiveJobs((prev) => [...prev, job])
    // Poll for job status
    pollJobStatus(job.id)
  }

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const status = await researchApi.getJobStatus(jobId)
        setActiveJobs((prev) =>
          prev.map((j) => (j.id === jobId ? { ...j, ...status } : j))
        )

        if (status.status === 'completed') {
          // Reload reports
          loadReports()
          // Remove from active jobs after a delay
          setTimeout(() => {
            setActiveJobs((prev) => prev.filter((j) => j.id !== jobId))
          }, 3000)
        } else if (status.status === 'failed') {
          setTimeout(() => {
            setActiveJobs((prev) => prev.filter((j) => j.id !== jobId))
          }, 5000)
        } else {
          // Continue polling
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
      }
    }
    poll()
  }

  return (
    <PageContainer>
      <PageHeader
        title="Interactive Research"
        description="Upload documents, analyze URLs, and generate AI-powered reports"
        actions={
          <div className="flex items-center gap-2">
            {activeJobs.length > 0 && (
              <Badge variant="secondary">
                <Clock className="h-3 w-3 mr-1" />
                {activeJobs.length} job{activeJobs.length > 1 ? 's' : ''} running
              </Badge>
            )}
          </div>
        }
      />

      {/* Active Jobs Status Bar */}
      {activeJobs.length > 0 && (
        <div className="mb-6 space-y-2">
          {activeJobs.map((job) => (
            <JobStatusBar key={job.id} job={job} />
          ))}
        </div>
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'new' | 'reports')}>
        <TabsList className="mb-6">
          <TabsTrigger value="new">
            <Plus className="h-4 w-4 mr-2" />
            New Research
          </TabsTrigger>
          <TabsTrigger value="reports">
            <FileText className="h-4 w-4 mr-2" />
            Reports
            {reports.length > 0 && (
              <Badge variant="muted" className="ml-2">
                {reports.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="new">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Input Methods */}
            <div className="lg:col-span-2 space-y-6">
              <PageSection title="Document Upload" description="Upload PDF, DOCX, or TXT files for analysis">
                <DocumentUpload onJobCreated={handleJobCreated} />
              </PageSection>

              <PageSection title="URL Analysis" description="Analyze web pages and extract insights">
                <UrlInput onJobCreated={handleJobCreated} />
              </PageSection>

              <PageSection title="Generate Report" description="Create a comprehensive research report">
                <ModelSelector onJobCreated={handleJobCreated} />
              </PageSection>
            </div>

            {/* Right Column - Chat */}
            <div className="lg:col-span-1">
              <PageSection title="Research Assistant" description="Ask questions about your documents">
                <ChatPanel />
              </PageSection>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="reports">
          {selectedReport ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ReportViewer
                  report={selectedReport}
                  onClose={() => setSelectedReport(null)}
                />
              </div>
              <div className="lg:col-span-1">
                <EntityPanel report={selectedReport} />
              </div>
            </div>
          ) : (
            <Grid cols={3} gap="md">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-48 rounded-terminal bg-bg-elevated animate-pulse"
                  />
                ))
              ) : reports.length === 0 ? (
                <div className="col-span-full text-center py-12">
                  <FileText className="h-12 w-12 text-text-muted mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-text-primary mb-2">
                    No reports yet
                  </h3>
                  <p className="text-text-muted mb-4">
                    Upload a document or analyze a URL to create your first report
                  </p>
                  <Button onClick={() => setActiveTab('new')}>
                    <Plus className="h-4 w-4 mr-2" />
                    Start New Research
                  </Button>
                </div>
              ) : (
                reports.map((report) => (
                  <ReportCard
                    key={report.id}
                    report={report}
                    onClick={() => setSelectedReport(report)}
                  />
                ))
              )}
            </Grid>
          )}
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}

function JobStatusBar({ job }: { job: Job }) {
  const getStatusIcon = () => {
    switch (job.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-accent-success" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-accent-danger" />
      default:
        return (
          <div className="h-4 w-4 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" />
        )
    }
  }

  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-terminal bg-bg-surface border border-border-default">
      {getStatusIcon()}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">
          {job.type === 'upload' && 'Processing document...'}
          {job.type === 'scrape' && 'Analyzing URL...'}
          {job.type === 'generate' && 'Generating report...'}
        </p>
        {job.progress !== undefined && job.status === 'processing' && (
          <div className="mt-1 h-1 bg-bg-elevated rounded-full overflow-hidden">
            <div
              className="h-full bg-accent-primary transition-all duration-300"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        )}
      </div>
      <Badge
        variant={
          job.status === 'completed'
            ? 'success'
            : job.status === 'failed'
            ? 'danger'
            : 'secondary'
        }
      >
        {job.status}
      </Badge>
    </div>
  )
}
