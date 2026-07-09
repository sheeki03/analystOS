import type { Metadata } from 'next'
import { JetBrains_Mono, Inter } from 'next/font/google'
import { AuthProvider } from '@/contexts/auth-context'
import '@/styles/globals.css'

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'analystOS | AI-Powered Research Platform',
  description: 'Premium research terminal for AI-powered analysis, crypto insights, and workflow automation',
  keywords: ['research', 'AI', 'crypto', 'automation', 'analysis'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${jetbrainsMono.variable} ${inter.variable}`}>
      <body className="font-sans antialiased bg-bg-primary text-text-primary">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
