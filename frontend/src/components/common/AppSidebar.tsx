import React from 'react'
import {
  LayoutDashboard,
  ShoppingCart,
  Truck,
  Receipt,
  Scale,
  Factory,
  Boxes,
  Database,
  Settings,
  ChevronRight,
  LogOut,
} from 'lucide-react'
import type { UserInfo } from '../../types/auth'

export type ERPView =
  | 'dashboard'
  | 'sales'
  | 'dispatch'
  | 'payments'
  | 'accounting'
  | 'production'
  | 'inventory'
  | 'masters'
  | 'settings'

interface AppSidebarProps {
  currentView: ERPView
  onSelectView: (view: ERPView) => void
  isCollapsed: boolean
  onToggleCollapse: () => void
  currentUser: UserInfo | null
  onLogout: () => void
}

export const navItems: { id: ERPView; label: string; icon: React.ElementType; badge?: string }[] = [
  { id: 'dashboard', label: 'Dashboard & Reports', icon: LayoutDashboard },
  { id: 'sales', label: 'Sales & Invoices', icon: ShoppingCart },
  { id: 'dispatch', label: 'Dispatch & Stock Out', icon: Truck },
  { id: 'payments', label: 'Payments & Ledger', icon: Receipt },
  { id: 'accounting', label: 'Accounting & Audit', icon: Scale },
  { id: 'production', label: 'Production & BOM', icon: Factory },
  { id: 'inventory', label: 'Inventory & Purchases', icon: Boxes },
  { id: 'masters', label: 'Master Data', icon: Database },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export function AppSidebar({
  currentView,
  onSelectView,
  isCollapsed,
  onToggleCollapse,
  currentUser,
  onLogout,
}: AppSidebarProps) {
  const getRoleBadgeStyle = (role?: string) => {
    switch (role) {
      case 'OWNER':
        return 'bg-[#F2EEFF] text-[#7655E8] border-[#EAE8F1]'
      case 'ADMIN':
        return 'bg-blue-50 text-blue-700 border-blue-100'
      case 'SALESMAN':
        return 'bg-emerald-50 text-emerald-700 border-emerald-100'
      case 'PRODUCTION':
        return 'bg-amber-50 text-amber-700 border-amber-100'
      case 'AUDITOR':
        return 'bg-purple-50 text-purple-700 border-purple-100'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen transition-all duration-300 ease-in-out bg-white border-r border-[#EAE8F1] flex flex-col justify-between shadow-[0_2px_12px_rgba(118,85,232,0.03)] ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#EAE8F1]">
          {!isCollapsed ? (
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="h-10 w-10 min-w-10 rounded-xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white shadow-md shadow-[#7655E8]/20">
                <Factory className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-1.5">
                  <span className="font-extrabold text-base tracking-tight text-[#17152B]">
                    KANAKKU<span className="text-[#7655E8]">FLOW</span>
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1]">
                    ERP
                  </span>
                </div>
                <span className="text-[11px] text-[#77758A] font-medium truncate">Order-to-Audit Suite</span>
              </div>
            </div>
          ) : (
            <div className="mx-auto">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white shadow-md shadow-[#7655E8]/20">
                <Factory className="h-5 w-5" />
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Nav Items */}
        <div className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-140px)]">
          <div className={`px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-[#77758A] ${isCollapsed ? 'text-center' : ''}`}>
            {isCollapsed ? '•••' : 'Management'}
          </div>

          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id
            return (
              <button
                key={item.id}
                onClick={() => onSelectView(item.id)}
                title={isCollapsed ? item.label : undefined}
                className={`w-full flex items-center ${
                  isCollapsed ? 'justify-center px-0' : 'justify-between px-3.5'
                } py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group relative ${
                  isActive
                    ? 'bg-[#F2EEFF] text-[#7655E8] shadow-sm font-semibold'
                    : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`p-1 rounded-lg transition-colors ${
                      isActive
                        ? 'text-[#7655E8]'
                        : 'text-[#77758A] group-hover:text-[#7655E8]'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                </div>

                {!isCollapsed && isActive && (
                  <div className="h-2 w-2 rounded-full bg-[#7655E8]"></div>
                )}

                {/* Tooltip on collapse */}
                {isCollapsed && (
                  <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-[#17152B] text-white text-xs font-medium rounded-lg whitespace-nowrap shadow-dropdown opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                    {item.label}
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Bottom User Profile Section */}
      <div className="p-3 border-t border-[#EAE8F1] bg-[#FAFAFD]">
        {currentUser ? (
          <div
            className={`flex items-center ${
              isCollapsed ? 'justify-center' : 'justify-between'
            } p-2 rounded-xl hover:bg-white transition-colors border border-transparent hover:border-[#EAE8F1]`}
          >
            {!isCollapsed ? (
              <div className="flex items-center space-x-3 overflow-hidden">
                <div className="h-9 w-9 min-w-9 rounded-full bg-gradient-to-tr from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white font-bold text-xs shadow-sm">
                  {currentUser.full_name?.charAt(0) || 'U'}
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-bold text-[#17152B] truncate">{currentUser.full_name}</span>
                  <div className="flex items-center space-x-1 mt-0.5">
                    <span
                      className={`text-[10px] font-semibold px-1.5 py-0.2 rounded-full border ${getRoleBadgeStyle(
                        currentUser.role
                      )}`}
                    >
                      {currentUser.role}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div
                className="h-9 w-9 rounded-full bg-gradient-to-tr from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white font-bold text-xs shadow-sm"
                title={`${currentUser.full_name} (${currentUser.role})`}
              >
                {currentUser.full_name?.charAt(0) || 'U'}
              </div>
            )}

            {!isCollapsed && (
              <button
                onClick={onLogout}
                className="p-1.5 text-[#77758A] hover:text-[#E05252] hover:bg-red-50 rounded-lg transition-colors"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="text-center py-1">
            {!isCollapsed && <span className="text-xs text-[#77758A]">Guest Session</span>}
          </div>
        )}

        {isCollapsed && (
          <button
            onClick={onToggleCollapse}
            className="w-full mt-2 p-1.5 text-[#77758A] hover:text-[#17152B] hover:bg-white rounded-lg flex justify-center transition-colors border border-transparent hover:border-[#EAE8F1]"
            title="Expand sidebar"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </aside>
  )
}
