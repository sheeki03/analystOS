'use client'

import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatCurrency, formatPercent } from '@/lib/utils/formatters'
import type { MarketData } from '@/types'

interface MarketOverviewProps {
  data: MarketData | null
}

export function MarketOverview({ data }: MarketOverviewProps) {
  if (!data) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-16 rounded-terminal bg-bg-elevated animate-pulse"
          />
        ))}
      </div>
    )
  }

  const isMarketUp = data.market_cap_change_24h >= 0

  return (
    <div className="space-y-4">
      {/* Total Market Cap */}
      <MetricCard
        icon={<DollarSign className="h-5 w-5" />}
        label="Total Market Cap"
        value={formatLargeCurrency(data.total_market_cap)}
        change={data.market_cap_change_24h}
        iconColor="text-accent-primary"
      />

      {/* 24h Volume */}
      <MetricCard
        icon={<BarChart3 className="h-5 w-5" />}
        label="24h Volume"
        value={formatLargeCurrency(data.total_volume)}
        iconColor="text-blue-400"
      />

      {/* BTC Dominance */}
      <MetricCard
        icon={<Activity className="h-5 w-5" />}
        label="BTC Dominance"
        value={`${data.btc_dominance.toFixed(1)}%`}
        iconColor="text-orange-400"
      />

      {/* Market Sentiment */}
      <div className="p-4 rounded-terminal bg-bg-elevated border border-border-default">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-text-muted">Market Sentiment</span>
          <span
            className={cn(
              'text-sm font-medium',
              isMarketUp ? 'text-accent-success' : 'text-accent-danger'
            )}
          >
            {isMarketUp ? 'Bullish' : 'Bearish'}
          </span>
        </div>
        <div className="h-2 bg-bg-primary rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-500',
              isMarketUp ? 'bg-accent-success' : 'bg-accent-danger'
            )}
            style={{
              width: `${50 + (isMarketUp ? Math.abs(data.market_cap_change_24h) : -Math.abs(data.market_cap_change_24h)) * 5}%`,
            }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-text-muted">
          <span>Fear</span>
          <span>Greed</span>
        </div>
      </div>

      {/* Active Coins */}
      {data.active_coins && (
        <div className="p-4 rounded-terminal bg-bg-elevated border border-border-default">
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-muted">Active Cryptocurrencies</span>
            <span className="text-lg font-mono font-semibold text-text-primary">
              {data.active_coins.toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

interface MetricCardProps {
  icon: React.ReactNode
  label: string
  value: string
  change?: number
  iconColor?: string
}

function MetricCard({ icon, label, value, change, iconColor }: MetricCardProps) {
  const isPositive = change !== undefined ? change >= 0 : undefined

  return (
    <div className="p-4 rounded-terminal bg-bg-elevated border border-border-default">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'w-10 h-10 rounded-terminal flex items-center justify-center bg-bg-primary',
              iconColor || 'text-text-muted'
            )}
          >
            {icon}
          </div>
          <div>
            <p className="text-sm text-text-muted">{label}</p>
            <p className="text-lg font-mono font-semibold text-text-primary">
              {value}
            </p>
          </div>
        </div>

        {change !== undefined && (
          <div
            className={cn(
              'flex items-center gap-1 px-2 py-1 rounded',
              isPositive
                ? 'bg-accent-success/10 text-accent-success'
                : 'bg-accent-danger/10 text-accent-danger'
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            <span className="text-xs font-mono">
              {isPositive ? '+' : ''}
              {change.toFixed(2)}%
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function formatLargeCurrency(value: number): string {
  if (value >= 1e12) return '$' + (value / 1e12).toFixed(2) + 'T'
  if (value >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B'
  if (value >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M'
  return '$' + value.toLocaleString()
}
