import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Terminal Luxe Color Palette
      colors: {
        // Backgrounds
        'bg-primary': '#09090b',
        'bg-surface': '#18181b',
        'bg-elevated': '#27272a',

        // Accents
        'accent-primary': '#00d4aa',
        'accent-secondary': '#f59e0b',
        'accent-danger': '#ef4444',
        'accent-success': '#22c55e',

        // Text
        'text-primary': '#fafafa',
        'text-secondary': '#e4e4e7',
        'text-muted': '#a1a1aa',
        'text-disabled': '#71717a',

        // Borders
        'border-default': '#3f3f46',
        'border-subtle': '#27272a',
        'border-accent': '#00d4aa',

        // Chart colors
        'chart-positive': '#00d4aa',
        'chart-negative': '#ef4444',
        'chart-neutral': '#a1a1aa',

        // Zinc scale for fine-tuning
        zinc: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b',
        },

        // Teal for accent variations
        teal: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#00d4aa',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
      },

      // Typography
      fontFamily: {
        mono: ['var(--font-jetbrains-mono)', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },

      fontSize: {
        'display': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
        'heading-1': ['2.25rem', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '600' }],
        'heading-2': ['1.875rem', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '600' }],
        'heading-3': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
        'heading-4': ['1.25rem', { lineHeight: '1.4', fontWeight: '500' }],
        'body-lg': ['1.125rem', { lineHeight: '1.6' }],
        'body': ['1rem', { lineHeight: '1.6' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'caption': ['0.75rem', { lineHeight: '1.4' }],
        'data': ['0.875rem', { lineHeight: '1.2', fontWeight: '500' }],
      },

      letterSpacing: {
        'tight': '-0.02em',
        'data': '0.01em',
      },

      // Spacing
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },

      // Border radius
      borderRadius: {
        'terminal': '0.375rem',
      },

      // Box shadows with glow effects
      boxShadow: {
        'glow-sm': '0 0 10px -3px rgba(0, 212, 170, 0.3)',
        'glow': '0 0 20px -5px rgba(0, 212, 170, 0.4)',
        'glow-lg': '0 0 30px -5px rgba(0, 212, 170, 0.5)',
        'glow-amber': '0 0 20px -5px rgba(245, 158, 11, 0.4)',
        'glow-danger': '0 0 20px -5px rgba(239, 68, 68, 0.4)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.3)',
        'elevated': '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4)',
      },

      // Animations
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'slide-in-up': 'slide-in-up 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
        'progress-sweep': 'progress-sweep 2s linear infinite',
        'blink': 'blink 1s step-end infinite',
      },

      keyframes: {
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 10px -3px rgba(0, 212, 170, 0.3)' },
          '50%': { boxShadow: '0 0 20px -3px rgba(0, 212, 170, 0.5)' },
        },
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-in-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'progress-sweep': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'blink': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },

      // Transitions
      transitionDuration: {
        '250': '250ms',
        '350': '350ms',
      },

      // Z-index scale
      zIndex: {
        'dropdown': '50',
        'sticky': '100',
        'modal': '200',
        'toast': '300',
      },

      // Background patterns
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-terminal': 'linear-gradient(135deg, #09090b 0%, #18181b 100%)',
        'grid-pattern': `linear-gradient(to right, #27272a 1px, transparent 1px),
                         linear-gradient(to bottom, #27272a 1px, transparent 1px)`,
      },

      backgroundSize: {
        'grid': '24px 24px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

export default config
