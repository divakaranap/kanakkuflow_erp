import React, { useState, useEffect } from 'react'
import {
  Boxes,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
  BookOpen,
  Scale,
  SlidersHorizontal,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownLeft,
} from 'lucide-react'
import { inventoryService } from '../../services/inventoryService'
import { masterService } from '../../services/masterService'
import { formatINR } from '../../lib/utils'
import type {
  StockSummaryItem,
  StockMovement,
  StockValuationSummary,
  StockReconciliationReport,
  InventoryAdjustment,
  Purchase,
  InventoryItemType,
  PurchaseItemType,
  AdjustmentType,
} from '../../types/inventory'
import type { Supplier, RawMaterial, PackagingItem, Product } from '../../types/masters'

export function InventoryOverview() {
  const [activeTab, setActiveTab] = useState<'summary' | 'purchases' | 'ledger' | 'reconciliation' | 'adjustments'>('summary')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Data states
  const [summaryItems, setSummaryItems] = useState<StockSummaryItem[]>([])
  const [valuation, setValuation] = useState<StockValuationSummary | null>(null)
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [movements, setMovements] = useState<StockMovement[]>([])
  const [reconciliation, setReconciliation] = useState<StockReconciliationReport | null>(null)
  const [adjustments, setAdjustments] = useState<InventoryAdjustment[]>([])

  // Filter states
  const [itemTypeFilter, setItemTypeFilter] = useState<InventoryItemType | 'ALL'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [lowStockOnly, setLowStockOnly] = useState(false)

  // Master lookups for modal forms
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [rawMaterials, setRawMaterials] = useState<RawMaterial[]>([])
  const [packagingItems, setPackagingItems] = useState<PackagingItem[]>([])
  const [products, setProducts] = useState<Product[]>([])

  // Modals
  const [isOpeningModalOpen, setIsOpeningModalOpen] = useState(false)
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false)
  const [isAdjustmentModalOpen, setIsAdjustmentModalOpen] = useState(false)

  // Opening form
  const [openingForm, setOpeningForm] = useState({
    item_type: 'RAW' as InventoryItemType,
    item_id: '',
    quantity: '',
    unit_cost_paise: '',
    notes: 'Opening stock initialization',
  })

  // Adjustment form
  const [adjForm, setAdjForm] = useState({
    item_type: 'RAW' as InventoryItemType,
    item_id: '',
    adjustment_type: 'INCREASE' as AdjustmentType,
    quantity: '',
    reason: '',
  })

  // Purchase form
  const [purchaseForm, setPurchaseForm] = useState({
    supplier_id: '',
    supplier_invoice_number: '',
    notes: '',
    lines: [
      {
        item_type: 'RAW' as PurchaseItemType,
        item_id: '',
        quantity: '',
        unit: 'kg',
        unit_rate_paise: '',
        tax_rate: '0.05',
      },
    ],
  })

  useEffect(() => {
    loadLookups()
    loadSummaryData()
  }, [])

  useEffect(() => {
    if (activeTab === 'summary') loadSummaryData()
    if (activeTab === 'purchases') loadPurchasesData()
    if (activeTab === 'ledger') loadLedgerData()
    if (activeTab === 'reconciliation') loadReconciliationData()
    if (activeTab === 'adjustments') loadAdjustmentsData()
  }, [activeTab, itemTypeFilter, lowStockOnly])

  const loadLookups = async () => {
    try {
      const [sup, rm, pkg, prd] = await Promise.all([
        masterService.getSuppliers(),
        masterService.getRawMaterials(),
        masterService.getPackaging(),
        masterService.getProducts(),
      ])
      setSuppliers(sup)
      setRawMaterials(rm)
      setPackagingItems(pkg)
      setProducts(prd)
      if (rm.length > 0) setOpeningForm((f) => ({ ...f, item_id: rm[0].id }))
    } catch {
      // ignore
    }
  }

  const loadSummaryData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [summary, val] = await Promise.all([
        inventoryService.getStockSummary({
          item_type: itemTypeFilter === 'ALL' ? undefined : itemTypeFilter,
          search: searchQuery || undefined,
          low_stock_only: lowStockOnly,
        }),
        inventoryService.getStockValuation(itemTypeFilter === 'ALL' ? undefined : itemTypeFilter),
      ])
      setSummaryItems(summary)
      setValuation(val)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load inventory summary')
    } finally {
      setLoading(false)
    }
  }

  const loadPurchasesData = async () => {
    setLoading(true)
    try {
      const res = await inventoryService.getPurchases()
      setPurchases(res.items)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load purchases')
    } finally {
      setLoading(false)
    }
  }

  const loadLedgerData = async () => {
    setLoading(true)
    try {
      const res = await inventoryService.getStockLedger({
        item_type: itemTypeFilter === 'ALL' ? undefined : itemTypeFilter,
      })
      setMovements(res.items)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load stock movements')
    } finally {
      setLoading(false)
    }
  }

  const loadReconciliationData = async () => {
    setLoading(true)
    try {
      const rep = await inventoryService.getReconciliationReport()
      setReconciliation(rep)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load reconciliation')
    } finally {
      setLoading(false)
    }
  }

  const loadAdjustmentsData = async () => {
    setLoading(true)
    try {
      const res = await inventoryService.getAdjustments()
      setAdjustments(res.items)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load adjustments')
    } finally {
      setLoading(false)
    }
  }

  // Handlers
  const handleRunReconciliation = async () => {
    setLoading(true)
    setErrorMsg('')
    setSuccessMsg('')
    try {
      const rep = await inventoryService.runReconciliation()
      setReconciliation(rep)
      setSuccessMsg('Reconciliation completed and cache synchronized successfully.')
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to run reconciliation')
    } finally {
      setLoading(false)
    }
  }

  const handlePostPurchase = async (purchaseId: string) => {
    setLoading(true)
    setErrorMsg('')
    setSuccessMsg('')
    try {
      await inventoryService.postPurchase(purchaseId)
      setSuccessMsg('Purchase posted! Inventory ledger and moving weighted average updated.')
      loadPurchasesData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to post purchase')
    } finally {
      setLoading(false)
    }
  }

  const handlePostAdjustment = async (adjId: string) => {
    setLoading(true)
    setErrorMsg('')
    setSuccessMsg('')
    try {
      await inventoryService.postAdjustment(adjId)
      setSuccessMsg('Adjustment posted and ledger updated.')
      loadAdjustmentsData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to post adjustment')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateOpeningStock = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')
    try {
      await inventoryService.initializeOpeningStock({
        item_type: openingForm.item_type,
        item_id: openingForm.item_id,
        quantity: parseFloat(openingForm.quantity),
        unit_cost_paise: Math.round(parseFloat(openingForm.unit_cost_paise) * 100),
        notes: openingForm.notes,
      })
      setSuccessMsg('Opening stock initialized successfully.')
      setIsOpeningModalOpen(false)
      loadSummaryData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to initialize opening stock')
    }
  }

  const handleCreateAdjustment = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')
    try {
      await inventoryService.createAdjustment({
        item_type: adjForm.item_type,
        item_id: adjForm.item_id,
        adjustment_type: adjForm.adjustment_type,
        quantity: parseFloat(adjForm.quantity),
        reason: adjForm.reason,
      })
      setSuccessMsg('Draft adjustment created successfully.')
      setIsAdjustmentModalOpen(false)
      loadAdjustmentsData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create adjustment')
    }
  }

  const handleCreatePurchase = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')
    try {
      const payload = {
        supplier_id: purchaseForm.supplier_id,
        supplier_invoice_number: purchaseForm.supplier_invoice_number,
        notes: purchaseForm.notes || undefined,
        lines: purchaseForm.lines.map((l) => ({
          item_type: l.item_type,
          item_id: l.item_id,
          quantity: parseFloat(l.quantity),
          unit: l.unit,
          unit_rate_paise: Math.round(parseFloat(l.unit_rate_paise) * 100),
          tax_rate: parseFloat(l.tax_rate),
        })),
      }
      await inventoryService.createPurchase(payload)
      setSuccessMsg('Purchase order created in DRAFT.')
      setIsPurchaseModalOpen(false)
      loadPurchasesData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create purchase order')
    }
  }

  const addPurchaseLine = () => {
    setPurchaseForm({
      ...purchaseForm,
      lines: [
        ...purchaseForm.lines,
        {
          item_type: 'RAW',
          item_id: rawMaterials[0]?.id || '',
          quantity: '',
          unit: 'kg',
          unit_rate_paise: '',
          tax_rate: '0.05',
        },
      ],
    })
  }

  const removePurchaseLine = (idx: number) => {
    setPurchaseForm({
      ...purchaseForm,
      lines: purchaseForm.lines.filter((_, i) => i !== idx),
    })
  }

  const getAvailableItemsForType = (type: InventoryItemType) => {
    if (type === 'RAW') return rawMaterials.map((r) => ({ id: r.id, name: `${r.material_name} (${r.material_code})` }))
    if (type === 'PACKAGING') return packagingItems.map((p) => ({ id: p.id, name: `${p.packaging_name} (${p.packaging_code})` }))
    return products.map((pr) => ({ id: pr.id, name: `${pr.product_name} (${pr.sku})` }))
  }

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {errorMsg && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <XCircle className="h-4 w-4 shrink-0 text-red-500" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-red-500 hover:text-red-700 font-bold">×</button>
        </div>
      )}
      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-700 hover:text-emerald-900 font-bold">×</button>
        </div>
      )}

      {/* KPI Cards Header */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#77758A] uppercase tracking-wider">Total Inventory Valuation</span>
          <div className="text-2xl font-extrabold text-[#17152B] mt-1">
            {formatINR(valuation?.total_valuation_paise || 0)}
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Moving weighted average</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#7655E8] uppercase tracking-wider">Raw Materials Valuation</span>
          <div className="text-2xl font-extrabold text-[#7655E8] mt-1">
            {formatINR(valuation?.raw_materials_valuation_paise || 0)}
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Flour, Oil, Spices</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#9675F5] uppercase tracking-wider">Packaging Valuation</span>
          <div className="text-2xl font-extrabold text-[#17152B] mt-1">
            {formatINR(valuation?.packaging_valuation_paise || 0)}
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Pouches &amp; Cartons</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#16A36A] uppercase tracking-wider">Finished Goods Valuation</span>
          <div className="text-2xl font-extrabold text-[#16A36A] mt-1">
            {formatINR(valuation?.finished_goods_valuation_paise || 0)}
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Packets in Stock</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#E9A23B] uppercase tracking-wider">Low Stock Alerts</span>
          <div className="text-2xl font-extrabold text-[#E9A23B] mt-1 flex items-center space-x-1.5">
            <AlertTriangle className="h-5 w-5 text-[#E9A23B]" />
            <span>{summaryItems.filter((i) => i.is_low_stock).length} Items</span>
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Below reorder point</span>
        </div>
      </div>

      {/* Tabs and Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-2.5 rounded-2xl border border-[#EAE8F1] shadow-card">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'summary' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <Boxes className="h-4 w-4" />
            <span>Stock Summary</span>
          </button>

          <button
            onClick={() => setActiveTab('purchases')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'purchases' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <ShoppingCart className="h-4 w-4" />
            <span>Purchases</span>
          </button>

          <button
            onClick={() => setActiveTab('ledger')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'ledger' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <BookOpen className="h-4 w-4" />
            <span>Stock Ledger</span>
          </button>

          <button
            onClick={() => setActiveTab('reconciliation')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'reconciliation' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Scale className="h-4 w-4" />
            <span>Reconciliation</span>
          </button>

          <button
            onClick={() => setActiveTab('adjustments')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'adjustments' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <SlidersHorizontal className="h-4 w-4" />
            <span>Adjustments</span>
          </button>
        </div>

        <div className="flex items-center space-x-2">
          {activeTab === 'summary' && (
            <button
              onClick={() => setIsOpeningModalOpen(true)}
              className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800 transition flex items-center space-x-1 shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Initialize Opening Stock</span>
            </button>
          )}

          {activeTab === 'purchases' && (
            <button
              onClick={() => setIsPurchaseModalOpen(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition flex items-center space-x-1 shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Purchase Order</span>
            </button>
          )}

          {activeTab === 'adjustments' && (
            <button
              onClick={() => setIsAdjustmentModalOpen(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition flex items-center space-x-1 shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Adjustment</span>
            </button>
          )}

          {activeTab === 'reconciliation' && (
            <button
              onClick={handleRunReconciliation}
              disabled={loading}
              className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold hover:bg-emerald-700 transition flex items-center space-x-1 shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Run Live Reconciliation</span>
            </button>
          )}
        </div>
      </div>

      {/* TAB 1: STOCK SUMMARY */}
      {activeTab === 'summary' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Filter Bar */}
          <div className="p-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4 bg-slate-50">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search item code or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadSummaryData()}
                  className="pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white w-64"
                />
              </div>

              <select
                value={itemTypeFilter}
                onChange={(e) => setItemTypeFilter(e.target.value as any)}
                className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 bg-white font-medium text-slate-700"
              >
                <option value="ALL">All Item Types</option>
                <option value="RAW">Raw Materials</option>
                <option value="PACKAGING">Packaging Items</option>
                <option value="FG">Finished Goods</option>
              </select>

              <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={lowStockOnly}
                  onChange={(e) => setLowStockOnly(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                <span>Low stock only</span>
              </label>
            </div>

            <button
              onClick={loadSummaryData}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-600 transition"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Item Code</th>
                  <th className="py-3 px-4">Item Name</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Unit</th>
                  <th className="py-3 px-4 text-right">Available Stock</th>
                  <th className="py-3 px-4 text-right">Reorder Level</th>
                  <th className="py-3 px-4 text-center">Stock Status</th>
                  <th className="py-3 px-4 text-right">Weighted Avg Rate</th>
                  <th className="py-3 px-4 text-right">Total Valuation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {summaryItems.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400">
                      No inventory records found. Initialize opening stocks or record purchases.
                    </td>
                  </tr>
                ) : (
                  summaryItems.map((item) => (
                    <tr key={`${item.item_type}-${item.item_id}`} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{item.item_code}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">{item.item_name}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                          {item.item_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{item.base_unit}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        {parseFloat(item.current_stock.toString()).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-500">
                        {parseFloat(item.reorder_level.toString()).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {item.is_low_stock ? (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-100 text-red-700 border border-red-200">
                            <AlertTriangle className="h-3 w-3" />
                            <span>Low Stock</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Healthy</span>
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-700">
                        {formatINR(item.weighted_avg_rate_paise)}/{item.base_unit}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        {formatINR(item.total_valuation_paise)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: PURCHASES */}
      {activeTab === 'purchases' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">Raw Material & Packaging Purchases</h3>
            <span className="text-xs text-slate-500 font-medium">Automatic Stock Inflow on Posting</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">PO Number</th>
                  <th className="py-3 px-4">Supplier</th>
                  <th className="py-3 px-4">Supplier Inv #</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Subtotal</th>
                  <th className="py-3 px-4 text-right">Tax</th>
                  <th className="py-3 px-4 text-right">Total</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {purchases.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400">
                      No purchase orders recorded. Click "New Purchase Order" to create one.
                    </td>
                  </tr>
                ) : (
                  purchases.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{p.purchase_number}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">{p.supplier_name}</td>
                      <td className="py-3 px-4 font-mono text-slate-700">{p.supplier_invoice_number}</td>
                      <td className="py-3 px-4 text-slate-600">{new Date(p.purchase_date).toLocaleDateString()}</td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            p.status === 'POSTED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-amber-100 text-amber-800 border-amber-200'
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono">{formatINR(p.subtotal_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-500">{formatINR(p.tax_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">{formatINR(p.total_paise)}</td>
                      <td className="py-3 px-4 text-center">
                        {p.status === 'DRAFT' ? (
                          <button
                            onClick={() => handlePostPurchase(p.id)}
                            className="px-2.5 py-1 bg-emerald-600 text-white rounded text-[11px] font-semibold hover:bg-emerald-700 transition"
                          >
                            Post Receipt
                          </button>
                        ) : (
                          <span className="text-[11px] text-emerald-600 font-semibold">Stock Inflowed</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: STOCK LEDGER */}
      {activeTab === 'ledger' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Immutable Stock Ledger</h3>
              <p className="text-xs text-slate-500">Every stock increase, issue, and adjustment is recorded with full auditability</p>
            </div>
            <button
              onClick={loadLedgerData}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-600 transition"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Item Code</th>
                  <th className="py-3 px-4">Item Name</th>
                  <th className="py-3 px-4">Movement Type</th>
                  <th className="py-3 px-4 text-right">Delta</th>
                  <th className="py-3 px-4 text-right">Unit Cost</th>
                  <th className="py-3 px-4 text-right">Total Value</th>
                  <th className="py-3 px-4">Reference</th>
                  <th className="py-3 px-4">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono">
                {movements.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400 font-sans">
                      No stock movements recorded yet.
                    </td>
                  </tr>
                ) : (
                  movements.map((m) => {
                    const isPositive = parseFloat(m.qty_delta.toString()) > 0
                    return (
                      <tr key={m.id} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-4 text-slate-500">{new Date(m.created_at).toLocaleString()}</td>
                        <td className="py-3 px-4 font-bold text-slate-900">{m.item_code}</td>
                        <td className="py-3 px-4 font-sans font-medium text-slate-800">{m.item_name}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold font-sans border ${
                              m.movement_type === 'OPENING'
                                ? 'bg-blue-100 text-blue-800 border-blue-200'
                                : m.movement_type === 'PURCHASE_RECEIPT'
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                                : m.movement_type === 'ADJUSTMENT'
                                ? 'bg-amber-100 text-amber-800 border-amber-200'
                                : 'bg-slate-100 text-slate-800 border-slate-200'
                            }`}
                          >
                            {m.movement_type}
                          </span>
                        </td>
                        <td
                          className={`py-3 px-4 text-right font-bold flex items-center justify-end space-x-1 ${
                            isPositive ? 'text-emerald-600' : 'text-red-600'
                          }`}
                        >
                          {isPositive ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownLeft className="h-3.5 w-3.5" />}
                          <span>
                            {isPositive ? '+' : ''}
                            {parseFloat(m.qty_delta.toString()).toFixed(2)}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right text-slate-600">
                          {m.unit_cost_paise ? formatINR(m.unit_cost_paise) : '—'}
                        </td>
                        <td className="py-3 px-4 text-right text-slate-900 font-bold">
                          {m.total_value_paise ? formatINR(m.total_value_paise) : '—'}
                        </td>
                        <td className="py-3 px-4 text-slate-600 font-sans">{m.reference_number || '—'}</td>
                        <td className="py-3 px-4 text-slate-500 font-sans">{m.notes || '—'}</td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: RECONCILIATION */}
      {activeTab === 'reconciliation' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div
                className={`p-2 rounded-lg ${
                  reconciliation?.is_fully_reconciled ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                }`}
              >
                <Scale className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  {reconciliation?.is_fully_reconciled
                    ? '100% Fully Reconciled with Single Source of Truth'
                    : 'Discrepancies Detected between Ledger and Cache'}
                </h3>
                <p className="text-xs text-slate-500">
                  Authoritative stock is strictly SUM(stock_movements.qty_delta). Cached table is verified and synchronized.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4 text-xs font-medium">
              <div>
                Total Items: <span className="font-bold text-slate-900">{reconciliation?.total_items || 0}</span>
              </div>
              <div className="text-emerald-600">
                Matched: <span className="font-bold">{reconciliation?.matched_items || 0}</span>
              </div>
              <div className="text-red-600">
                Mismatches: <span className="font-bold">{reconciliation?.mismatched_items || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Item Code</th>
                    <th className="py-3 px-4">Item Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Unit</th>
                    <th className="py-3 px-4 text-right">Ledger SUM(qty_delta)</th>
                    <th className="py-3 px-4 text-right">Cached Balance</th>
                    <th className="py-3 px-4 text-right">Variance</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 font-mono">
                  {reconciliation?.items?.map((item) => (
                    <tr key={`${item.item_type}-${item.item_id}`} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-bold text-slate-900">{item.item_code}</td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-800">{item.item_name}</td>
                      <td className="py-3 px-4 font-sans text-slate-600">{item.item_type}</td>
                      <td className="py-3 px-4 font-sans text-slate-600">{item.base_unit}</td>
                      <td className="py-3 px-4 text-right font-bold text-blue-600">
                        {parseFloat(item.ledger_qty.toString()).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-700">
                        {parseFloat(item.cached_qty.toString()).toFixed(2)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-bold ${
                          parseFloat(item.difference.toString()) === 0 ? 'text-slate-400' : 'text-red-600'
                        }`}
                      >
                        {parseFloat(item.difference.toString()).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-center font-sans">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            item.status === 'MATCHED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-red-100 text-red-800 border-red-200'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: ADJUSTMENTS */}
      {activeTab === 'adjustments' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Physical Stock Adjustments</h3>
              <p className="text-xs text-slate-500">Record wastage, damages, or count reconciliations</p>
            </div>
            <button
              onClick={loadAdjustmentsData}
              className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-600 transition"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Adjustment #</th>
                  <th className="py-3 px-4">Item Code</th>
                  <th className="py-3 px-4">Item Name</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono">
                {adjustments.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400 font-sans">
                      No inventory adjustments recorded.
                    </td>
                  </tr>
                ) : (
                  adjustments.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-bold text-slate-900">{a.adjustment_number}</td>
                      <td className="py-3 px-4 font-bold text-blue-600">{a.item_code}</td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-800">{a.item_name}</td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            a.adjustment_type === 'INCREASE'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-red-100 text-red-800 border-red-200'
                          }`}
                        >
                          {a.adjustment_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-900">
                        {parseFloat(a.quantity.toString()).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-sans text-slate-600">{a.reason}</td>
                      <td className="py-3 px-4 text-center font-sans">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            a.status === 'POSTED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-amber-100 text-amber-800 border-amber-200'
                          }`}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-sans">
                        {a.status === 'DRAFT' ? (
                          <button
                            onClick={() => handlePostAdjustment(a.id)}
                            className="px-2.5 py-1 bg-blue-600 text-white rounded text-[11px] font-semibold hover:bg-blue-700 transition"
                          >
                            Post Adjustment
                          </button>
                        ) : (
                          <span className="text-[11px] text-emerald-600 font-semibold">Applied</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: INITIALIZE OPENING STOCK */}
      {isOpeningModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm">Initialize Opening Stock (Single Ledger Entry)</h3>
              <button onClick={() => setIsOpeningModalOpen(false)} className="text-slate-400 hover:text-slate-600">×</button>
            </div>
            <form onSubmit={handleCreateOpeningStock} className="p-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Item Category</label>
                <select
                  value={openingForm.item_type}
                  onChange={(e) => {
                    const t = e.target.value as InventoryItemType
                    const items = getAvailableItemsForType(t)
                    setOpeningForm({
                      ...openingForm,
                      item_type: t,
                      item_id: items[0]?.id || '',
                    })
                  }}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                >
                  <option value="RAW">Raw Material</option>
                  <option value="PACKAGING">Packaging Item</option>
                  <option value="FG">Finished Goods Product</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Item</label>
                <select
                  value={openingForm.item_id}
                  onChange={(e) => setOpeningForm({ ...openingForm, item_id: e.target.value })}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                  required
                >
                  {getAvailableItemsForType(openingForm.item_type).map((it) => (
                    <option key={it.id} value={it.id}>{it.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity (Base Units)</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    placeholder="e.g. 100"
                    value={openingForm.quantity}
                    onChange={(e) => setOpeningForm({ ...openingForm, quantity: e.target.value })}
                    className="w-full text-xs p-2 rounded-lg border border-slate-300"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Unit Cost (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="e.g. 42.00"
                    value={openingForm.unit_cost_paise}
                    onChange={(e) => setOpeningForm({ ...openingForm, unit_cost_paise: e.target.value })}
                    className="w-full text-xs p-2 rounded-lg border border-slate-300"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={openingForm.notes}
                  onChange={(e) => setOpeningForm({ ...openingForm, notes: e.target.value })}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsOpeningModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700"
                >
                  Initialize Stock
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: NEW PURCHASE ORDER */}
      {isPurchaseModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm">Create New Purchase Order (Draft)</h3>
              <button onClick={() => setIsPurchaseModalOpen(false)} className="text-slate-400 hover:text-slate-600">×</button>
            </div>
            <form onSubmit={handleCreatePurchase} className="p-4 space-y-4 max-h-[80vh] overflow-y-auto">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Supplier</label>
                  <select
                    value={purchaseForm.supplier_id}
                    onChange={(e) => setPurchaseForm({ ...purchaseForm, supplier_id: e.target.value })}
                    className="w-full text-xs p-2 rounded-lg border border-slate-300"
                    required
                  >
                    <option value="">Select Supplier...</option>
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>{s.supplier_name} ({s.supplier_code})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Supplier Invoice Number</label>
                  <input
                    type="text"
                    placeholder="e.g. INV-2026-001"
                    value={purchaseForm.supplier_invoice_number}
                    onChange={(e) => setPurchaseForm({ ...purchaseForm, supplier_invoice_number: e.target.value })}
                    className="w-full text-xs p-2 rounded-lg border border-slate-300"
                    required
                  />
                </div>
              </div>

              {/* Purchase Lines */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-800 uppercase">Purchase Line Items</h4>
                  <button
                    type="button"
                    onClick={addPurchaseLine}
                    className="text-xs text-blue-600 font-semibold hover:underline flex items-center space-x-1"
                  >
                    <Plus className="h-3 w-3" />
                    <span>Add Item</span>
                  </button>
                </div>

                {purchaseForm.lines.map((line, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                    <div className="grid grid-cols-4 gap-2">
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-600 mb-1">Item Type</label>
                        <select
                          value={line.item_type}
                          onChange={(e) => {
                            const newLines = [...purchaseForm.lines]
                            const itype = e.target.value as PurchaseItemType
                            newLines[idx].item_type = itype
                            newLines[idx].item_id = itype === 'RAW' ? rawMaterials[0]?.id || '' : packagingItems[0]?.id || ''
                            setPurchaseForm({ ...purchaseForm, lines: newLines })
                          }}
                          className="w-full text-xs p-1.5 rounded border border-slate-300"
                        >
                          <option value="RAW">Raw Material</option>
                          <option value="PACKAGING">Packaging Item</option>
                        </select>
                      </div>

                      <div className="col-span-2">
                        <label className="block text-[10px] font-semibold text-slate-600 mb-1">Item</label>
                        <select
                          value={line.item_id}
                          onChange={(e) => {
                            const newLines = [...purchaseForm.lines]
                            newLines[idx].item_id = e.target.value
                            setPurchaseForm({ ...purchaseForm, lines: newLines })
                          }}
                          className="w-full text-xs p-1.5 rounded border border-slate-300"
                          required
                        >
                          {line.item_type === 'RAW'
                            ? rawMaterials.map((r) => <option key={r.id} value={r.id}>{r.material_name}</option>)
                            : packagingItems.map((p) => <option key={p.id} value={p.id}>{p.packaging_name}</option>)}
                        </select>
                      </div>

                      <div>
                        <label className="block text-[10px] font-semibold text-slate-600 mb-1">Unit</label>
                        <select
                          value={line.unit}
                          onChange={(e) => {
                            const newLines = [...purchaseForm.lines]
                            newLines[idx].unit = e.target.value
                            setPurchaseForm({ ...purchaseForm, lines: newLines })
                          }}
                          className="w-full text-xs p-1.5 rounded border border-slate-300"
                        >
                          <option value="kg">kg</option>
                          <option value="g">g</option>
                          <option value="litre">litre</option>
                          <option value="piece">piece</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2 items-center">
                      <div>
                        <label className="block text-[10px] font-semibold text-slate-600 mb-1">Quantity</label>
                        <input
                          type="number"
                          step="0.0001"
                          placeholder="e.g. 60"
                          value={line.quantity}
                          onChange={(e) => {
                            const newLines = [...purchaseForm.lines]
                            newLines[idx].quantity = e.target.value
                            setPurchaseForm({ ...purchaseForm, lines: newLines })
                          }}
                          className="w-full text-xs p-1.5 rounded border border-slate-300"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-semibold text-slate-600 mb-1">Rate (₹/unit)</label>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="e.g. 45.00"
                          value={line.unit_rate_paise}
                          onChange={(e) => {
                            const newLines = [...purchaseForm.lines]
                            newLines[idx].unit_rate_paise = e.target.value
                            setPurchaseForm({ ...purchaseForm, lines: newLines })
                          }}
                          className="w-full text-xs p-1.5 rounded border border-slate-300"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-semibold text-slate-600 mb-1">GST Rate</label>
                        <select
                          value={line.tax_rate}
                          onChange={(e) => {
                            const newLines = [...purchaseForm.lines]
                            newLines[idx].tax_rate = e.target.value
                            setPurchaseForm({ ...purchaseForm, lines: newLines })
                          }}
                          className="w-full text-xs p-1.5 rounded border border-slate-300"
                        >
                          <option value="0.05">5% GST</option>
                          <option value="0.12">12% GST</option>
                          <option value="0.18">18% GST</option>
                        </select>
                      </div>

                      <div className="flex justify-end pt-4">
                        {purchaseForm.lines.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removePurchaseLine(idx)}
                            className="text-xs text-red-600 hover:text-red-800 font-semibold"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Notes</label>
                <input
                  type="text"
                  placeholder="Optional memo..."
                  value={purchaseForm.notes}
                  onChange={(e) => setPurchaseForm({ ...purchaseForm, notes: e.target.value })}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsPurchaseModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700"
                >
                  Create Purchase Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: NEW ADJUSTMENT */}
      {isAdjustmentModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="font-bold text-slate-900 text-sm">Create Stock Adjustment (Draft)</h3>
              <button onClick={() => setIsAdjustmentModalOpen(false)} className="text-slate-400 hover:text-slate-600">×</button>
            </div>
            <form onSubmit={handleCreateAdjustment} className="p-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Item Category</label>
                <select
                  value={adjForm.item_type}
                  onChange={(e) => {
                    const t = e.target.value as InventoryItemType
                    const items = getAvailableItemsForType(t)
                    setAdjForm({
                      ...adjForm,
                      item_type: t,
                      item_id: items[0]?.id || '',
                    })
                  }}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                >
                  <option value="RAW">Raw Material</option>
                  <option value="PACKAGING">Packaging Item</option>
                  <option value="FG">Finished Goods Product</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Item</label>
                <select
                  value={adjForm.item_id}
                  onChange={(e) => setAdjForm({ ...adjForm, item_id: e.target.value })}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                  required
                >
                  {getAvailableItemsForType(adjForm.item_type).map((it) => (
                    <option key={it.id} value={it.id}>{it.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Adjustment Type</label>
                  <select
                    value={adjForm.adjustment_type}
                    onChange={(e) => setAdjForm({ ...adjForm, adjustment_type: e.target.value as AdjustmentType })}
                    className="w-full text-xs p-2 rounded-lg border border-slate-300"
                  >
                    <option value="INCREASE">INCREASE (+)</option>
                    <option value="DECREASE">DECREASE (-)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    placeholder="e.g. 5"
                    value={adjForm.quantity}
                    onChange={(e) => setAdjForm({ ...adjForm, quantity: e.target.value })}
                    className="w-full text-xs p-2 rounded-lg border border-slate-300"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reason / Memo</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Packaging damage or physical stock audit..."
                  value={adjForm.reason}
                  onChange={(e) => setAdjForm({ ...adjForm, reason: e.target.value })}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300"
                  required
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsAdjustmentModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700"
                >
                  Save Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
