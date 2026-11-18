import React, { useState } from 'react'
import {
  Sparkles,
  KeyRound,
  AlertCircle,
  ArrowRight,
  ShoppingBag,
  Boxes,
  Factory,
  Receipt,
  Truck,
  ShieldCheck,
  CheckCircle2,
  Lock,
  User,
  Eye,
  EyeOff,
  ExternalLink,
  Activity,
  Layers,
} from 'lucide-react'

export interface DemoAccount {
  name: string
  user: string
  role: string
  pass: string
  color: string
  badge: string
}

export interface LandingPageProps {
  onLogin: (e?: React.FormEvent, customUser?: string, customPass?: string) => Promise<void>
  loading: boolean
  errorMsg: string
  healthStatus: { status: string; database?: string } | null
  username: string
  setUsername: (val: string) => void
  password: string
  setPassword: (val: string) => void
  demoAccounts: DemoAccount[]
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onLogin,
  loading,
  errorMsg,
  healthStatus,
  username,
  setUsername,
  password,
  setPassword,
  demoAccounts,
}) => {
  const [showPassword, setShowPassword] = useState(false)

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="min-h-screen bg-[#FAFAFD] text-[#17152B] flex flex-col font-sans selection:bg-[#F2EEFF] selection:text-[#7655E8]">
      {/* ------------------------------------------------------------------- */}
      {/* TOP HEADER / NAVIGATION BAR                                         */}
      {/* ------------------------------------------------------------------- */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-[#EAE8F1]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white shadow-sm shadow-[#7655E8]/20">
              <Factory className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-[#17152B]">
                  KANAKKU<span className="text-[#7655E8]">Flow</span>
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1]">
                  ERP 2.0
                </span>
              </div>
              <p className="text-[11px] text-[#77758A] hidden sm:block">
                Order-to-Audit Manufacturing Suite
              </p>
            </div>
          </div>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center space-x-8 text-xs font-semibold text-[#77758A]">
            <button
              onClick={() => scrollToSection('features')}
              className="hover:text-[#7655E8] transition flex items-center space-x-1"
            >
              <span>Explore Platform</span>
            </button>
            <button
              onClick={() => scrollToSection('workflow')}
              className="hover:text-[#7655E8] transition flex items-center space-x-1"
            >
              <span>Manufacturing Workflow</span>
            </button>
            <button
              onClick={() => scrollToSection('architecture')}
              className="hover:text-[#7655E8] transition"
            >
              <span>Trust &amp; Architecture</span>
            </button>
            <a
              href="/api/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#7655E8] transition flex items-center space-x-1"
            >
              <span>API Docs</span>
              <ExternalLink className="h-3 w-3 opacity-60" />
            </a>
          </nav>

          {/* Right Status & Action */}
          <div className="flex items-center space-x-3">
            <div
              className={`hidden sm:inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                healthStatus?.status === 'ok'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-[#F2EEFF] text-[#7655E8] border-[#EAE8F1]'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  healthStatus?.status === 'ok' ? 'bg-emerald-500 animate-pulse' : 'bg-[#7655E8]'
                }`}
              />
              <span className="text-[11px]">
                {healthStatus?.status === 'ok' ? 'Backend: Online' : 'Connecting...'}
              </span>
            </div>

            <button
              onClick={() => scrollToSection('login-card')}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-[#7655E8] to-[#9675F5] text-white shadow-sm shadow-[#7655E8]/20 hover:opacity-95 transition"
            >
              Sign In
            </button>
          </div>
        </div>
      </header>

      {/* ------------------------------------------------------------------- */}
      {/* HERO SECTION: LEFT DETAILS & RIGHT LOGIN CARD                       */}
      {/* ------------------------------------------------------------------- */}
      <section className="relative overflow-hidden pt-8 pb-16 lg:py-20 border-b border-[#EAE8F1]">
        {/* Soft decorative background lavender gradient blobs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-[#F2EEFF]/70 via-[#F8F7FC] to-transparent rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* ============================================================ */}
            {/* HERO LEFT SIDE: Headlines, Description, Buttons, Illustration */}
            {/* ============================================================ */}
            <div className="lg:col-span-7 space-y-6">
              {/* Eyebrow Label */}
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#F2EEFF] border border-[#EAE8F1] text-[#7655E8] text-xs font-bold shadow-xs">
                <Sparkles className="h-3.5 w-3.5 text-[#7655E8]" />
                <span className="tracking-wide">MANUFACTURING ERP PLATFORM</span>
              </div>

              {/* Main Headline */}
              <div className="space-y-2">
                <h1 className="text-4xl sm:text-5xl lg:text-[54px] font-extrabold tracking-tight text-[#17152B] leading-[1.12]">
                  From Raw Materials <br className="hidden sm:inline" />
                  to <span className="bg-gradient-to-r from-[#7655E8] via-[#8565EE] to-[#9675F5] bg-clip-text text-transparent">Revenue.</span>
                </h1>
                <p className="text-xl sm:text-2xl font-bold text-[#7655E8]">
                  One Intelligent Manufacturing ERP.
                </p>
              </div>

              {/* Description */}
              <p className="text-sm sm:text-base text-[#77758A] leading-relaxed max-w-2xl">
                Connect your entire manufacturing business through one intelligent platform. Manage procurement,
                inventory, production, sales, GST invoicing, dispatch and financial auditing seamlessly.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => scrollToSection('features')}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#7655E8] to-[#9675F5] text-white text-xs sm:text-sm font-bold shadow-sm shadow-[#7655E8]/25 hover:shadow-md hover:shadow-[#7655E8]/30 hover:opacity-95 transition flex items-center space-x-2"
                >
                  <span>Explore Platform</span>
                  <ArrowRight className="h-4 w-4" />
                </button>

                <button
                  type="button"
                  onClick={() => scrollToSection('workflow')}
                  className="px-5 py-2.5 rounded-xl bg-white border border-[#EAE8F1] text-[#17152B] text-xs sm:text-sm font-bold hover:bg-[#F8F7FC] hover:border-[#7655E8]/30 transition flex items-center space-x-2 shadow-xs"
                >
                  <Activity className="h-4 w-4 text-[#7655E8]" />
                  <span>Manufacturing Workflow</span>
                </button>
              </div>

              {/* Custom SaaS Manufacturing Illustration */}
              <div className="pt-4">
                <div className="bg-white rounded-3xl border border-[#EAE8F1] p-4 sm:p-5 shadow-card hover:shadow-cardHover transition duration-300">
                  <div className="flex items-center justify-between pb-3 border-b border-[#EAE8F1] text-xs">
                    <span className="font-bold text-[#17152B] flex items-center space-x-2">
                      <span className="h-2 w-2 rounded-full bg-[#16A36A] animate-pulse" />
                      <span>Live Production Pipeline &bull; Kai Murukku 200g</span>
                    </span>
                    <span className="font-mono text-[11px] text-[#7655E8] font-bold bg-[#F2EEFF] px-2 py-0.5 rounded-md">
                      Batch #BAT-202611-001
                    </span>
                  </div>

                  {/* Flow Diagram Mini Map */}
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 pt-3 text-center">
                    <div className="p-2 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
                      <div className="h-7 w-7 mx-auto rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                        <ShoppingBag className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-[10px] font-bold text-[#17152B] mt-1.5">Raw Flour</div>
                      <div className="text-[9px] text-[#77758A]">GRN #001</div>
                    </div>

                    <div className="p-2 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
                      <div className="h-7 w-7 mx-auto rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                        <Boxes className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-[10px] font-bold text-[#17152B] mt-1.5">Stock Ledger</div>
                      <div className="text-[9px] text-[#16A36A] font-semibold">120 kg Avail</div>
                    </div>

                    <div className="p-2 rounded-xl bg-[#F2EEFF]/60 border border-[#7655E8]/30">
                      <div className="h-7 w-7 mx-auto rounded-lg bg-[#7655E8] text-white flex items-center justify-center shadow-xs">
                        <Factory className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-[10px] font-bold text-[#7655E8] mt-1.5">Frying &amp; Pack</div>
                      <div className="text-[9px] text-[#7655E8] font-semibold">Yield 95.2%</div>
                    </div>

                    <div className="p-2 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
                      <div className="h-7 w-7 mx-auto rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                        <Receipt className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-[10px] font-bold text-[#17152B] mt-1.5">GST Invoice</div>
                      <div className="text-[9px] text-[#77758A]">5% HSN 1905</div>
                    </div>

                    <div className="p-2 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
                      <div className="h-7 w-7 mx-auto rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                        <Truck className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-[10px] font-bold text-[#17152B] mt-1.5">Dispatch</div>
                      <div className="text-[9px] text-[#16A36A] font-semibold">150 Pkts Out</div>
                    </div>

                    <div className="p-2 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
                      <div className="h-7 w-7 mx-auto rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                        <ShieldCheck className="h-3.5 w-3.5" />
                      </div>
                      <div className="text-[10px] font-bold text-[#17152B] mt-1.5">Audit Ledger</div>
                      <div className="text-[9px] text-[#16A36A] font-semibold">₹0.00 Drift</div>
                    </div>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-[#EAE8F1] flex items-center justify-between text-[11px] text-[#77758A]">
                    <span className="flex items-center space-x-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-[#16A36A]" />
                      <span>Traceable moving weighted average &bull; Zero negative inventory locks</span>
                    </span>
                    <span className="font-semibold text-[#17152B]">
                      Unit Cost: <span className="text-[#7655E8] font-bold">₹24.60</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* ============================================================ */}
            {/* HERO RIGHT SIDE: LOGIN CARD                                  */}
            {/* ============================================================ */}
            <div className="lg:col-span-5" id="login-card">
              <div className="bg-white rounded-3xl border border-[#EAE8F1] shadow-cardHover p-7 sm:p-8 space-y-6 relative overflow-hidden backdrop-blur-sm">
                {/* Subtle top-right decorative accent */}
                <div className="absolute -top-12 -right-12 w-32 h-32 bg-[#F2EEFF] rounded-full blur-2xl pointer-events-none" />

                {/* Card Title & Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white shadow-sm shadow-[#7655E8]/20">
                      <KeyRound className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-[#17152B]">Sign In</h2>
                      <p className="text-xs text-[#77758A]">Access KANAKKUFlow Order-to-Audit Suite</p>
                    </div>
                  </div>

                  {healthStatus?.status === 'ok' && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <span>Ready</span>
                    </span>
                  )}
                </div>

                {/* Error Banner */}
                {errorMsg && (
                  <div className="p-3.5 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200 flex items-start space-x-2.5 animate-in fade-in">
                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{errorMsg}</span>
                  </div>
                )}

                {/* Form */}
                <form onSubmit={onLogin} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-[#17152B] mb-1.5">
                      Username
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#77758A]">
                        <User className="h-4 w-4" />
                      </div>
                      <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="e.g. admin or owner"
                        autoComplete="username"
                        required
                        className="w-full pl-10 pr-3.5 py-2.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] placeholder:text-[#77758A]/60 focus:outline-none focus:ring-2 focus:ring-[#7655E8]/20 focus:border-[#7655E8] transition"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#17152B] mb-1.5">
                      Password
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#77758A]">
                        <Lock className="h-4 w-4" />
                      </div>
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        autoComplete="current-password"
                        required
                        className="w-full pl-10 pr-10 py-2.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] placeholder:text-[#77758A]/60 focus:outline-none focus:ring-2 focus:ring-[#7655E8]/20 focus:border-[#7655E8] transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#77758A] hover:text-[#7655E8] transition"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 bg-gradient-to-r from-[#7655E8] to-[#9675F5] hover:opacity-95 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition shadow-md shadow-[#7655E8]/20 flex items-center justify-center space-x-2"
                  >
                    {loading ? (
                      <>
                        <span className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Authenticating...</span>
                      </>
                    ) : (
                      <span>Sign In with Credentials</span>
                    )}
                  </button>
                </form>

                {/* 1-Click Instant Demo Login Divider */}
                <div className="relative flex py-1 items-center">
                  <div className="flex-grow border-t border-[#EAE8F1]" />
                  <span className="flex-shrink mx-3 text-[10px] text-[#77758A] uppercase tracking-wider font-bold">
                    1-Click Instant Demo Login
                  </span>
                  <div className="flex-grow border-t border-[#EAE8F1]" />
                </div>

                {/* Demo Role Selection Cards */}
                <div className="grid grid-cols-2 gap-2">
                  {demoAccounts.map((demo) => (
                    <button
                      key={demo.user}
                      type="button"
                      disabled={loading}
                      onClick={() => {
                        setUsername(demo.user)
                        setPassword(demo.pass)
                        onLogin(undefined, demo.user, demo.pass)
                      }}
                      className={`text-left p-2.5 rounded-xl border ${demo.color} transition flex flex-col group bg-white shadow-xs hover:shadow-sm disabled:opacity-50`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[#17152B] group-hover:text-[#7655E8] transition">
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

                {/* Security Footnote */}
                <p className="text-[11px] text-center text-[#77758A] pt-1">
                  Protected by 256-bit JWT authentication &bull; Zero-drift audit trail
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------- */}
      {/* SECTION 4: BUSINESS WORKFLOW STRIP                                  */}
      {/* ------------------------------------------------------------------- */}
      <section id="workflow" className="py-16 bg-[#FAFAFD] border-b border-[#EAE8F1]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-2 mb-10">
            <span className="text-xs font-bold text-[#7655E8] uppercase tracking-wider bg-[#F2EEFF] px-3 py-1 rounded-full border border-[#EAE8F1]">
              INTEGRATED OPERATIONS PIPELINE
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#17152B] tracking-tight">
              Six Connected Stages &bull; Zero Re-entry &bull; Zero Reconciliation Drift
            </h2>
            <p className="text-xs sm:text-sm text-[#77758A]">
              From purchase order weighment to customer dispatch and GST audit, each transaction updates the unified general ledger automatically.
            </p>
          </div>

          {/* Workflow Sequence Strip (Horizontally scrollable on mobile) */}
          <div className="flex overflow-x-auto gap-4 pb-4 sm:grid sm:grid-cols-6 sm:gap-3 no-scrollbar">
            {/* Step 1: Purchase */}
            <div className="flex-shrink-0 w-52 sm:w-auto p-4 rounded-2xl bg-white border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="h-9 w-9 rounded-xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-bold">
                    <ShoppingBag className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold text-[#7655E8] bg-[#F2EEFF] px-2 py-0.5 rounded-full">
                    Step 1
                  </span>
                </div>
                <h3 className="font-extrabold text-sm text-[#17152B]">Purchase</h3>
                <p className="text-xs text-[#77758A] mt-1">Vendor POs, RM/PM Receipts &amp; Weighment</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#EAE8F1] text-[10px] font-bold text-[#7655E8]">
                GRN Auto-Valuation
              </div>
            </div>

            {/* Step 2: Inventory */}
            <div className="flex-shrink-0 w-52 sm:w-auto p-4 rounded-2xl bg-white border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="h-9 w-9 rounded-xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-bold">
                    <Boxes className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold text-[#7655E8] bg-[#F2EEFF] px-2 py-0.5 rounded-full">
                    Step 2
                  </span>
                </div>
                <h3 className="font-extrabold text-sm text-[#17152B]">Inventory</h3>
                <p className="text-xs text-[#77758A] mt-1">Weighted-Avg Ledger &amp; Batch Shelves</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#EAE8F1] text-[10px] font-bold text-[#16A36A]">
                Zero Ghost Stock
              </div>
            </div>

            {/* Step 3: Production */}
            <div className="flex-shrink-0 w-52 sm:w-auto p-4 rounded-2xl bg-white border border-[#7655E8]/30 shadow-card hover:shadow-cardHover transition flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-12 h-12 bg-[#F2EEFF] rounded-bl-full pointer-events-none" />
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="h-9 w-9 rounded-xl bg-[#7655E8] text-white flex items-center justify-center font-bold shadow-xs">
                    <Factory className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold text-white bg-[#7655E8] px-2 py-0.5 rounded-full">
                    Step 3
                  </span>
                </div>
                <h3 className="font-extrabold text-sm text-[#17152B]">Production</h3>
                <p className="text-xs text-[#77758A] mt-1">Recipe BOMs, Work Orders &amp; Actual Output</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#EAE8F1] text-[10px] font-bold text-[#7655E8]">
                Yield &amp; Scrap Tracking
              </div>
            </div>

            {/* Step 4: Sales */}
            <div className="flex-shrink-0 w-52 sm:w-auto p-4 rounded-2xl bg-white border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="h-9 w-9 rounded-xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-bold">
                    <Receipt className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold text-[#7655E8] bg-[#F2EEFF] px-2 py-0.5 rounded-full">
                    Step 4
                  </span>
                </div>
                <h3 className="font-extrabold text-sm text-[#17152B]">Sales</h3>
                <p className="text-xs text-[#77758A] mt-1">Orders, Price Lists &amp; GST Invoices</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#EAE8F1] text-[10px] font-bold text-[#9675F5]">
                Auto HSN &amp; GSTR-1
              </div>
            </div>

            {/* Step 5: Dispatch */}
            <div className="flex-shrink-0 w-52 sm:w-auto p-4 rounded-2xl bg-white border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="h-9 w-9 rounded-xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-bold">
                    <Truck className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold text-[#7655E8] bg-[#F2EEFF] px-2 py-0.5 rounded-full">
                    Step 5
                  </span>
                </div>
                <h3 className="font-extrabold text-sm text-[#17152B]">Dispatch</h3>
                <p className="text-xs text-[#77758A] mt-1">Challans, Batch Allocation &amp; POD</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#EAE8F1] text-[10px] font-bold text-[#16A36A]">
                FIFO Expiry Lock
              </div>
            </div>

            {/* Step 6: Audit */}
            <div className="flex-shrink-0 w-52 sm:w-auto p-4 rounded-2xl bg-white border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="h-9 w-9 rounded-xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-bold">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <span className="text-[10px] font-bold text-[#7655E8] bg-[#F2EEFF] px-2 py-0.5 rounded-full">
                    Step 6
                  </span>
                </div>
                <h3 className="font-extrabold text-sm text-[#17152B]">Audit</h3>
                <p className="text-xs text-[#77758A] mt-1">Double-Entry Ledger, P&amp;L &amp; Trial Balance</p>
              </div>
              <div className="mt-3 pt-2 border-t border-[#EAE8F1] text-[10px] font-bold text-[#7655E8]">
                Statutory Export Center
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------- */}
      {/* SECTION 5: FOUR ENTERPRISE FEATURE CARDS                            */}
      {/* ------------------------------------------------------------------- */}
      <section id="features" className="py-16 bg-white border-b border-[#EAE8F1]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-2 mb-12">
            <span className="text-xs font-bold text-[#7655E8] uppercase tracking-wider bg-[#F2EEFF] px-3 py-1 rounded-full border border-[#EAE8F1]">
              INTELLIGENT ERP CAPABILITIES
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#17152B] tracking-tight">
              Engineered for Precision Food Manufacturing
            </h2>
            <p className="text-xs sm:text-sm text-[#77758A]">
              Designed around actual factory shop-floor constraints, raw material fluctuations, and compliance audits.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1: Smart Inventory */}
            <div className="p-6 rounded-3xl bg-[#FAFAFD] border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition duration-200 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-11 w-11 rounded-2xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                  <Boxes className="h-5 w-5" />
                </div>
                <h3 className="text-base font-extrabold text-[#17152B] tracking-tight">
                  SMART INVENTORY
                </h3>
                <p className="text-xs text-[#77758A] leading-relaxed">
                  Track raw materials, packaging and finished goods through a traceable stock ledger.
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-[#EAE8F1] space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Valuation Mode:</span>
                  <span className="font-bold text-[#17152B]">Moving Weighted Avg</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Negative Stock:</span>
                  <span className="font-bold text-[#16A36A]">Hard-locked at API</span>
                </div>
              </div>
            </div>

            {/* Feature 2: Production Intelligence */}
            <div className="p-6 rounded-3xl bg-[#FAFAFD] border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition duration-200 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-11 w-11 rounded-2xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                  <Factory className="h-5 w-5" />
                </div>
                <h3 className="text-base font-extrabold text-[#17152B] tracking-tight">
                  PRODUCTION INTELLIGENCE
                </h3>
                <p className="text-xs text-[#77758A] leading-relaxed">
                  Manage BOMs, actual consumption, production yield and cost per packet.
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-[#EAE8F1] space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Benchmark BOM:</span>
                  <span className="font-bold text-[#17152B]">Kai Murukku 200g</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Variance Alert:</span>
                  <span className="font-bold text-[#7655E8]">&plusmn;3% Tolerance</span>
                </div>
              </div>
            </div>

            {/* Feature 3: GST and Sales */}
            <div className="p-6 rounded-3xl bg-[#FAFAFD] border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition duration-200 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-11 w-11 rounded-2xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                  <Receipt className="h-5 w-5" />
                </div>
                <h3 className="text-base font-extrabold text-[#17152B] tracking-tight">
                  GST AND SALES
                </h3>
                <p className="text-xs text-[#77758A] leading-relaxed">
                  Manage customer orders, GST invoices, payments and dispatch operations.
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-[#EAE8F1] space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">GST Rate Engine:</span>
                  <span className="font-bold text-[#17152B]">5% (CGST 2.5% + SGST 2.5%)</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Exports:</span>
                  <span className="font-bold text-[#16A36A]">GSTR-1 &amp; GSTR-2</span>
                </div>
              </div>
            </div>

            {/* Feature 4: Audit and Analytics */}
            <div className="p-6 rounded-3xl bg-[#FAFAFD] border border-[#EAE8F1] shadow-card hover:shadow-cardHover transition duration-200 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-11 w-11 rounded-2xl bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <h3 className="text-base font-extrabold text-[#17152B] tracking-tight">
                  AUDIT AND ANALYTICS
                </h3>
                <p className="text-xs text-[#77758A] leading-relaxed">
                  Generate financial reports, reconcile stock and maintain complete transaction traceability.
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-[#EAE8F1] space-y-2 text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Double-Entry:</span>
                  <span className="font-bold text-[#16A36A]">Zero-Drift Balanced</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#77758A]">Export Formats:</span>
                  <span className="font-bold text-[#7655E8]">CSV, Excel, PDF</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------- */}
      {/* SECTION 7: TRUST, ARCHITECTURE & PLATFORM INFO                      */}
      {/* ------------------------------------------------------------------- */}
      <section id="architecture" className="py-14 bg-[#FAFAFD] border-b border-[#EAE8F1]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-3xl border border-[#EAE8F1] p-6 sm:p-8 shadow-card flex flex-col lg:flex-row items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#F2EEFF] text-[#7655E8] text-xs font-bold">
                <Layers className="h-3.5 w-3.5" />
                <span>Enterprise Architecture</span>
              </div>
              <h3 className="text-xl font-extrabold text-[#17152B]">
                High-Availability Serverless Cloud ERP
              </h3>
              <p className="text-xs sm:text-sm text-[#77758A] leading-relaxed">
                Powered by FastAPI 0.115 on Python 3.12, PostgreSQL 16 transactional backend, and React 18 with Vite.
                Every sales dispatch automatically posts double-entry inventory and GST ledger debits/credits without batch delays.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 w-full lg:w-auto text-center">
              <div className="p-3 bg-[#F8F7FC] rounded-2xl border border-[#EAE8F1]">
                <div className="text-lg font-extrabold text-[#7655E8]">18+</div>
                <div className="text-[11px] text-[#77758A]">Export Endpoints</div>
              </div>
              <div className="p-3 bg-[#F8F7FC] rounded-2xl border border-[#EAE8F1]">
                <div className="text-lg font-extrabold text-[#16A36A]">0.00%</div>
                <div className="text-[11px] text-[#77758A]">Ledger Drift</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------- */}
      {/* SECTION 7: FOOTER                                                   */}
      {/* ------------------------------------------------------------------- */}
      <footer className="py-8 bg-white text-xs text-[#77758A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-[#EAE8F1] pb-6">
            <div className="flex items-center space-x-2.5">
              <div className="h-7 w-7 rounded-xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white">
                <Factory className="h-3.5 w-3.5" />
              </div>
              <div>
                <span className="font-extrabold text-sm text-[#17152B]">
                  KANAKKU<span className="text-[#7655E8]">Flow</span> ERP
                </span>
                <span className="text-[10px] text-[#77758A] block">
                  Order-to-Audit Management Suite
                </span>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-6 text-[11px]">
              <a href="/api/health" target="_blank" rel="noreferrer" className="hover:text-[#7655E8] transition">
                System Health
              </a>
              <a href="/api/health/ready" target="_blank" rel="noreferrer" className="hover:text-[#7655E8] transition">
                DB Readiness
              </a>
              <a href="/api/docs" target="_blank" rel="noreferrer" className="hover:text-[#7655E8] transition">
                API Documentation
              </a>
              <a
                href="https://github.com/divakaranap/kanakkuflow_erp"
                target="_blank"
                rel="noreferrer"
                className="hover:text-[#7655E8] transition flex items-center space-x-1"
              >
                <span>GitHub Repository</span>
                <ExternalLink className="h-3 w-3 opacity-60" />
              </a>
            </div>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-[#77758A]">
            <p>
              &copy; 2026 KANAKKUFlow ERP. Built for Food Manufacturers &amp; Enterprise Operations.
            </p>
            <p className="text-[10px] text-[#77758A]/80">
              Research &amp; evaluation specification &bull; Centre for Digital Infrastructure &bull; NIT Tiruchirappalli
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
