import React, { useState } from 'react'
import { Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react'
import { ReportDateFilter, type DateFilterValues } from './ReportDateFilter'
import { ReportExportCard, type ReportCardDef } from './ReportExportCard'
import { ReportPreviewModal } from './ReportPreviewModal'
import { ExportHistoryTable } from './ExportHistoryTable'
import { reportService } from '../../services/reportService'
import type { ReportPreviewData, ExportHistoryItem } from '../../types/reports'

const REPORT_CARDS: ReportCardDef[] = [
  {
    key: 'gstr1',
    title: 'GSTR-1 Sales Register',
    categoryBadge: 'Statutory GST',
    badgeBg: 'bg-[#F2EEFF]',
    badgeText: 'text-[#7655E8]',
    description:
      'Detailed outward supplies register with HSN breakdown, buyer GSTIN, taxable values, and calculated CGST, SGST, and IGST.',
    metricsHint: 'Buyer GSTIN, Taxable ₹, CGST, SGST, IGST, Total',
    reportPath: '/reports/gstr1',
    filenamePrefix: 'GSTR1_Sales_Register',
    requiresDateRange: true,
  },
  {
    key: 'gstr2',
    title: 'GSTR-2 Purchase Register',
    categoryBadge: 'Procurement Audit',
    badgeBg: 'bg-[#EBF9F1]',
    badgeText: 'text-[#16A36A]',
    description:
      'Inward procurement register recording supplier bill numbers, vendor GSTIN, raw material receipts, and eligible input tax credits.',
    metricsHint: 'Supplier GSTIN, Bill #, Taxable ₹, Input Tax ₹',
    reportPath: '/reports/purchase-register',
    filenamePrefix: 'GSTR2_Purchase_Register',
    requiresDateRange: true,
  },
  {
    key: 'stock_ledger',
    title: 'Stock Movement Ledger',
    categoryBadge: 'Inventory Subledger',
    badgeBg: 'bg-[#FFF6E6]',
    badgeText: 'text-[#E9A23B]',
    description:
      'Immutable item-level movement trail tracking opening balances, GRN receipts, production issues, dispatch deductions, and closing valuations.',
    metricsHint: 'Opening, Inward, Outward, Closing, Moving Weighted Cost',
    reportPath: '/reports/stock-movements',
    filenamePrefix: 'Stock_Movement_Ledger',
    requiresSnapshot: true,
  },
  {
    key: 'production_yield',
    title: 'Production Yield Variance',
    categoryBadge: 'Manufacturing Ops',
    badgeBg: 'bg-[#EFF6FF]',
    badgeText: 'text-[#3B82F6]',
    description:
      'Batch-by-batch physical output tracking planned vs actual yields, material consumption efficiency, unit packet costing, and wastage tolerances.',
    metricsHint: 'Batch #, Expected Pkts, Actual Good, Yield %, Cost/Pkt',
    reportPath: '/reports/production-variance',
    filenamePrefix: 'Production_Yield_Report',
    requiresDateRange: true,
  },
  {
    key: 'receivables_ageing',
    title: 'Receivables Ageing Analysis',
    categoryBadge: 'Working Capital',
    badgeBg: 'bg-[#FDF2F8]',
    badgeText: 'text-[#DB2777]',
    description:
      'Comprehensive debtor schedule categorizing overdue customer balances across five standardized ageing buckets: Not Due, 0–30, 31–60, 61–90, and >90 days.',
    metricsHint: 'Customer, Total Outstanding, 0-30d, 31-60d, >90d',
    reportPath: '/reports/receivables-ageing',
    filenamePrefix: 'Receivables_Ageing',
    requiresSnapshot: true,
  },
  {
    key: 'trial_balance',
    title: 'Financial Trial Balance',
    categoryBadge: 'Double-Entry GL',
    badgeBg: 'bg-[#F5F3FF]',
    badgeText: 'text-[#7C3AED]',
    description:
      'Strict double-entry ledger balance report proving zero mathematical discrepancy across Assets, Liabilities, Equity, Revenue, and Expense accounts.',
    metricsHint: 'COA Code, Opening Dr/Cr, Period Dr/Cr, Closing Dr/Cr',
    reportPath: '/reports/trial-balance',
    filenamePrefix: 'Trial_Balance',
    requiresSnapshot: true,
  },
]

export const ReportExportCenter: React.FC = () => {
  const todayStr = new Date().toISOString().slice(0, 10)
  const past30Str = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

  // Filters state
  const [filters, setFilters] = useState<DateFilterValues>({
    fromDate: past30Str,
    toDate: todayStr,
    asOfDate: todayStr,
  })

  // Export & Preview states
  const [activeExport, setActiveExport] = useState<{
    cardKey: string
    format: 'csv' | 'xlsx' | 'pdf'
  } | null>(null)
  const [previewCard, setPreviewCard] = useState<ReportCardDef | null>(null)
  const [previewData, setPreviewData] = useState<ReportPreviewData | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)
  const [history, setHistory] = useState<ExportHistoryItem[]>([])
  const [downloadingHistoryId, setDownloadingHistoryId] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  )

  const showToast = (type: 'success' | 'error', text: string) => {
    setToastMessage({ type, text })
    setTimeout(() => setToastMessage(null), 4000)
  }

  const getQueryParams = (_card?: ReportCardDef): Record<string, string> => {
    const params: Record<string, string> = {}
    if (filters.fromDate) params.from_date = filters.fromDate
    if (filters.toDate) params.to_date = filters.toDate
    if (filters.asOfDate) params.as_of_date = filters.asOfDate
    return params
  }

  // Handle Export
  const handleExport = async (card: ReportCardDef, format: 'csv' | 'xlsx' | 'pdf') => {
    try {
      setActiveExport({ cardKey: card.key, format })
      const params = getQueryParams(card)
      const downloadedFilename = await reportService.downloadReport(
        card.reportPath,
        format,
        card.filenamePrefix,
        params
      )

      // Add to session history
      const periodLabel = card.requiresDateRange
        ? `${filters.fromDate || 'Start'} to ${filters.toDate || 'Present'}`
        : `As of ${filters.asOfDate || 'Current'}`

      const historyItem: ExportHistoryItem = {
        id: `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        reportName: card.title,
        reportPath: card.reportPath,
        format,
        periodLabel,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'Ready',
        params,
      }

      setHistory((prev) => [historyItem, ...prev.slice(0, 19)])
      showToast('success', `Export generated successfully: ${downloadedFilename}`)
    } catch (err) {
      console.error('Export error:', err)
      const msg = err instanceof Error ? err.message : 'Report generation failed. Please try again.'
      showToast('error', msg)
    } finally {
      setActiveExport(null)
    }
  }

  // Handle Preview
  const handlePreview = async (card: ReportCardDef) => {
    try {
      setPreviewCard(card)
      setIsPreviewLoading(true)
      const params = getQueryParams(card)
      const data = await reportService.getReportPreview(card.reportPath, params)
      setPreviewData(data)
    } catch (err) {
      console.error('Preview error:', err)
      showToast('error', 'Failed to load report preview.')
      setPreviewCard(null)
    } finally {
      setIsPreviewLoading(false)
    }
  }

  // Re-download from history
  const handleRedownload = async (item: ExportHistoryItem) => {
    try {
      setDownloadingHistoryId(item.id)
      const matchedCard = REPORT_CARDS.find((c) => c.title === item.reportName)
      const prefix = matchedCard ? matchedCard.filenamePrefix : 'Report'
      await reportService.downloadReport(item.reportPath, item.format, prefix, item.params)
      showToast('success', `Saved ${item.reportName} (${item.format.toUpperCase()})`)
    } catch (err) {
      showToast('error', 'Could not re-download file.')
    } finally {
      setDownloadingHistoryId(null)
    }
  }

  return (
    <section className="mt-10 mb-8" id="report-export-center">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 animate-in slide-in-from-top-3 duration-300">
          <div
            className={`px-4 py-3 rounded-2xl shadow-lg border flex items-center gap-2.5 text-xs font-semibold ${
              toastMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-red-50 text-red-800 border-red-200'
            }`}
          >
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            )}
            <span>{toastMessage.text}</span>
          </div>
        </div>
      )}

      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#F2EEFF] text-[#7655E8]">
              Audit & Compliance
            </span>
            <h2 className="text-xl font-bold text-[#17152B]">
              Statutory &amp; Management Report Export Center
            </h2>
          </div>
          <p className="text-xs text-[#77758A] mt-1 max-w-3xl leading-relaxed">
            Generate audit-ready management reports directly from posted business transactions and immutable
            ledgers into CSV, Excel (.xlsx) and PDF.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-[#7655E8] bg-[#F8F7FC] border border-[#EAE8F1] px-3 py-1.5 rounded-xl">
          <Sparkles className="w-4 h-4 text-[#7655E8]" />
          <span>18 Real Export Endpoints</span>
        </div>
      </div>

      {/* Global Filter Bar */}
      <ReportDateFilter
        filters={filters}
        onChange={setFilters}
        onApply={() => {
          showToast('success', 'Global report parameters updated.')
        }}
        onReset={() => {
          setFilters({
            fromDate: past30Str,
            toDate: todayStr,
            asOfDate: todayStr,
          })
          showToast('success', 'Filters reset to default 30-day window.')
        }}
      />

      {/* 6 Report Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 mt-6">
        {REPORT_CARDS.map((card) => (
          <ReportExportCard
            key={card.key}
            card={card}
            onPreview={handlePreview}
            onExport={handleExport}
            activeExportFormat={
              activeExport?.cardKey === card.key ? activeExport.format : null
            }
            isPreviewLoading={isPreviewLoading && previewCard?.key === card.key}
          />
        ))}
      </div>

      {/* Export History Activity Table */}
      <ExportHistoryTable
        history={history}
        onClear={() => {
          setHistory([])
          showToast('success', 'Session export log cleared.')
        }}
        onRedownload={handleRedownload}
        isDownloadingId={downloadingHistoryId}
      />

      {/* Tabular Preview Modal */}
      <ReportPreviewModal
        isOpen={Boolean(previewCard)}
        onClose={() => {
          setPreviewCard(null)
          setPreviewData(null)
        }}
        data={previewData}
        isLoading={isPreviewLoading}
        reportName={previewCard?.title || 'Report Preview'}
        onExport={(format) => {
          if (previewCard) handleExport(previewCard, format)
        }}
        isExporting={Boolean(activeExport)}
      />
    </section>
  )
}
