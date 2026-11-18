import React, { useState, useEffect } from 'react'
import { authService } from './services/authService'
import { api } from './services/api'
import { AppSidebar, type ERPView } from './components/common/AppSidebar'
import { AppHeader } from './components/common/AppHeader'
import { MasterDataOverview } from './features/masters/MasterDataOverview'
import { InventoryOverview } from './features/inventory/InventoryOverview'
import { ProductionOverview } from './features/production/ProductionOverview'
import { SalesOverview } from './features/sales/SalesOverview'
import { DispatchOverview } from './features/dispatch/DispatchOverview'
import { PaymentOverview } from './features/payments/PaymentOverview'
import { AccountingOverview } from './features/accounting/AccountingOverview'
import { ExecutiveDashboard } from './features/dashboard/ExecutiveDashboard'
import { SettingsOverview } from './features/settings/SettingsOverview'
import { LandingPage } from './features/landing/LandingPage'
import type { UserInfo } from './types/auth'

export function App() {
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(authService.getStoredUser())
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [healthStatus, setHealthStatus] = useState<{ status: string; database?: string } | null>(null)
  const [currentView, setCurrentView] = useState<ERPView>('dashboard')
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  useEffect(() => {
    // Check backend health
    api.get('/health')
      .then((res) => setHealthStatus(res.data))
      .catch(() => setHealthStatus({ status: 'unreachable', database: 'disconnected' }))

    // If token exists, verify session
    if (authService.getToken()) {
      authService.getCurrentUser()
        .then((user) => setCurrentUser(user))
        .catch(() => {
          authService.logout()
          setCurrentUser(null)
        })
    }
  }, [])

  const handleLogin = async (e?: React.FormEvent, customUser?: string, customPass?: string) => {
    if (e) e.preventDefault()
    const u = customUser || username
    const p = customPass || password
    if (!u || !p) {
      setErrorMsg('Please enter both username and password')
      return
    }

    setLoading(true)
    setErrorMsg('')
    try {
      const res = await authService.login(u, p)
      setCurrentUser(res.user)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Authentication failed. Ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    authService.logout()
    setCurrentUser(null)
    setUsername('')
    setPassword('')
  }

  const demoAccounts = [
    {
      name: 'Owner',
      user: 'owner',
      role: 'OWNER',
      pass: 'demo123',
      color: 'border-[#EAE8F1] hover:border-[#7655E8]/40 hover:bg-[#F2EEFF]/40',
      badge: 'bg-[#F2EEFF] text-[#7655E8]',
    },
    {
      name: 'Admin',
      user: 'admin',
      role: 'ADMIN',
      pass: 'demo123',
      color: 'border-[#EAE8F1] hover:border-blue-400 hover:bg-blue-50/40',
      badge: 'bg-blue-50 text-blue-700',
    },
    {
      name: 'Salesman TN',
      user: 'salesA',
      role: 'SALESMAN',
      pass: 'demo123',
      color: 'border-[#EAE8F1] hover:border-emerald-400 hover:bg-emerald-50/40',
      badge: 'bg-emerald-50 text-[#16A36A]',
    },
    {
      name: 'Production',
      user: 'prod',
      role: 'PRODUCTION',
      pass: 'demo123',
      color: 'border-[#EAE8F1] hover:border-amber-400 hover:bg-amber-50/40',
      badge: 'bg-amber-50 text-[#E9A23B]',
    },
    {
      name: 'Auditor',
      user: 'auditor',
      role: 'AUDITOR',
      pass: 'demo123',
      color: 'border-[#EAE8F1] hover:border-purple-400 hover:bg-purple-50/40',
      badge: 'bg-purple-50 text-purple-700',
    },
  ]

  return (
    <div className="min-h-screen bg-[#FAFAFD] text-[#17152B] flex flex-col font-sans selection:bg-[#F2EEFF] selection:text-[#7655E8]">
      {currentUser ? (
        <>
          {/* Left Fixed Sidebar */}
          <AppSidebar
            currentView={currentView}
            onSelectView={setCurrentView}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            currentUser={currentUser}
            onLogout={handleLogout}
          />

          {/* Top Header */}
          <AppHeader
            currentView={currentView}
            currentUser={currentUser}
            onLogout={handleLogout}
            healthStatus={healthStatus}
            isSidebarCollapsed={isSidebarCollapsed}
            onSelectView={setCurrentView}
          />

          {/* Main Body Content */}
          <main
            className={`flex-1 transition-all duration-300 p-6 lg:p-8 ${
              isSidebarCollapsed ? 'ml-20' : 'ml-64'
            }`}
          >
            {currentView === 'dashboard' && <ExecutiveDashboard />}
            {currentView === 'accounting' && <AccountingOverview />}
            {currentView === 'payments' && <PaymentOverview />}
            {currentView === 'dispatch' && <DispatchOverview />}
            {currentView === 'sales' && <SalesOverview />}
            {currentView === 'production' && <ProductionOverview />}
            {currentView === 'inventory' && <InventoryOverview />}
            {currentView === 'masters' && <MasterDataOverview />}
            {currentView === 'settings' && <SettingsOverview />}
          </main>

          {/* Subtle Clean Footer */}
          <footer
            className={`transition-all duration-300 py-3 px-6 text-center text-xs text-[#77758A] border-t border-[#EAE8F1] bg-white ${
              isSidebarCollapsed ? 'ml-20' : 'ml-64'
            }`}
          >
            KANAKKUFLOW ERP &bull; Order-to-Audit Management System &bull; National Institute of Technology Tiruchirappalli
          </footer>
        </>
      ) : (
        <LandingPage
          onLogin={handleLogin}
          loading={loading}
          errorMsg={errorMsg}
          healthStatus={healthStatus}
          username={username}
          setUsername={setUsername}
          password={password}
          setPassword={setPassword}
          demoAccounts={demoAccounts}
        />
      )}
    </div>
  )
}

export default App
