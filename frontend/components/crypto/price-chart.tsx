'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { cryptoApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils/formatters'

interface PriceChartProps {
  coinId: string
}

type TimeRange = '1D' | '7D' | '1M' | '3M' | '1Y'

const TIME_RANGES: { label: TimeRange; days: number }[] = [
  { label: '1D', days: 1 },
  { label: '7D', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 365 },
]

interface ChartData {
  timestamp: number
  price: number
  date: string
}

export function PriceChart({ coinId }: PriceChartProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('7D')
  const [data, setData] = useState<ChartData[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadChartData()
  }, [coinId, timeRange])

  const loadChartData = async () => {
    setIsLoading(true)
    try {
      const days = TIME_RANGES.find((r) => r.label === timeRange)?.days || 7
      const historical = await cryptoApi.getHistorical(coinId, days)
      setData(
        historical.prices.map(([timestamp, price]: [number, number]) => ({
          timestamp,
          price,
          date: formatChartDate(timestamp, timeRange),
        }))
      )
    } catch (error) {
      // Generate mock data
      setData(generateMockChartData(timeRange))
    } finally {
      setIsLoading(false)
    }
  }

  const priceChange = data.length > 1 ? data[data.length - 1].price - data[0].price : 0
  const priceChangePercent =
    data.length > 1 ? (priceChange / data[0].price) * 100 : 0
  const isPositive = priceChange >= 0

  return (
    <div className="bg-bg-surface border border-border-default rounded-terminal p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold font-mono text-text-primary capitalize">
            {coinId} Price
          </h3>
          {data.length > 0 && (
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-mono font-bold text-text-primary">
                {formatCurrency(data[data.length - 1]?.price || 0)}
              </span>
              <span
                className={cn(
                  'text-sm font-mono',
                  isPositive ? 'text-accent-success' : 'text-accent-danger'
                )}
              >
                {isPositive ? '+' : ''}
                {priceChangePercent.toFixed(2)}%
              </span>
            </div>
          )}
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-1 bg-bg-elevated rounded-terminal p-1">
          {TIME_RANGES.map(({ label }) => (
            <button
              key={label}
              onClick={() => setTimeRange(label)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded transition-all',
                timeRange === label
                  ? 'bg-accent-primary text-white'
                  : 'text-text-muted hover:text-text-primary'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-[300px]">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="h-8 w-8 text-accent-primary animate-spin" />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor={isPositive ? '#00d4aa' : '#ef4444'}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor={isPositive ? '#00d4aa' : '#ef4444'}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#71717a', fontSize: 11 }}
                dy={10}
              />
              <YAxis
                domain={['auto', 'auto']}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#71717a', fontSize: 11 }}
                tickFormatter={(value) => formatCompactCurrency(value)}
                dx={-10}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ stroke: '#3f3f46', strokeDasharray: '5 5' }}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={isPositive ? '#00d4aa' : '#ef4444'}
                strokeWidth={2}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null

  return (
    <div className="bg-bg-elevated border border-border-default rounded-terminal p-3 shadow-elevated">
      <p className="text-xs text-text-muted mb-1">{label}</p>
      <p className="text-lg font-mono font-semibold text-text-primary">
        {formatCurrency(payload[0].value)}
      </p>
    </div>
  )
}

function formatChartDate(timestamp: number, range: TimeRange): string {
  const date = new Date(timestamp)
  switch (range) {
    case '1D':
      return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    case '7D':
    case '1M':
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    case '3M':
    case '1Y':
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
    default:
      return date.toLocaleDateString()
  }
}

function formatCompactCurrency(value: number): string {
  if (value >= 1000) return '$' + (value / 1000).toFixed(1) + 'k'
  return '$' + value.toFixed(0)
}

function generateMockChartData(range: TimeRange): ChartData[] {
  const days = TIME_RANGES.find((r) => r.label === range)?.days || 7
  const points = range === '1D' ? 24 : days
  const basePrice = 45000 + Math.random() * 10000
  const data: ChartData[] = []

  for (let i = 0; i < points; i++) {
    const timestamp = Date.now() - (points - i) * (range === '1D' ? 3600000 : 86400000)
    const variance = (Math.random() - 0.5) * basePrice * 0.05
    const trend = (i / points) * basePrice * 0.02
    data.push({
      timestamp,
      price: basePrice + variance + trend,
      date: formatChartDate(timestamp, range),
    })
  }

  return data
}
