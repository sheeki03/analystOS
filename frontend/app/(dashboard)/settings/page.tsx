'use client'

import { useState } from 'react'
import { PageContainer, PageHeader, PageSection } from '@/components/layout'
import { Button, Input, Card, CardContent, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui'
import { useAuth } from '@/contexts/auth-context'
import { User, Key, Bell, Shield, Palette, Save, LogOut } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState('profile')
  const [isSaving, setIsSaving] = useState(false)

  // Form states
  const [username, setUsername] = useState(user?.username || '')
  const [email, setEmail] = useState(user?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const handleSaveProfile = async () => {
    setIsSaving(true)
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsSaving(false)
  }

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      return
    }
    setIsSaving(true)
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
    setIsSaving(false)
  }

  return (
    <PageContainer>
      <PageHeader
        title="Settings"
        description="Manage your account settings and preferences"
      />

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:w-64 shrink-0">
          <nav className="space-y-1">
            <SettingsNavItem
              icon={<User className="h-4 w-4" />}
              label="Profile"
              isActive={activeTab === 'profile'}
              onClick={() => setActiveTab('profile')}
            />
            <SettingsNavItem
              icon={<Key className="h-4 w-4" />}
              label="Security"
              isActive={activeTab === 'security'}
              onClick={() => setActiveTab('security')}
            />
            <SettingsNavItem
              icon={<Bell className="h-4 w-4" />}
              label="Notifications"
              isActive={activeTab === 'notifications'}
              onClick={() => setActiveTab('notifications')}
            />
            <SettingsNavItem
              icon={<Palette className="h-4 w-4" />}
              label="Appearance"
              isActive={activeTab === 'appearance'}
              onClick={() => setActiveTab('appearance')}
            />
            <SettingsNavItem
              icon={<Shield className="h-4 w-4" />}
              label="API Keys"
              isActive={activeTab === 'api'}
              onClick={() => setActiveTab('api')}
            />
          </nav>

          <div className="mt-8 pt-8 border-t border-border-default">
            <Button
              variant="ghost"
              className="w-full justify-start text-accent-danger hover:text-accent-danger hover:bg-accent-danger/10"
              onClick={logout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {activeTab === 'profile' && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold font-mono text-text-primary mb-6">
                  Profile Information
                </h2>

                <div className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-accent-primary/20 flex items-center justify-center">
                      <span className="text-accent-primary font-mono font-bold text-2xl">
                        {user?.username?.charAt(0).toUpperCase() || 'U'}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-text-primary">{user?.username}</p>
                      <p className="text-sm text-text-muted">{user?.email}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-1.5">
                        Username
                      </label>
                      <Input
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-1.5">
                        Email
                      </label>
                      <Input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button onClick={handleSaveProfile} disabled={isSaving}>
                      {isSaving ? (
                        <>
                          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          Save Changes
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold font-mono text-text-primary mb-6">
                  Change Password
                </h2>

                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Current Password
                    </label>
                    <Input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      New Password
                    </label>
                    <Input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1.5">
                      Confirm New Password
                    </label>
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                    {newPassword && confirmPassword && newPassword !== confirmPassword && (
                      <p className="mt-1 text-sm text-accent-danger">
                        Passwords do not match
                      </p>
                    )}
                  </div>

                  <Button
                    onClick={handleChangePassword}
                    disabled={
                      isSaving ||
                      !currentPassword ||
                      !newPassword ||
                      newPassword !== confirmPassword
                    }
                  >
                    {isSaving ? 'Updating...' : 'Update Password'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold font-mono text-text-primary mb-6">
                  Notification Preferences
                </h2>

                <div className="space-y-4">
                  <NotificationToggle
                    title="Job Completion"
                    description="Get notified when a research job completes"
                    defaultChecked
                  />
                  <NotificationToggle
                    title="Report Ready"
                    description="Get notified when a report is ready to download"
                    defaultChecked
                  />
                  <NotificationToggle
                    title="Price Alerts"
                    description="Get notified when crypto prices hit your targets"
                  />
                  <NotificationToggle
                    title="Automation Updates"
                    description="Get notified about automation workflow status"
                    defaultChecked
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'appearance' && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold font-mono text-text-primary mb-6">
                  Appearance
                </h2>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-3">
                      Theme
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      <ThemeOption label="Dark" isActive />
                      <ThemeOption label="Light" disabled />
                      <ThemeOption label="System" disabled />
                    </div>
                    <p className="mt-2 text-xs text-text-muted">
                      Terminal Luxe theme is currently the only available option.
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-3">
                      Accent Color
                    </label>
                    <div className="flex gap-2">
                      <ColorSwatch color="#00d4aa" isActive />
                      <ColorSwatch color="#3b82f6" />
                      <ColorSwatch color="#8b5cf6" />
                      <ColorSwatch color="#f59e0b" />
                      <ColorSwatch color="#ef4444" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'api' && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold font-mono text-text-primary mb-6">
                  API Keys
                </h2>

                <div className="space-y-6">
                  <div className="p-4 rounded-terminal bg-bg-elevated border border-border-default">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-text-primary">
                        Personal Access Token
                      </span>
                      <Badge variant="success">Active</Badge>
                    </div>
                    <code className="text-xs text-text-muted font-mono">
                      ••••••••••••••••••••••••••••••••
                    </code>
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" variant="secondary">
                        Regenerate
                      </Button>
                      <Button size="sm" variant="ghost">
                        Copy
                      </Button>
                    </div>
                  </div>

                  <div className="p-4 rounded-terminal border border-dashed border-border-default">
                    <p className="text-sm text-text-muted mb-3">
                      Need to integrate with external services? Generate an API key for
                      programmatic access.
                    </p>
                    <Button variant="secondary" size="sm">
                      Generate New Key
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </PageContainer>
  )
}

interface SettingsNavItemProps {
  icon: React.ReactNode
  label: string
  isActive: boolean
  onClick: () => void
}

function SettingsNavItem({ icon, label, isActive, onClick }: SettingsNavItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-3 w-full px-3 py-2 rounded-terminal text-sm transition-colors',
        isActive
          ? 'bg-accent-primary/10 text-accent-primary'
          : 'text-text-muted hover:bg-bg-elevated hover:text-text-primary'
      )}
    >
      {icon}
      {label}
    </button>
  )
}

interface NotificationToggleProps {
  title: string
  description: string
  defaultChecked?: boolean
}

function NotificationToggle({
  title,
  description,
  defaultChecked,
}: NotificationToggleProps) {
  const [checked, setChecked] = useState(defaultChecked ?? false)

  return (
    <div className="flex items-center justify-between py-3 border-b border-border-default last:border-0">
      <div>
        <p className="text-sm font-medium text-text-primary">{title}</p>
        <p className="text-xs text-text-muted">{description}</p>
      </div>
      <button
        onClick={() => setChecked(!checked)}
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors',
          checked ? 'bg-accent-primary' : 'bg-bg-elevated'
        )}
      >
        <span
          className={cn(
            'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
            checked ? 'left-6' : 'left-1'
          )}
        />
      </button>
    </div>
  )
}

function ThemeOption({
  label,
  isActive,
  disabled,
}: {
  label: string
  isActive?: boolean
  disabled?: boolean
}) {
  return (
    <button
      disabled={disabled}
      className={cn(
        'p-3 rounded-terminal border text-sm font-medium transition-all',
        isActive
          ? 'border-accent-primary bg-accent-primary/10 text-accent-primary'
          : disabled
          ? 'border-border-default bg-bg-elevated text-text-muted cursor-not-allowed opacity-50'
          : 'border-border-default hover:border-text-muted text-text-secondary'
      )}
    >
      {label}
    </button>
  )
}

function ColorSwatch({ color, isActive, onClick }: { color: string; isActive?: boolean; onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-8 h-8 rounded-full transition-transform',
        isActive && 'ring-2 ring-offset-2 ring-offset-bg-primary ring-white scale-110'
      )}
      style={{ backgroundColor: color }}
    />
  )
}
