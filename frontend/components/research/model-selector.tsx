'use client'

import { useState } from 'react'
import { Sparkles, Zap, Brain, AlertCircle, Loader2 } from 'lucide-react'
import { Button, Textarea } from '@/components/ui'
import { cn } from '@/lib/utils'
import { researchApi } from '@/lib/api'
import type { Job } from '@/types'

interface ModelSelectorProps {
  onJobCreated: (job: Job) => void
}

interface Model {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  speed: 'fast' | 'medium' | 'slow'
  quality: 'good' | 'better' | 'best'
}

const MODELS: Model[] = [
  {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    description: 'Fast and efficient for most tasks',
    icon: <Zap className="h-5 w-5" />,
    speed: 'fast',
    quality: 'good',
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    description: 'Balanced speed and intelligence',
    icon: <Sparkles className="h-5 w-5" />,
    speed: 'medium',
    quality: 'better',
  },
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    description: 'Best for complex analysis',
    icon: <Brain className="h-5 w-5" />,
    speed: 'slow',
    quality: 'best',
  },
]

export function ModelSelector({ onJobCreated }: ModelSelectorProps) {
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o')
  const [prompt, setPrompt] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!prompt.trim()) {
      setError('Please enter a research topic or question')
      return
    }

    setIsSubmitting(true)

    try {
      const job = await researchApi.generate(prompt.trim(), selectedModel)
      onJobCreated(job)
      setPrompt('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Model Selection */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-2">
          Select Model
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {MODELS.map((model) => (
            <ModelCard
              key={model.id}
              model={model}
              isSelected={selectedModel === model.id}
              onClick={() => setSelectedModel(model.id)}
            />
          ))}
        </div>
      </div>

      {/* Research Prompt */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-2">
          Research Topic
        </label>
        <Textarea
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value)
            setError(null)
          }}
          placeholder="Enter a topic, question, or description for your research report..."
          rows={4}
          disabled={isSubmitting}
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-terminal bg-accent-danger/10 border border-accent-danger/20">
          <AlertCircle className="h-4 w-4 text-accent-danger flex-shrink-0" />
          <p className="text-sm text-accent-danger">{error}</p>
        </div>
      )}

      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting || !prompt.trim()}
      >
        {isSubmitting ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Generating Report...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 mr-2" />
            Generate Report
          </>
        )}
      </Button>
    </form>
  )
}

interface ModelCardProps {
  model: Model
  isSelected: boolean
  onClick: () => void
}

function ModelCard({ model, isSelected, onClick }: ModelCardProps) {
  const speedColors = {
    fast: 'bg-accent-success',
    medium: 'bg-accent-secondary',
    slow: 'bg-accent-primary',
  }

  const qualityLabels = {
    good: 'Good',
    better: 'Better',
    best: 'Best',
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative p-4 rounded-terminal border text-left transition-all',
        isSelected
          ? 'border-accent-primary bg-accent-primary/10'
          : 'border-border-default hover:border-text-muted hover:bg-bg-elevated'
      )}
    >
      <div
        className={cn(
          'w-10 h-10 rounded-terminal flex items-center justify-center mb-3',
          isSelected
            ? 'bg-accent-primary/20 text-accent-primary'
            : 'bg-bg-elevated text-text-muted'
        )}
      >
        {model.icon}
      </div>
      <h3 className="font-medium text-text-primary text-sm">{model.name}</h3>
      <p className="text-xs text-text-muted mt-1">{model.description}</p>

      <div className="flex items-center gap-2 mt-3">
        <div className="flex items-center gap-1">
          <span className={cn('w-2 h-2 rounded-full', speedColors[model.speed])} />
          <span className="text-xs text-text-muted capitalize">{model.speed}</span>
        </div>
        <span className="text-text-muted">·</span>
        <span className="text-xs text-text-muted">{qualityLabels[model.quality]}</span>
      </div>

      {isSelected && (
        <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-accent-primary" />
      )}
    </button>
  )
}
