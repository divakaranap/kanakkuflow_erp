import { useState, useEffect } from 'react'
import {
  TrendingUp,
  Package,
  Layers,
  IndianRupee,
  Download,
  Calendar,
  FileSpreadsheet,
  FileText,
  AlertCircle,
  RefreshCw,
  Users,
  CheckCircle2,
} from 'lucide-react'
import { reportService } from '../../services/reportService'
import type { DashboardSummary } from '../../types/reports'

export function ExecutiveDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [downloading, setDownloading] = useState<string>('')

  // Report Export Filter States
  const [fromDate, setFromDate] = useState<string>(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  )
  const [toDate, setToDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [asOfDate, setAsOfDate] = useState<string>(new Date().toISOString().split('T')[0])

  useEffect(() => {
    loadSummary()
  }, [])

  const loadSummary = async () => {
    try {
      setLoading(true)
      setErrorMsg('')
      const data = await reportService.getDashboardSummary()
      setSummary(data)
    } catch (err: any) {
      console.error('Failed to load dashboard summary:', err)
      setErrorMsg(err.response?.data?.detail || 'Failed to load executive analytics summary')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (
    reportPath: string,
    format: 'csv' | 'xlsx' | 'pdf',
    filenamePrefix: string,
    reportKey: string,
    params?: Record<string, string>
  ) => {
    try {
      setDownloading(reportKey)
      await reportService.downloadReport(reportPath, format, filenamePrefix, params)
    } catch (err: any) {
      console.error(`Export failed for ${reportKey}:`, err)
      alert(err.response?.data?.detail || `Failed to export ${filenamePrefix} (${format.toUpperCase()})`)
    } finally {
      setDownloading('')
    }
  }

  const formatCurrency = (paise: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100)
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Executive Management Analytics</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
              Real-time Ledger
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            End-to-end operational KPIs, factory floor yields, financial health and statutory audit exports.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadSummary}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3.5 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Sales KPI */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Net Sales Revenue</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {summary ? formatCurrency(summary.sales.total_revenue_paise) : '—'}
              </h3>
            </div>
            <div className="p-2.5 bg-emerald-50 rounded-lg text-emerald-600">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Orders: {summary?.sales.orders_count || 0}</span>
            <span>Invoices: {summary?.sales.invoices_count || 0}</span>
            <span>Tax: {summary ? formatCurrency(summary.sales.total_tax_paise) : '—'}</span>
          </div>
        </div>

        {/* Production KPI */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Finished Goods Output</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {summary ? `${summary.production.total_packets_produced.toLocaleString()} Pkts` : '—'}
              </h3>
            </div>
            <div className="p-2.5 bg-blue-50 rounded-lg text-blue-600">
              <Package className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Runs: {summary?.production.completed_runs_count || 0} completed</span>
            <span
              className={`font-semibold ${
                (summary?.production.avg_yield_variance_pct || 0) < 0
                  ? 'text-amber-600'
                  : 'text-emerald-600'
              }`}
            >
              Yield Var: {summary?.production.avg_yield_variance_pct || 0}%
            </span>
          </div>
        </div>

        {/* Inventory KPI */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Inventory Valuation</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {summary ? formatCurrency(summary.inventory.total_valuation_paise) : '—'}
              </h3>
            </div>
            <div className="p-2.5 bg-purple-50 rounded-lg text-purple-600">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>RM: {summary ? formatCurrency(summary.inventory.raw_materials_paise) : '—'}</span>
            <span>FG: {summary ? formatCurrency(summary.inventory.finished_goods_paise) : '—'}</span>
          </div>
        </div>

        {/* Finance Receivables KPI */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Receivables</p>
              <h3 className="text-2xl font-bold text-gray-900 mt-1">
                {summary ? formatCurrency(summary.finance.total_receivables_paise) : '—'}
              </h3>
            </div>
            <div className="p-2.5 bg-amber-50 rounded-lg text-amber-600">
              <IndianRupee className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Collected: {summary ? formatCurrency(summary.finance.total_collections_paise) : '—'}</span>
            <span className="text-red-600 font-semibold">
              &gt;30d: {summary ? formatCurrency(summary.finance.over_30_days_paise) : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Two Column Grid: Top Selling Products and Top Debtors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Selling Products */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-gray-500" />
              <h2 className="text-base font-semibold text-gray-900">Top Selling Products</h2>
            </div>
            <span className="text-xs text-gray-500">By Total Revenue</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead>
                <tr className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="pb-3">Product Name</th>
                  <th className="pb-3 text-right">Quantity Sold</th>
                  <th className="pb-3 text-right">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {summary && summary.top_products.length > 0 ? (
                  summary.top_products.map((p, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/50">
                      <td className="py-2.5 font-medium text-gray-800">{p.product_name}</td>
                      <td className="py-2.5 text-right text-gray-600">{p.total_quantity.toLocaleString()} pkts</td>
                      <td className="py-2.5 text-right font-semibold text-gray-900">
                        {formatCurrency(p.total_revenue_paise)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-4 text-center text-gray-400 text-xs">
                      No sales records available yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Debtors & Outstanding */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-gray-500" />
              <h2 className="text-base font-semibold text-gray-900">Top Debtors & Ageing Exposure</h2>
            </div>
            <span className="text-xs text-gray-500">Active Balances</span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead>
                <tr className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="pb-3">Customer</th>
                  <th className="pb-3 text-right">Outstanding</th>
                  <th className="pb-3 text-right">&gt; 30 Days Overdue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {summary && summary.top_debtors.length > 0 ? (
                  summary.top_debtors.map((d, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/50">
                      <td className="py-2.5 font-medium text-gray-800">{d.customer_name}</td>
                      <td className="py-2.5 text-right font-semibold text-gray-900">
                        {formatCurrency(d.outstanding_paise)}
                      </td>
                      <td className="py-2.5 text-right text-red-600 font-medium">
                        {formatCurrency(d.over_30_days_paise)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-4 text-center text-gray-400 text-xs">
                      All customer receivables are fully settled.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* One-Click Statutory & Audit Export Center */}
      <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-6">
        <div className="border-b border-gray-100 pb-4">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-gray-900">Statutory & Management Report Export Center</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Export unmanipulated, audit-ready reports directly from database ledgers into CSV, Excel (.xlsx), and PDF.
          </p>
        </div>

        {/* Global Export Filter Bar */}
        <div className="flex flex-wrap items-center gap-4 bg-gray-50 p-4 rounded-lg border border-gray-200/60 text-sm">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="font-medium text-gray-700">Period:</span>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">From:</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-gray-300 rounded-md text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500">To:</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-gray-300 rounded-md text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-xs text-gray-500">Snapshot As-Of:</label>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-gray-300 rounded-md text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Export Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* GSTR-1 Sales */}
          <div className="p-4 rounded-lg border border-gray-200 bg-white hover:border-blue-200 transition-all shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <FileSpreadsheet className="w-4 h-4" />
                <h3 className="font-semibold text-gray-900 text-sm">GSTR-1 Sales Register</h3>
              </div>
              <p className="text-xs text-gray-500">
                GSTIN, taxable values, IGST/CGST/SGST breakdown, and invoice totals.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() =>
                  handleExport('/reports/gstr1', 'csv', 'GSTR1_Sales', 'gstr1-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr1-csv'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-gray-300 hover:bg-gray-50 text-gray-700 text-center"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/gstr1', 'xlsx', 'GSTR1_Sales', 'gstr1-xlsx', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr1-xlsx'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-center"
              >
                Excel
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/gstr1', 'pdf', 'GSTR1_Sales', 'gstr1-pdf', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr1-pdf'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100 text-center"
              >
                PDF
              </button>
            </div>
          </div>

          {/* GSTR-2 Purchases */}
          <div className="p-4 rounded-lg border border-gray-200 bg-white hover:border-blue-200 transition-all shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <FileSpreadsheet className="w-4 h-4" />
                <h3 className="font-semibold text-gray-900 text-sm">GSTR-2 Purchase Register</h3>
              </div>
              <p className="text-xs text-gray-500">
                Supplier GSTIN, GRN inward vouchers, raw materials purchases and ITC eligible.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() =>
                  handleExport('/reports/gstr2', 'csv', 'GSTR2_Purchases', 'gstr2-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr2-csv'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-gray-300 hover:bg-gray-50 text-gray-700 text-center"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/gstr2', 'xlsx', 'GSTR2_Purchases', 'gstr2-xlsx', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr2-xlsx'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-center"
              >
                Excel
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/gstr2', 'pdf', 'GSTR2_Purchases', 'gstr2-pdf', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr2-pdf'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100 text-center"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Stock Movement Ledger */}
          <div className="p-4 rounded-lg border border-gray-200 bg-white hover:border-blue-200 transition-all shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-emerald-600 mb-1">
                <Layers className="w-4 h-4" />
                <h3 className="font-semibold text-gray-900 text-sm">Stock Movement Ledger</h3>
              </div>
              <p className="text-xs text-gray-500">
                Full chronological ledger for RM, Packaging & FG stock ins and outs.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() =>
                  handleExport('/reports/stock-movement', 'csv', 'Stock_Movement_Ledger', 'stock-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'stock-csv'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-gray-300 hover:bg-gray-50 text-gray-700 text-center"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/stock-movement', 'xlsx', 'Stock_Movement_Ledger', 'stock-xlsx', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'stock-xlsx'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-center"
              >
                Excel
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/stock-movement', 'pdf', 'Stock_Movement_Ledger', 'stock-pdf', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'stock-pdf'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100 text-center"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Production Yield Variance */}
          <div className="p-4 rounded-lg border border-gray-200 bg-white hover:border-blue-200 transition-all shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <Package className="w-4 h-4" />
                <h3 className="font-semibold text-gray-900 text-sm">Production Yield Variance</h3>
              </div>
              <p className="text-xs text-gray-500">
                Batch yield analysis, planned vs actual packets, waste % and cost per packet.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() =>
                  handleExport('/reports/production-yield', 'csv', 'Yield_Variance_Report', 'yield-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'yield-csv'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-gray-300 hover:bg-gray-50 text-gray-700 text-center"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/production-yield', 'xlsx', 'Yield_Variance_Report', 'yield-xlsx', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'yield-xlsx'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-center"
              >
                Excel
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/production-yield', 'pdf', 'Yield_Variance_Report', 'yield-pdf', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'yield-pdf'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100 text-center"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Receivables Ageing */}
          <div className="p-4 rounded-lg border border-gray-200 bg-white hover:border-blue-200 transition-all shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-amber-600 mb-1">
                <IndianRupee className="w-4 h-4" />
                <h3 className="font-semibold text-gray-900 text-sm">Receivables Ageing Analysis</h3>
              </div>
              <p className="text-xs text-gray-500">
                0-30, 31-60, 61-90 and &gt;90 days overdue buckets per distributor/retailer.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() =>
                  handleExport('/reports/receivables-ageing', 'csv', 'Receivables_Ageing', 'ageing-csv', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'ageing-csv'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-gray-300 hover:bg-gray-50 text-gray-700 text-center"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/receivables-ageing', 'xlsx', 'Receivables_Ageing', 'ageing-xlsx', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'ageing-xlsx'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-center"
              >
                Excel
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/receivables-ageing', 'pdf', 'Receivables_Ageing', 'ageing-pdf', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'ageing-pdf'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100 text-center"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Full Trial Balance */}
          <div className="p-4 rounded-lg border border-gray-200 bg-white hover:border-blue-200 transition-all shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-teal-600 mb-1">
                <FileText className="w-4 h-4" />
                <h3 className="font-semibold text-gray-900 text-sm">Financial Trial Balance</h3>
              </div>
              <p className="text-xs text-gray-500">
                Complete Chart of Accounts with verified debits, credits and zero balance check.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={() =>
                  handleExport('/reports/trial-balance', 'csv', 'Trial_Balance', 'tb-csv', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'tb-csv'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-gray-300 hover:bg-gray-50 text-gray-700 text-center"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/trial-balance', 'xlsx', 'Trial_Balance', 'tb-xlsx', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'tb-xlsx'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-center"
              >
                Excel
              </button>
              <button
                onClick={() =>
                  handleExport('/reports/trial-balance', 'pdf', 'Trial_Balance', 'tb-pdf', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'tb-pdf'}
                className="flex-1 py-1 px-2 text-xs font-medium rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100 text-center"
              >
                PDF
              </button>
            </div>
          </div>
        </div>

        <div className="p-3 bg-blue-50/60 rounded-lg border border-blue-100 text-xs text-blue-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-blue-600" />
          <span>
            All exported reports reflect live posted entries from the immutable double-entry ledger and inventory movement journals.
          </span>
        </div>
      </div>
    </div>
  )
}
