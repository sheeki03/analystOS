/**
 * Crypto API functions
 */

import { api } from './client'
import type {
  CoinPrice,
  TrendingCoin,
  SearchResult,
  MarketOverview,
  HistoricalDataPoint,
  ChatMessage,
} from '@/types'

/**
 * Get coin price
 */
export async function getCoinPrice(coinId: string): Promise<CoinPrice> {
  return api.get<CoinPrice>(`/crypto/price/${coinId}`)
}

/**
 * Get trending coins
 */
export async function getTrending(): Promise<{ coins: TrendingCoin[] }> {
  return api.get<{ coins: TrendingCoin[] }>('/crypto/trending')
}

/**
 * Search coins
 */
export async function searchCoins(query: string): Promise<{ coins: SearchResult[] }> {
  return api.get<{ coins: SearchResult[] }>('/crypto/search', { q: query })
}

/**
 * Get market overview
 */
export async function getMarketOverview(): Promise<MarketOverview> {
  return api.get<MarketOverview>('/crypto/market-overview')
}

/**
 * Get historical price data
 */
export async function getHistorical(
  coinId: string,
  days = 7
): Promise<{ coin_id: string; prices: HistoricalDataPoint[]; days: number }> {
  return api.get<{ coin_id: string; prices: HistoricalDataPoint[]; days: number }>(
    `/crypto/historical/${coinId}`,
    { days: String(days) }
  )
}

/**
 * Send chat message
 */
export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = [],
  context?: Record<string, unknown>
): Promise<{ message: string; context?: Record<string, unknown> }> {
  return api.post<{ message: string; context?: Record<string, unknown> }>('/crypto/chat', {
    message,
    history,
    context,
  })
}
