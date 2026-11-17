import React, { useState, useEffect } from 'react'
import {
  ShieldCheck,
  Factory,
  LogOut,
  Server,
  Activity,
  CheckCircle2,
  AlertCircle,
  KeyRound,
} from 'lucide-react'
import { authService } from './services/authService'
import { api } from './services/api'
import type { UserInfo, UserRole } from './types/auth'

export function App() {
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(authService.getStoredUser())
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [healthStatus, setHealthStatus] = useState<{ status: string; database?: string } | null>(null)

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

  const roleBadgeColor = (role: UserRole) => {
    switch (role) {
      case 'OWNER':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'ADMIN':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'SALESMAN':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200'
      case 'PRODUCTION':
        return 'bg-amber-100 text-amber-800 border-amber-200'
      case 'AUDITOR':
        return 'bg-slate-100 text-slate-800 border-slate-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const demoAccounts = [
    { name: 'Owner', user: 'owner', role: 'OWNER', pass: 'demo123', color: 'border-purple-300 hover:bg-purple-50' },
    { name: 'Admin', user: 'admin', role: 'ADMIN', pass: 'demo123', color: 'border-blue-300 hover:bg-blue-50' },
    { name: 'Salesman TN', user: 'salesA', role: 'SALESMAN', pass: 'demo123', color: 'border-emerald-300 hover:bg-emerald-50' },
    { name: 'Production', user: 'prod', role: 'PRODUCTION', pass: 'demo123', color: 'border-amber-300 hover:bg-amber-50' },
    { name: 'Auditor', user: 'auditor', role: 'AUDITOR', pass: 'demo123', color: 'border-slate-300 hover:bg-slate-50' },
  ]

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#172033] flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-white border-b border-[#E2E8F0] px-6 py-4 flex items-center justify-between sticky top-0 z-50 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Factory className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-[#172033]">FACTORYFLOW</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                Phase 1 Scaffolding
              </span>
            </div>
            <p className="text-xs text-[#64748B]">From Order to Production. From Stock to Audit.</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs bg-slate-50 px-3 py-1.5 rounded-md border border-[#E2E8F0]">
            <Server className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-600 font-medium">Backend:</span>
            {healthStatus?.status === 'ok' ? (
              <span className="flex items-center text-emerald-600 font-semibold">
                <span className="h-2 w-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                Connected (DB: {healthStatus.database})
              </span>
            ) : (
              <span className="flex items-center text-amber-600 font-semibold">
                <span className="h-2 w-2 rounded-full bg-amber-500 mr-1.5"></span>
                {healthStatus?.status || 'Connecting...'}
              </span>
            )}
          </div>

          {currentUser && (
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-sm font-semibold text-[#172033]">{currentUser.full_name}</div>
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${roleBadgeColor(currentUser.role)}`}>
                  {currentUser.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                title="Log out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-6 flex flex-col justify-center">
        {currentUser ? (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-8 space-y-6">
            <div className="flex items-start justify-between border-b border-[#E2E8F0] pb-6">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="h-6 w-6 text-emerald-600" />
                  <h2 className="text-2xl font-bold text-[#172033]">Welcome, {currentUser.full_name}</h2>
                </div>
                <p className="text-sm text-[#64748B]">
                  Authenticated session active with role <span className="font-semibold text-blue-600">{currentUser.role}</span>.
                </p>
              </div>
              <span className={`text-xs px-3 py-1 font-semibold rounded-full border ${roleBadgeColor(currentUser.role)}`}>
                Role: {currentUser.role}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 bg-slate-50 rounded-lg border border-[#E2E8F0] space-y-1">
                <span className="text-xs font-medium text-[#64748B]">Username</span>
                <p className="text-sm font-semibold text-[#172033]">{currentUser.username}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-[#E2E8F0] space-y-1">
                <span className="text-xs font-medium text-[#64748B]">Email Address</span>
                <p className="text-sm font-semibold text-[#172033]">{currentUser.email}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-[#E2E8F0] space-y-1">
                <span className="text-xs font-medium text-[#64748B]">Account Status</span>
                <p className="text-sm font-semibold text-emerald-600 flex items-center">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 mr-1.5"></span> Active
                </p>
              </div>
            </div>

            <div className="p-5 bg-blue-50/50 rounded-xl border border-blue-100 flex items-start space-x-3">
              <ShieldCheck className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900 space-y-1">
                <p className="font-semibold">Phase 1 Architecture Verification Successful</p>
                <p className="text-blue-800/80 leading-relaxed">
                  FastAPI backend, PostgreSQL models, Alembic migrations, Docker Compose configuration,
                  and JWT authentication with role-based access control (RBAC) are verified.
                </p>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                Log Out
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Column: Context & Overview */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
                <Activity className="h-3.5 w-3.5" />
                <span>Centre for Digital Infrastructure – NIT Tiruchirappalli</span>
              </div>
              <h1 className="text-4xl font-extrabold tracking-tight text-[#172033] leading-tight">
                Order-to-Audit Management for Food Manufacturing
              </h1>
              <p className="text-base text-[#64748B] leading-relaxed">
                FACTORYFLOW connects the entire food manufacturing lifecycle: from Salesman order placement,
                production batch allocation, Bill of Materials (BOM) yield calculation, GST invoicing, and real-time
                ledger-based inventory to monthly auditor reports.
              </p>

              <div className="grid grid-cols-3 gap-4 pt-2">
                <div className="p-4 bg-white rounded-lg border border-[#E2E8F0] shadow-sm">
                  <div className="text-blue-600 font-bold text-lg">5 Roles</div>
                  <div className="text-xs text-[#64748B] mt-0.5">Owner, Admin, Sales, Production, Auditor</div>
                </div>
                <div className="p-4 bg-white rounded-lg border border-[#E2E8F0] shadow-sm">
                  <div className="text-emerald-600 font-bold text-lg">Paise Engine</div>
                  <div className="text-xs text-[#64748B] mt-0.5">Exact integer calculations &amp; INR formatting</div>
                </div>
                <div className="p-4 bg-white rounded-lg border border-[#E2E8F0] shadow-sm">
                  <div className="text-purple-600 font-bold text-lg">Ledger Based</div>
                  <div className="text-xs text-[#64748B] mt-0.5">Immutable audit trail &amp; zero silent overwrites</div>
                </div>
              </div>
            </div>

            {/* Right Column: Demo Login Card */}
            <div className="lg:col-span-5 bg-white rounded-2xl border border-[#E2E8F0] shadow-lg p-7 space-y-6">
              <div>
                <h3 className="text-xl font-bold text-[#172033] flex items-center space-x-2">
                  <KeyRound className="h-5 w-5 text-blue-600" />
                  <span>Sign In</span>
                </h3>
                <p className="text-xs text-[#64748B] mt-1">Enter credentials or click any demo role below</p>
              </div>

              {errorMsg && (
                <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. admin or salesA"
                    className="w-full px-3 py-2 text-sm border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-2 text-sm border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-sm rounded-lg transition shadow-md shadow-blue-500/20"
                >
                  {loading ? 'Authenticating...' : 'Sign In with Credentials'}
                </button>
              </form>

              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-[#E2E8F0]"></div>
                <span className="flex-shrink mx-3 text-xs text-[#64748B] uppercase tracking-wider font-semibold">
                  1-Click Demo Accounts
                </span>
                <div className="flex-grow border-t border-[#E2E8F0]"></div>
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
                    className={`text-left p-2.5 rounded-lg border ${demo.color} transition flex flex-col group`}
                  >
                    <span className="text-xs font-bold text-[#172033] group-hover:text-blue-600">
                      {demo.name}
                    </span>
                    <span className="text-[10px] text-[#64748B]">
                      {demo.user} / {demo.pass}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-[#E2E8F0] py-3 px-6 text-center text-xs text-[#64748B]">
        FACTORYFLOW ERP System &bull; Phase 1 Architecture Verification &bull; Centre for Digital Infrastructure, NIT Tiruchirappalli
      </footer>
    </div>
  )
}

export default App
