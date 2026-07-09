import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = cn(
      'inline-flex items-center justify-center font-medium',
      'rounded-terminal transition-all duration-250',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    )

    const variants = {
      primary: cn(
        'bg-accent-primary text-bg-primary',
        'hover:bg-accent-primary/90 hover:shadow-glow',
        'active:bg-accent-primary/80'
      ),
      secondary: cn(
        'bg-bg-elevated text-text-primary border border-border-default',
        'hover:bg-zinc-700 hover:border-border-accent/50',
        'active:bg-zinc-600'
      ),
      ghost: cn(
        'text-text-secondary',
        'hover:bg-bg-elevated hover:text-text-primary',
        'active:bg-zinc-700'
      ),
      danger: cn(
        'bg-accent-danger text-white',
        'hover:bg-accent-danger/90 hover:shadow-glow-danger',
        'active:bg-accent-danger/80'
      ),
      outline: cn(
        'border border-accent-primary text-accent-primary bg-transparent',
        'hover:bg-accent-primary/10 hover:shadow-glow-sm',
        'active:bg-accent-primary/20'
      ),
    }

    const sizes = {
      sm: 'h-8 px-3 text-sm gap-1.5',
      md: 'h-10 px-4 text-sm gap-2',
      lg: 'h-12 px-6 text-base gap-2.5',
    }

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button }
