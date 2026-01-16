// ============================================================================
// Authentication Types
// ============================================================================

export interface User {
  user_id: string
  username: string
  email?: string
  role: string
  created_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface RefreshResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// ============================================================================
// Job Types
// ============================================================================

export type JobStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'retrying'

export type JobType = 'upload' | 'scrape' | 'generate' | 'extract_entities'

export interface Job {
  job_id: string
  user_id: string
  job_type: JobType
  status: JobStatus
  progress: number
  result_path?: string
  error?: string
  attempts: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface JobCreatedResponse {
  job_id: string
  job_type: JobType
  status: JobStatus
  message: string
}

// ============================================================================
// Research Types
// ============================================================================

export interface UploadResponse {
  job_id: string
  filenames: string[]
  message: string
}

export interface ScrapeRequest {
  urls?: string[]
  sitemap_url?: string
}

export interface ScrapeResponse {
  job_id: string
  url_count: number
  message: string
}

export interface GenerateRequest {
  model: string
  sources: string[]
  query?: string
}

export interface GenerateResponse {
  job_id: string
  model: string
  source_count: number
  message: string
}

export interface ReportSummary {
  report_id: string
  title: string
  model: string
  source_count: number
  created_at: string
  word_count?: number
}

export interface ReportDetail {
  report_id: string
  title: string
  model: string
  content: string
  sources: string[]
  entities?: EntityExtractionResult
  created_at: string
  word_count: number
}

export interface ExtractedEntity {
  entity_type: string
  name: string
  description?: string
  confidence: number
  source_refs: string[]
}

export interface EntityExtractionResult {
  people: ExtractedEntity[]
  organizations: ExtractedEntity[]
  technologies: ExtractedEntity[]
  locations: ExtractedEntity[]
  other: ExtractedEntity[]
}

// ============================================================================
// Crypto Types
// ============================================================================

export interface CoinPrice {
  coin_id: string
  name: string
  symbol: string
  current_price: number
  price_change_24h: number
  price_change_percentage_24h: number
  market_cap: number
  volume_24h: number
  last_updated: string
}

export interface TrendingCoin {
  coin_id: string
  name: string
  symbol: string
  market_cap_rank?: number
  price_btc: number
  score: number
}

export interface SearchResult {
  coin_id: string
  name: string
  symbol: string
  market_cap_rank?: number
  thumb?: string
}

export interface MarketOverview {
  total_market_cap: number
  total_volume_24h: number
  btc_dominance: number
  eth_dominance: number
  active_cryptocurrencies: number
  markets: number
  market_cap_change_24h: number
}

export interface HistoricalDataPoint {
  timestamp: number
  price: number
  volume?: number
  market_cap?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

// ============================================================================
// Automation Types
// ============================================================================

export interface NotionStatus {
  connected: boolean
  workspace_name?: string
  database_id?: string
  last_sync?: string
  sync_interval_minutes: number
  error?: string
}

export interface QueueItem {
  item_id: string
  title: string
  status: string
  priority?: string
  created_at: string
  source_type?: string
  source_url?: string
}

export interface HistoryItem {
  item_id: string
  title: string
  completed_at: string
  score?: number
  score_breakdown?: Record<string, number>
  report_id?: string
  duration_seconds?: number
}

export interface WorkflowConfig {
  auto_process: boolean
  default_model: string
  auto_score: boolean
  notify_on_complete: boolean
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiError {
  detail: string
  error_code?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string | number
}

export interface ModelOption {
  id: string
  name: string
  provider: string
  isFree?: boolean
}

// Model options from backend config
export const AI_MODEL_OPTIONS: ModelOption[] = [
  { id: 'openai/gpt-5.2', name: 'GPT-5.2', provider: 'OpenAI' },
  { id: 'openai/gpt-5.2-pro', name: 'GPT-5.2 Pro', provider: 'OpenAI' },
  { id: 'anthropic/claude-sonnet-4.5', name: 'Claude Sonnet 4.5', provider: 'Anthropic' },
  { id: 'anthropic/claude-opus-4.5', name: 'Claude Opus 4.5', provider: 'Anthropic' },
  { id: 'google/gemini-3', name: 'Gemini 3', provider: 'Google' },
  { id: 'google/gemini-2.5-pro', name: 'Gemini 2.5 Pro', provider: 'Google' },
  { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google' },
  { id: 'qwen/qwen3-30b-a3b:free', name: 'Qwen3 30B', provider: 'Qwen', isFree: true },
  { id: 'qwen/qwen3-235b-a22b:free', name: 'Qwen3 235B', provider: 'Qwen', isFree: true },
  { id: 'tngtech/deepseek-r1t-chimera:free', name: 'DeepSeek R1T Chimera', provider: 'DeepSeek', isFree: true },
]
