export type StatusVariant =
  | 'POSTED'
  | 'DRAFT'
  | 'FULFILLED'
  | 'DISPATCHED'
  | 'DELIVERED'
  | 'CLEARED'
  | 'RECORDED'
  | 'CANCELLED'
  | 'NORMAL'
  | 'WARNING'
  | 'CRITICAL'
  | 'ACTIVE'
  | 'INACTIVE'
  | 'RETAILER'
  | 'DISTRIBUTOR'
  | string

interface StatusBadgeProps {
  status: StatusVariant
  className?: string
  dot?: boolean
}

export function StatusBadge({ status, className = '', dot = true }: StatusBadgeProps) {
  const norm = String(status || '').toUpperCase()

  let style = 'bg-gray-50 text-[#77758A] border-[#EAE8F1]'
  let dotColor = 'bg-[#77758A]'

  if (['POSTED', 'FULFILLED', 'DELIVERED', 'CLEARED', 'NORMAL', 'ACTIVE'].includes(norm)) {
    style = 'bg-emerald-50 text-[#16A36A] border-emerald-100'
    dotColor = 'bg-[#16A36A]'
  } else if (['DISPATCHED', 'DISTRIBUTOR', 'INFO'].includes(norm)) {
    style = 'bg-[#F2EEFF] text-[#7655E8] border-[#EAE8F1]'
    dotColor = 'bg-[#7655E8]'
  } else if (['WARNING', 'RECORDED', 'DRAFT'].includes(norm)) {
    style = 'bg-amber-50 text-[#E9A23B] border-amber-100'
    dotColor = 'bg-[#E9A23B]'
  } else if (['CRITICAL', 'CANCELLED', 'INACTIVE', 'BOUNCED'].includes(norm)) {
    style = 'bg-red-50 text-[#E05252] border-red-100'
    dotColor = 'bg-[#E05252]'
  } else if (['RETAILER'].includes(norm)) {
    style = 'bg-blue-50 text-[#4385E8] border-blue-100'
    dotColor = 'bg-[#4385E8]'
  }

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${style} ${className}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />}
      <span>{norm}</span>
    </span>
  )
}
