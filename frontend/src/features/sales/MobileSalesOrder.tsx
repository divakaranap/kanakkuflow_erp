import { useState, useEffect } from 'react'
import {
  Wifi,
  WifiOff,
  CloudUpload,
  RefreshCw,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Check,
  Package,
} from 'lucide-react'
import {
  offlineStorage,
  type CachedCustomer,
  type CachedProduct,
  type QueuedOrder,
  type QueuedOrderItem,
} from '../../lib/offlineDb'
import { syncService } from '../../services/syncService'

export function MobileSalesOrder() {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine)
  const [customers, setCustomers] = useState<CachedCustomer[]>([])
  const [products, setProducts] = useState<CachedProduct[]>([])
  const [queuedOrders, setQueuedOrders] = useState<QueuedOrder[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [syncing, setSyncing] = useState<boolean>(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null)

  // Order Form State
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('')
  const [deliveryDate, setDeliveryDate] = useState<string>('')
  const [notes, setNotes] = useState<string>('')
  const [lineItems, setLineItems] = useState<
    { product_id: string; product_name: string; quantity: number; unit_price_paise: number }[]
  >([])

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      // Trigger auto-sync on reconnect
      handleSyncOrders()
    }
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    loadLocalData()

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const loadLocalData = async () => {
    try {
      const cachedCusts = await offlineStorage.getCachedCustomers()
      const cachedProds = await offlineStorage.getCachedProducts()
      const orders = await offlineStorage.getAllQueuedOrders()

      setCustomers(cachedCusts)
      setProducts(cachedProds)
      setQueuedOrders(orders)

      // If no local cache yet and online, auto-fetch
      if (cachedCusts.length === 0 && navigator.onLine) {
        await handleRefreshReferenceData()
      }
    } catch (err) {
      console.error('Error loading local offline data:', err)
    }
  }

  const handleRefreshReferenceData = async () => {
    if (!navigator.onLine) {
      setMessage({ text: 'Cannot refresh master data while offline', type: 'error' })
      return
    }
    try {
      setLoading(true)
      const res = await syncService.refreshOfflineReferenceData()
      const updatedCusts = await offlineStorage.getCachedCustomers()
      const updatedProds = await offlineStorage.getCachedProducts()
      setCustomers(updatedCusts)
      setProducts(updatedProds)
      setMessage({
        text: `Successfully cached ${res.customerCount} customers and ${res.productCount} products for offline use!`,
        type: 'success',
      })
    } catch (err: any) {
      console.error('Failed to refresh offline master data:', err)
      setMessage({ text: 'Failed to download master data from server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleSyncOrders = async () => {
    if (!navigator.onLine) {
      setMessage({ text: 'No internet connection. Orders will remain queued locally.', type: 'info' })
      return
    }
    try {
      setSyncing(true)
      const res = await syncService.syncPendingOrders()
      const updatedOrders = await offlineStorage.getAllQueuedOrders()
      setQueuedOrders(updatedOrders)

      if (res.syncedCount > 0) {
        setMessage({
          text: `Successfully synchronized ${res.syncedCount} order(s) with central server!`,
          type: 'success',
        })
      } else if (res.failedCount > 0) {
        setMessage({
          text: `${res.failedCount} order(s) failed validation. Check queue details below.`,
          type: 'error',
        })
      }
    } catch (err: any) {
      console.error('Sync failed:', err)
      setMessage({ text: 'Sync network error. Orders preserved in local database.', type: 'error' })
    } finally {
      setSyncing(false)
    }
  }

  const handleAddLineItem = () => {
    if (products.length === 0) return
    const defaultProduct = products[0]
    setLineItems([
      ...lineItems,
      {
        product_id: defaultProduct.id,
        product_name: defaultProduct.product_name,
        quantity: 50,
        unit_price_paise: defaultProduct.selling_price_paise,
      },
    ])
  }

  const handleRemoveLineItem = (index: number) => {
    setLineItems(lineItems.filter((_, idx) => idx !== index))
  }

  const handleProductChange = (index: number, productId: string) => {
    const prod = products.find((p) => p.id === productId)
    if (!prod) return
    const updated = [...lineItems]
    updated[index] = {
      ...updated[index],
      product_id: prod.id,
      product_name: prod.product_name,
      unit_price_paise: prod.selling_price_paise,
    }
    setLineItems(updated)
  }

  const handleQuantityChange = (index: number, qty: number) => {
    const updated = [...lineItems]
    updated[index].quantity = Math.max(1, qty)
    setLineItems(updated)
  }

  const calculateSubtotalPaise = () => {
    return lineItems.reduce((acc, item) => acc + item.quantity * item.unit_price_paise, 0)
  }

  const calculateEstimatedGrandTotalPaise = () => {
    const subtotal = calculateSubtotalPaise()
    const tax = Math.round(subtotal * 0.05) // standard 5% snack GST
    return subtotal + tax
  }

  const handleSaveOrder = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCustomerId) {
      setMessage({ text: 'Please select a customer', type: 'error' })
      return
    }
    if (lineItems.length === 0) {
      setMessage({ text: 'Please add at least one line item', type: 'error' })
      return
    }

    const selectedCust = customers.find((c) => c.id === selectedCustomerId)
    const clientUuid = crypto.randomUUID()
    const grandTotal = calculateEstimatedGrandTotalPaise()

    const queuedItems: QueuedOrderItem[] = lineItems.map((li) => ({
      product_id: li.product_id,
      product_name: li.product_name,
      ordered_quantity: li.quantity,
      unit_price_paise: li.unit_price_paise,
      line_total_paise: li.quantity * li.unit_price_paise,
    }))

    const orderData: Omit<QueuedOrder, 'created_at'> = {
      client_order_uuid: clientUuid,
      customer_id: selectedCustomerId,
      customer_name: selectedCust?.customer_name || 'Retailer',
      order_date: new Date().toISOString().split('T')[0],
      delivery_date: deliveryDate || undefined,
      notes: notes || undefined,
      items: queuedItems,
      total_amount_paise: grandTotal,
      sync_status: 'PENDING',
    }

    try {
      const syncedNow = await syncService.queueAndAttemptSync(orderData)
      const updatedOrders = await offlineStorage.getAllQueuedOrders()
      setQueuedOrders(updatedOrders)

      // Reset form
      setLineItems([])
      setNotes('')
      setDeliveryDate('')

      if (syncedNow) {
        setMessage({
          text: 'Order created and instantly synchronized with central ERP server!',
          type: 'success',
        })
      } else {
        setMessage({
          text: 'Order saved locally to offline storage. It will automatically synchronize when connection resumes.',
          type: 'info',
        })
      }
    } catch (err: any) {
      console.error('Failed to save offline order:', err)
      setMessage({ text: 'Failed to record order locally', type: 'error' })
    }
  }

  const formatCurrency = (paise: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100)
  }

  const pendingCount = queuedOrders.filter((o) => o.sync_status === 'PENDING').length

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto space-y-6">
      {/* Network Status Header Banner */}
      <div
        className={`p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm transition-colors ${
          isOnline
            ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
            : 'bg-amber-50 border-amber-200 text-amber-900'
        }`}
      >
        <div className="flex items-center gap-3">
          {isOnline ? (
            <div className="p-2 bg-emerald-100 rounded-lg text-emerald-700">
              <Wifi className="w-5 h-5 animate-pulse" />
            </div>
          ) : (
            <div className="p-2 bg-amber-100 rounded-lg text-amber-700">
              <WifiOff className="w-5 h-5" />
            </div>
          )}
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider">
              {isOnline ? 'Online — Connected to Factory Server' : 'Offline Mode — Local Storage Active'}
            </h2>
            <p className="text-xs opacity-90 mt-0.5">
              {isOnline
                ? 'Orders are synchronized in real-time with double-entry accounting.'
                : 'Zero data loss: orders are stored in IndexedDB and queued for sync.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-stretch sm:self-auto">
          {isOnline && (
            <button
              onClick={handleRefreshReferenceData}
              disabled={loading}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-emerald-300 bg-white text-emerald-800 hover:bg-emerald-50 transition shadow-xs disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Update Catalog
            </button>
          )}
          <button
            onClick={handleSyncOrders}
            disabled={syncing || !isOnline || pendingCount === 0}
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition shadow-xs disabled:opacity-40"
          >
            <CloudUpload className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            Sync Now ({pendingCount})
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-lg border text-sm flex items-center justify-between ${
            message.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : message.type === 'error'
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-blue-50 border-blue-200 text-blue-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' && <Check className="w-4 h-4 text-emerald-600" />}
            {message.type === 'error' && <AlertTriangle className="w-4 h-4 text-red-600" />}
            {message.type === 'info' && <Clock className="w-4 h-4 text-blue-600" />}
            <span>{message.text}</span>
          </div>
          <button
            onClick={() => setMessage(null)}
            className="text-xs font-bold opacity-60 hover:opacity-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Mobile Sales Order Entry Form */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
          <div>
            <h1 className="text-base font-bold text-gray-900">Mobile Sales Order Booking</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Optimized for salesman field visits. Cached master data enables instant booking.
            </p>
          </div>
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-md border border-gray-200">
            {customers.length} Customers | {products.length} Products Cached
          </span>
        </div>

        <form onSubmit={handleSaveOrder} className="p-5 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Customer / Retailer *
              </label>
              <select
                value={selectedCustomerId}
                onChange={(e) => setSelectedCustomerId(e.target.value)}
                required
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select Customer --</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.customer_name} ({c.customer_code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Expected Delivery Date
              </label>
              <input
                type="date"
                value={deliveryDate}
                onChange={(e) => setDeliveryDate(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Line Items Section */}
          <div className="space-y-3 pt-2 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700">Order Items</h3>
              <button
                type="button"
                onClick={handleAddLineItem}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md border border-blue-200 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Product
              </button>
            </div>

            {lineItems.length === 0 ? (
              <div className="text-center py-6 bg-gray-50 rounded-lg border border-dashed border-gray-300 text-xs text-gray-500">
                <Package className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                No products added yet. Click &quot;Add Product&quot; to book items.
              </div>
            ) : (
              <div className="space-y-2">
                {lineItems.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex-1 w-full">
                      <select
                        value={item.product_id}
                        onChange={(e) => handleProductChange(idx, e.target.value)}
                        className="w-full px-2.5 py-1.5 bg-white border border-gray-300 rounded text-xs text-gray-900 font-medium"
                      >
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.product_name} ({p.sku}) — {formatCurrency(p.selling_price_paise)}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-gray-500">Qty:</span>
                        <input
                          type="number"
                          min="1"
                          value={item.quantity}
                          onChange={(e) => handleQuantityChange(idx, parseInt(e.target.value) || 1)}
                          className="w-20 px-2 py-1 bg-white border border-gray-300 rounded text-xs font-bold text-center"
                        />
                      </div>

                      <div className="text-right min-w-[90px]">
                        <span className="text-xs font-bold text-gray-900">
                          {formatCurrency(item.quantity * item.unit_price_paise)}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRemoveLineItem(idx)}
                        className="text-red-500 hover:text-red-700 p-1"
                        title="Remove"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
              Order Notes / Delivery Instructions
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Urgent morning delivery before 10 AM"
              className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Order Summary & Submit Bar */}
          <div className="pt-4 border-t border-gray-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-0.5 text-xs text-gray-600">
              <div>Subtotal: {formatCurrency(calculateSubtotalPaise())}</div>
              <div>Est. GST (5%): {formatCurrency(Math.round(calculateSubtotalPaise() * 0.05))}</div>
              <div className="text-base font-bold text-gray-900">
                Grand Total: {formatCurrency(calculateEstimatedGrandTotalPaise())}
              </div>
            </div>

            <button
              type="submit"
              disabled={lineItems.length === 0 || !selectedCustomerId}
              className="w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition disabled:opacity-50"
            >
              {isOnline ? 'Book & Sync Order' : 'Save Order (Offline Queue)'}
            </button>
          </div>
        </form>
      </div>

      {/* Local Queue & Sync Status Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
          <div className="flex items-center gap-2">
            <CloudUpload className="w-4 h-4 text-gray-600" />
            <h3 className="text-sm font-bold text-gray-900">Local Device Queue &amp; Sync History</h3>
          </div>
          <span className="text-xs text-gray-500">IndexedDB Persisted</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-xs">
            <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold text-left">
              <tr>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4">Customer</th>
                <th className="py-2.5 px-4">Items</th>
                <th className="py-2.5 px-4 text-right">Amount</th>
                <th className="py-2.5 px-4">Server Order #</th>
                <th className="py-2.5 px-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {queuedOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-gray-400">
                    No orders in device queue.
                  </td>
                </tr>
              ) : (
                queuedOrders.map((order) => (
                  <tr key={order.client_order_uuid} className="hover:bg-gray-50/60">
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      {order.sync_status === 'SYNCED' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          SYNCED
                        </span>
                      ) : order.sync_status === 'FAILED' ? (
                        <span
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-800 border border-red-200"
                          title={order.error_message}
                        >
                          <AlertTriangle className="w-3 h-3 text-red-600" />
                          FAILED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                          <Clock className="w-3 h-3 text-amber-600" />
                          PENDING
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-semibold text-gray-800">{order.customer_name}</td>
                    <td className="py-2.5 px-4 text-gray-600">
                      {order.items.reduce((sum, it) => sum + it.ordered_quantity, 0)} pkts ({order.items.length} items)
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-gray-900">
                      {formatCurrency(order.total_amount_paise)}
                    </td>
                    <td className="py-2.5 px-4 font-mono font-medium text-blue-600">
                      {order.server_order_number || '—'}
                    </td>
                    <td className="py-2.5 px-4 text-gray-500">
                      {order.created_at.slice(0, 16).replace('T', ' ')}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
