import React from 'react'
import { Calendar, RotateCcw, Filter, AlertCircle } from 'lucide-react'

export interface DateFilterValues {
  fromDate: string
  toDate: string
  asOfDate: string
}

interface ReportDateFilterProps {
  filters: DateFilterValues
  onChange: (filters: DateFilterValues) => void
  onApply: () => void
  onReset: () => void
  isLoading?: boolean
}

export const ReportDateFilter: React.FC<ReportDateFilterProps> = ({
  filters,
  onChange,
  onApply,
  onReset,
  isLoading = false,
}) => {
  const isInvalid = Boolean(filters.fromDate && filters.toDate && filters.fromDate > filters.toDate)

  const handlePreset = (type: 'this_month' | 'last_30_days' | 'q3_2026') => {
    const today = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const formatYMD = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

    if (type === 'this_month') {
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
      onChange({
        fromDate: formatYMD(firstDay),
        toDate: formatYMD(today),
        asOfDate: formatYMD(today),
      })
    } else if (type === 'last_30_days') {
      const past30 = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
      onChange({
        fromDate: formatYMD(past30),
        toDate: formatYMD(today),
        asOfDate: formatYMD(today),
      })
    } else if (type === 'q3_2026') {
      onChange({
        fromDate: '2026-07-01',
        toDate: '2026-09-30',
        asOfDate: '2026-09-30',
      })
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-[#EAE8F1] p-5 shadow-xs transition-all">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#F0EFF6]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-semibold">
            <Filter className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#17152B]">Global Report Parameters</h4>
            <p className="text-xs text-[#77758A]">
              Filter transaction periods and snapshot dates applied to all generated reports
            </p>
          </div>
        </div>

        {/* Preset Quick Filters */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-[#77758A] font-medium mr-1">Quick Presets:</span>
          <button
            type="button"
            onClick={() => handlePreset('this_month')}
            className="px-2.5 py-1 text-xs rounded-lg bg-[#F8F7FC] hover:bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1] transition-colors font-medium"
          >
            This Month
          </button>
          <button
            type="button"
            onClick={() => handlePreset('last_30_days')}
            className="px-2.5 py-1 text-xs rounded-lg bg-[#F8F7FC] hover:bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1] transition-colors font-medium"
          >
            Last 30 Days
          </button>
          <button
            type="button"
            onClick={() => handlePreset('q3_2026')}
            className="px-2.5 py-1 text-xs rounded-lg bg-[#F8F7FC] hover:bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1] transition-colors font-medium"
          >
            Q3 2026
          </button>
        </div>
      </div>

      {/* Date Input Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
        <div>
          <label className="block text-xs font-semibold text-[#77758A] mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#7655E8]" />
            Period From Date
          </label>
          <input
            type="date"
            value={filters.fromDate}
            onChange={(e) => onChange({ ...filters, fromDate: e.target.value })}
            className="w-full px-3 py-2 text-sm rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] text-[#17152B] focus:outline-none focus:border-[#7655E8] focus:bg-white transition-colors"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-[#77758A] mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#7655E8]" />
            Period To Date
          </label>
          <input
            type="date"
            value={filters.toDate}
            onChange={(e) => onChange({ ...filters, toDate: e.target.value })}
            className="w-full px-3 py-2 text-sm rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] text-[#17152B] focus:outline-none focus:border-[#7655E8] focus:bg-white transition-colors"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-[#77758A] mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#9675F5]" />
            As-Of Snapshot Date
          </label>
          <input
            type="date"
            value={filters.asOfDate}
            onChange={(e) => onChange({ ...filters, asOfDate: e.target.value })}
            className="w-full px-3 py-2 text-sm rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] text-[#17152B] focus:outline-none focus:border-[#7655E8] focus:bg-white transition-colors"
          />
        </div>
      </div>

      {isInvalid && (
        <div className="mt-3 flex items-center gap-2 p-2.5 rounded-lg bg-red-50 text-red-700 text-xs font-medium">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
          <span>Invalid range: "Period From Date" cannot be later than "Period To Date".</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-4 pt-3 flex items-center justify-between border-t border-[#F0EFF6]">
        <div className="text-xs text-[#77758A]">
          Applied: <span className="font-semibold text-[#17152B]">{filters.fromDate || 'All'}</span> to{' '}
          <span className="font-semibold text-[#17152B]">{filters.toDate || 'Present'}</span> • Snapshot:{' '}
          <span className="font-semibold text-[#7655E8]">{filters.asOfDate || 'Current'}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onReset}
            className="px-3 py-1.5 text-xs font-semibold rounded-xl border border-[#EAE8F1] bg-white text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B] transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Defaults
          </button>
          <button
            type="button"
            onClick={onApply}
            disabled={isInvalid || isLoading}
            className="px-4 py-1.5 text-xs font-semibold rounded-xl bg-[#7655E8] hover:bg-[#6846db] text-white shadow-xs disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-1.5"
          >
            {isLoading ? 'Updating...' : 'Apply Filters'}
          </button>
        </div>
      </div>
    </div>
  )
}
