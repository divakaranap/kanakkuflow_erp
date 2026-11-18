import React, { useState, useEffect } from 'react'
import {
  ShoppingCart,
  Plus,
  RefreshCw,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Download,
  Eye,
  Check,
  Ban,
  Smartphone,
} from 'lucide-react'
import { salesService } from '../../services/salesService'
import { masterService } from '../../services/masterService'
import { formatINR } from '../../lib/utils'
import { MobileSalesOrder } from './MobileSalesOrder'
import type {
  SalesOrder,
  SalesInvoice,
  ProductStockCheckResponse,
} from '../../types/sales'
import type { Customer, Product } from '../../types/masters'

export function SalesOverview() {
  const [activeTab, setActiveTab] = useState<'orders' | 'new-order' | 'invoices' | 'invoice-preview' | 'mobile-order'>('orders')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Data
  const [orders, setOrders] = useState<SalesOrder[]>([])
  const [invoices, setInvoices] = useState<SalesInvoice[]>([])
  const [selectedOrder, setSelectedOrder] = useState<SalesOrder | null>(null)
  const [selectedInvoice, setSelectedInvoice] = useState<SalesInvoice | null>(null)

  // Lookups
  const [customers, setCustomers] = useState<Customer[]>([])
  const [products, setProducts] = useState<Product[]>([])

  // Order Entry Form
  const [selectedCustomerId, setSelectedCustomerId] = useState('')
  const [selectedProductId, setSelectedProductId] = useState('')
  const [orderQuantity, setOrderQuantity] = useState('150')
  const [unitPriceRs, setUnitPriceRs] = useState('50')
  const [discountRs, setDiscountRs] = useState('0')
  const [deliveryDate, setDeliveryDate] = useState('')
  const [orderNotes, setOrderNotes] = useState('Benchmark order')
  const [stockCheck, setStockCheck] = useState<ProductStockCheckResponse | null>(null)

  // Cancellation Modal
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false)
  const [cancelTargetInvoiceId, setCancelTargetInvoiceId] = useState('')
  const [cancelReason, setCancelReason] = useState('')

  useEffect(() => {
    loadLookups()
    loadOrders()
    loadInvoices()
  }, [])

  useEffect(() => {
    if (activeTab === 'orders') loadOrders()
    if (activeTab === 'invoices') loadInvoices()
  }, [activeTab])

  // Trigger live stock check when product or quantity changes
  useEffect(() => {
    if (selectedProductId && parseFloat(orderQuantity) > 0) {
      checkAvailability(selectedProductId, parseFloat(orderQuantity))
    }
  }, [selectedProductId, orderQuantity])

  const loadLookups = async () => {
    try {
      const [custs, prds] = await Promise.all([
        masterService.getCustomers(),
        masterService.getProducts(),
      ])
      setCustomers(custs)
      setProducts(prds)
      if (custs.length > 0) setSelectedCustomerId(custs[0].id)
      if (prds.length > 0) {
        setSelectedProductId(prds[0].id)
        setUnitPriceRs((prds[0].selling_price_paise / 100).toString())
      }
    } catch {
      // ignore
    }
  }

  const loadOrders = async () => {
    setLoading(true)
    try {
      const res = await salesService.getSalesOrders()
      setOrders(res.items)
      if (res.items.length > 0 && !selectedOrder) {
        setSelectedOrder(res.items[0])
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load sales orders')
    } finally {
      setLoading(false)
    }
  }

  const loadInvoices = async () => {
    setLoading(true)
    try {
      const res = await salesService.getSalesInvoices()
      setInvoices(res.items)
      if (res.items.length > 0 && !selectedInvoice) {
        setSelectedInvoice(res.items[0])
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load sales invoices')
    } finally {
      setLoading(false)
    }
  }

  const checkAvailability = async (prodId: string, qty: number) => {
    try {
      const chk = await salesService.checkStock(prodId, qty)
      setStockCheck(chk)
    } catch {
      // ignore
    }
  }

  const handleCustomerChange = (custId: string) => {
    setSelectedCustomerId(custId)
    // Could update prices based on price list
    const cust = customers.find((c) => c.id === custId)
    if (cust && cust.customer_type === 'DISTRIBUTOR') {
      setUnitPriceRs('42') // Default distributor rate
    } else {
      setUnitPriceRs('50') // Retailer rate
    }
  }

  const handleCreateOrder = async (e: React.FormEvent, autoSubmit = false) => {
    e.preventDefault()
    if (!selectedCustomerId || !selectedProductId) {
      setErrorMsg('Please select a customer and product')
      return
    }

    try {
      const order = await salesService.createSalesOrder({
        customer_id: selectedCustomerId,
        delivery_date: deliveryDate || undefined,
        notes: orderNotes,
        items: [
          {
            product_id: selectedProductId,
            ordered_quantity: parseFloat(orderQuantity) || 1,
            unit_price_paise: Math.round(parseFloat(unitPriceRs) * 100),
            discount_paise: Math.round(parseFloat(discountRs) * 100),
          },
        ],
      })

      if (autoSubmit) {
        await salesService.submitSalesOrder(order.id)
        setSuccessMsg(`Sales Order ${order.order_number} created and submitted for approval!`)
      } else {
        setSuccessMsg(`Sales Order ${order.order_number} saved as DRAFT.`)
      }

      setActiveTab('orders')
      loadOrders()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create sales order')
    }
  }

  const handleSubmitOrder = async (orderId: string) => {
    try {
      await salesService.submitSalesOrder(orderId)
      setSuccessMsg('Sales Order submitted successfully!')
      loadOrders()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to submit order')
    }
  }

  const handleApproveOrder = async (orderId: string) => {
    try {
      await salesService.approveSalesOrder(orderId)
      setSuccessMsg('Sales Order approved by Admin!')
      loadOrders()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to approve order')
    }
  }

  const handleGenerateInvoice = async (orderId: string) => {
    try {
      const inv = await salesService.createSalesInvoice({ sales_order_id: orderId })
      setSuccessMsg(`GST Invoice ${inv.invoice_number} generated and posted!`)
      setSelectedInvoice(inv)
      setActiveTab('invoices')
      loadInvoices()
      loadOrders()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to generate invoice')
    }
  }

  const handleDownloadPdf = async (inv: SalesInvoice) => {
    try {
      await salesService.downloadInvoicePdf(inv.id, inv.invoice_number)
      setSuccessMsg(`Invoice ${inv.invoice_number} PDF downloaded!`)
    } catch {
      setErrorMsg('Failed to download PDF invoice')
    }
  }

  const handleCancelInvoice = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!cancelReason.trim()) {
      setErrorMsg('Please specify a cancellation reason')
      return
    }
    try {
      await salesService.cancelSalesInvoice(cancelTargetInvoiceId, cancelReason)
      setSuccessMsg('Invoice cancelled successfully with audit note.')
      setIsCancelModalOpen(false)
      setCancelReason('')
      loadInvoices()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to cancel invoice')
    }
  }

  // Live order calculations
  const selectedCust = customers.find((c) => c.id === selectedCustomerId)
  const isIntraState = selectedCust?.state_code === '33' || !selectedCust?.state_code || selectedCust.state_code === ''
  const qtyNum = parseFloat(orderQuantity) || 0
  const rateNum = parseFloat(unitPriceRs) || 0
  const discNum = parseFloat(discountRs) || 0
  const liveTaxable = Math.max(0, qtyNum * rateNum - discNum)
  const liveCgst = isIntraState ? (liveTaxable * 0.025) : 0
  const liveSgst = isIntraState ? (liveTaxable * 0.025) : 0
  const liveIgst = !isIntraState ? (liveTaxable * 0.05) : 0
  const liveGrandTotal = liveTaxable + liveCgst + liveSgst + liveIgst

  // KPI Calculations
  const totalSalesValPaise = invoices.reduce((acc, inv) => (inv.status === 'POSTED' ? acc + inv.grand_total_paise : acc), 0)
  const totalGstValPaise = invoices.reduce((acc, inv) => (inv.status === 'POSTED' ? acc + inv.total_tax_paise : acc), 0)
  const pendingApprovalsCount = orders.filter((o) => o.status === 'SUBMITTED').length
  const readyToInvoiceCount = orders.filter((o) => o.status === 'APPROVED').length

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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Sales Invoiced</span>
          <div className="text-xl font-bold text-slate-900 mt-1">{formatINR(totalSalesValPaise)}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">{invoices.filter((i) => i.status === 'POSTED').length} Posted Invoices</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider">GST Collected</span>
          <div className="text-xl font-bold text-blue-900 mt-1">{formatINR(totalGstValPaise)}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">CGST + SGST + IGST</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Pending Approval</span>
          <div className="text-xl font-bold text-amber-900 mt-1">{pendingApprovalsCount} Orders</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Awaiting Admin check</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Ready for Invoicing</span>
          <div className="text-xl font-bold text-emerald-900 mt-1">{readyToInvoiceCount} Orders</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Approved by Admin</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-purple-600 uppercase tracking-wider">Total Orders</span>
          <div className="text-xl font-bold text-purple-900 mt-1">{orders.length}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">All statuses</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab('orders')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'orders' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <ShoppingCart className="h-4 w-4" />
            <span>Sales Orders</span>
          </button>

          <button
            onClick={() => setActiveTab('new-order')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'new-order' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Plus className="h-4 w-4" />
            <span>New Sales Order</span>
          </button>

          <button
            onClick={() => setActiveTab('invoices')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'invoices' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <FileText className="h-4 w-4" />
            <span>GST Tax Invoices</span>
          </button>

          {selectedInvoice && (
            <button
              onClick={() => setActiveTab('invoice-preview')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                activeTab === 'invoice-preview' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Eye className="h-4 w-4" />
              <span>Invoice Preview</span>
            </button>
          )}

          <button
            onClick={() => setActiveTab('mobile-order')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              activeTab === 'mobile-order' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Smartphone className="h-4 w-4" />
            <span>Mobile Offline Booking</span>
          </button>
        </div>

        <button
          onClick={() => {
            loadOrders()
            loadInvoices()
          }}
          disabled={loading}
          className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-600 transition self-end sm:self-auto flex items-center gap-1"
          title="Refresh"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          {loading && <span className="text-xs text-blue-600 font-medium">Syncing...</span>}
        </button>
      </div>

      {/* TAB 1: SALES ORDERS TABLE */}
      {activeTab === 'orders' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">Customer Sales Orders</h3>
            <span className="text-xs text-slate-500 font-medium">
              Salesman Entry &rarr; Admin Approval &rarr; GST Invoice
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Order #</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Place of Supply</th>
                  <th className="py-3 px-4">Order Date</th>
                  <th className="py-3 px-4 text-right">Taxable</th>
                  <th className="py-3 px-4 text-right">Total Tax</th>
                  <th className="py-3 px-4 text-right">Grand Total</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {orders.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400">
                      No sales orders found. Click "New Sales Order" to record an order.
                    </td>
                  </tr>
                ) : (
                  orders.map((o) => (
                    <tr
                      key={o.id}
                      onClick={() => setSelectedOrder(o)}
                      className={`hover:bg-slate-50 transition cursor-pointer ${
                        selectedOrder?.id === o.id ? 'bg-blue-50/50' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-blue-600">{o.order_number}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">
                        {o.customer_name || 'Customer'}
                        {o.customer_gstin && (
                          <span className="block text-[10px] font-mono text-slate-500">GSTIN: {o.customer_gstin}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono">State {o.place_of_supply_state_code}</td>
                      <td className="py-3 px-4 text-slate-600">{o.order_date}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-700">{formatINR(o.taxable_amount_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-700">{formatINR(o.total_tax_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">{formatINR(o.grand_total_paise)}</td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            o.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : o.status === 'SUBMITTED'
                              ? 'bg-blue-100 text-blue-800 border-blue-200'
                              : o.status === 'DRAFT'
                              ? 'bg-amber-100 text-amber-800 border-amber-200'
                              : o.status === 'FULFILLED'
                              ? 'bg-purple-100 text-purple-800 border-purple-200'
                              : 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}
                        >
                          {o.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center space-x-1.5" onClick={(e) => e.stopPropagation()}>
                          {o.status === 'DRAFT' && (
                            <button
                              onClick={() => handleSubmitOrder(o.id)}
                              className="px-2 py-1 bg-blue-600 text-white rounded text-[11px] font-semibold hover:bg-blue-700 transition"
                            >
                              Submit
                            </button>
                          )}
                          {o.status === 'SUBMITTED' && (
                            <button
                              onClick={() => handleApproveOrder(o.id)}
                              className="px-2 py-1 bg-emerald-600 text-white rounded text-[11px] font-semibold hover:bg-emerald-700 transition flex items-center space-x-1"
                            >
                              <Check className="h-3 w-3" />
                              <span>Approve</span>
                            </button>
                          )}
                          {o.status === 'APPROVED' && (
                            <button
                              onClick={() => handleGenerateInvoice(o.id)}
                              className="px-2.5 py-1 bg-purple-600 text-white rounded text-[11px] font-semibold hover:bg-purple-700 transition flex items-center space-x-1"
                            >
                              <FileText className="h-3 w-3" />
                              <span>Generate Invoice</span>
                            </button>
                          )}
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

      {/* TAB 2: GUIDED NEW SALES ORDER FORM */}
      {activeTab === 'new-order' && (
        <form onSubmit={(e) => handleCreateOrder(e, true)} className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-200 pb-4">
              <h3 className="text-base font-bold text-slate-900">Guided Sales Order Entry</h3>
              <p className="text-xs text-slate-500 mt-1">
                Select customer, product and quantities. System checks available inventory and calculates GST in real-time.
              </p>
            </div>

            {/* Customer & Destination Selection */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Customer / Buyer</label>
                <select
                  value={selectedCustomerId}
                  onChange={(e) => handleCustomerChange(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                >
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.customer_name} ({c.customer_type}) - {c.state} [{c.state_code}]
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Customer GSTIN</label>
                <input
                  type="text"
                  value={selectedCust?.gstin || 'Unregistered (URP)'}
                  readOnly
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-slate-50 font-mono text-slate-700"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Place of Supply (POS)</label>
                <input
                  type="text"
                  value={`${selectedCust?.state || 'Tamil Nadu'} (State Code: ${selectedCust?.state_code || '33'})`}
                  readOnly
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-slate-50 font-medium text-slate-700"
                />
              </div>
            </div>

            {/* Product & Quantity Selection */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Product Item</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.product_name} ({p.sku}) - MRP: ₹{p.selling_price_paise / 100}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Order Quantity (Packets)</label>
                <input
                  type="number"
                  value={orderQuantity}
                  onChange={(e) => setOrderQuantity(e.target.value)}
                  min="1"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 font-mono font-bold"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Unit Selling Price (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={unitPriceRs}
                  onChange={(e) => setUnitPriceRs(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Discount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={discountRs}
                  onChange={(e) => setDiscountRs(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Expected Delivery Date</label>
                <input
                  type="date"
                  value={deliveryDate}
                  onChange={(e) => setDeliveryDate(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Order Notes / Delivery Instructions</label>
                <input
                  type="text"
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="e.g. Special festive dispatch instructions"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300"
                />
              </div>
            </div>

            {/* Inventory Stock Availability Check Banner */}
            {stockCheck && (
              <div
                className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
                  stockCheck.is_sufficient
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                    : 'bg-amber-50 border-amber-200 text-amber-900'
                }`}
              >
                <div className="flex items-center space-x-2">
                  {stockCheck.is_sufficient ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                  )}
                  <span>
                    Finished Goods Stock: <b>{parseFloat(stockCheck.available_qty.toString()).toFixed(0)} pkts available</b>.{' '}
                    {stockCheck.is_sufficient
                      ? 'Stock is sufficient to fulfill this order.'
                      : `Warning: Order quantity exceeds available stock by ${parseFloat(
                          stockCheck.shortage_qty.toString()
                        ).toFixed(0)} packets.`}
                  </span>
                </div>
                <span className="font-semibold text-[11px] underline">
                  {stockCheck.is_sufficient ? 'Fulfillment Ready' : 'Production Required'}
                </span>
              </div>
            )}

            {/* Live GST Calculation Summary Box */}
            <div className="p-4 bg-slate-900 text-white rounded-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
                  Real-Time GST Calculation
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-950 text-blue-300 font-mono border border-blue-800">
                  {isIntraState ? 'INTRA-STATE (CGST 2.5% + SGST 2.5%)' : 'INTER-STATE (IGST 5.0%)'}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block text-[11px]">Taxable Amount</span>
                  <span className="text-base font-bold font-mono">₹{liveTaxable.toFixed(2)}</span>
                </div>
                {isIntraState ? (
                  <>
                    <div>
                      <span className="text-slate-400 block text-[11px]">CGST (2.5%)</span>
                      <span className="text-base font-bold font-mono text-blue-400">₹{liveCgst.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[11px]">SGST (2.5%)</span>
                      <span className="text-base font-bold font-mono text-blue-400">₹{liveSgst.toFixed(2)}</span>
                    </div>
                  </>
                ) : (
                  <div>
                    <span className="text-slate-400 block text-[11px]">IGST (5.0%)</span>
                    <span className="text-base font-bold font-mono text-purple-400">₹{liveIgst.toFixed(2)}</span>
                  </div>
                )}
                <div>
                  <span className="text-slate-400 block text-[11px]">Total Tax</span>
                  <span className="text-base font-bold font-mono text-amber-400">
                    ₹{(liveCgst + liveSgst + liveIgst).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-emerald-400 block text-[11px] font-bold">Grand Total</span>
                  <span className="text-lg font-bold font-mono text-emerald-400">₹{liveGrandTotal.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={(e) => handleCreateOrder(e, false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition"
              >
                Save as Draft
              </button>
              <button
                type="submit"
                className="px-5 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition flex items-center space-x-1.5 shadow-sm"
              >
                <span>Submit Order for Approval</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </form>
      )}

      {/* TAB 3: GST TAX INVOICES TABLE */}
      {activeTab === 'invoices' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">Immutable GST Tax Invoices</h3>
            <span className="text-xs text-slate-500 font-medium">Traceable to Sales Order & Customer Ledger</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Order Ref</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Taxable</th>
                  <th className="py-3 px-4 text-right">CGST</th>
                  <th className="py-3 px-4 text-right">SGST</th>
                  <th className="py-3 px-4 text-right">IGST</th>
                  <th className="py-3 px-4 text-right">Grand Total</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="py-8 text-center text-slate-400">
                      No invoices found. Generate an invoice from an Approved Sales Order.
                    </td>
                  </tr>
                ) : (
                  invoices.map((inv) => (
                    <tr
                      key={inv.id}
                      onClick={() => {
                        setSelectedInvoice(inv)
                        setActiveTab('invoice-preview')
                      }}
                      className="hover:bg-slate-50 transition cursor-pointer"
                    >
                      <td className="py-3 px-4 font-mono font-bold text-purple-600">{inv.invoice_number}</td>
                      <td className="py-3 px-4 font-mono text-slate-600">{inv.order_number || 'N/A'}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">
                        {inv.customer_name}
                        {inv.buyer_gstin && (
                          <span className="block text-[10px] font-mono text-slate-500">GST: {inv.buyer_gstin}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-600">{inv.invoice_date}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatINR(inv.taxable_amount_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-600">{formatINR(inv.cgst_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-600">{formatINR(inv.sgst_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-600">{formatINR(inv.igst_paise)}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        {formatINR(inv.grand_total_paise)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            inv.status === 'POSTED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : 'bg-red-100 text-red-800 border-red-200'
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center space-x-1.5">
                          <button
                            onClick={() => handleDownloadPdf(inv)}
                            className="p-1.5 rounded bg-blue-50 text-blue-600 hover:bg-blue-100 transition"
                            title="Download PDF"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                          {inv.status === 'POSTED' && (
                            <button
                              onClick={() => {
                                setCancelTargetInvoiceId(inv.id)
                                setIsCancelModalOpen(true)
                              }}
                              className="p-1.5 rounded bg-red-50 text-red-600 hover:bg-red-100 transition"
                              title="Cancel Invoice"
                            >
                              <Ban className="h-3.5 w-3.5" />
                            </button>
                          )}
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

      {/* TAB 4: TAX INVOICE PREVIEW */}
      {activeTab === 'invoice-preview' && selectedInvoice && (
        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm max-w-4xl mx-auto space-y-6">
          <div className="flex items-center justify-between border-b pb-4">
            <div>
              <span className="text-xs uppercase font-bold text-blue-600 tracking-wider">GST Tax Invoice</span>
              <h2 className="text-xl font-bold text-slate-900 mt-0.5">{selectedInvoice.invoice_number}</h2>
              <span className="text-xs text-slate-500 font-medium">Original for Recipient</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleDownloadPdf(selectedInvoice)}
                className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 flex items-center space-x-1"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download PDF</span>
              </button>
            </div>
          </div>

          {/* Parties Header */}
          <div className="grid grid-cols-2 gap-6 p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="font-bold text-slate-900 block mb-1">FACTORYFLOW FOODS PRIVATE LIMITED</span>
              <p className="text-slate-600">Plot 12, Food Processing SEZ, Thuvakudi, Tiruchirappalli, Tamil Nadu</p>
              <p className="font-mono mt-1 text-slate-700">GSTIN: {selectedInvoice.seller_gstin}</p>
              <p className="text-slate-500 mt-0.5">State Code: 33 (Tamil Nadu)</p>
            </div>
            <div>
              <span className="font-bold text-slate-900 block mb-1">BILLED TO (BUYER):</span>
              <p className="font-semibold text-slate-800">{selectedInvoice.customer_name}</p>
              <p className="font-mono mt-1 text-slate-700">GSTIN: {selectedInvoice.buyer_gstin || 'Unregistered (URP)'}</p>
              <p className="text-slate-500 mt-0.5">Place of Supply: State Code {selectedInvoice.place_of_supply_state_code}</p>
            </div>
          </div>

          {/* Line Items Table */}
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-100 text-slate-700 font-semibold font-sans border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Item Description</th>
                  <th className="py-2.5 px-3">HSN</th>
                  <th className="py-2.5 px-3 text-right">Quantity</th>
                  <th className="py-2.5 px-3 text-right">Rate</th>
                  <th className="py-2.5 px-3 text-right">Taxable</th>
                  <th className="py-2.5 px-3 text-right">GST Breakup</th>
                  <th className="py-2.5 px-3 text-right">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {selectedInvoice.items.map((it) => (
                  <tr key={it.id}>
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-800">{it.product_name}</td>
                    <td className="py-2.5 px-3 text-slate-600">{it.hsn_code}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                      {parseFloat(it.quantity.toString()).toFixed(0)} {it.unit}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-600">{formatINR(it.unit_price_paise)}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900">{formatINR(it.taxable_value_paise)}</td>
                    <td className="py-2.5 px-3 text-right text-slate-600 text-[11px]">
                      {it.cgst_paise > 0 && `CGST: ${formatINR(it.cgst_paise)} `}
                      {it.sgst_paise > 0 && `SGST: ${formatINR(it.sgst_paise)} `}
                      {it.igst_paise > 0 && `IGST: ${formatINR(it.igst_paise)}`}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900">{formatINR(it.line_total_paise)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Grand Totals */}
          <div className="flex justify-end">
            <div className="w-72 bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
              <div className="flex justify-between text-slate-600">
                <span>Taxable Amount:</span>
                <span className="font-mono font-bold">{formatINR(selectedInvoice.taxable_amount_paise)}</span>
              </div>
              {selectedInvoice.cgst_paise > 0 && (
                <div className="flex justify-between text-slate-600">
                  <span>CGST (2.5%):</span>
                  <span className="font-mono">{formatINR(selectedInvoice.cgst_paise)}</span>
                </div>
              )}
              {selectedInvoice.sgst_paise > 0 && (
                <div className="flex justify-between text-slate-600">
                  <span>SGST (2.5%):</span>
                  <span className="font-mono">{formatINR(selectedInvoice.sgst_paise)}</span>
                </div>
              )}
              {selectedInvoice.igst_paise > 0 && (
                <div className="flex justify-between text-slate-600">
                  <span>IGST (5.0%):</span>
                  <span className="font-mono">{formatINR(selectedInvoice.igst_paise)}</span>
                </div>
              )}
              <div className="flex justify-between border-t border-slate-200 pt-2 text-sm font-bold text-slate-900">
                <span>Grand Total:</span>
                <span className="font-mono text-blue-600">{formatINR(selectedInvoice.grand_total_paise)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: MOBILE OFFLINE BOOKING */}
      {activeTab === 'mobile-order' && <MobileSalesOrder />}

      {/* Cancellation Modal */}
      {isCancelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Cancel Posted GST Invoice</h3>
            <p className="text-xs text-slate-500">
              In accordance with GST compliance, cancelling an invoice requires an audit justification reason.
            </p>
            <form onSubmit={handleCancelInvoice} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Cancellation</label>
                <textarea
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Order cancelled by buyer prior to dispatch"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 h-20"
                  required
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCancelModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg"
                >
                  Confirm Cancellation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
