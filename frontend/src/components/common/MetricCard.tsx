import React from 'react'

interface MetricCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  badgeText?: string
  badgeVariant?: 'success' | 'warning' | 'danger' | 'info' | 'purple'
  subtitle?: string
  footer?: React.ReactNode
  iconBgColor?: string
  iconColor?: string
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  badgeText,
  badgeVariant = 'purple',
  subtitle,
  footer,
  iconBgColor = 'bg-[#F2EEFF]',
  iconColor = 'text-[#7655E8]',
}: MetricCardProps) {
  const getBadgeStyle = () => {
    switch (badgeVariant) {
      case 'success':
        return 'bg-emerald-50 text-[#16A36A] border-emerald-100'
      case 'warning':
        return 'bg-amber-50 text-[#E9A23B] border-amber-100'
      case 'danger':
        return 'bg-red-50 text-[#E05252] border-red-100'
      case 'info':
        return 'bg-blue-50 text-[#4385E8] border-blue-100'
      case 'purple':
      default:
        return 'bg-[#F2EEFF] text-[#7655E8] border-[#EAE8F1]'
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-[#EAE8F1] p-5 shadow-card hover:shadow-cardHover hover:-translate-y-0.5 transition-all duration-200 flex flex-col justify-between group">
      <div>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#77758A]">
              {title}
            </span>
            <div className="flex items-baseline space-x-2">
              <h3 className="text-2xl lg:text-3xl font-extrabold text-[#17152B] tracking-tight">
                {value}
              </h3>
              {badgeText && (
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${getBadgeStyle()}`}
                >
                  {badgeText}
                </span>
              )}
            </div>
            {subtitle && <p className="text-xs text-[#77758A] mt-1">{subtitle}</p>}
          </div>

          <div
            className={`h-11 w-11 rounded-xl ${iconBgColor} ${iconColor} flex items-center justify-center transition-transform duration-200 group-hover:scale-105 shadow-sm`}
          >
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </div>

      {footer && (
        <div className="mt-4 pt-3 border-t border-[#EAE8F1] text-xs text-[#77758A]">
          {footer}
        </div>
      )}
    </div>
  )
}
