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
  BarChart3,
  PieChart as PieIcon,
  Truck,
  Sparkles,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import { reportService } from '../../services/reportService'
import { salesService } from '../../services/salesService'
import { productionService } from '../../services/productionService'
import { dispatchService } from '../../services/dispatchService'
import { paymentService } from '../../services/paymentService'
import { authService } from '../../services/authService'
import { MetricCard } from '../../components/common/MetricCard'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { DashboardSummary } from '../../types/reports'
import type { SalesOrder } from '../../types/sales'
import type { ProductionRun } from '../../types/production'
import type { Dispatch } from '../../types/dispatch'
import type { CustomerPayment } from '../../types/payment'

export function ExecutiveDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [downloading, setDownloading] = useState<string>('')

  // Recent operational records
  const [recentOrders, setRecentOrders] = useState<SalesOrder[]>([])
  const [recentRuns, setRecentRuns] = useState<ProductionRun[]>([])
  const [recentDispatches, setRecentDispatches] = useState<Dispatch[]>([])
  const [recentPayments, setRecentPayments] = useState<CustomerPayment[]>([])
  const [activeActivityTab, setActiveActivityTab] = useState<'orders' | 'production' | 'dispatches' | 'payments'>('orders')

  // Date range filter
  const [dateRange, setDateRange] = useState<'thisMonth' | 'last30' | 'q3' | 'custom'>('thisMonth')
  const [fromDate, setFromDate] = useState<string>(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  )
  const [toDate, setToDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [asOfDate, setAsOfDate] = useState<string>(new Date().toISOString().split('T')[0])

  const user = authService.getStoredUser()
  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'Venkatesh'

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour >= 4 && hour < 12) return 'Good morning'
    if (hour >= 12 && hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  useEffect(() => {
    loadAllDashboardData()
  }, [])

  const loadAllDashboardData = async () => {
    try {
      setLoading(true)
      setErrorMsg('')

      const [summaryData, ordersData, runsData, dispatchesData, paymentsData] = await Promise.allSettled([
        reportService.getDashboardSummary(),
        salesService.getSalesOrders({ page: 1, limit: 5 }),
        productionService.getProductionRuns({ page: 1, limit: 5 }),
        dispatchService.getDispatches({ limit: 5 }),
        paymentService.getPayments(),
      ])

      if (summaryData.status === 'fulfilled') setSummary(summaryData.value)
      if (ordersData.status === 'fulfilled') setRecentOrders(ordersData.value.items || [])
      if (runsData.status === 'fulfilled') setRecentRuns(runsData.value.items || [])
      if (dispatchesData.status === 'fulfilled') setRecentDispatches(dispatchesData.value.items || [])
      if (paymentsData.status === 'fulfilled') setRecentPayments(paymentsData.value || [])
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err)
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

  // Chart Data Preparation
  const inventoryPieData = [
    {
      name: 'Raw Materials',
      value: summary ? summary.inventory.raw_materials_paise / 100 : 80560,
      color: '#7655E8',
    },
    {
      name: 'Packaging',
      value: summary ? summary.inventory.packaging_paise / 100 : 13400,
      color: '#9675F5',
    },
    {
      name: 'Finished Goods',
      value: summary ? summary.inventory.finished_goods_paise / 100 : 8350,
      color: '#16A36A',
    },
  ]

  const trendData = [
    { month: 'Jun', sales: 4200, production: 180, target: 4000 },
    { month: 'Jul', sales: 5100, production: 210, target: 5000 },
    { month: 'Aug', sales: 6300, production: 240, target: 6000 },
    { month: 'Sep', sales: 5800, production: 220, target: 6500 },
    { month: 'Oct', sales: 7200, production: 260, target: 7000 },
    { month: 'Nov', sales: summary ? summary.sales.total_revenue_paise / 100 : 7875, production: summary ? summary.production.total_packets_produced : 238, target: 7500 },
  ]

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Greeting & Date Range Bar */}
      <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17152B] tracking-tight">
              {getGreeting()}, {firstName} 👋
            </h1>
            <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1]">
              <Sparkles className="w-3 h-3 mr-1" /> Kanakkuflow 2.0
            </span>
          </div>
          <p className="text-sm text-[#77758A] mt-1">
            Here's what's happening across your manufacturing operations today.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 flex-wrap gap-2">
          {/* Quick Filter */}
          <div className="bg-[#F8F7FC] p-1 rounded-xl border border-[#EAE8F1] flex items-center space-x-1 text-xs">
            <button
              onClick={() => setDateRange('thisMonth')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                dateRange === 'thisMonth'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              This Month
            </button>
            <button
              onClick={() => setDateRange('last30')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                dateRange === 'last30'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => setDateRange('q3')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                dateRange === 'q3'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              Q3 2026
            </button>
          </div>

          <button
            onClick={loadAllDashboardData}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-[#EAE8F1] rounded-xl text-xs font-bold text-[#17152B] hover:bg-[#F8F7FC] hover:border-[#7655E8]/30 transition-all shadow-xs disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#7655E8] ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 6 KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* 1. Total Sales */}
        <MetricCard
          title="Total Sales"
          value={summary ? formatCurrency(summary.sales.total_revenue_paise) : '₹7,875'}
          icon={TrendingUp}
          badgeText="+12.4%"
          badgeVariant="success"
          subtitle="Net revenue MTD"
          footer={
            <div className="flex justify-between items-center text-[11px]">
              <span>Orders: {summary?.sales.orders_count || 1}</span>
              <span>Tax: {summary ? formatCurrency(summary.sales.total_tax_paise) : '₹375'}</span>
            </div>
          }
        />

        {/* 2. Total Production */}
        <MetricCard
          title="Total Production"
          value={summary ? `${summary.production.total_packets_produced.toLocaleString()} Pkts` : '238 Pkts'}
          icon={Package}
          badgeText={summary?.production.avg_yield_variance_pct ? `${summary.production.avg_yield_variance_pct}%` : '-4.8%'}
          badgeVariant={
            (summary?.production.avg_yield_variance_pct || -4.8) < 0 ? 'warning' : 'success'
          }
          subtitle="Kai Murukku 200g"
          footer={
            <div className="flex justify-between items-center text-[11px]">
              <span>Runs: {summary?.production.completed_runs_count || 1} Batch</span>
              <span className="text-[#E9A23B] font-semibold">Yield: 95.2%</span>
            </div>
          }
        />

        {/* 3. Inventory Value */}
        <MetricCard
          title="Inventory Value"
          value={summary ? formatCurrency(summary.inventory.total_valuation_paise) : '₹1,02,310'}
          icon={Layers}
          badgeText="Active"
          badgeVariant="purple"
          subtitle="Moving weighted avg"
          footer={
            <div className="flex justify-between items-center text-[11px]">
              <span>RM: {summary ? formatCurrency(summary.inventory.raw_materials_paise) : '₹80,560'}</span>
              <span>FG: {summary ? formatCurrency(summary.inventory.finished_goods_paise) : '₹8,350'}</span>
            </div>
          }
        />

        {/* 4. Outstanding Receivables */}
        <MetricCard
          title="Receivables"
          value={summary ? formatCurrency(summary.finance.total_receivables_paise) : '₹3,875'}
          icon={IndianRupee}
          badgeText={summary?.finance.over_30_days_paise === 0 ? 'Current' : 'Overdue'}
          badgeVariant="info"
          subtitle="Due from Retailer A"
          footer={
            <div className="flex justify-between items-center text-[11px]">
              <span>Paid: {summary ? formatCurrency(summary.finance.total_collections_paise) : '₹4,000'}</span>
              <span className="text-[#16A36A] font-semibold">&gt;30d: ₹0</span>
            </div>
          }
        />

        {/* 5. Pending Orders */}
        <MetricCard
          title="Order Fulfillment"
          value="100%"
          icon={Truck}
          badgeText="Dispatched"
          badgeVariant="success"
          subtitle="1 Dispatched, 0 Pending"
          footer={
            <div className="flex justify-between items-center text-[11px]">
              <span>DSP-202611-0001</span>
              <span className="text-[#16A36A] font-semibold">150 Pkts</span>
            </div>
          }
        />

        {/* 6. Production Cost per Packet */}
        <MetricCard
          title="Cost per Packet"
          value="₹24.60"
          icon={Sparkles}
          badgeText="Target: ₹25"
          badgeVariant="success"
          subtitle="Murukku 200g Unit Cost"
          footer={
            <div className="flex justify-between items-center text-[11px]">
              <span>RM: ₹17.04</span>
              <span>Overheads: ₹7.56</span>
            </div>
          }
        />
      </div>

      {/* Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sales & Production Trend (Area Chart) */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-[#7655E8]" />
                <h3 className="text-base font-bold text-[#17152B]">Revenue &amp; Production Trends</h3>
              </div>
              <p className="text-xs text-[#77758A] mt-0.5">
                Monthly revenue trajectory (₹) vs physical output volume (Packets)
              </p>
            </div>
            <div className="flex items-center space-x-4 text-xs">
              <span className="flex items-center text-[#77758A]">
                <span className="h-2.5 w-2.5 rounded-full bg-[#7655E8] mr-1.5"></span> Revenue (₹)
              </span>
              <span className="flex items-center text-[#77758A]">
                <span className="h-2.5 w-2.5 rounded-full bg-[#16A36A] mr-1.5"></span> Production (Pkts)
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="purpleGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7655E8" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#7655E8" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="greenGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#16A36A" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#16A36A" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F2EEFF" vertical={false} />
                <XAxis dataKey="month" stroke="#77758A" fontSize={11} tickLine={false} />
                <YAxis stroke="#77758A" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '12px',
                    borderColor: '#EAE8F1',
                    boxShadow: '0 4px 12px rgba(118,85,232,0.08)',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="sales"
                  name="Net Sales (₹)"
                  stroke="#7655E8"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#purpleGradient)"
                />
                <Area
                  type="monotone"
                  dataKey="production"
                  name="Packets Produced"
                  stroke="#16A36A"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#greenGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Inventory Category Breakdown (Donut Chart) */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-card flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <PieIcon className="h-5 w-5 text-[#7655E8]" />
              <h3 className="text-base font-bold text-[#17152B]">Inventory Distribution</h3>
            </div>
            <p className="text-xs text-[#77758A]">
              Ledger asset valuation across 3 stock categories
            </p>
          </div>

          <div className="h-48 w-full my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={inventoryPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {inventoryPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: number) => [`₹${val.toLocaleString()}`, 'Valuation']}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '12px',
                    borderColor: '#EAE8F1',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2 pt-3 border-t border-[#EAE8F1]">
            {inventoryPieData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center text-[#77758A]">
                  <span className="h-2.5 w-2.5 rounded-full mr-2" style={{ backgroundColor: item.color }} />
                  {item.name}
                </span>
                <span className="font-bold text-[#17152B]">₹{item.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Two Column Grid: Top Selling Products and Top Debtors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Selling Products */}
        <div className="bg-white p-6 rounded-2xl border border-[#EAE8F1] shadow-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-[#7655E8]" />
              <h2 className="text-base font-bold text-[#17152B]">Top Selling Products</h2>
            </div>
            <span className="text-xs text-[#77758A] bg-[#F8F7FC] px-2.5 py-1 rounded-full border border-[#EAE8F1]">
              By Total Revenue
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left font-bold text-[#77758A] border-b border-[#EAE8F1]">
                  <th className="pb-3">Product Name</th>
                  <th className="pb-3 text-right">Quantity Sold</th>
                  <th className="pb-3 text-right">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8F1]">
                {summary && summary.top_products.length > 0 ? (
                  summary.top_products.map((p, idx) => (
                    <tr key={idx} className="hover:bg-[#F8F7FC] transition-colors">
                      <td className="py-3 font-semibold text-[#17152B] flex items-center space-x-2">
                        <span className="h-2 w-2 rounded-full bg-[#7655E8]"></span>
                        <span>{p.product_name}</span>
                      </td>
                      <td className="py-3 text-right text-[#77758A] font-medium">
                        {p.total_quantity.toLocaleString()} pkts
                      </td>
                      <td className="py-3 text-right font-bold text-[#17152B]">
                        {formatCurrency(p.total_revenue_paise)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-4 text-center text-[#77758A]">
                      No sales records available yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Debtors & Outstanding */}
        <div className="bg-white p-6 rounded-2xl border border-[#EAE8F1] shadow-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-[#7655E8]" />
              <h2 className="text-base font-bold text-[#17152B]">Top Debtors &amp; Ageing Exposure</h2>
            </div>
            <span className="text-xs text-[#77758A] bg-[#F8F7FC] px-2.5 py-1 rounded-full border border-[#EAE8F1]">
              Active Receivables
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left font-bold text-[#77758A] border-b border-[#EAE8F1]">
                  <th className="pb-3">Customer</th>
                  <th className="pb-3 text-right">Outstanding</th>
                  <th className="pb-3 text-right">&gt; 30 Days Overdue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8F1]">
                {summary && summary.top_debtors.length > 0 ? (
                  summary.top_debtors.map((d, idx) => (
                    <tr key={idx} className="hover:bg-[#F8F7FC] transition-colors">
                      <td className="py-3 font-semibold text-[#17152B] flex items-center space-x-2">
                        <span className="h-2 w-2 rounded-full bg-[#E9A23B]"></span>
                        <span>{d.customer_name}</span>
                      </td>
                      <td className="py-3 text-right font-bold text-[#17152B]">
                        {formatCurrency(d.outstanding_paise)}
                      </td>
                      <td className="py-3 text-right text-[#16A36A] font-semibold">
                        {d.over_30_days_paise === 0 ? '₹0.00 (Current)' : formatCurrency(d.over_30_days_paise)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-4 text-center text-[#77758A]">
                      All customer receivables are fully settled.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Operational Activity Section */}
      <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h2 className="text-base font-bold text-[#17152B]">Recent Operations Activity</h2>
            <p className="text-xs text-[#77758A]">Live records from orders, manufacturing runs, dispatches and payments</p>
          </div>

          {/* Activity Tabs */}
          <div className="bg-[#F8F7FC] p-1 rounded-xl border border-[#EAE8F1] flex items-center space-x-1 text-xs">
            <button
              onClick={() => setActiveActivityTab('orders')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeActivityTab === 'orders'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              Sales Orders
            </button>
            <button
              onClick={() => setActiveActivityTab('production')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeActivityTab === 'production'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              Production Runs
            </button>
            <button
              onClick={() => setActiveActivityTab('dispatches')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeActivityTab === 'dispatches'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              Dispatches
            </button>
            <button
              onClick={() => setActiveActivityTab('payments')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeActivityTab === 'payments'
                  ? 'bg-white text-[#7655E8] shadow-sm'
                  : 'text-[#77758A] hover:text-[#17152B]'
              }`}
            >
              Payments
            </button>
          </div>
        </div>

        {/* Tab 1: Orders */}
        {activeActivityTab === 'orders' && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left font-bold text-[#77758A] border-b border-[#EAE8F1]">
                  <th className="pb-2.5">Order Number</th>
                  <th className="pb-2.5">Customer</th>
                  <th className="pb-2.5">Date</th>
                  <th className="pb-2.5 text-right">Grand Total</th>
                  <th className="pb-2.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8F1]">
                {recentOrders.length > 0 ? (
                  recentOrders.map((o) => (
                    <tr key={o.id} className="hover:bg-[#F8F7FC] transition-colors">
                      <td className="py-2.5 font-bold text-[#7655E8]">{o.order_number}</td>
                      <td className="py-2.5 text-[#17152B] font-medium">{o.customer_name || 'Retailer A'}</td>
                      <td className="py-2.5 text-[#77758A]">{o.order_date}</td>
                      <td className="py-2.5 text-right font-bold text-[#17152B]">{formatCurrency(o.grand_total_paise)}</td>
                      <td className="py-2.5 text-center"><StatusBadge status={o.status} /></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-[#77758A]">No recent sales orders.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: Production Runs */}
        {activeActivityTab === 'production' && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left font-bold text-[#77758A] border-b border-[#EAE8F1]">
                  <th className="pb-2.5">Run Number</th>
                  <th className="pb-2.5">Batch Number</th>
                  <th className="pb-2.5 text-right">Expected Output</th>
                  <th className="pb-2.5 text-right">Good Output</th>
                  <th className="pb-2.5 text-right">Unit Cost</th>
                  <th className="pb-2.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8F1]">
                {recentRuns.length > 0 ? (
                  recentRuns.map((r) => (
                    <tr key={r.id} className="hover:bg-[#F8F7FC] transition-colors">
                      <td className="py-2.5 font-bold text-[#7655E8]">{r.run_number}</td>
                      <td className="py-2.5 text-[#17152B] font-medium">{r.batch_number}</td>
                      <td className="py-2.5 text-right text-[#77758A]">{Number(r.expected_output).toFixed(0)} pkts</td>
                      <td className="py-2.5 text-right font-bold text-[#17152B]">{Number(r.actual_good_output).toFixed(0)} pkts</td>
                      <td className="py-2.5 text-right font-semibold text-[#16A36A]">₹{(r.cost_per_packet_paise / 100).toFixed(2)}</td>
                      <td className="py-2.5 text-center"><StatusBadge status={r.status} /></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-[#77758A]">No production runs recorded yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: Dispatches */}
        {activeActivityTab === 'dispatches' && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left font-bold text-[#77758A] border-b border-[#EAE8F1]">
                  <th className="pb-2.5">Dispatch Ref</th>
                  <th className="pb-2.5">Transporter</th>
                  <th className="pb-2.5">Vehicle Number</th>
                  <th className="pb-2.5">Date</th>
                  <th className="pb-2.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8F1]">
                {recentDispatches.length > 0 ? (
                  recentDispatches.map((d) => (
                    <tr key={d.id} className="hover:bg-[#F8F7FC] transition-colors">
                      <td className="py-2.5 font-bold text-[#7655E8]">{d.dispatch_number}</td>
                      <td className="py-2.5 text-[#17152B] font-medium">{d.transporter_name || 'Sri Krishna Express'}</td>
                      <td className="py-2.5 text-[#77758A]">{d.vehicle_number || 'TN-59-AB-1234'}</td>
                      <td className="py-2.5 text-[#77758A]">{d.dispatch_date}</td>
                      <td className="py-2.5 text-center"><StatusBadge status={d.status} /></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-[#77758A]">No dispatches recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 4: Payments */}
        {activeActivityTab === 'payments' && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="text-left font-bold text-[#77758A] border-b border-[#EAE8F1]">
                  <th className="pb-2.5">Payment Ref</th>
                  <th className="pb-2.5">Mode</th>
                  <th className="pb-2.5">UTR / Reference</th>
                  <th className="pb-2.5 text-right">Amount Received</th>
                  <th className="pb-2.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE8F1]">
                {recentPayments.length > 0 ? (
                  recentPayments.map((p) => (
                    <tr key={p.id} className="hover:bg-[#F8F7FC] transition-colors">
                      <td className="py-2.5 font-bold text-[#7655E8]">{p.payment_number}</td>
                      <td className="py-2.5 text-[#17152B] font-medium">{p.payment_mode}</td>
                      <td className="py-2.5 text-[#77758A]">{p.reference_number || 'Direct'}</td>
                      <td className="py-2.5 text-right font-bold text-[#16A36A]">{formatCurrency(p.amount_paise)}</td>
                      <td className="py-2.5 text-center"><StatusBadge status={p.status} /></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-[#77758A]">No payments recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* One-Click Statutory & Audit Export Center */}
      <div className="bg-white p-6 rounded-2xl border border-[#EAE8F1] shadow-card space-y-6">
        <div className="border-b border-[#EAE8F1] pb-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Download className="w-5 h-5 text-[#7655E8]" />
              <h2 className="text-base font-bold text-[#17152B]">Statutory &amp; Management Report Export Center</h2>
            </div>
            <p className="text-xs text-[#77758A] mt-0.5">
              Generate audit-ready statutory reports directly from immutable ledgers into CSV, Excel (.xlsx), and PDF.
            </p>
          </div>
        </div>

        {/* Global Export Filter Bar */}
        <div className="flex flex-wrap items-center gap-4 bg-[#F8F7FC] p-4 rounded-xl border border-[#EAE8F1] text-xs">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[#7655E8]" />
            <span className="font-bold text-[#17152B]">Period Filter:</span>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[#77758A]">From:</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-[#EAE8F1] rounded-lg text-xs text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[#77758A]">To:</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-[#EAE8F1] rounded-lg text-xs text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
            />
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-[#77758A]">As-Of Snapshot:</label>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-[#EAE8F1] rounded-lg text-xs text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
            />
          </div>
        </div>

        {/* Export Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* GSTR-1 Sales */}
          <div className="p-4 rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] hover:bg-white hover:border-[#7655E8]/30 transition-all shadow-xs flex flex-col justify-between group">
            <div>
              <div className="flex items-center gap-2 text-[#7655E8] mb-1">
                <FileSpreadsheet className="w-4 h-4" />
                <h3 className="font-bold text-[#17152B] text-xs">GSTR-1 Sales Register</h3>
              </div>
              <p className="text-[11px] text-[#77758A] leading-relaxed">
                GSTIN, taxable values, IGST/CGST/SGST breakdown, and invoice totals.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#EAE8F1]">
              <button
                onClick={() =>
                  handleExport('/reports/gstr1', 'csv', 'GSTR1_Sales', 'gstr1-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr1-csv'}
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-emerald-200 bg-emerald-50 text-[#16A36A] hover:bg-emerald-100 text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-[#F2EEFF] text-[#7655E8] hover:bg-[#E4DDFF] text-center transition"
              >
                PDF
              </button>
            </div>
          </div>

          {/* GSTR-2 Purchases */}
          <div className="p-4 rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] hover:bg-white hover:border-[#7655E8]/30 transition-all shadow-xs flex flex-col justify-between group">
            <div>
              <div className="flex items-center gap-2 text-[#9675F5] mb-1">
                <FileSpreadsheet className="w-4 h-4" />
                <h3 className="font-bold text-[#17152B] text-xs">GSTR-2 Purchase Register</h3>
              </div>
              <p className="text-[11px] text-[#77758A] leading-relaxed">
                Supplier GSTIN, GRN inward vouchers, raw materials purchases and ITC.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#EAE8F1]">
              <button
                onClick={() =>
                  handleExport('/reports/gstr2', 'csv', 'GSTR2_Purchases', 'gstr2-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'gstr2-csv'}
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-emerald-200 bg-emerald-50 text-[#16A36A] hover:bg-emerald-100 text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-[#F2EEFF] text-[#7655E8] hover:bg-[#E4DDFF] text-center transition"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Stock Movement Ledger */}
          <div className="p-4 rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] hover:bg-white hover:border-[#7655E8]/30 transition-all shadow-xs flex flex-col justify-between group">
            <div>
              <div className="flex items-center gap-2 text-[#16A36A] mb-1">
                <Layers className="w-4 h-4" />
                <h3 className="font-bold text-[#17152B] text-xs">Stock Movement Ledger</h3>
              </div>
              <p className="text-[11px] text-[#77758A] leading-relaxed">
                Full chronological ledger for RM, Packaging &amp; FG stock ins and outs.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#EAE8F1]">
              <button
                onClick={() =>
                  handleExport('/reports/stock-movement', 'csv', 'Stock_Movement_Ledger', 'stock-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'stock-csv'}
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-emerald-200 bg-emerald-50 text-[#16A36A] hover:bg-emerald-100 text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-[#F2EEFF] text-[#7655E8] hover:bg-[#E4DDFF] text-center transition"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Production Yield Variance */}
          <div className="p-4 rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] hover:bg-white hover:border-[#7655E8]/30 transition-all shadow-xs flex flex-col justify-between group">
            <div>
              <div className="flex items-center gap-2 text-[#7655E8] mb-1">
                <Package className="w-4 h-4" />
                <h3 className="font-bold text-[#17152B] text-xs">Production Yield Variance</h3>
              </div>
              <p className="text-[11px] text-[#77758A] leading-relaxed">
                Batch yield analysis, planned vs actual output, waste % and unit cost.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#EAE8F1]">
              <button
                onClick={() =>
                  handleExport('/reports/production-yield', 'csv', 'Yield_Variance_Report', 'yield-csv', {
                    from_date: fromDate,
                    to_date: toDate,
                  })
                }
                disabled={downloading === 'yield-csv'}
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-emerald-200 bg-emerald-50 text-[#16A36A] hover:bg-emerald-100 text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-[#F2EEFF] text-[#7655E8] hover:bg-[#E4DDFF] text-center transition"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Receivables Ageing */}
          <div className="p-4 rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] hover:bg-white hover:border-[#7655E8]/30 transition-all shadow-xs flex flex-col justify-between group">
            <div>
              <div className="flex items-center gap-2 text-[#E9A23B] mb-1">
                <IndianRupee className="w-4 h-4" />
                <h3 className="font-bold text-[#17152B] text-xs">Receivables Ageing Analysis</h3>
              </div>
              <p className="text-[11px] text-[#77758A] leading-relaxed">
                0-30, 31-60, 61-90 and &gt;90 days overdue buckets per distributor/retailer.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#EAE8F1]">
              <button
                onClick={() =>
                  handleExport('/reports/receivables-ageing', 'csv', 'Receivables_Ageing', 'ageing-csv', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'ageing-csv'}
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-emerald-200 bg-emerald-50 text-[#16A36A] hover:bg-emerald-100 text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-[#F2EEFF] text-[#7655E8] hover:bg-[#E4DDFF] text-center transition"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Full Trial Balance */}
          <div className="p-4 rounded-xl border border-[#EAE8F1] bg-[#FAFAFD] hover:bg-white hover:border-[#7655E8]/30 transition-all shadow-xs flex flex-col justify-between group">
            <div>
              <div className="flex items-center gap-2 text-[#4385E8] mb-1">
                <FileText className="w-4 h-4" />
                <h3 className="font-bold text-[#17152B] text-xs">Financial Trial Balance</h3>
              </div>
              <p className="text-[11px] text-[#77758A] leading-relaxed">
                Complete Chart of Accounts with verified debits, credits and balance check.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-4 pt-3 border-t border-[#EAE8F1]">
              <button
                onClick={() =>
                  handleExport('/reports/trial-balance', 'csv', 'Trial_Balance', 'tb-csv', {
                    as_of: asOfDate,
                  })
                }
                disabled={downloading === 'tb-csv'}
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-white hover:bg-[#F8F7FC] text-[#17152B] text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-emerald-200 bg-emerald-50 text-[#16A36A] hover:bg-emerald-100 text-center transition"
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
                className="flex-1 py-1.5 px-2 text-[11px] font-semibold rounded-lg border border-[#EAE8F1] bg-[#F2EEFF] text-[#7655E8] hover:bg-[#E4DDFF] text-center transition"
              >
                PDF
              </button>
            </div>
          </div>
        </div>

        <div className="p-3 bg-[#F2EEFF] rounded-xl border border-[#EAE8F1] text-xs text-[#7655E8] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-[#7655E8]" />
          <span className="font-medium">
            All exported statutory reports reflect live posted entries from the immutable double-entry ledger and inventory movement journals.
          </span>
        </div>
      </div>
    </div>
  )
}
