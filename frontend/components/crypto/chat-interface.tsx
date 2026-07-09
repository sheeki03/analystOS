'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, TrendingUp, TrendingDown } from 'lucide-react'
import { Button, Input, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'
import { cryptoApi } from '@/lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  coinMentions?: string[]
}

interface ChatInterfaceProps {
  selectedCoin: string
}

export function ChatInterface({ selectedCoin }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        'Hello! I\'m your crypto AI assistant. Ask me about market trends, specific coins, technical analysis, or investment strategies. What would you like to know?',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Add context message when selected coin changes
  useEffect(() => {
    if (selectedCoin && messages.length > 1) {
      const contextMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I see you're interested in ${selectedCoin.charAt(0).toUpperCase() + selectedCoin.slice(1)}. Feel free to ask me any questions about it!`,
        timestamp: new Date(),
        coinMentions: [selectedCoin],
      }
      setMessages((prev) => [...prev, contextMessage])
    }
  }, [selectedCoin])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await cryptoApi.chat(input.trim(), selectedCoin)
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        coinMentions: response.coins_mentioned,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      // Fallback to mock response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateMockCryptoResponse(input.trim(), selectedCoin),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const suggestedQuestions = [
    `What's the outlook for ${selectedCoin}?`,
    'Top coins to watch this week?',
    'Explain DeFi to me',
    'Market sentiment analysis',
  ]

  return (
    <div className="flex flex-col h-[600px] bg-bg-surface border border-border-default rounded-terminal">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-default">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-accent-primary/20 flex items-center justify-center">
            <Bot className="h-4 w-4 text-accent-primary" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-text-primary">Crypto AI</h3>
            <p className="text-xs text-text-muted">Powered by GPT-4</p>
          </div>
        </div>
        {selectedCoin && (
          <Badge variant="secondary">
            Analyzing: {selectedCoin}
          </Badge>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-accent-primary/20 flex items-center justify-center flex-shrink-0">
              <Bot className="h-4 w-4 text-accent-primary" />
            </div>
            <div className="flex items-center gap-2 p-3 rounded-terminal bg-bg-elevated">
              <Loader2 className="h-4 w-4 text-accent-primary animate-spin" />
              <span className="text-sm text-text-muted">Analyzing market data...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length < 3 && (
        <div className="px-4 py-2 border-t border-border-default">
          <p className="text-xs text-text-muted mb-2">Suggested questions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, i) => (
              <button
                key={i}
                onClick={() => setInput(question)}
                className="text-xs px-2 py-1 rounded bg-bg-elevated text-text-secondary hover:text-text-primary hover:bg-bg-elevated/80 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border-default">
        <div className="flex items-center gap-2">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about crypto markets..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            type="submit"
            size="sm"
            disabled={!input.trim() || isLoading}
            className="px-3"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}

interface ChatMessageProps {
  message: Message
}

function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex items-start gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-bg-elevated' : 'bg-accent-primary/20'
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-text-muted" />
        ) : (
          <Bot className="h-4 w-4 text-accent-primary" />
        )}
      </div>
      <div className={cn('max-w-[80%]')}>
        <div
          className={cn(
            'p-3 rounded-terminal',
            isUser ? 'bg-accent-primary text-white' : 'bg-bg-elevated text-text-secondary'
          )}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Coin mentions */}
        {message.coinMentions && message.coinMentions.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {message.coinMentions.map((coin) => (
              <Badge key={coin} variant="muted" className="text-xs">
                {coin}
              </Badge>
            ))}
          </div>
        )}

        <p className={cn('text-xs mt-1', isUser ? 'text-right' : '')} style={{ color: 'var(--text-muted)' }}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  )
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

function generateMockCryptoResponse(query: string, coin: string): string {
  const responses = [
    `Based on my analysis of ${coin}, the current market conditions suggest cautious optimism. Key indicators show strong support levels with potential for upward movement. However, always consider market volatility and do your own research.`,
    `Looking at the technical indicators for ${coin}, we're seeing interesting patterns. The RSI is neutral, and the MACD shows potential momentum shift. Volume has been steady, suggesting continued interest from traders.`,
    `The broader crypto market is showing mixed signals. While ${coin} has shown resilience, macroeconomic factors continue to influence price action. It's important to maintain a diversified approach and stay updated on regulatory developments.`,
    `Great question! ${coin} has been performing within expected ranges. The key levels to watch are the support around recent lows and resistance at recent highs. Market sentiment appears cautiously bullish based on social metrics.`,
  ]
  return responses[Math.floor(Math.random() * responses.length)]
}
