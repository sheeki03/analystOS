'use client'

import { TrendingUp, TrendingDown, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatCurrency, formatPercent } from '@/lib/utils/formatters'
import type { CoinPrice } from '@/types'

interface PriceCardProps {
  coinId: string
  price?: CoinPrice
  isSelected?: boolean
  onClick?: () => void
  onRemove?: () => void
  compact?: boolean
}

const COIN_ICONS: Record<string, string> = {
  bitcoin: 'BTC',
  ethereum: 'ETH',
  solana: 'SOL',
  cardano: 'ADA',
  polkadot: 'DOT',
  avalanche: 'AVAX',
  polygon: 'MATIC',
  chainlink: 'LINK',
}

const COIN_COLORS: Record<string, string> = {
  bitcoin: 'bg-orange-500/20 text-orange-400',
  ethereum: 'bg-blue-500/20 text-blue-400',
  solana: 'bg-purple-500/20 text-purple-400',
  cardano: 'bg-blue-400/20 text-blue-300',
  polkadot: 'bg-pink-500/20 text-pink-400',
  avalanche: 'bg-red-500/20 text-red-400',
  polygon: 'bg-purple-400/20 text-purple-300',
  chainlink: 'bg-blue-600/20 text-blue-500',
}

export function PriceCard({
  coinId,
  price,
  isSelected,
  onClick,
  onRemove,
  compact,
}: PriceCardProps) {
  const isPositive = price ? price.change_24h >= 0 : true
  const symbol = COIN_ICONS[coinId] || coinId.substring(0, 3).toUpperCase()
  const colorClass = COIN_COLORS[coinId] || 'bg-accent-primary/20 text-accent-primary'

  if (compact) {
    return (
      <div
        onClick={onClick}
        className={cn(
          'p-3 rounded-terminal border cursor-pointer transition-all',
          isSelected
            ? 'border-accent-primary bg-accent-primary/10'
            : 'border-border-default hover:border-text-muted hover:bg-bg-elevated/50'
        )}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className={cn('w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold', colorClass)}>
            {symbol.charAt(0)}
          </div>
          <span className="text-sm font-medium text-text-primary">{symbol}</span>
        </div>
        <p className="text-lg font-mono font-semibold text-text-primary">
          {price ? formatCurrency(price.price) : '--'}
        </p>
        <p
          className={cn(
            'text-sm font-mono',
            isPositive ? 'text-accent-success' : 'text-accent-danger'
          )}
        >
          {isPositive ? '+' : ''}
          {price ? formatPercent(price.change_24h) : '--'}
        </p>
      </div>
    )
  }

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative p-4 rounded-terminal border cursor-pointer transition-all group',
        isSelected
          ? 'border-accent-primary bg-accent-primary/5'
          : 'border-border-default hover:border-text-muted hover:bg-bg-elevated/50'
      )}
    >
      {/* Remove button */}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-bg-elevated text-text-muted hover:text-text-primary transition-all"
        >
          <X className="h-3 w-3" />
        </button>
      )}

      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'w-10 h-10 rounded-full flex items-center justify-center font-bold',
              colorClass
            )}
          >
            {symbol.charAt(0)}
          </div>
          <div>
            <h3 className="font-medium text-text-primary capitalize">{coinId}</h3>
            <p className="text-sm text-text-muted">{symbol}</p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-lg font-mono font-semibold text-text-primary">
            {price ? formatCurrency(price.price) : '--'}
          </p>
          <div
            className={cn(
              'flex items-center justify-end gap-1',
              isPositive ? 'text-accent-success' : 'text-accent-danger'
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span className="text-sm font-mono">
              {isPositive ? '+' : ''}
              {price ? formatPercent(price.change_24h) : '--'}
            </span>
          </div>
        </div>
      </div>

      {/* Additional stats */}
      {price && (
        <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-border-default">
          <div>
            <p className="text-xs text-text-muted">24h High</p>
            <p className="text-sm font-mono text-text-primary">
              {formatCurrency(price.high_24h)}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-muted">24h Low</p>
            <p className="text-sm font-mono text-text-primary">
              {formatCurrency(price.low_24h)}
            </p>
          </div>
          <div>
            <p className="text-xs text-text-muted">Volume</p>
            <p className="text-sm font-mono text-text-primary">
              {formatCompactNumber(price.volume_24h)}
            </p>
          </div>
        </div>
      )}

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-accent-primary rounded-r" />
      )}
    </div>
  )
}

function formatCompactNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B'
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M'
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
  return num.toFixed(0)
}
