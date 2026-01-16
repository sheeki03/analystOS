'use client'

import { useState, useEffect, useCallback } from 'react'
import { Search, Plus, Loader2, X, TrendingUp, TrendingDown } from 'lucide-react'
import { Input, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import { cryptoApi } from '@/lib/api'
import { formatCurrency, formatPercent } from '@/lib/utils/formatters'
import { useDebounce } from '@/lib/hooks/use-debounce'

interface CoinSearchProps {
  onSelect: (coinId: string) => void
}

interface SearchResult {
  id: string
  name: string
  symbol: string
  thumb?: string
  market_cap_rank?: number
  price?: number
  change_24h?: number
}

export function CoinSearch({ onSelect }: CoinSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const debouncedQuery = useDebounce(query, 300)

  useEffect(() => {
    if (debouncedQuery.trim()) {
      searchCoins(debouncedQuery)
    } else {
      setResults([])
      setHasSearched(false)
    }
  }, [debouncedQuery])

  const searchCoins = async (searchQuery: string) => {
    setIsLoading(true)
    setHasSearched(true)
    try {
      const data = await cryptoApi.search(searchQuery)
      setResults(data.coins || [])
    } catch (error) {
      console.error('Search failed:', error)
      // Fallback to mock results
      setResults(generateMockResults(searchQuery))
    } finally {
      setIsLoading(false)
    }
  }

  const clearSearch = () => {
    setQuery('')
    setResults([])
    setHasSearched(false)
  }

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
          <Search className="h-4 w-4" />
        </div>
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for a cryptocurrency..."
          className="pl-10 pr-10"
        />
        {query && (
          <button
            onClick={clearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 text-accent-primary animate-spin" />
        </div>
      )}

      {/* Results */}
      {!isLoading && results.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-text-muted">
            Found {results.length} result{results.length > 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {results.map((coin) => (
              <SearchResultCard
                key={coin.id}
                coin={coin}
                onSelect={() => onSelect(coin.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && hasSearched && results.length === 0 && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">
            No results found
          </h3>
          <p className="text-text-muted">
            Try searching for a different cryptocurrency
          </p>
        </div>
      )}

      {/* Initial State */}
      {!isLoading && !hasSearched && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">
            Search for cryptocurrencies
          </h3>
          <p className="text-text-muted">
            Enter a coin name or symbol to find it
          </p>

          {/* Popular Searches */}
          <div className="mt-6">
            <p className="text-sm text-text-muted mb-3">Popular searches:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {['Bitcoin', 'Ethereum', 'Solana', 'Cardano', 'Polygon'].map(
                (coin) => (
                  <button
                    key={coin}
                    onClick={() => setQuery(coin)}
                    className="px-3 py-1.5 rounded-terminal bg-bg-elevated text-sm text-text-secondary hover:text-text-primary hover:bg-bg-elevated/80 transition-colors"
                  >
                    {coin}
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface SearchResultCardProps {
  coin: SearchResult
  onSelect: () => void
}

function SearchResultCard({ coin, onSelect }: SearchResultCardProps) {
  const isPositive = coin.change_24h !== undefined ? coin.change_24h >= 0 : true

  return (
    <div
      onClick={onSelect}
      className={cn(
        'p-4 rounded-terminal border cursor-pointer transition-all group',
        'border-border-default hover:border-text-muted hover:bg-bg-elevated/50'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {coin.thumb ? (
            <img
              src={coin.thumb}
              alt={coin.name}
              className="w-10 h-10 rounded-full"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-accent-primary/20 flex items-center justify-center">
              <span className="text-sm font-bold text-accent-primary">
                {coin.symbol.charAt(0)}
              </span>
            </div>
          )}
          <div>
            <h3 className="font-medium text-text-primary group-hover:text-accent-primary transition-colors">
              {coin.name}
            </h3>
            <p className="text-sm text-text-muted">{coin.symbol.toUpperCase()}</p>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onSelect()
          }}
          className="p-2 rounded-terminal bg-accent-primary/10 text-accent-primary opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      {/* Price Info */}
      {coin.price && (
        <div className="mt-3 pt-3 border-t border-border-default flex items-center justify-between">
          <span className="text-lg font-mono font-semibold text-text-primary">
            {formatCurrency(coin.price)}
          </span>
          {coin.change_24h !== undefined && (
            <span
              className={cn(
                'flex items-center gap-1 text-sm font-mono',
                isPositive ? 'text-accent-success' : 'text-accent-danger'
              )}
            >
              {isPositive ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {isPositive ? '+' : ''}
              {coin.change_24h.toFixed(2)}%
            </span>
          )}
        </div>
      )}

      {/* Market Cap Rank */}
      {coin.market_cap_rank && (
        <Badge variant="muted" className="mt-2">
          Rank #{coin.market_cap_rank}
        </Badge>
      )}
    </div>
  )
}

function generateMockResults(query: string): SearchResult[] {
  const allCoins: SearchResult[] = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC', market_cap_rank: 1, price: 45000, change_24h: 2.5 },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH', market_cap_rank: 2, price: 2800, change_24h: -1.2 },
    { id: 'solana', name: 'Solana', symbol: 'SOL', market_cap_rank: 5, price: 120, change_24h: 5.8 },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA', market_cap_rank: 8, price: 0.55, change_24h: -0.8 },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT', market_cap_rank: 12, price: 7.5, change_24h: 1.2 },
    { id: 'polygon', name: 'Polygon', symbol: 'MATIC', market_cap_rank: 15, price: 0.85, change_24h: 3.1 },
    { id: 'chainlink', name: 'Chainlink', symbol: 'LINK', market_cap_rank: 18, price: 15, change_24h: -2.3 },
    { id: 'avalanche', name: 'Avalanche', symbol: 'AVAX', market_cap_rank: 10, price: 35, change_24h: 4.5 },
  ]

  const lowerQuery = query.toLowerCase()
  return allCoins.filter(
    (coin) =>
      coin.name.toLowerCase().includes(lowerQuery) ||
      coin.symbol.toLowerCase().includes(lowerQuery)
  )
}
