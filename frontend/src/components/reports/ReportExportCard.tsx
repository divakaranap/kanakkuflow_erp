import React from 'react'
import { Eye, FileSpreadsheet, FileText, Download, Loader2 } from 'lucide-react'

export interface ReportCardDef {
  key: string
  title: string
  categoryBadge: string
  badgeBg: string
  badgeText: string
  description: string
  metricsHint: string
  reportPath: string
  filenamePrefix: string
  requiresDateRange?: boolean
  requiresSnapshot?: boolean
}

interface ReportExportCardProps {
  card: ReportCardDef
  onPreview: (card: ReportCardDef) => void
  onExport: (card: ReportCardDef, format: 'csv' | 'xlsx' | 'pdf') => void
  activeExportFormat?: 'csv' | 'xlsx' | 'pdf' | null
  isPreviewLoading?: boolean
}

export const ReportExportCard: React.FC<ReportExportCardProps> = ({
  card,
  onPreview,
  onExport,
  activeExportFormat = null,
  isPreviewLoading = false,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-[#EAE8F1] p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between group">
      <div>
        {/* Top Header with Badge */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${card.badgeBg} ${card.badgeText}`}
          >
            {card.categoryBadge}
          </span>
          <button
            type="button"
            onClick={() => onPreview(card)}
            disabled={isPreviewLoading}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#7655E8] hover:text-[#5e3ed4] bg-[#F2EEFF] hover:bg-[#e8e0fc] px-2.5 py-1 rounded-lg transition-colors disabled:opacity-50"
            title="Preview tabular data in modal"
          >
            {isPreviewLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Eye className="w-3.5 h-3.5" />
            )}
            Preview
          </button>
        </div>

        {/* Title & Description */}
        <h3 className="text-base font-bold text-[#17152B] group-hover:text-[#7655E8] transition-colors leading-snug">
          {card.title}
        </h3>
        <p className="text-xs text-[#77758A] mt-1.5 line-clamp-2 leading-relaxed">
          {card.description}
        </p>

        {/* Audit Details */}
        <div className="mt-3.5 pt-3 border-t border-[#F0EFF6] flex items-center justify-between text-[11px] text-[#77758A]">
          <span>Audit Fields:</span>
          <span className="font-medium text-[#17152B] truncate max-w-[180px]">{card.metricsHint}</span>
        </div>
      </div>

      {/* 3 Export Action Buttons */}
      <div className="mt-5 pt-3 border-t border-[#F0EFF6]">
        <div className="text-[11px] font-semibold text-[#77758A] uppercase tracking-wider mb-2">
          Download File
        </div>
        <div className="grid grid-cols-3 gap-2">
          {/* CSV Button */}
          <button
            type="button"
            onClick={() => onExport(card, 'csv')}
            disabled={Boolean(activeExportFormat)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-xl text-xs font-semibold border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] transition-all disabled:opacity-50"
          >
            {activeExportFormat === 'csv' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7655E8]" />
            ) : (
              <FileText className="w-3.5 h-3.5 text-[#7655E8]" />
            )}
            <span>CSV</span>
          </button>

          {/* Excel Button */}
          <button
            type="button"
            onClick={() => onExport(card, 'xlsx')}
            disabled={Boolean(activeExportFormat)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-xl text-xs font-semibold bg-[#EBF9F1] hover:bg-[#d8f5e4] text-[#16A36A] border border-[#d1f2e0] transition-all disabled:opacity-50"
          >
            {activeExportFormat === 'xlsx' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#16A36A]" />
            ) : (
              <FileSpreadsheet className="w-3.5 h-3.5 text-[#16A36A]" />
            )}
            <span>Excel</span>
          </button>

          {/* PDF Button */}
          <button
            type="button"
            onClick={() => onExport(card, 'pdf')}
            disabled={Boolean(activeExportFormat)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-xl text-xs font-semibold bg-[#F2EEFF] hover:bg-[#e6deff] text-[#7655E8] border border-[#e4dcfc] transition-all disabled:opacity-50"
          >
            {activeExportFormat === 'pdf' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7655E8]" />
            ) : (
              <Download className="w-3.5 h-3.5 text-[#7655E8]" />
            )}
            <span>PDF</span>
          </button>
        </div>
      </div>
    </div>
  )
}
