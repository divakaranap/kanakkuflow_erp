import React from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  badgeText?: string
  actions?: React.ReactNode
}

export function PageHeader({ title, subtitle, badgeText, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-2">
      <div>
        <div className="flex items-center space-x-3">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17152B] tracking-tight">
            {title}
          </h1>
          {badgeText && (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1]">
              {badgeText}
            </span>
          )}
        </div>
        {subtitle && <p className="text-sm text-[#77758A] mt-1">{subtitle}</p>}
      </div>

      {actions && <div className="flex items-center space-x-2.5 flex-wrap gap-2">{actions}</div>}
    </div>
  )
}
