import { useState, useEffect, useRef } from 'react'
import {
  Search,
  Bell,
  Server,
  LogOut,
  ChevronDown,
  ShieldCheck,
  Clock,
  Package,
  Users,
  ShoppingCart,
  Receipt,
  Factory,
  Truck,
  Boxes,
  X,
  Loader2,
  ArrowRight,
} from 'lucide-react'
import type { UserInfo } from '../../types/auth'
import type { ERPView } from './AppSidebar'
import { searchService, type SearchResultItem } from '../../services/searchService'

interface AppHeaderProps {
  currentView: ERPView
  currentUser: UserInfo | null
  onLogout: () => void
  healthStatus: { status: string; database?: string } | null
  isSidebarCollapsed: boolean
  onSelectView?: (view: ERPView) => void
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
  settings: { title: 'System Settings & Audit Profile', breadcrumb: 'Settings' },
}

export function AppHeader({
  currentView,
  currentUser,
  onLogout,
  healthStatus,
  isSidebarCollapsed,
  onSelectView,
}: AppHeaderProps) {
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showNotificationMenu, setShowNotificationMenu] = useState(false)
  
  // Global search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const searchContainerRef = useRef<HTMLDivElement>(null)

  const meta = viewMeta[currentView] || { title: 'Dashboard', breadcrumb: 'ERP' }

  // Keyboard shortcut: Cmd/Ctrl + K to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        searchInputRef.current?.focus()
        searchInputRef.current?.select()
        setIsSearchOpen(true)
      } else if (e.key === 'Escape') {
        setIsSearchOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Close search when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced live search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      setIsSearching(false)
      return
    }

    const timer = setTimeout(async () => {
      setIsSearching(true)
      try {
        const res = await searchService.search(searchQuery)
        setSearchResults(res.results || [])
        setIsSearchOpen(true)
      } catch (err) {
        console.error('Search query failed:', err)
      } finally {
        setIsSearching(false)
      }
    }, 200)

    return () => clearTimeout(timer)
  }, [searchQuery])

  const handleSelectResult = (item: SearchResultItem) => {
    if (onSelectView) {
      onSelectView(item.view)
    }
    setIsSearchOpen(false)
    setSearchQuery('')
  }

  const getTypeIcon = (type: SearchResultItem['type']) => {
    switch (type) {
      case 'product':
        return <Package className="h-4 w-4 text-[#7655E8]" />
      case 'customer':
        return <Users className="h-4 w-4 text-blue-600" />
      case 'order':
        return <ShoppingCart className="h-4 w-4 text-emerald-600" />
      case 'invoice':
        return <Receipt className="h-4 w-4 text-indigo-600" />
      case 'production':
        return <Factory className="h-4 w-4 text-amber-600" />
      case 'dispatch':
        return <Truck className="h-4 w-4 text-cyan-600" />
      case 'raw_material':
        return <Boxes className="h-4 w-4 text-purple-600" />
      default:
        return <Search className="h-4 w-4 text-[#77758A]" />
    }
  }

  const getTypeBadgeClass = (type: SearchResultItem['type']) => {
    switch (type) {
      case 'product':
        return 'bg-[#F2EEFF] text-[#7655E8] border-[#EAE8F1]'
      case 'customer':
        return 'bg-blue-50 text-blue-700 border-blue-200'
      case 'order':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'invoice':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200'
      case 'production':
        return 'bg-amber-50 text-amber-700 border-amber-200'
      case 'dispatch':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200'
      case 'raw_material':
        return 'bg-purple-50 text-purple-700 border-purple-200'
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

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

      {/* Middle: Real-time Global Search */}
      <div ref={searchContainerRef} className="hidden md:flex items-center max-w-md w-full mx-6 relative">
        <div className="relative w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#77758A]" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onFocus={() => {
              if (searchQuery.trim().length > 0) setIsSearchOpen(true)
            }}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search orders, invoices, products, customers..."
            className="w-full pl-9 pr-14 py-2 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] placeholder-[#77758A] focus:outline-none focus:ring-2 focus:ring-[#7655E8]/20 focus:border-[#7655E8] transition-all"
          />

          <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center space-x-1.5">
            {isSearching ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-[#7655E8]" />
            ) : searchQuery ? (
              <button
                onClick={() => {
                  setSearchQuery('')
                  setSearchResults([])
                  setIsSearchOpen(false)
                }}
                className="p-0.5 text-[#77758A] hover:text-[#17152B] rounded transition-colors"
                title="Clear search"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            ) : (
              <span className="text-[10px] font-semibold text-[#77758A] bg-white border border-[#EAE8F1] px-1.5 py-0.5 rounded shadow-sm">
                ⌘K
              </span>
            )}
          </div>
        </div>

        {/* Search Results Dropdown Palette */}
        {isSearchOpen && searchQuery.trim().length > 0 && (
          <div className="absolute left-0 top-11 w-full bg-white rounded-2xl border border-[#EAE8F1] shadow-dropdown py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150 max-h-96 overflow-y-auto">
            <div className="px-3.5 py-1.5 border-b border-[#EAE8F1] flex items-center justify-between text-[11px] text-[#77758A]">
              <span className="font-semibold text-[#17152B]">
                {isSearching ? 'Searching...' : `Found ${searchResults.length} result(s)`}
              </span>
              <span>Press ESC to close</span>
            </div>

            {isSearching && (
              <div className="py-6 flex flex-col items-center justify-center space-y-2 text-[#77758A]">
                <Loader2 className="h-5 w-5 animate-spin text-[#7655E8]" />
                <span className="text-xs">Searching database...</span>
              </div>
            )}

            {!isSearching && searchResults.length === 0 && (
              <div className="py-6 px-4 text-center text-xs text-[#77758A]">
                No matching records found for <span className="font-semibold text-[#17152B]">"{searchQuery}"</span>
              </div>
            )}

            {!isSearching && searchResults.length > 0 && (
              <div className="divide-y divide-[#EAE8F1]/60">
                {searchResults.map((item) => (
                  <div
                    key={`${item.type}-${item.id}`}
                    onClick={() => handleSelectResult(item)}
                    className="px-3.5 py-2.5 hover:bg-[#F2EEFF]/50 transition-colors cursor-pointer flex items-center justify-between group"
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="h-8 w-8 min-w-8 rounded-lg bg-[#F8F7FC] border border-[#EAE8F1] flex items-center justify-center group-hover:border-[#7655E8]/30 transition-colors">
                        {getTypeIcon(item.type)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-[#17152B] truncate group-hover:text-[#7655E8] transition-colors">
                            {item.title}
                          </span>
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${getTypeBadgeClass(
                              item.type
                            )}`}
                          >
                            {item.badge}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#77758A] truncate mt-0.5">{item.subtitle}</p>
                      </div>
                    </div>
                    <div className="text-xs text-[#77758A] opacity-0 group-hover:opacity-100 flex items-center space-x-1 pl-2 text-[#7655E8] font-semibold transition-all">
                      <span>Jump</span>
                      <ArrowRight className="h-3 w-3" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
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
                  className="text-xs font-semibold text-[#7655E8] hover:underline"
                >
                  Mark all as read
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowProfileMenu(!showProfileMenu)
              setShowNotificationMenu(false)
            }}
            className="flex items-center space-x-2.5 p-1.5 pl-2.5 hover:bg-[#F8F7FC] rounded-xl transition-colors border border-transparent hover:border-[#EAE8F1]"
          >
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#7655E8] to-[#9675F5] text-white flex items-center justify-center font-bold text-xs shadow-sm">
              {currentUser?.username.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-bold text-[#17152B] leading-none">
                {currentUser?.username || 'User'}
              </span>
              <span className="text-[10px] text-[#77758A] font-semibold tracking-wide uppercase mt-0.5">
                {currentUser?.role || 'Guest'}
              </span>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-[#77758A]" />
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl border border-[#EAE8F1] shadow-dropdown py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="px-4 py-2 border-b border-[#EAE8F1]">
                <p className="text-xs font-bold text-[#17152B]">{currentUser?.full_name || currentUser?.username}</p>
                <p className="text-[11px] text-[#77758A] truncate">{currentUser?.email || 'user@kanakkuflow.erp'}</p>
                <div className="mt-1.5 inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#F2EEFF] text-[#7655E8] text-[10px] font-bold border border-[#EAE8F1]">
                  <ShieldCheck className="h-3 w-3" />
                  <span>{currentUser?.role} PRIVILEGES</span>
                </div>
              </div>

              <div className="py-1">
                <button
                  onClick={() => {
                    setShowProfileMenu(false)
                    onLogout()
                  }}
                  className="w-full px-4 py-2 text-left text-xs text-[#E05252] hover:bg-red-50 flex items-center space-x-2 transition-colors font-medium"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
