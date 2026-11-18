import React from 'react'
import { History, Download, Trash2, CheckCircle2, FileSpreadsheet, FileText } from 'lucide-react'
import type { ExportHistoryItem } from '../../types/reports'

interface ExportHistoryTableProps {
  history: ExportHistoryItem[]
  onClear: () => void
  onRedownload: (item: ExportHistoryItem) => void
  isDownloadingId?: string | null
}

export const ExportHistoryTable: React.FC<ExportHistoryTableProps> = ({
  history,
  onClear,
  onRedownload,
  isDownloadingId = null,
}) => {
  if (history.length === 0) return null

  return (
    <div className="bg-white rounded-2xl border border-[#EAE8F1] p-5 shadow-xs mt-8">
      <div className="flex items-center justify-between pb-4 border-b border-[#F0EFF6]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#F2EEFF] text-[#7655E8] flex items-center justify-center font-semibold">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#17152B]">Session Export Activity</h4>
            <p className="text-xs text-[#77758A]">
              Audit trail of documents generated during this browser session
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClear}
          className="text-xs font-semibold text-[#77758A] hover:text-[#E05252] flex items-center gap-1.5 transition-colors px-2.5 py-1 rounded-lg hover:bg-red-50"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Clear Log
        </button>
      </div>

      <div className="overflow-x-auto mt-3">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#EAE8F1] text-[#77758A] font-semibold">
              <th className="py-2.5 px-3">Report Document</th>
              <th className="py-2.5 px-3">Format</th>
              <th className="py-2.5 px-3">Filter Period / Snapshot</th>
              <th className="py-2.5 px-3">Generated At</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F0EFF6]">
            {history.map((item) => (
              <tr key={item.id} className="hover:bg-[#FAFAFD] transition-colors">
                <td className="py-2.5 px-3 font-semibold text-[#17152B]">{item.reportName}</td>
                <td className="py-2.5 px-3">
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                      item.format === 'xlsx'
                        ? 'bg-[#EBF9F1] text-[#16A36A]'
                        : item.format === 'pdf'
                        ? 'bg-[#F2EEFF] text-[#7655E8]'
                        : 'bg-[#F8F7FC] text-[#17152B] border border-[#EAE8F1]'
                    }`}
                  >
                    {item.format === 'xlsx' ? (
                      <FileSpreadsheet className="w-3 h-3" />
                    ) : (
                      <FileText className="w-3 h-3" />
                    )}
                    {item.format.toUpperCase()}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-[#77758A]">{item.periodLabel}</td>
                <td className="py-2.5 px-3 text-[#77758A]">{item.timestamp}</td>
                <td className="py-2.5 px-3">
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#16A36A]">
                    <CheckCircle2 className="w-3 h-3 text-[#16A36A]" />
                    Ready
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right">
                  <button
                    type="button"
                    onClick={() => onRedownload(item)}
                    disabled={isDownloadingId === item.id}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-[#7655E8] hover:text-[#5e3ed4] hover:bg-[#F2EEFF] rounded-lg transition-colors disabled:opacity-50"
                  >
                    <Download className="w-3 h-3" />
                    {isDownloadingId === item.id ? 'Saving...' : 'Save File'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
