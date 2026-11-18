import React, { useState, useMemo } from 'react'
import { X, Search, Download, FileSpreadsheet, FileText, CheckCircle2 } from 'lucide-react'
import type { ReportPreviewData } from '../../types/reports'

interface ReportPreviewModalProps {
  isOpen: boolean
  onClose: () => void
  data: ReportPreviewData | null
  isLoading: boolean
  reportName: string
  onExport: (format: 'csv' | 'xlsx' | 'pdf') => void
  isExporting?: boolean
}

export const ReportPreviewModal: React.FC<ReportPreviewModalProps> = ({
  isOpen,
  onClose,
  data,
  isLoading,
  reportName,
  onExport,
  isExporting = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredRows = useMemo(() => {
    if (!data?.rows) return []
    if (!searchTerm.trim()) return data.rows

    const term = searchTerm.toLowerCase().trim()
    return data.rows.filter((row) => {
      // Always keep total row visible
      const isTotal = String(row[0]).toUpperCase() === 'TOTAL'
      if (isTotal) return true
      return row.some((cell) => String(cell || '').toLowerCase().includes(term))
    })
  }, [data, searchTerm])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-[#17152B]/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl border border-[#EAE8F1] shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#F0EFF6] bg-[#FAFAFD]">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#F2EEFF] text-[#7655E8]">
                Audit Preview
              </span>
              <h3 className="text-base font-bold text-[#17152B]">{reportName}</h3>
            </div>
            <p className="text-xs text-[#77758A] mt-0.5">
              {data?.date_info || 'Immutable ledger transaction records'} &bull;{' '}
              <span className="font-semibold text-[#17152B]">{data?.total_records ?? 0} posted records</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#77758A] hover:text-[#17152B] hover:bg-[#EAE8F1] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar & Search */}
        <div className="p-4 border-b border-[#F0EFF6] flex flex-col sm:flex-row items-center justify-between gap-3 bg-white">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-[#77758A] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search in preview data..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] text-[#17152B] focus:outline-none focus:border-[#7655E8] focus:bg-white transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <span className="text-xs text-[#77758A] font-medium mr-1 hidden sm:inline">Export As:</span>
            <button
              type="button"
              disabled={isExporting || isLoading}
              onClick={() => onExport('csv')}
              className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-[#F8F7FC] text-[#17152B] border border-[#EAE8F1] transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <FileText className="w-3.5 h-3.5 text-[#7655E8]" />
              CSV
            </button>
            <button
              type="button"
              disabled={isExporting || isLoading}
              onClick={() => onExport('xlsx')}
              className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-[#EBF9F1] hover:bg-[#d8f5e4] text-[#16A36A] border border-[#d1f2e0] transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              Excel (.xlsx)
            </button>
            <button
              type="button"
              disabled={isExporting || isLoading}
              onClick={() => onExport('pdf')}
              className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-[#F2EEFF] hover:bg-[#e6deff] text-[#7655E8] border border-[#e4dcfc] transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              PDF
            </button>
          </div>
        </div>

        {/* Modal Table Content */}
        <div className="flex-1 overflow-auto p-4 bg-[#FAFAFD]">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 text-[#77758A]">
              <div className="w-8 h-8 border-2 border-[#7655E8] border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-xs font-medium">Querying ledger records & calculating balances...</p>
            </div>
          ) : !data || filteredRows.length === 0 ? (
            <div className="text-center py-20 text-[#77758A]">
              <p className="text-sm font-semibold text-[#17152B]">No records found</p>
              <p className="text-xs mt-1">Try adjusting the filter range or clearing your search term.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-[#EAE8F1] overflow-hidden shadow-xs">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-[#F8F7FC] border-b border-[#EAE8F1] text-[#17152B]">
                    {data.headers.map((h, i) => (
                      <th key={i} className="px-3.5 py-2.5 font-bold whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0EFF6]">
                  {filteredRows.map((row, rIdx) => {
                    const isTotal = String(row[0]).toUpperCase() === 'TOTAL'
                    return (
                      <tr
                        key={rIdx}
                        className={
                          isTotal
                            ? 'bg-[#F2EEFF]/60 font-bold text-[#17152B] border-t-2 border-b border-[#7655E8]/30'
                            : 'hover:bg-[#FAFAFD] text-[#2B2844] transition-colors'
                        }
                      >
                        {row.map((val, cIdx) => (
                          <td
                            key={cIdx}
                            className={`px-3.5 py-2 whitespace-nowrap ${
                              String(val).startsWith('₹') || (!isNaN(Number(val)) && val !== '')
                                ? 'text-right'
                                : 'text-left'
                            }`}
                          >
                            {val ?? '—'}
                          </td>
                        ))}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-[#F0EFF6] bg-white flex items-center justify-between text-xs text-[#77758A]">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#16A36A]" />
            <span>Directly verified from double-entry accounting journals & stock balances.</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-[#FAFAFD] hover:bg-[#F2EEFF] text-[#17152B] border border-[#EAE8F1] transition-colors"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  )
}
