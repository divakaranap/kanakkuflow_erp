import React, { useState, useEffect } from 'react'
import {
  AlertCircle,
  KeyRound,
  Sparkles,
} from 'lucide-react'
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
        /* Modern Premium SaaS Sign-In Screen */
        <div className="min-h-screen flex items-center justify-center p-6 bg-[#FAFAFD]">
          <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Column: Context & Overview */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#F2EEFF] border border-[#EAE8F1] text-[#7655E8] text-xs font-bold">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Centre for Digital Infrastructure – NIT Tiruchirappalli</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#17152B] leading-tight">
                Modern Manufacturing <span className="text-[#7655E8]">Order-to-Audit</span> ERP
              </h1>
              <p className="text-sm sm:text-base text-[#77758A] leading-relaxed">
                Connect the entire manufacturing lifecycle: Recipe BOMs, real-time inventory ledger,
                GST invoices, delivery dispatches, customer payments, and balanced general accounting.
              </p>

              <div className="grid grid-cols-3 gap-4 pt-2">
                <div className="p-4 bg-white rounded-2xl border border-[#EAE8F1] shadow-card">
                  <div className="text-[#7655E8] font-extrabold text-lg">8 Modules</div>
                  <div className="text-xs text-[#77758A] mt-0.5">Sales, Production, Inventory, Finance</div>
                </div>
                <div className="p-4 bg-white rounded-2xl border border-[#EAE8F1] shadow-card">
                  <div className="text-[#16A36A] font-extrabold text-lg">Balanced</div>
                  <div className="text-xs text-[#77758A] mt-0.5">Zero-drift double entry ledger</div>
                </div>
                <div className="p-4 bg-white rounded-2xl border border-[#EAE8F1] shadow-card">
                  <div className="text-[#9675F5] font-extrabold text-lg">GST Ready</div>
                  <div className="text-xs text-[#77758A] mt-0.5">Automated GSTR-1 &amp; GSTR-2</div>
                </div>
              </div>
            </div>

            {/* Right Column: Demo Login Card */}
            <div className="lg:col-span-5 bg-white rounded-3xl border border-[#EAE8F1] shadow-cardHover p-7 space-y-6">
              <div>
                <div className="flex items-center space-x-2">
                  <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white shadow-sm">
                    <KeyRound className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-[#17152B]">Sign In</h3>
                    <p className="text-xs text-[#77758A]">Sign in or pick any 1-Click demo role below</p>
                  </div>
                </div>
              </div>

              {errorMsg && (
                <div className="p-3.5 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200 flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-[#17152B] mb-1">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. admin or owner"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] focus:outline-none focus:ring-2 focus:ring-[#7655E8]/20 focus:border-[#7655E8] transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#17152B] mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] focus:outline-none focus:ring-2 focus:ring-[#7655E8]/20 focus:border-[#7655E8] transition"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 bg-gradient-to-r from-[#7655E8] to-[#9675F5] hover:opacity-95 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition shadow-md shadow-[#7655E8]/20"
                >
                  {loading ? 'Authenticating...' : 'Sign In with Credentials'}
                </button>
              </form>

              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-[#EAE8F1]"></div>
                <span className="flex-shrink mx-3 text-[10px] text-[#77758A] uppercase tracking-wider font-bold">
                  1-Click Instant Demo Login
                </span>
                <div className="flex-grow border-t border-[#EAE8F1]"></div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {demoAccounts.map((demo) => (
                  <button
                    key={demo.user}
                    type="button"
                    onClick={() => {
                      setUsername(demo.user)
                      setPassword(demo.pass)
                      handleLogin(undefined, demo.user, demo.pass)
                    }}
                    className={`text-left p-2.5 rounded-xl border ${demo.color} transition flex flex-col group bg-white shadow-xs`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#17152B] group-hover:text-[#7655E8]">
                        {demo.name}
                      </span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full ${demo.badge}`}>
                        {demo.role}
                      </span>
                    </div>
                    <span className="text-[10px] text-[#77758A] font-mono mt-0.5">
                      {demo.user}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
