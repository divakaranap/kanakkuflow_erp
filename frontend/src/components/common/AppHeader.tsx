import { useState } from 'react'
import {
  Search,
  Bell,
  Server,
  LogOut,
  ChevronDown,
  ShieldCheck,
  Clock,
} from 'lucide-react'
import type { UserInfo } from '../../types/auth'
import type { ERPView } from './AppSidebar'

interface AppHeaderProps {
  currentView: ERPView
  currentUser: UserInfo | null
  onLogout: () => void
  healthStatus: { status: string; database?: string } | null
  isSidebarCollapsed: boolean
}

const viewMeta: Record<ERPView, { title: string; breadcrumb: string }> = {
  dashboard: { title: 'Executive Analytics', breadcrumb: 'Dashboard' },
  sales: { title: 'Sales Orders & GST Invoicing', breadcrumb: 'Sales & Invoices' },
  dispatch: { title: 'Dispatch & Stock Out', breadcrumb: 'Dispatch' },
  payments: { title: 'Payments & Receivables Ledger', breadcrumb: 'Payments' },
  accounting: { title: 'Accounting & Audit Trail', breadcrumb: 'Finance' },
  production: { title: 'Production & Recipe BOM Engine', breadcrumb: 'Manufacturing' },
  inventory: { title: 'Inventory Movement & Valuations', breadcrumb: 'Inventory' },
  masters: { title: 'Master Data Management', breadcrumb: 'Configuration' },
}

export function AppHeader({
  currentView,
  currentUser,
  onLogout,
  healthStatus,
  isSidebarCollapsed,
}: AppHeaderProps) {
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showNotificationMenu, setShowNotificationMenu] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const meta = viewMeta[currentView] || { title: 'Dashboard', breadcrumb: 'ERP' }

  const notifications = [
    {
      id: 1,
      title: 'Batch BATCH-MUR-001 completed',
      time: '10m ago',
      type: 'info',
      desc: '238 good packets produced (-4.8% yield variance)',
    },
    {
      id: 2,
      title: 'Payment Received: ₹4,000.00',
      time: '25m ago',
      type: 'success',
      desc: 'NEFT credit from Retailer A against INV-202611-0001',
    },
    {
      id: 3,
      title: 'Stock Ledger Reconciled',
      time: '1h ago',
      type: 'success',
      desc: 'Finished goods and raw material balances updated',
    },
  ]

  return (
    <header
      className={`h-16 bg-white border-b border-[#EAE8F1] px-6 flex items-center justify-between sticky top-0 z-30 transition-all duration-300 ${
        isSidebarCollapsed ? 'ml-20' : 'ml-64'
      }`}
    >
      {/* Left: Breadcrumbs & Page Title */}
      <div className="flex items-center space-x-3">
        <div className="flex flex-col">
          <div className="flex items-center space-x-2 text-xs text-[#77758A]">
            <span>Kanakkuflow</span>
            <span>/</span>
            <span className="text-[#7655E8] font-medium">{meta.breadcrumb}</span>
          </div>
          <h1 className="text-lg font-bold text-[#17152B] tracking-tight">{meta.title}</h1>
        </div>
      </div>

      {/* Middle: Global Search */}
      <div className="hidden md:flex items-center max-w-md w-full mx-6">
        <div className="relative w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#77758A]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search orders, invoices, products, customers..."
            className="w-full pl-9 pr-12 py-2 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] placeholder-[#77758A] focus:outline-none focus:ring-2 focus:ring-[#7655E8]/20 focus:border-[#7655E8] transition-all"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-[#77758A] bg-white border border-[#EAE8F1] px-1.5 py-0.5 rounded">
            ⌘K
          </span>
        </div>
      </div>

      {/* Right: Actions, Health, Notifications & Profile */}
      <div className="flex items-center space-x-3">
        {/* Backend Status Indicator */}
        <div className="flex items-center space-x-2 text-xs bg-[#F8F7FC] px-3 py-1.5 rounded-xl border border-[#EAE8F1]">
          <Server className="h-3.5 w-3.5 text-[#77758A]" />
          <span className="text-[#77758A] font-medium hidden sm:inline">Backend:</span>
          {healthStatus?.status === 'ok' ? (
            <span className="flex items-center text-[#16A36A] font-semibold">
              <span className="h-2 w-2 rounded-full bg-[#16A36A] mr-1.5 animate-pulse"></span>
              Connected
            </span>
          ) : (
            <span className="flex items-center text-[#E9A23B] font-semibold">
              <span className="h-2 w-2 rounded-full bg-[#E9A23B] mr-1.5"></span>
              {healthStatus?.status || 'Connecting...'}
            </span>
          )}
        </div>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotificationMenu(!showNotificationMenu)
              setShowProfileMenu(false)
            }}
            className="p-2 text-[#77758A] hover:text-[#17152B] hover:bg-[#F8F7FC] rounded-xl transition-colors relative border border-[#EAE8F1]"
            title="Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#7655E8] ring-2 ring-white"></span>
          </button>

          {showNotificationMenu && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl border border-[#EAE8F1] shadow-dropdown py-3 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="px-4 pb-2 border-b border-[#EAE8F1] flex items-center justify-between">
                <span className="text-xs font-bold text-[#17152B]">System Activity & Alerts</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#F2EEFF] text-[#7655E8]">
                  3 New
                </span>
              </div>
              <div className="divide-y divide-[#EAE8F1] max-h-72 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="p-3 hover:bg-[#F8F7FC] transition-colors cursor-pointer">
                    <div className="flex items-start justify-between">
                      <span className="text-xs font-semibold text-[#17152B]">{n.title}</span>
                      <span className="text-[10px] text-[#77758A] flex items-center gap-1">
                        <Clock className="h-3 w-3" /> {n.time}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#77758A] mt-0.5 leading-relaxed">{n.desc}</p>
                  </div>
                ))}
              </div>
              <div className="px-3 pt-2 border-t border-[#EAE8F1] text-center">
                <button
                  onClick={() => setShowNotificationMenu(false)}
                  className="text-[11px] font-semibold text-[#7655E8] hover:underline"
                >
                  Mark all as read
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Dropdown */}
        {currentUser && (
          <div className="relative">
            <button
              onClick={() => {
                setShowProfileMenu(!showProfileMenu)
                setShowNotificationMenu(false)
              }}
              className="flex items-center space-x-2.5 p-1.5 rounded-xl hover:bg-[#F8F7FC] transition-colors border border-[#EAE8F1]"
            >
              <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white font-bold text-xs shadow-sm">
                {currentUser.full_name?.charAt(0) || 'U'}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-bold text-[#17152B] leading-none">{currentUser.username}</span>
                <span className="text-[10px] text-[#77758A] leading-tight font-medium mt-0.5">
                  {currentUser.role}
                </span>
              </div>
              <ChevronDown className="h-3.5 w-3.5 text-[#77758A]" />
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl border border-[#EAE8F1] shadow-dropdown py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                <div className="px-4 py-2 border-b border-[#EAE8F1]">
                  <p className="text-xs font-bold text-[#17152B]">{currentUser.full_name}</p>
                  <p className="text-[11px] text-[#77758A] truncate">{currentUser.email}</p>
                  <div className="mt-1.5 inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#F2EEFF] text-[#7655E8] text-[10px] font-semibold">
                    <ShieldCheck className="h-3 w-3" />
                    <span>Role: {currentUser.role}</span>
                  </div>
                </div>

                <div className="py-1">
                  <div className="px-4 py-1.5 text-[11px] text-[#77758A]">
                    Access Level: <span className="text-[#17152B] font-medium">{currentUser.role}</span>
                  </div>
                </div>

                <div className="pt-1 border-t border-[#EAE8F1]">
                  <button
                    onClick={() => {
                      setShowProfileMenu(false)
                      onLogout()
                    }}
                    className="w-full px-4 py-2 text-left text-xs text-[#E05252] hover:bg-red-50 flex items-center space-x-2 transition-colors font-medium"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    <span>Sign Out of FactoryFlow</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
