'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react'
import { Button, Input } from '@/components/ui'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        'Hello! I\'m your research assistant. Ask me questions about your uploaded documents or any research topic.',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateMockResponse(userMessage.content),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-[500px] bg-bg-surface border border-border-default rounded-terminal">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border-default">
        <div className="w-8 h-8 rounded-full bg-accent-primary/20 flex items-center justify-center">
          <Sparkles className="h-4 w-4 text-accent-primary" />
        </div>
        <div>
          <h3 className="text-sm font-medium text-text-primary">Research Assistant</h3>
          <p className="text-xs text-text-muted">Ask questions about your documents</p>
        </div>
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
              <span className="text-sm text-text-muted">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border-default">
        <div className="flex items-center gap-2">
          <Input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
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
        <p className="text-xs text-text-muted mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
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
      <div
        className={cn(
          'max-w-[80%] p-3 rounded-terminal',
          isUser ? 'bg-accent-primary text-white' : 'bg-bg-elevated text-text-secondary'
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <p
          className={cn(
            'text-xs mt-2',
            isUser ? 'text-white/70' : 'text-text-muted'
          )}
        >
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

// Mock response generator
function generateMockResponse(query: string): string {
  const responses = [
    "Based on the documents I've analyzed, I can provide some insights on that topic. The key points include the importance of data-driven decision making and the role of AI in modern research workflows.",
    "That's an interesting question. From my analysis of your documents, I found several relevant sections that discuss this. Would you like me to provide more specific details?",
    "I found relevant information in your uploaded documents. The research suggests that this area has seen significant developments recently, particularly in terms of automation and efficiency improvements.",
    "Let me help you with that. Based on the context from your documents, there are multiple perspectives to consider here. The main takeaways involve understanding both the technical and practical implications.",
  ]
  return responses[Math.floor(Math.random() * responses.length)]
}
