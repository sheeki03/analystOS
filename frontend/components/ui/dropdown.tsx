'use client'

import {
  createContext,
  useContext,
  useState,
  useRef,
  useEffect,
  useCallback,
  type ReactNode,
  type HTMLAttributes,
  type ButtonHTMLAttributes,
} from 'react'
import { createPortal } from 'react-dom'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DropdownContextType {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  selectedValue: string | null
  setSelectedValue: (value: string) => void
  triggerRef: React.RefObject<HTMLButtonElement>
}

const DropdownContext = createContext<DropdownContextType | undefined>(undefined)

function useDropdown() {
  const context = useContext(DropdownContext)
  if (!context) {
    throw new Error('Dropdown components must be used within a Dropdown provider')
  }
  return context
}

interface DropdownProps {
  value?: string
  onValueChange?: (value: string) => void
  children: ReactNode
}

function Dropdown({ value, onValueChange, children }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedValue, setSelectedValue] = useState(value ?? null)
  const triggerRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (value !== undefined) {
      setSelectedValue(value)
    }
  }, [value])

  const handleValueChange = useCallback(
    (newValue: string) => {
      setSelectedValue(newValue)
      onValueChange?.(newValue)
      setIsOpen(false)
    },
    [onValueChange]
  )

  return (
    <DropdownContext.Provider
      value={{
        isOpen,
        setIsOpen,
        selectedValue,
        setSelectedValue: handleValueChange,
        triggerRef,
      }}
    >
      <div className="relative inline-block">{children}</div>
    </DropdownContext.Provider>
  )
}

interface DropdownTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  placeholder?: string
}

function DropdownTrigger({
  className,
  placeholder = 'Select...',
  children,
  ...props
}: DropdownTriggerProps) {
  const { isOpen, setIsOpen, selectedValue, triggerRef } = useDropdown()

  return (
    <button
      ref={triggerRef}
      type="button"
      role="combobox"
      aria-expanded={isOpen}
      aria-haspopup="listbox"
      onClick={() => setIsOpen(!isOpen)}
      className={cn(
        'flex items-center justify-between gap-2 w-full',
        'h-10 px-3 text-sm',
        'bg-bg-elevated border border-border-default rounded-terminal',
        'text-left transition-all duration-250',
        'hover:border-border-accent/50',
        'focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary/50',
        isOpen && 'border-accent-primary ring-1 ring-accent-primary/50',
        className
      )}
      {...props}
    >
      <span className={cn(!selectedValue && 'text-text-muted')}>
        {children || (selectedValue ?? placeholder)}
      </span>
      <ChevronDown
        className={cn(
          'h-4 w-4 text-text-muted transition-transform duration-200',
          isOpen && 'rotate-180'
        )}
      />
    </button>
  )
}

interface DropdownContentProps extends HTMLAttributes<HTMLDivElement> {}

function DropdownContent({ className, children, ...props }: DropdownContentProps) {
  const { isOpen, setIsOpen, triggerRef } = useDropdown()
  const contentRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0 })

  // Calculate position
  useEffect(() => {
    if (isOpen && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPosition({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
      })
    }
  }, [isOpen, triggerRef])

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        contentRef.current &&
        !contentRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, setIsOpen, triggerRef])

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false)
        triggerRef.current?.focus()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, setIsOpen, triggerRef])

  if (!isOpen) return null

  return createPortal(
    <div
      ref={contentRef}
      role="listbox"
      className={cn(
        'fixed z-dropdown',
        'bg-bg-elevated border border-border-default rounded-terminal shadow-elevated',
        'py-1 max-h-60 overflow-auto',
        'animate-slide-in-up',
        className
      )}
      style={{
        top: position.top,
        left: position.left,
        width: position.width,
      }}
      {...props}
    >
      {children}
    </div>,
    document.body
  )
}

interface DropdownItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
}

function DropdownItem({
  value,
  className,
  children,
  ...props
}: DropdownItemProps) {
  const { selectedValue, setSelectedValue } = useDropdown()
  const isSelected = selectedValue === value

  return (
    <button
      role="option"
      aria-selected={isSelected}
      onClick={() => setSelectedValue(value)}
      className={cn(
        'flex items-center justify-between w-full px-3 py-2 text-sm text-left',
        'transition-colors duration-150',
        isSelected
          ? 'bg-accent-primary/10 text-accent-primary'
          : 'text-text-secondary hover:bg-bg-primary hover:text-text-primary',
        className
      )}
      {...props}
    >
      {children}
      {isSelected && <Check className="h-4 w-4" />}
    </button>
  )
}

function DropdownLabel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'px-3 py-1.5 text-xs font-medium text-text-muted uppercase tracking-wider',
        className
      )}
      {...props}
    />
  )
}

function DropdownSeparator({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('my-1 h-px bg-border-default', className)}
      {...props}
    />
  )
}

export {
  Dropdown,
  DropdownTrigger,
  DropdownContent,
  DropdownItem,
  DropdownLabel,
  DropdownSeparator,
}
