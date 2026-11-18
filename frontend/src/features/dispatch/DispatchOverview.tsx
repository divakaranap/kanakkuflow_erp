import React, { useState, useEffect } from 'react'
import {
  Truck,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Download,
  Eye,
  Check,
  PackageCheck,
  Clock,
} from 'lucide-react'
import { dispatchService } from '../../services/dispatchService'
import { salesService } from '../../services/salesService'
import type {
  Dispatch,
  OrderDispatchStatusResponse,
} from '../../types/dispatch'
import type { SalesOrder } from '../../types/sales'

export function DispatchOverview() {
  const [activeTab, setActiveTab] = useState<'dispatches' | 'pending' | 'new-dispatch' | 'challan-preview'>('pending')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Data
  const [dispatches, setDispatches] = useState<Dispatch[]>([])
  const [approvedOrders, setApprovedOrders] = useState<SalesOrder[]>([])
  const [selectedOrderDispatchStatus, setSelectedOrderDispatchStatus] = useState<OrderDispatchStatusResponse | null>(null)
  const [selectedDispatch, setSelectedDispatch] = useState<Dispatch | null>(null)

  // Guided Dispatch Form State
  const [selectedOrderId, setSelectedOrderId] = useState('')
  const [transporterName, setTransporterName] = useState('TN Fast Cargo')
  const [vehicleNumber, setVehicleNumber] = useState('TN-45-AB-1234')
  const [trackingReference, setTrackingReference] = useState('LR-992144')
  const [dispatchNotes, setDispatchNotes] = useState('Standard food grade transport')
  const [dispatchQuantities, setDispatchQuantities] = useState<Record<string, string>>({})

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (activeTab === 'dispatches') loadDispatches()
    if (activeTab === 'pending') loadPendingOrders()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      await Promise.all([loadDispatches(), loadPendingOrders()])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const loadDispatches = async () => {
    try {
      const res = await dispatchService.getDispatches()
      setDispatches(res.items)
      if (res.items.length > 0 && !selectedDispatch) {
        setSelectedDispatch(res.items[0])
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load dispatches')
    }
  }

  const loadPendingOrders = async () => {
    try {
      const res = await salesService.getSalesOrders()
      // Filter for approved or partially fulfilled orders
      const pending = res.items.filter(
        (o) => o.status === 'APPROVED' || o.status === 'PARTIALLY_FULFILLED'
      )
      setApprovedOrders(pending)
      if (pending.length > 0 && !selectedOrderId) {
        handleSelectOrderForDispatch(pending[0].id)
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load pending orders')
    }
  }

  const handleSelectOrderForDispatch = async (orderId: string) => {
    setSelectedOrderId(orderId)
    setErrorMsg('')
    try {
      const statusRes = await dispatchService.getOrderDispatchStatus(orderId)
      setSelectedOrderDispatchStatus(statusRes)

      // Initialize dispatch quantities to the max available dispatchable quantity
      const initQtys: Record<string, string> = {}
      for (const it of statusRes.items) {
        const pending = parseFloat(it.pending_quantity.toString())
        const avail = parseFloat(it.available_stock_quantity.toString())
        const dispatchable = Math.min(pending, avail)
        initQtys[it.sales_order_item_id] = dispatchable.toString()
      }
      setDispatchQuantities(initQtys)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load order dispatch status')
    }
  }

  const handleCreateDispatch = async (e: React.FormEvent, autoPost = true) => {
    e.preventDefault()
    if (!selectedOrderDispatchStatus) {
      setErrorMsg('No order selected')
      return
    }

    const itemsPayload = selectedOrderDispatchStatus.items.map((it) => {
      const userQty = parseFloat(dispatchQuantities[it.sales_order_item_id] || '0')
      return {
        sales_order_item_id: it.sales_order_item_id,
        product_id: it.product_id,
        quantity_dispatched: userQty,
      }
    }).filter((it) => it.quantity_dispatched > 0)

    if (itemsPayload.length === 0) {
      setErrorMsg('Please specify at least one item quantity to dispatch')
      return
    }

    try {
      const disp = await dispatchService.createDispatch({
        sales_order_id: selectedOrderDispatchStatus.sales_order_id,
        transporter_name: transporterName,
        vehicle_number: vehicleNumber,
        tracking_reference: trackingReference,
        notes: dispatchNotes,
        items: itemsPayload,
      })

      if (autoPost) {
        const posted = await dispatchService.postDispatch(disp.id)
        setSuccessMsg(`Dispatch ${posted.dispatch_number} posted and finished goods inventory deducted!`)
        setSelectedDispatch(posted)
        setActiveTab('dispatches')
      } else {
        setSuccessMsg(`Dispatch ${disp.dispatch_number} saved as DRAFT.`)
        setSelectedDispatch(disp)
        setActiveTab('dispatches')
      }

      loadData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to execute dispatch')
    }
  }

  const handlePostDispatch = async (dispId: string) => {
    try {
      const posted = await dispatchService.postDispatch(dispId)
      setSuccessMsg(`Dispatch ${posted.dispatch_number} posted! Finished goods stock reduced.`)
      loadData()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to post dispatch')
    }
  }

  const handleDownloadChallan = async (disp: Dispatch) => {
    try {
      await dispatchService.downloadChallanPdf(disp.id, disp.dispatch_number)
      setSuccessMsg(`Delivery Challan ${disp.dispatch_number} downloaded!`)
    } catch {
      setErrorMsg('Failed to download Delivery Challan PDF')
    }
  }

  // KPIs
  const totalDispatchedCount = dispatches.filter((d) => d.status === 'DISPATCHED').length
  const pendingOrdersCount = approvedOrders.length
  const totalPktsDispatched = dispatches
    .filter((d) => d.status === 'DISPATCHED')
    .reduce((sum, d) => sum + d.items.reduce((iSum, it) => iSum + parseFloat(it.quantity_dispatched.toString()), 0), 0)

  return (
    <div className="space-y-6">
      {/* Alert Banners */}
      {errorMsg && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <XCircle className="h-4 w-4 shrink-0 text-red-500" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-red-500 hover:text-red-700 font-bold">✕</button>
        </div>
      )}
      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-700 hover:text-emerald-900 font-bold">✕</button>
        </div>
      )}

      {/* KPI Cards Header */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#77758A] uppercase tracking-wider">Total Dispatches Posted</span>
          <div className="text-2xl font-extrabold text-[#17152B] mt-1">{totalDispatchedCount} Dispatches</div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Physically issued from factory</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#7655E8] uppercase tracking-wider">Total Packets Dispatched</span>
          <div className="text-2xl font-extrabold text-[#7655E8] mt-1">{totalPktsDispatched.toFixed(0)} Packets</div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Finished Goods Output</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#E9A23B] uppercase tracking-wider">Pending Orders</span>
          <div className="text-2xl font-extrabold text-[#E9A23B] mt-1">{pendingOrdersCount} Orders</div>
          <span className="text-[11px] text-[#77758A] mt-1 block">Approved &amp; awaiting dispatch</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-[#EAE8F1] shadow-card">
          <span className="text-[11px] font-bold text-[#16A36A] uppercase tracking-wider">Stock Traceability</span>
          <div className="text-2xl font-extrabold text-[#16A36A] mt-1 flex items-center space-x-1.5">
            <PackageCheck className="h-5 w-5 text-[#16A36A]" />
            <span>100% Ledger Synced</span>
          </div>
          <span className="text-[11px] text-[#77758A] mt-1 block">INVOICE_DISPATCH movements</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-2.5 rounded-2xl border border-[#EAE8F1] shadow-card">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <button
            onClick={() => setActiveTab('pending')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'pending' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <Clock className="h-4 w-4" />
            <span>Pending Dispatch Queue</span>
          </button>

          <button
            onClick={() => setActiveTab('new-dispatch')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'new-dispatch' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <Plus className="h-4 w-4" />
            <span>Create Dispatch</span>
          </button>

          <button
            onClick={() => setActiveTab('dispatches')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'dispatches' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
            }`}
          >
            <Truck className="h-4 w-4" />
            <span>Dispatched History</span>
          </button>

          {selectedDispatch && (
            <button
              onClick={() => setActiveTab('challan-preview')}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition ${
                activeTab === 'challan-preview' ? 'bg-[#F2EEFF] text-[#7655E8] shadow-xs' : 'text-[#77758A] hover:bg-[#F8F7FC] hover:text-[#17152B]'
              }`}
            >
              <Eye className="h-4 w-4" />
              <span>Challan Preview</span>
            </button>
          )}
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="p-2 rounded-xl border border-[#EAE8F1] bg-[#F8F7FC] hover:bg-white text-[#77758A] hover:text-[#17152B] transition self-end sm:self-auto flex items-center gap-1.5 shadow-xs"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-[#7655E8]' : ''}`} />
          {loading && <span className="text-xs text-[#7655E8] font-bold">Syncing...</span>}
        </button>
      </div>

      {/* TAB 1: PENDING DISPATCH QUEUE */}
      {activeTab === 'pending' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-4">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Orders Awaiting Dispatch</h3>
              <p className="text-xs text-slate-500">Approved sales orders ready for shipment and stock deduction</p>
            </div>
            <span className="text-xs font-mono font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
              {approvedOrders.length} Pending Orders
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Order #</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Order Date</th>
                  <th className="py-3 px-4 text-right">Items / Ordered</th>
                  <th className="py-3 px-4 text-center">Order Status</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {approvedOrders.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No pending orders awaiting dispatch.
                    </td>
                  </tr>
                ) : (
                  approvedOrders.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{o.order_number}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">{o.customer_name}</td>
                      <td className="py-3 px-4 text-slate-600">{o.order_date}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-900 font-bold">
                        {o.items.reduce((s, it) => s + parseFloat(it.ordered_quantity.toString()), 0)} pkts
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                            o.status === 'APPROVED'
                              ? 'bg-blue-100 text-blue-800 border-blue-200'
                              : 'bg-purple-100 text-purple-800 border-purple-200'
                          }`}
                        >
                          {o.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => {
                            handleSelectOrderForDispatch(o.id)
                            setActiveTab('new-dispatch')
                          }}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition flex items-center space-x-1 mx-auto"
                        >
                          <Truck className="h-3.5 w-3.5" />
                          <span>Dispatch Order</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: DISPATCHED HISTORY */}
      {activeTab === 'dispatches' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">Dispatch Notes &amp; Delivery History</h3>
            <span className="text-xs text-slate-500 font-medium">Traceable to Finished Goods Stock Movements</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Dispatch #</th>
                  <th className="py-3 px-4">Order Ref</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Transporter &amp; Vehicle</th>
                  <th className="py-3 px-4 text-right">Packets</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {dispatches.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      No dispatches found. Select an approved order from the Pending queue to dispatch.
                    </td>
                  </tr>
                ) : (
                  dispatches.map((d) => (
                    <tr
                      key={d.id}
                      onClick={() => {
                        setSelectedDispatch(d)
                        setActiveTab('challan-preview')
                      }}
                      className="hover:bg-slate-50 transition cursor-pointer"
                    >
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{d.dispatch_number}</td>
                      <td className="py-3 px-4 font-mono text-slate-700">{d.order_number}</td>
                      <td className="py-3 px-4 font-medium text-slate-900">{d.customer_name}</td>
                      <td className="py-3 px-4 text-slate-600">{d.dispatch_date}</td>
                      <td className="py-3 px-4 text-slate-600">
                        {d.transporter_name || 'Direct'} ({d.vehicle_number || 'N/A'})
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        {d.items.reduce((sum, it) => sum + parseFloat(it.quantity_dispatched.toString()), 0)} pkts
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            d.status === 'DISPATCHED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : d.status === 'DRAFT'
                              ? 'bg-amber-100 text-amber-800 border-amber-200'
                              : 'bg-red-100 text-red-800 border-red-200'
                          }`}
                        >
                          {d.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center space-x-1.5">
                          {d.status === 'DRAFT' && (
                            <button
                              onClick={() => handlePostDispatch(d.id)}
                              className="px-2 py-1 bg-emerald-600 text-white rounded text-[11px] font-semibold hover:bg-emerald-700 transition flex items-center space-x-1"
                            >
                              <Check className="h-3 w-3" />
                              <span>Post &amp; Deduct Stock</span>
                            </button>
                          )}
                          <button
                            onClick={() => handleDownloadChallan(d)}
                            className="p-1.5 rounded bg-blue-50 text-blue-600 hover:bg-blue-100 transition"
                            title="Download Delivery Challan PDF"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: GUIDED NEW DISPATCH FORM */}
      {activeTab === 'new-dispatch' && (
        <form onSubmit={(e) => handleCreateDispatch(e, true)} className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-200 pb-4 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">Execute Order Dispatch</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Issue goods from factory finished goods inventory and generate a delivery challan.
                </p>
              </div>
              {selectedOrderDispatchStatus && (
                <span className="text-xs px-3 py-1 rounded-full font-mono font-bold bg-slate-100 text-slate-800 border border-slate-200">
                  Target: {selectedOrderDispatchStatus.order_number}
                </span>
              )}
            </div>

            {/* Order Selector */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Sales Order to Dispatch</label>
                <select
                  value={selectedOrderId}
                  onChange={(e) => handleSelectOrderForDispatch(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                >
                  <option value="">-- Choose Order --</option>
                  {approvedOrders.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.order_number} - {o.customer_name} ({o.status})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Customer / Consignee</label>
                <input
                  type="text"
                  value={selectedOrderDispatchStatus?.customer_name || 'No order selected'}
                  readOnly
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-slate-50 font-semibold text-slate-800"
                />
              </div>
            </div>

            {/* Transport & Carrier Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Transporter / Carrier</label>
                <input
                  type="text"
                  value={transporterName}
                  onChange={(e) => setTransporterName(e.target.value)}
                  placeholder="e.g. TN Logistics"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Vehicle Number</label>
                <input
                  type="text"
                  value={vehicleNumber}
                  onChange={(e) => setVehicleNumber(e.target.value)}
                  placeholder="e.g. TN-45-AB-1234"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tracking / LR Reference</label>
                <input
                  type="text"
                  value={trackingReference}
                  onChange={(e) => setTrackingReference(e.target.value)}
                  placeholder="e.g. LR-102938"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Dispatch Notes / Remarks</label>
                <input
                  type="text"
                  value={dispatchNotes}
                  onChange={(e) => setDispatchNotes(e.target.value)}
                  placeholder="e.g. Handed over to driver"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                />
              </div>
            </div>

            {/* Items & Stock Availability Table */}
            {selectedOrderDispatchStatus && (
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                  Ordered Line Items &amp; Inventory Allocation
                </span>

                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Product Item</th>
                        <th className="py-2.5 px-3 text-right">Ordered Qty</th>
                        <th className="py-2.5 px-3 text-right">Fulfilled</th>
                        <th className="py-2.5 px-3 text-right">Pending Qty</th>
                        <th className="py-2.5 px-3 text-right">Available FG Stock</th>
                        <th className="py-2.5 px-3 text-center">Dispatch Quantity</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 font-mono">
                      {selectedOrderDispatchStatus.items.map((it) => {
                        const pendingNum = parseFloat(it.pending_quantity.toString())
                        const availNum = parseFloat(it.available_stock_quantity.toString())
                        const userQty = parseFloat(dispatchQuantities[it.sales_order_item_id] || '0')
                        const hasExcess = userQty > availNum

                        return (
                          <tr key={it.sales_order_item_id} className="hover:bg-slate-50 transition font-sans">
                            <td className="py-3 px-3 font-medium text-slate-900">{it.product_name}</td>
                            <td className="py-3 px-3 text-right font-mono">{parseFloat(it.ordered_quantity.toString()).toFixed(0)} pkts</td>
                            <td className="py-3 px-3 text-right font-mono text-emerald-600">{parseFloat(it.fulfilled_quantity.toString()).toFixed(0)} pkts</td>
                            <td className="py-3 px-3 text-right font-mono font-bold text-slate-800">{pendingNum.toFixed(0)} pkts</td>
                            <td className="py-3 px-3 text-right font-mono">
                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                availNum >= pendingNum ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                              }`}>
                                {availNum.toFixed(0)} pkts
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center">
                              <input
                                type="number"
                                min="0"
                                max={pendingNum}
                                value={dispatchQuantities[it.sales_order_item_id] || ''}
                                onChange={(e) =>
                                  setDispatchQuantities({
                                    ...dispatchQuantities,
                                    [it.sales_order_item_id]: e.target.value,
                                  })
                                }
                                className={`w-28 text-center text-xs p-1.5 rounded-lg border font-mono font-bold ${
                                  hasExcess
                                    ? 'border-red-500 bg-red-50 text-red-700'
                                    : 'border-slate-300 bg-white text-slate-900'
                                }`}
                                required
                              />
                              {hasExcess && (
                                <span className="block text-[10px] text-red-600 font-semibold mt-0.5">
                                  Shortage: {(userQty - availNum).toFixed(0)} pkts
                                </span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={(e) => handleCreateDispatch(e, false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition"
              >
                Save as Draft
              </button>
              <button
                type="submit"
                className="px-5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition flex items-center space-x-1.5 shadow-sm"
              >
                <span>Confirm &amp; Deduct Finished Stock</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </form>
      )}

      {/* TAB 4: DELIVERY CHALLAN PREVIEW */}
      {activeTab === 'challan-preview' && selectedDispatch && (
        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm max-w-4xl mx-auto space-y-6">
          <div className="flex items-center justify-between border-b pb-4">
            <div>
              <span className="text-xs uppercase font-bold text-emerald-600 tracking-wider">Delivery Challan &amp; Dispatch Note</span>
              <h2 className="text-xl font-bold text-slate-900 mt-0.5">{selectedDispatch.dispatch_number}</h2>
              <span className="text-xs text-slate-500 font-medium">Traceable to Inventory Movement Ledger</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleDownloadChallan(selectedDispatch)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 flex items-center space-x-1"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Challan PDF</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="font-bold text-slate-900 block mb-1">CONSIGNOR (FACTORY):</span>
              <p className="font-semibold text-slate-800">KANAKKUFLOW FOODS PRIVATE LIMITED</p>
              <p className="text-slate-600">Food Processing SEZ, Thuvakudi, Tiruchirappalli, Tamil Nadu</p>
              <p className="font-mono mt-1 text-slate-700">Dispatch Date: {selectedDispatch.dispatch_date}</p>
            </div>
            <div>
              <span className="font-bold text-slate-900 block mb-1">CONSIGNEE (DELIVER TO):</span>
              <p className="font-semibold text-slate-800">{selectedDispatch.customer_name}</p>
              <p className="text-slate-600 mt-1">Transporter: {selectedDispatch.transporter_name || 'Factory Fleet'}</p>
              <p className="font-mono text-slate-700">Vehicle: {selectedDispatch.vehicle_number || 'N/A'}</p>
              <p className="font-mono text-slate-500">Order Ref: {selectedDispatch.order_number}</p>
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-100 text-slate-700 font-semibold font-sans border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Item Description</th>
                  <th className="py-2.5 px-3">SKU</th>
                  <th className="py-2.5 px-3">Batch Reference</th>
                  <th className="py-2.5 px-3 text-right">Quantity Dispatched</th>
                  <th className="py-2.5 px-3">Unit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {selectedDispatch.items.map((it) => (
                  <tr key={it.id}>
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-800">{it.product_name || 'Food Product'}</td>
                    <td className="py-2.5 px-3 text-slate-600">{it.product_sku || 'MUR-200'}</td>
                    <td className="py-2.5 px-3 text-slate-600">{it.batch_reference || '-'}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                      {parseFloat(it.quantity_dispatched.toString()).toFixed(0)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 font-sans">{it.unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-700">Total Goods Dispatched:</span>
            <span className="font-mono font-bold text-base text-blue-700">
              {selectedDispatch.items.reduce((s, it) => s + parseFloat(it.quantity_dispatched.toString()), 0)} Packets
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
