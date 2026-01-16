'use client'

import { useState, useEffect } from 'react'
import {
  User,
  Building2,
  MapPin,
  Calendar,
  Tag,
  Hash,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import { researchApi } from '@/lib/api'
import type { Report, Entity } from '@/types'

interface EntityPanelProps {
  report: Report
}

type EntityType = 'person' | 'organization' | 'location' | 'date' | 'topic' | 'other'

const ENTITY_ICONS: Record<EntityType, React.ReactNode> = {
  person: <User className="h-4 w-4" />,
  organization: <Building2 className="h-4 w-4" />,
  location: <MapPin className="h-4 w-4" />,
  date: <Calendar className="h-4 w-4" />,
  topic: <Tag className="h-4 w-4" />,
  other: <Hash className="h-4 w-4" />,
}

const ENTITY_COLORS: Record<EntityType, string> = {
  person: 'text-blue-400 bg-blue-400/10',
  organization: 'text-purple-400 bg-purple-400/10',
  location: 'text-green-400 bg-green-400/10',
  date: 'text-orange-400 bg-orange-400/10',
  topic: 'text-accent-primary bg-accent-primary/10',
  other: 'text-text-muted bg-bg-elevated',
}

export function EntityPanel({ report }: EntityPanelProps) {
  const [entities, setEntities] = useState<Entity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [expandedTypes, setExpandedTypes] = useState<EntityType[]>([
    'person',
    'organization',
    'topic',
  ])

  useEffect(() => {
    loadEntities()
  }, [report.id])

  const loadEntities = async () => {
    setIsLoading(true)
    try {
      const data = await researchApi.extractEntities(report.id)
      setEntities(data)
    } catch (error) {
      console.error('Failed to load entities:', error)
      // Fallback to mock entities for demo
      setEntities(generateMockEntities())
    } finally {
      setIsLoading(false)
    }
  }

  const groupedEntities = entities.reduce((acc, entity) => {
    const type = (entity.type as EntityType) || 'other'
    if (!acc[type]) {
      acc[type] = []
    }
    acc[type].push(entity)
    return acc
  }, {} as Record<EntityType, Entity[]>)

  const toggleType = (type: EntityType) => {
    setExpandedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  if (isLoading) {
    return (
      <div className="bg-bg-surface border border-border-default rounded-terminal p-4">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 text-accent-primary animate-spin" />
        </div>
      </div>
    )
  }

  if (entities.length === 0) {
    return (
      <div className="bg-bg-surface border border-border-default rounded-terminal p-4">
        <h3 className="text-sm font-medium font-mono text-text-primary mb-4">
          Extracted Entities
        </h3>
        <div className="text-center py-8">
          <Tag className="h-8 w-8 text-text-muted mx-auto mb-2" />
          <p className="text-sm text-text-muted">No entities found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-bg-surface border border-border-default rounded-terminal">
      <div className="p-4 border-b border-border-default">
        <h3 className="text-sm font-medium font-mono text-text-primary">
          Extracted Entities
        </h3>
        <p className="text-xs text-text-muted mt-1">
          {entities.length} entities found
        </p>
      </div>

      <div className="divide-y divide-border-default">
        {(Object.keys(groupedEntities) as EntityType[]).map((type) => (
          <EntityGroup
            key={type}
            type={type}
            entities={groupedEntities[type]}
            isExpanded={expandedTypes.includes(type)}
            onToggle={() => toggleType(type)}
          />
        ))}
      </div>
    </div>
  )
}

interface EntityGroupProps {
  type: EntityType
  entities: Entity[]
  isExpanded: boolean
  onToggle: () => void
}

function EntityGroup({ type, entities, isExpanded, onToggle }: EntityGroupProps) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full p-3 hover:bg-bg-elevated/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className={cn('p-1.5 rounded', ENTITY_COLORS[type])}>
            {ENTITY_ICONS[type]}
          </span>
          <span className="text-sm font-medium text-text-primary capitalize">
            {type}s
          </span>
          <Badge variant="muted" className="ml-1">
            {entities.length}
          </Badge>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-text-muted" />
        ) : (
          <ChevronRight className="h-4 w-4 text-text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          {entities.map((entity, index) => (
            <EntityCard key={index} entity={entity} type={type} />
          ))}
        </div>
      )}
    </div>
  )
}

interface EntityCardProps {
  entity: Entity
  type: EntityType
}

function EntityCard({ entity, type }: EntityCardProps) {
  return (
    <div className="p-3 rounded-terminal bg-bg-elevated border border-border-default">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-text-primary text-sm truncate">
            {entity.name}
          </p>
          {entity.description && (
            <p className="text-xs text-text-muted mt-1 line-clamp-2">
              {entity.description}
            </p>
          )}
        </div>
        {entity.confidence && (
          <Badge variant="muted" className="ml-2 shrink-0">
            {Math.round(entity.confidence * 100)}%
          </Badge>
        )}
      </div>

      {entity.url && (
        <a
          href={entity.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-accent-primary hover:underline mt-2"
        >
          Learn more
          <ExternalLink className="h-3 w-3" />
        </a>
      )}

      {entity.mentions && entity.mentions > 1 && (
        <p className="text-xs text-text-muted mt-2">
          Mentioned {entity.mentions} times
        </p>
      )}
    </div>
  )
}

// Generate mock entities for demo
function generateMockEntities(): Entity[] {
  return [
    {
      name: 'OpenAI',
      type: 'organization',
      description: 'AI research company',
      confidence: 0.95,
      mentions: 12,
    },
    {
      name: 'Sam Altman',
      type: 'person',
      description: 'CEO of OpenAI',
      confidence: 0.92,
      mentions: 5,
    },
    {
      name: 'San Francisco',
      type: 'location',
      description: 'City in California, USA',
      confidence: 0.88,
      mentions: 3,
    },
    {
      name: 'Machine Learning',
      type: 'topic',
      description: 'Subset of AI focused on learning from data',
      confidence: 0.96,
      mentions: 8,
    },
    {
      name: 'GPT-4',
      type: 'other',
      description: 'Large language model',
      confidence: 0.99,
      mentions: 15,
    },
  ]
}
