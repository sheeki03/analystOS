'use client'

import { TrendingUp, Flame, Plus } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import type { TrendingCoin } from '@/types'

interface TrendingListProps {
  coins: TrendingCoin[]
  onSelect: (coinId: string) => void
}

export function TrendingList({ coins, onSelect }: TrendingListProps) {
  if (coins.length === 0) {
    return (
      <div className="text-center py-8">
        <Flame className="h-8 w-8 text-text-muted mx-auto mb-2" />
        <p className="text-sm text-text-muted">No trending coins available</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {coins.slice(0, 7).map((coin, index) => (
        <TrendingItem
          key={coin.id}
          coin={coin}
          rank={index + 1}
          onSelect={() => onSelect(coin.id)}
        />
      ))}
    </div>
  )
}

interface TrendingItemProps {
  coin: TrendingCoin
  rank: number
  onSelect: () => void
}

function TrendingItem({ coin, rank, onSelect }: TrendingItemProps) {
  const rankColors: Record<number, string> = {
    1: 'text-yellow-400',
    2: 'text-gray-400',
    3: 'text-orange-400',
  }

  return (
    <div
      className={cn(
        'flex items-center justify-between p-2 rounded-terminal',
        'hover:bg-bg-elevated/50 transition-colors group cursor-pointer'
      )}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3">
        {/* Rank */}
        <span
          className={cn(
            'w-6 text-center text-sm font-mono font-bold',
            rankColors[rank] || 'text-text-muted'
          )}
        >
          {rank}
        </span>

        {/* Coin Icon/Symbol */}
        {coin.thumb ? (
          <img
            src={coin.thumb}
            alt={coin.name}
            className="w-6 h-6 rounded-full"
          />
        ) : (
          <div className="w-6 h-6 rounded-full bg-accent-primary/20 flex items-center justify-center">
            <span className="text-xs font-bold text-accent-primary">
              {coin.symbol.charAt(0)}
            </span>
          </div>
        )}

        {/* Coin Info */}
        <div>
          <p className="text-sm font-medium text-text-primary">{coin.name}</p>
          <p className="text-xs text-text-muted">{coin.symbol}</p>
        </div>
      </div>

      {/* Market Cap Rank Badge */}
      <div className="flex items-center gap-2">
        {coin.market_cap_rank && (
          <Badge variant="muted" className="text-xs">
            #{coin.market_cap_rank}
          </Badge>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation()
            onSelect()
          }}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
