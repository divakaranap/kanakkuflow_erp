import React, { useState, useEffect } from 'react'
import {
  Factory,
  Plus,
  RefreshCw,
  BookOpen,
  Scale,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
} from 'lucide-react'
import { productionService } from '../../services/productionService'
import { masterService } from '../../services/masterService'
import { formatINR } from '../../lib/utils'
import type {
  BOM,
  ProductionRun,
  ProductionRunCreate,
  ProductionVarianceReport,
  ProductionCostingReport,
  ProductionSummary,
  BOMScalingResponse,
} from '../../types/production'
import type { Product } from '../../types/masters'
import type { InventoryItemType } from '../../types/inventory'

export function ProductionOverview() {
  const [activeTab, setActiveTab] = useState<'runs' | 'new-run' | 'boms' | 'variance' | 'costing'>('runs')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Data
  const [summary, setSummary] = useState<ProductionSummary | null>(null)
  const [runs, setRuns] = useState<ProductionRun[]>([])
  const [boms, setBoms] = useState<BOM[]>([])
  const [selectedRun, setSelectedRun] = useState<ProductionRun | null>(null)
  const [varianceReport, setVarianceReport] = useState<ProductionVarianceReport | null>(null)
  const [costingReport, setCostingReport] = useState<ProductionCostingReport | null>(null)

  // Master lookups
  const [products, setProducts] = useState<Product[]>([])

  // New Production Run Guided Form State
  const [selectedProductId, setSelectedProductId] = useState('')
  const [activeBOM, setActiveBOM] = useState<BOM | null>(null)
  const [batchCount, setBatchCount] = useState('1.00')
  const [scaledBOM, setScaledBOM] = useState<BOMScalingResponse | null>(null)
  const [batchNumber, setBatchNumber] = useState('')
  const [actualOutput, setActualOutput] = useState('188')
  const [damagedPackaging, setDamagedPackaging] = useState('6')
  const [actualMaterials, setActualMaterials] = useState<Array<{
    item_type: InventoryItemType
    item_id: string
    name: string
    code: string
    unit: string
    planned_quantity: string
    actual_quantity: string
  }>>([])
  const [labourPaise, setLabourPaise] = useState('1200') // ₹1,200
  const [utilityPaise, setUtilityPaise] = useState('600')  // ₹600

  // New BOM Modal State
  const [isNewBOMOpen, setIsNewBOMOpen] = useState(false)
  const [newBOMProductId, setNewBOMProductId] = useState('')
  const [newBOMYield, setNewBOMYield] = useState('200')
  const [newBOMTolerance, setNewBOMTolerance] = useState('3.00')
  const [newBOMDesc, setNewBOMDesc] = useState('')

  useEffect(() => {
    loadLookups()
    loadSummary()
    loadRuns()
  }, [])

  useEffect(() => {
    if (activeTab === 'runs') loadRuns()
    if (activeTab === 'boms') loadBOMs()
  }, [activeTab])

  const loadLookups = async () => {
    try {
      const prds = await masterService.getProducts()
      setProducts(prds)
      if (prds.length > 0) {
        setSelectedProductId(prds[0].id)
        handleProductSelect(prds[0].id)
      }
    } catch {
      // ignore
    }
  }


  const loadSummary = async () => {
    try {
      const s = await productionService.getProductionSummary()
      setSummary(s)
    } catch {
      // ignore
    }
  }


  const loadRuns = async () => {
    setLoading(true)
    try {
      const res = await productionService.getProductionRuns()
      setRuns(res.items)
      if (res.items.length > 0 && !selectedRun) {
        handleSelectRun(res.items[0])
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load production runs')
    } finally {
      setLoading(false)
    }
  }


  const loadBOMs = async () => {
    setLoading(true)
    try {
      const res = await productionService.getBOMs()
      setBoms(res.items)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load BOMs')
    } finally {
      setLoading(false)
    }
  }


  const handleProductSelect = async (prodId: string) => {
    setSelectedProductId(prodId)
    setErrorMsg('')
    try {
      const b = await productionService.getActiveBOM(prodId)
      setActiveBOM(b)
      const scaled = await productionService.scaleBOM(b.id, parseFloat(batchCount) || 1)
      setScaledBOM(scaled)
      setActualMaterials(
        scaled.items.map((it) => ({
          item_type: it.item_type,
          item_id: it.item_id,
          name: it.item_name,
          code: it.item_code,
          unit: it.unit,
          planned_quantity: it.planned_quantity.toString(),
          actual_quantity: it.planned_quantity.toString(),
        }))
      )
      setBatchNumber(`BATCH-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-01`)
    } catch {
      setActiveBOM(null)
      setScaledBOM(null)
      setActualMaterials([])
    }
  }


  const handleBatchCountChange = async (batchesStr: string) => {
    setBatchCount(batchesStr)
    const bNum = parseFloat(batchesStr)
    if (activeBOM && bNum > 0) {
      try {
        const scaled = await productionService.scaleBOM(activeBOM.id, bNum)
        setScaledBOM(scaled)
        setActualMaterials(
          scaled.items.map((it) => ({
            item_type: it.item_type,
            item_id: it.item_id,
            name: it.item_name,
            code: it.item_code,
            unit: it.unit,
            planned_quantity: it.planned_quantity.toString(),
            actual_quantity: it.planned_quantity.toString(),
          }))
        )
      } catch {
        // ignore
      }
    }
  }


  const handleSelectRun = async (run: ProductionRun) => {
    setSelectedRun(run)
    try {
      const [v, c] = await Promise.all([
        productionService.getVarianceReport(run.id),
        productionService.getCostingReport(run.id),
      ])
      setVarianceReport(v)
      setCostingReport(c)
    } catch {
      // ignore
    }
  }


  const handlePostRun = async (runId: string) => {
    setLoading(true)
    setErrorMsg('')
    setSuccessMsg('')
    try {
      await productionService.postProductionRun(runId)
      setSuccessMsg('Production run posted! Inventory ledger, finished goods, and costing updated.')
      loadRuns()
      loadSummary()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to post production run')
    } finally {
      setLoading(false)
    }
  }


  const handleActivateBOM = async (bomId: string) => {
    setLoading(true)
    try {
      await productionService.activateBOM(bomId)
      setSuccessMsg('BOM activated successfully.')
      loadBOMs()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to activate BOM')
    } finally {
      setLoading(false)
    }
  }


  const handleArchiveBOM = async (bomId: string) => {
    setLoading(true)
    try {
      await productionService.archiveBOM(bomId)
      setSuccessMsg('BOM archived successfully.')
      loadBOMs()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to archive BOM')
    } finally {
      setLoading(false)
    }
  }


  const handleCreateRun = async (e: React.FormEvent, autoPost: boolean = false) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')
    if (!activeBOM) {
      setErrorMsg('No active recipe BOM loaded for selected product')
      return
    }

    try {
      const payload: ProductionRunCreate = {
        product_id: selectedProductId,
        bom_id: activeBOM.id,
        batch_number: batchNumber,
        number_of_batches: parseFloat(batchCount),
        actual_good_output: parseFloat(actualOutput),
        damaged_packaging: parseFloat(damagedPackaging),
        materials: actualMaterials.map((m) => ({
          item_type: m.item_type,
          item_id: m.item_id,
          issued_quantity: parseFloat(m.actual_quantity),
          consumed_quantity: parseFloat(m.actual_quantity),
          unit: m.unit,
        })),
        overheads: [
          {
            expense_type: 'LABOUR',
            amount_paise: Math.round(parseFloat(labourPaise) * 100),
            description: 'Direct factory labour',
          },
          {
            expense_type: 'GAS',
            amount_paise: Math.round(parseFloat(utilityPaise) * 100),
            description: 'LPG Gas / electricity power',
          },
        ],
      }

      const run = await productionService.createProductionRun(payload)
      if (autoPost) {
        await productionService.postProductionRun(run.id)
        setSuccessMsg(`Production run ${run.run_number} posted and stock ledger updated!`)
      } else {
        setSuccessMsg(`Draft production run ${run.run_number} saved.`)
      }
      setActiveTab('runs')
      loadRuns()
      loadSummary()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to execute production run')
    }
  }



  const handleCreateBOM = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newBOMProductId) {
      setErrorMsg('Please select a product for the new BOM')
      return
    }
    try {
      await productionService.createBOM({
        product_id: newBOMProductId,
        batch_yield_packets: parseFloat(newBOMYield) || 200,
        tolerance_pct: parseFloat(newBOMTolerance) || 3.0,
        description: newBOMDesc || 'Standard Production Recipe',
        items: [],
      })
      setSuccessMsg('BOM created successfully as DRAFT. You can add items or activate it.')
      setIsNewBOMOpen(false)
      loadBOMs()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create BOM')
    }
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
          <span className="text-[11px] font-bold text-[#77758A] uppercase tracking-wider">Total Packets Produced</span>
          <div className="text-2xl font-extrabold text-[#17152B] mt-1">
            {summary?.total_good_packets_produced || 0} Packets
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Good output across runs</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#7655E8] uppercase tracking-wider">Overall Yield Rate</span>
          <div className="text-2xl font-extrabold text-[#7655E8] mt-1">
            {summary?.overall_yield_pct?.toFixed(2) || '100.00'}%
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Actual vs Expected</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#9675F5] uppercase tracking-wider">Total Production Cost</span>
          <div className="text-2xl font-extrabold text-[#17152B] mt-1">
            {formatINR(summary?.total_production_cost_paise || 0)}
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Materials + Direct Overheads</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#16A36A] uppercase tracking-wider">Avg Cost Per Packet</span>
          <div className="text-2xl font-extrabold text-[#16A36A] mt-1">
            {formatINR(summary?.avg_cost_per_packet_paise || 0)}/pkt
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Moving weighted average</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#E9A23B] uppercase tracking-wider">Variance Alerts</span>
          <div className="text-2xl font-extrabold text-[#E9A23B] mt-1 flex items-center space-x-1.5">
            <AlertTriangle className="h-5 w-5 text-[#E9A23B]" />
            <span>{summary?.runs_with_variance_alerts || 0} Runs</span>
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">&gt; 3% tolerance threshold</span>
        </div>
      </div>

      {/* Tabs and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-2.5 rounded-2xl border border-[#EAE8F1] shadow-card">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <button
            onClick={() => setActiveTab('runs')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'runs' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <Factory className="h-4 w-4" />
            <span>Production Runs</span>
          </button>

          <button
            onClick={() => setActiveTab('new-run')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'new-run' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <Plus className="h-4 w-4" />
            <span>New Production Run</span>
          </button>

          <button
            onClick={() => setActiveTab('boms')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'boms' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <BookOpen className="h-4 w-4" />
            <span>Recipe BOMs</span>
          </button>

          {selectedRun && (
            <>
              <button
                onClick={() => setActiveTab('variance')}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
                  activeTab === 'variance' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
                }`}
              >
                <Scale className="h-4 w-4" />
                <span>Yield Variance</span>
              </button>

              <button
                onClick={() => setActiveTab('costing')}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
                  activeTab === 'costing' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
                }`}
              >
                <DollarSign className="h-4 w-4" />
                <span>Cost Analysis</span>
              </button>
            </>
          )}
        </div>

        <button
          onClick={() => {
            loadRuns()
            loadSummary()
            if (activeTab === 'boms') loadBOMs()
          }}
          disabled={loading}
          className="p-2 rounded-xl border border-[#EAE8F1] bg-[#F8F7FC] hover:bg-white text-[#77758A] hover:text-[#17152B] transition self-end sm:self-auto flex items-center gap-1.5 shadow-xs"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-[#7655E8]' : ''}`} />
          {loading && <span className="text-xs text-[#7655E8] font-bold">Syncing...</span>}
        </button>
      </div>

      {/* TAB 1: PRODUCTION RUNS TABLE */}
      {activeTab === 'runs' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">Production Execution History</h3>
            <span className="text-xs text-slate-500 font-medium">Traceable to Inventory Ledger</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Run #</th>
                  <th className="py-3 px-4">Product</th>
                  <th className="py-3 px-4">Batch #</th>
                  <th className="py-3 px-4 text-center">Batches</th>
                  <th className="py-3 px-4 text-right">Good Output</th>
                  <th className="py-3 px-4 text-right">Damaged Pkg</th>
                  <th className="py-3 px-4 text-right">Cost / Packet</th>
                  <th className="py-3 px-4 text-center">Variance Alert</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="py-8 text-center text-slate-400">
                      No production runs found. Click "New Production Run" to start one.
                    </td>
                  </tr>
                ) : (
                  runs.map((r) => (
                    <tr
                      key={r.id}
                      onClick={() => handleSelectRun(r)}
                      className={`hover:bg-slate-50 transition cursor-pointer ${
                        selectedRun?.id === r.id ? 'bg-blue-50/50' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{r.run_number}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">{r.product_name}</td>
                      <td className="py-3 px-4 font-mono text-slate-700">{r.batch_number}</td>
                      <td className="py-3 px-4 text-center font-mono">{r.number_of_batches}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        {parseFloat(r.actual_good_output.toString()).toFixed(0)} pkts
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-red-600">
                        {parseFloat(r.damaged_packaging.toString()).toFixed(0)} pcs
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        {formatINR(r.cost_per_packet_paise)}/pkt
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            r.variance_status === 'NORMAL'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-amber-100 text-amber-800 border-amber-200'
                          }`}
                        >
                          {r.variance_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            r.status === 'POSTED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-amber-100 text-amber-800 border-amber-200'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                        {r.status === 'DRAFT' ? (
                          <button
                            onClick={() => handlePostRun(r.id)}
                            className="px-2.5 py-1 bg-emerald-600 text-white rounded text-[11px] font-semibold hover:bg-emerald-700 transition"
                          >
                            Post Run
                          </button>
                        ) : (
                          <span className="text-[11px] text-emerald-600 font-semibold">Posted</span>
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

      {/* TAB 2: GUIDED PRODUCTION RUN WIZARD */}
      {activeTab === 'new-run' && (
        <form onSubmit={(e) => handleCreateRun(e, false)} className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">Production Execution Wizard</h3>
                <p className="text-xs text-slate-500">
                  Select finished product to automatically scale standard recipe BOM and check stock sufficiency.
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">
                NIT Trichy Benchmark Workflow
              </span>
            </div>

            {/* Step 1 & 2: Select Product & Batches */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Finished Product</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => handleProductSelect(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-medium"
                  required
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>{p.product_name} ({p.sku})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Batch Number</label>
                <input
                  type="text"
                  value={batchNumber}
                  onChange={(e) => setBatchNumber(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Number of Batches</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={batchCount}
                  onChange={(e) => handleBatchCountChange(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono"
                  required
                />
              </div>
            </div>

            {/* Expected Yield Display */}
            {scaledBOM && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between text-xs text-blue-900 font-medium">
                <div>
                  Active Recipe: <span className="font-bold">{scaledBOM.bom_code} (v{scaledBOM.version})</span>
                </div>
                <div>
                  Expected Output: <span className="font-bold text-sm text-blue-700">{scaledBOM.expected_output_packets} Packets</span>
                </div>
                <div>
                  Variance Tolerance: <span className="font-bold">±{scaledBOM.tolerance_pct}%</span>
                </div>
              </div>
            )}

            {/* Materials Consumption Table (Planned vs Actuals & Stock Sufficiency) */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Raw Materials & Packaging Requirements
              </h4>
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Item</th>
                      <th className="py-2.5 px-3">Unit</th>
                      <th className="py-2.5 px-3 text-right">Standard Planned</th>
                      <th className="py-2.5 px-3 text-right">Available Stock</th>
                      <th className="py-2.5 px-3 text-center">Stock Sufficiency</th>
                      <th className="py-2.5 px-3 text-right w-40">Actual Issued / Consumed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {actualMaterials.map((m, idx) => {
                      const plannedNum = parseFloat(m.planned_quantity)
                      const actualNum = parseFloat(m.actual_quantity)
                      const varPct = plannedNum > 0 ? ((actualNum - plannedNum) / plannedNum) * 100 : 0

                      return (
                        <tr key={m.item_id} className="hover:bg-slate-50 transition">
                          <td className="py-2.5 px-3 font-medium text-slate-900">
                            {m.name} <span className="text-[11px] text-slate-500 font-mono">({m.code})</span>
                          </td>
                          <td className="py-2.5 px-3 text-slate-600">{m.unit}</td>
                          <td className="py-2.5 px-3 text-right font-mono text-slate-700">
                            {parseFloat(m.planned_quantity).toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                            {scaledBOM?.items?.find((i) => i.item_id === m.item_id)?.available_stock || '0.00'}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            {scaledBOM?.items?.find((i) => i.item_id === m.item_id)?.is_sufficient ? (
                              <span className="inline-flex items-center text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                <CheckCircle2 className="h-3 w-3 mr-1" /> Sufficient
                              </span>
                            ) : (
                              <span className="inline-flex items-center text-[10px] text-red-700 font-semibold bg-red-50 px-2 py-0.5 rounded border border-red-200">
                                <AlertTriangle className="h-3 w-3 mr-1" /> Insufficient
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <div className="flex items-center justify-end space-x-2">
                              <input
                                type="number"
                                step="0.0001"
                                min="0"
                                value={m.actual_quantity}
                                onChange={(e) => {
                                  const newArr = [...actualMaterials]
                                  newArr[idx].actual_quantity = e.target.value
                                  setActualMaterials(newArr)
                                }}
                                className="w-28 text-xs p-1 text-right font-mono rounded border border-slate-300 font-bold text-blue-600"
                                required
                              />
                              {varPct !== 0 && (
                                <span className={`text-[10px] font-bold ${varPct > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                  {varPct > 0 ? `+${varPct.toFixed(1)}%` : `${varPct.toFixed(1)}%`}
                                </span>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actual Output & Overheads Entry */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Actual Good Output (Packets)
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={actualOutput}
                  onChange={(e) => setActualOutput(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono font-bold text-emerald-700 bg-white"
                  required
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Increases Finished Goods stock</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Damaged Packaging (Pouches)
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={damagedPackaging}
                  onChange={(e) => setDamagedPackaging(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono font-bold text-red-600 bg-white"
                  required
                />
                <span className="text-[10px] text-slate-500 mt-1 block">Scrapped, included in cost</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Direct Labour Charge (₹)
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={labourPaise}
                  onChange={(e) => setLabourPaise(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono bg-white"
                  required
                />
                <span className="text-[10px] text-slate-500 mt-1 block">₹1,200 standard</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Gas / Utilities (₹)
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={utilityPaise}
                  onChange={(e) => setUtilityPaise(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-slate-300 font-mono bg-white"
                  required
                />
                <span className="text-[10px] text-slate-500 mt-1 block">₹600 fuel / power</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setActiveTab('runs')}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition"
              >
                Save Draft Run
              </button>
              <button
                type="button"
                onClick={(e) => handleCreateRun(e, true)}
                className="px-5 py-2 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm flex items-center space-x-1"
              >
                <span>Post Run to Inventory</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </form>
      )}

      {/* TAB 3: BILL OF MATERIALS (BOM) */}
      {activeTab === 'boms' && (
        <div className="space-y-4">
          {isNewBOMOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
              <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
                <div className="flex items-center justify-between border-b pb-3 border-slate-100">
                  <h3 className="font-bold text-slate-900 text-sm">Create New Recipe BOM</h3>
                  <button
                    onClick={() => setIsNewBOMOpen(false)}
                    className="text-slate-400 hover:text-slate-600 font-bold"
                  >
                    ✕
                  </button>
                </div>
                <form onSubmit={handleCreateBOM} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Target Product</label>
                    <select
                      value={newBOMProductId}
                      onChange={(e) => setNewBOMProductId(e.target.value)}
                      className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                      required
                    >
                      <option value="">-- Select Product --</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.product_name} ({p.sku})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Yield (Packets)</label>
                      <input
                        type="number"
                        value={newBOMYield}
                        onChange={(e) => setNewBOMYield(e.target.value)}
                        className="w-full text-xs p-2.5 rounded-lg border border-slate-300"
                        required
                        min="1"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Tolerance %</label>
                      <input
                        type="number"
                        step="0.01"
                        value={newBOMTolerance}
                        onChange={(e) => setNewBOMTolerance(e.target.value)}
                        className="w-full text-xs p-2.5 rounded-lg border border-slate-300"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                    <input
                      type="text"
                      value={newBOMDesc}
                      onChange={(e) => setNewBOMDesc(e.target.value)}
                      placeholder="e.g. Traditional Spicy Recipe"
                      className="w-full text-xs p-2.5 rounded-lg border border-slate-300"
                    />
                  </div>
                  <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setIsNewBOMOpen(false)}
                      className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                    >
                      Save Recipe
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between bg-slate-50">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Recipe Bills of Materials (BOM)</h3>
              <p className="text-xs text-slate-500">Standard recipes for batch production with versioning and tolerance thresholds</p>
            </div>
            <button
              onClick={() => setIsNewBOMOpen(true)}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition flex items-center space-x-1"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Create Recipe BOM</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {boms.map((b) => (
              <div key={b.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-slate-900">{b.bom_code}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        v{b.version}
                      </span>
                    </div>
                    <h4 className="text-sm font-semibold text-slate-800 mt-1">{b.product_name}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">{b.description || 'Standard Production Recipe'}</p>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${
                      b.status === 'ACTIVE'
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                        : b.status === 'ARCHIVED'
                        ? 'bg-slate-100 text-slate-600 border-slate-200'
                        : 'bg-amber-100 text-amber-800 border-amber-200'
                    }`}
                  >
                    {b.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 p-2.5 bg-slate-50 rounded-lg text-xs border border-slate-200">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Batch Yield:</span>
                    <span className="font-bold text-slate-900">{b.batch_yield_packets} packets</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Tolerance:</span>
                    <span className="font-bold text-slate-900">±{b.tolerance_pct}%</span>
                  </div>
                </div>

                {/* Recipe Composition */}
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">Recipe Composition</span>
                  <div className="divide-y divide-slate-100 border border-slate-100 rounded-lg overflow-hidden">
                    {b.items.map((it) => (
                      <div key={it.id} className="px-3 py-1.5 text-xs flex items-center justify-between bg-slate-50/50">
                        <span className="text-slate-800 font-medium">{it.item_name}</span>
                        <span className="font-mono font-bold text-slate-900">
                          {parseFloat(it.quantity_per_batch.toString()).toFixed(2)} {it.unit}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-200">
                  {b.status === 'DRAFT' && (
                    <button
                      onClick={() => handleActivateBOM(b.id)}
                      className="px-3 py-1 bg-emerald-600 text-white rounded text-xs font-semibold hover:bg-emerald-700"
                    >
                      Activate Recipe
                    </button>
                  )}
                  {b.status === 'ACTIVE' && (
                    <button
                      onClick={() => handleArchiveBOM(b.id)}
                      className="px-3 py-1 bg-slate-600 text-white rounded text-xs font-semibold hover:bg-slate-700"
                    >
                      Archive
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: VARIANCE ANALYSIS */}
      {activeTab === 'variance' && (
        <div className="space-y-4">
          {selectedRun ? (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
              <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Variance Analysis: {selectedRun.run_number} ({selectedRun.product_name})
                  </h3>
                  <p className="text-xs text-slate-500">
                    Formula: ((Actual - Planned) / Planned) × 100. Threshold tolerance: ±3.00%
                  </p>
                </div>
                <span
                  className={`px-3 py-1 text-xs font-bold rounded-full border ${
                    varianceReport?.has_alerts
                      ? 'bg-amber-100 text-amber-800 border-amber-200'
                      : 'bg-emerald-100 text-emerald-800 border-emerald-200'
                  }`}
                >
                  {varianceReport?.has_alerts ? 'WARNING: Tolerance Exceeded' : 'All Materials Within Tolerance'}
                </span>
              </div>

              {/* Alerts Box */}
              {varianceReport?.alerts && varianceReport.alerts.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-1.5">
                  <div className="flex items-center space-x-2 text-amber-900 font-bold text-xs uppercase">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <span>Active Production Variance Alerts</span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-amber-800 font-medium pl-2 space-y-1">
                    {varianceReport.alerts.map((al, idx) => (
                      <li key={idx}>{al}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Yield Variance Card */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <span className="text-[11px] text-slate-500 block uppercase">Expected Yield Output</span>
                  <span className="text-lg font-bold font-mono text-slate-900">
                    {varianceReport?.expected_output} Packets
                  </span>
                </div>
                <div>
                  <span className="text-[11px] text-slate-500 block uppercase">Actual Good Output</span>
                  <span className="text-lg font-bold font-mono text-emerald-700">
                    {varianceReport?.actual_good_output} Packets
                  </span>
                </div>
                <div>
                  <span className="text-[11px] text-slate-500 block uppercase">Yield Variance %</span>
                  <span className={`text-lg font-bold font-mono ${
                    parseFloat(varianceReport?.yield_variance_pct?.toString() || '0') < 0 ? 'text-red-600' : 'text-emerald-600'
                  }`}>
                    {parseFloat(varianceReport?.yield_variance_pct?.toString() || '0').toFixed(2)}%
                  </span>
                </div>
                <div>
                  <span className="text-[11px] text-slate-500 block uppercase">Yield Tolerance Status</span>
                  <span className={`inline-block mt-1 text-xs px-2.5 py-0.5 rounded-full font-bold border ${
                    varianceReport?.yield_status === 'WARNING'
                      ? 'bg-amber-100 text-amber-800 border-amber-200'
                      : 'bg-emerald-100 text-emerald-800 border-emerald-200'
                  }`}>
                    {varianceReport?.yield_status}
                  </span>
                </div>
              </div>

              {/* Material Variance Table */}
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Material</th>
                      <th className="py-2.5 px-3">Code</th>
                      <th className="py-2.5 px-3">Unit</th>
                      <th className="py-2.5 px-3 text-right">Planned Qty</th>
                      <th className="py-2.5 px-3 text-right">Actual Qty</th>
                      <th className="py-2.5 px-3 text-right">Difference</th>
                      <th className="py-2.5 px-3 text-right">Variance %</th>
                      <th className="py-2.5 px-3 text-center">Tolerance</th>
                      <th className="py-2.5 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 font-mono">
                    {varianceReport?.material_variances?.map((m) => (
                      <tr key={m.item_id} className="hover:bg-slate-50 transition">
                        <td className="py-2.5 px-3 font-sans font-medium text-slate-900">{m.item_name}</td>
                        <td className="py-2.5 px-3 text-slate-600">{m.item_code}</td>
                        <td className="py-2.5 px-3 font-sans text-slate-600">{m.unit}</td>
                        <td className="py-2.5 px-3 text-right text-slate-700">
                          {parseFloat(m.planned_quantity.toString()).toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                          {parseFloat(m.actual_quantity.toString()).toFixed(2)}
                        </td>
                        <td className={`py-2.5 px-3 text-right font-bold ${
                          parseFloat(m.difference.toString()) > 0 ? 'text-amber-600' : 'text-slate-600'
                        }`}>
                          {parseFloat(m.difference.toString()) > 0 ? '+' : ''}
                          {parseFloat(m.difference.toString()).toFixed(2)}
                        </td>
                        <td className={`py-2.5 px-3 text-right font-bold ${
                          m.status === 'WARNING' ? 'text-amber-600' : 'text-slate-700'
                        }`}>
                          {parseFloat(m.variance_pct.toString()) > 0 ? '+' : ''}
                          {parseFloat(m.variance_pct.toString()).toFixed(2)}%
                        </td>
                        <td className="py-2.5 px-3 text-center text-slate-500">±{m.tolerance_pct}%</td>
                        <td className="py-2.5 px-3 text-center font-sans">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              m.status === 'OK'
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                                : 'bg-amber-100 text-amber-800 border-amber-200'
                            }`}
                          >
                            {m.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-400">
              Select a production run from the Production Runs tab to inspect its variance report.
            </div>
          )}
        </div>
      )}

      {/* TAB 5: COSTING & MARGINS */}
      {activeTab === 'costing' && (
        <div className="space-y-4">
          {selectedRun ? (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
              <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Costing Analysis: {selectedRun.run_number} ({selectedRun.product_name})
                  </h3>
                  <p className="text-xs text-slate-500">
                    Integrated with Phase 3 moving weighted-average inventory valuation rates
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-500 block">Unit Cost Per Packet:</span>
                  <span className="text-xl font-bold font-mono text-emerald-700">
                    {formatINR(costingReport?.cost_per_packet_paise || 0)}
                  </span>
                </div>
              </div>

              {/* Cost Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block">Raw Materials Cost</span>
                  <span className="text-lg font-bold font-mono text-slate-900">
                    {formatINR(costingReport?.raw_materials_cost_paise || 0)}
                  </span>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block">Packaging Cost (incl. scrap)</span>
                  <span className="text-lg font-bold font-mono text-purple-900">
                    {formatINR(costingReport?.packaging_cost_paise || 0)}
                  </span>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-xs text-slate-500 block">Direct Overheads (Labour+Gas)</span>
                  <span className="text-lg font-bold font-mono text-blue-900">
                    {formatINR(costingReport?.total_overheads_paise || 0)}
                  </span>
                </div>

                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                  <span className="text-xs text-emerald-800 font-semibold block">Total Production Cost</span>
                  <span className="text-lg font-bold font-mono text-emerald-900">
                    {formatINR(costingReport?.total_production_cost_paise || 0)}
                  </span>
                </div>
              </div>

              {/* Profitability & Margin Card */}
              <div className="p-4 bg-slate-900 text-white rounded-xl grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                <div>
                  <span className="text-xs text-slate-400 block">Good Packets Output</span>
                  <span className="text-lg font-bold font-mono">{costingReport?.actual_good_output} pkts</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Selling Price (MRP)</span>
                  <span className="text-lg font-bold font-mono">{formatINR(costingReport?.selling_price_paise || 0)}</span>
                </div>
                <div>
                  <span className="text-xs text-emerald-400 block">Gross Margin / Packet</span>
                  <span className="text-lg font-bold font-mono text-emerald-400">
                    {formatINR(costingReport?.gross_margin_paise || 0)}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-emerald-400 block">Gross Margin %</span>
                  <span className="text-lg font-bold font-mono text-emerald-400">
                    {parseFloat(costingReport?.gross_margin_pct?.toString() || '0').toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Detailed Materials Cost Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Material & Packaging Valuation Breakdown
                </h4>
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200 font-sans">
                      <tr>
                        <th className="py-2.5 px-3">Item</th>
                        <th className="py-2.5 px-3">Code</th>
                        <th className="py-2.5 px-3">Type</th>
                        <th className="py-2.5 px-3 text-right">Consumed Qty</th>
                        <th className="py-2.5 px-3 text-right">Weighted Avg Rate</th>
                        <th className="py-2.5 px-3 text-right">Line Total Cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {costingReport?.material_breakdown?.map((item) => (
                        <tr key={item.item_id} className="hover:bg-slate-50 transition">
                          <td className="py-2.5 px-3 font-sans font-medium text-slate-900">{item.item_name}</td>
                          <td className="py-2.5 px-3 text-slate-600">{item.item_code}</td>
                          <td className="py-2.5 px-3 font-sans text-slate-600">{item.item_type}</td>
                          <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                            {parseFloat(item.consumed_quantity).toFixed(2)} {item.unit}
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-600">
                            {formatINR(item.unit_cost_paise)}/{item.unit}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                            {formatINR(item.line_cost_paise)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-400">
              Select a production run from the Production Runs tab to inspect its costing report.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
