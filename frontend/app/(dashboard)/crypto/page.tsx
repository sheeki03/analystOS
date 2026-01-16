'use client'

import { useState, useEffect } from 'react'
import { PageContainer, PageHeader, PageSection, Grid } from '@/components/layout'
import {
  ChatInterface,
  PriceCard,
  PriceChart,
  TrendingList,
  MarketOverview,
  CoinSearch,
} from '@/components/crypto'
import { Tabs, TabsList, TabsTrigger, TabsContent, Badge } from '@/components/ui'
import { MessageSquare, TrendingUp, BarChart3, Search } from 'lucide-react'
import { cryptoApi } from '@/lib/api'
import type { CoinPrice, TrendingCoin, MarketData } from '@/types'

export default function CryptoPage() {
  const [watchlist, setWatchlist] = useState<string[]>(['bitcoin', 'ethereum', 'solana'])
  const [prices, setPrices] = useState<Record<string, CoinPrice>>({})
  const [trending, setTrending] = useState<TrendingCoin[]>([])
  const [marketData, setMarketData] = useState<MarketData | null>(null)
  const [selectedCoin, setSelectedCoin] = useState<string>('bitcoin')
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'chat' | 'market' | 'search'>('chat')

  useEffect(() => {
    loadMarketData()
    const interval = setInterval(loadMarketData, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (watchlist.length > 0) {
      loadPrices()
    }
  }, [watchlist])

  const loadMarketData = async () => {
    try {
      const [trendingData, overview] = await Promise.all([
        cryptoApi.getTrending(),
        cryptoApi.getMarketOverview(),
      ])
      setTrending(trendingData)
      setMarketData(overview)
    } catch (error) {
      console.error('Failed to load market data:', error)
    }
  }

  const loadPrices = async () => {
    try {
      setIsLoading(true)
      const pricePromises = watchlist.map(async (coinId) => {
        const price = await cryptoApi.getPrice(coinId)
        return [coinId, price] as const
      })
      const results = await Promise.all(pricePromises)
      setPrices(Object.fromEntries(results))
    } catch (error) {
      console.error('Failed to load prices:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const addToWatchlist = (coinId: string) => {
    if (!watchlist.includes(coinId)) {
      setWatchlist([...watchlist, coinId])
    }
  }

  const removeFromWatchlist = (coinId: string) => {
    setWatchlist(watchlist.filter((id) => id !== coinId))
  }

  return (
    <PageContainer>
      <PageHeader
        title="Crypto AI Assistant"
        description="Real-time market data, AI-powered insights, and portfolio tracking"
        actions={
          marketData && (
            <Badge variant={marketData.market_cap_change_24h >= 0 ? 'success' : 'danger'}>
              Market {marketData.market_cap_change_24h >= 0 ? '↑' : '↓'}{' '}
              {Math.abs(marketData.market_cap_change_24h).toFixed(2)}%
            </Badge>
          )
        }
      />

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList className="mb-6">
          <TabsTrigger value="chat">
            <MessageSquare className="h-4 w-4 mr-2" />
            AI Chat
          </TabsTrigger>
          <TabsTrigger value="market">
            <BarChart3 className="h-4 w-4 mr-2" />
            Market
          </TabsTrigger>
          <TabsTrigger value="search">
            <Search className="h-4 w-4 mr-2" />
            Search
          </TabsTrigger>
        </TabsList>

        <TabsContent value="chat">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Chat Interface */}
            <div className="lg:col-span-2">
              <ChatInterface selectedCoin={selectedCoin} />
            </div>

            {/* Right Column - Price Cards & Trending */}
            <div className="space-y-6">
              <PageSection title="Watchlist">
                <div className="space-y-3">
                  {isLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <div
                        key={i}
                        className="h-24 rounded-terminal bg-bg-elevated animate-pulse"
                      />
                    ))
                  ) : (
                    watchlist.map((coinId) => (
                      <PriceCard
                        key={coinId}
                        coinId={coinId}
                        price={prices[coinId]}
                        isSelected={selectedCoin === coinId}
                        onClick={() => setSelectedCoin(coinId)}
                        onRemove={() => removeFromWatchlist(coinId)}
                      />
                    ))
                  )}
                </div>
              </PageSection>

              <PageSection title="Trending">
                <TrendingList
                  coins={trending}
                  onSelect={(coinId) => {
                    addToWatchlist(coinId)
                    setSelectedCoin(coinId)
                  }}
                />
              </PageSection>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="market">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <PageSection title="Price Chart">
                <PriceChart coinId={selectedCoin} />
              </PageSection>
            </div>

            <div>
              <PageSection title="Market Overview">
                <MarketOverview data={marketData} />
              </PageSection>
            </div>
          </div>

          <div className="mt-6">
            <PageSection title="Watchlist Performance">
              <Grid cols={4} gap="md">
                {watchlist.map((coinId) => (
                  <PriceCard
                    key={coinId}
                    coinId={coinId}
                    price={prices[coinId]}
                    isSelected={selectedCoin === coinId}
                    onClick={() => setSelectedCoin(coinId)}
                    compact
                  />
                ))}
              </Grid>
            </PageSection>
          </div>
        </TabsContent>

        <TabsContent value="search">
          <CoinSearch
            onSelect={(coinId) => {
              addToWatchlist(coinId)
              setSelectedCoin(coinId)
              setActiveTab('chat')
            }}
          />
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
