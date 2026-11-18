import React, { useState, useEffect } from 'react'
import {
  CreditCard,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Download,
  Eye,
  Building2,
  Receipt,
  Check,
} from 'lucide-react'
import { paymentService } from '../../services/paymentService'
import { masterService } from '../../services/masterService'
import type {
  CustomerPayment,
  PaymentMode,
  CustomerLedgerStatement,
  ReceivablesAgeingSummary,
  UnpaidInvoiceSummary,
} from '../../types/payment'
import type { Customer } from '../../types/masters'

export function PaymentOverview() {
  const [activeTab, setActiveTab] = useState<'payments' | 'new-payment' | 'ledger' | 'ageing'>('payments')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Data
  const [payments, setPayments] = useState<CustomerPayment[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [ageingReport, setAgeingReport] = useState<ReceivablesAgeingSummary | null>(null)
  const [selectedLedgerCustomer, setSelectedLedgerCustomer] = useState('')
  const [ledgerStatement, setLedgerStatement] = useState<CustomerLedgerStatement | null>(null)

  // Guided Payment Form State
  const [selectedCustomerId, setSelectedCustomerId] = useState('')
  const [paymentAmountRs, setPaymentAmountRs] = useState('4000')
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('UPI')
  const [referenceNumber, setReferenceNumber] = useState('UPI-IND-8829104')
  const [bankName, setBankName] = useState('State Bank of India')
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split('T')[0])
  const [paymentNotes, setPaymentNotes] = useState('Payment on account / invoice settlement')
  const [unpaidInvoices, setUnpaidInvoices] = useState<UnpaidInvoiceSummary[]>([])
  const [allocations, setAllocations] = useState<Record<string, string>>({})

  // Detail Modal
  const [viewPayment, setViewPayment] = useState<CustomerPayment | null>(null)

  useEffect(() => {
    loadBaseData()
  }, [])

  useEffect(() => {
    if (selectedCustomerId) {
      loadUnpaidInvoices(selectedCustomerId)
    } else {
      setUnpaidInvoices([])
      setAllocations({})
    }
  }, [selectedCustomerId])

  useEffect(() => {
    if (selectedLedgerCustomer) {
      loadCustomerLedger(selectedLedgerCustomer)
    }
  }, [selectedLedgerCustomer])

  const loadBaseData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [allPayments, custList, ageing] = await Promise.all([
        paymentService.getPayments(),
        masterService.getCustomers(),
        paymentService.getReceivablesAgeing(),
      ])
      setPayments(allPayments)
      setCustomers(custList)
      setAgeingReport(ageing)
      if (custList.length > 0 && !selectedLedgerCustomer) {
        setSelectedLedgerCustomer(custList[0].id)
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load payments data')
    } finally {
      setLoading(false)
    }
  }

  const loadUnpaidInvoices = async (custId: string) => {
    try {
      const invoices = await paymentService.getUnpaidInvoices(custId)
      setUnpaidInvoices(invoices)
      // Auto pre-populate allocation if there's only 1 invoice
      if (invoices.length > 0) {
        const first = invoices[0]
        const remainingRs = (first.remaining_unpaid_paise / 100).toString()
        const initialAlloc = Math.min(parseFloat(paymentAmountRs || '0'), parseFloat(remainingRs)).toString()
        setAllocations({ [first.id]: initialAlloc })
      }
    } catch (err: any) {
      console.error('Failed to load unpaid invoices:', err)
    }
  }

  const loadCustomerLedger = async (custId: string) => {
    setLoading(true)
    try {
      const stmt = await paymentService.getCustomerLedger(custId)
      setLedgerStatement(stmt)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load ledger statement')
    } finally {
      setLoading(false)
    }
  }

  const handleAutoAllocateFIFO = () => {
    const totalRs = parseFloat(paymentAmountRs) || 0
    let remainingToDistribute = totalRs
    const newAlloc: Record<string, string> = {}

    for (const inv of unpaidInvoices) {
      if (remainingToDistribute <= 0) break
      const invUnpaidRs = inv.remaining_unpaid_paise / 100
      const allocRs = Math.min(remainingToDistribute, invUnpaidRs)
      newAlloc[inv.id] = allocRs.toFixed(2)
      remainingToDistribute -= allocRs
    }
    setAllocations(newAlloc)
  }

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')

    if (!selectedCustomerId) {
      setErrorMsg('Please select a customer')
      return
    }

    const totalAmountPaise = Math.round((parseFloat(paymentAmountRs) || 0) * 100)
    if (totalAmountPaise <= 0) {
      setErrorMsg('Payment amount must be greater than zero')
      return
    }

    // Build allocations
    const allocList = Object.entries(allocations)
      .map(([invId, amtStr]) => ({
        invoice_id: invId,
        allocated_amount_paise: Math.round((parseFloat(amtStr) || 0) * 100),
      }))
      .filter((a) => a.allocated_amount_paise > 0)

    const sumAllocPaise = allocList.reduce((sum, a) => sum + a.allocated_amount_paise, 0)
    if (sumAllocPaise > totalAmountPaise) {
      setErrorMsg(
        `Total allocated (₹${(sumAllocPaise / 100).toFixed(2)}) exceeds payment amount (₹${(
          totalAmountPaise / 100
        ).toFixed(2)})`
      )
      return
    }

    setLoading(true)
    try {
      const newPay = await paymentService.recordPayment({
        customer_id: selectedCustomerId,
        payment_date: paymentDate,
        amount_paise: totalAmountPaise,
        payment_mode: paymentMode,
        reference_number: referenceNumber,
        bank_name: bankName,
        notes: paymentNotes,
        allocations: allocList,
      })

      setSuccessMsg(`Payment receipt ${newPay.payment_number} recorded successfully!`)
      await loadBaseData()
      if (selectedCustomerId === selectedLedgerCustomer) {
        await loadCustomerLedger(selectedCustomerId)
      }
      setActiveTab('payments')
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to record customer payment')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadReceipt = async (paymentId: string, receiptNum: string) => {
    try {
      await paymentService.downloadReceiptPdf(paymentId, receiptNum)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to download receipt PDF')
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <Receipt className="h-5 w-5" />
            </span>
            <h2 className="text-xl font-bold text-slate-900">Payments &amp; Receivables Ledger</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Phase 7: Traceable customer receipts, multi-invoice allocations, running ledger statements &amp; ageing analysis.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              loadBaseData()
              if (selectedLedgerCustomer) loadCustomerLedger(selectedLedgerCustomer)
            }}
            disabled={loading}
            className="px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 border border-slate-200 rounded-lg bg-white flex items-center space-x-1 hover:bg-slate-50 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setActiveTab('new-payment')}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg flex items-center space-x-1.5 transition shadow-sm"
          >
            <Plus className="h-4 w-4" />
            <span>Record Payment</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center space-x-2">
            <XCircle className="h-4 w-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-red-500 hover:text-red-700 font-bold">
            &times;
          </button>
        </div>
      )}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-700">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-500 hover:text-emerald-700 font-bold">
            &times;
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('payments')}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'payments'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Payment Receipts ({payments.length})
        </button>
        <button
          onClick={() => setActiveTab('new-payment')}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'new-payment'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Record Payment
        </button>
        <button
          onClick={() => setActiveTab('ledger')}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'ledger'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Customer Ledger &amp; Statement
        </button>
        <button
          onClick={() => setActiveTab('ageing')}
          className={`py-2 px-4 text-xs font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'ageing'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Receivables Ageing Analysis
        </button>
      </div>

      {/* TAB 1: ALL PAYMENTS */}
      {activeTab === 'payments' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Recorded Customer Payments</h3>
              <p className="text-xs text-slate-500">Immutable receipts with atomic invoice settlements.</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-slate-700">
              Total Receipts: {payments.length}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Receipt Number</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Mode / Ref</th>
                  <th className="py-3 px-4 text-right">Amount (₹)</th>
                  <th className="py-3 px-4 text-center">Allocated Invoices</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">
                      No customer payments recorded yet. Click &quot;Record Payment&quot; to log incoming funds.
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => {
                    const totalAlloc = p.allocations.reduce((s, a) => s + a.allocated_amount_paise, 0)
                    return (
                      <tr key={p.id} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-4 font-mono font-bold text-emerald-600">{p.payment_number}</td>
                        <td className="py-3 px-4 text-slate-600">{p.payment_date}</td>
                        <td className="py-3 px-4 font-medium text-slate-900">{p.customer_name || 'Customer'}</td>
                        <td className="py-3 px-4 text-slate-600">
                          <span className="font-semibold">{p.payment_mode}</span>
                          {p.reference_number && <span className="font-mono text-slate-500 ml-1">({p.reference_number})</span>}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                          ₹{(p.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {p.allocations.length > 0 ? (
                            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                              {p.allocations.length} settled (₹{(totalAlloc / 100).toFixed(2)})
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">On Account</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              p.status === 'CLEARED'
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                                : p.status === 'RECORDED'
                                ? 'bg-amber-100 text-amber-800 border-amber-200'
                                : 'bg-red-100 text-red-800 border-red-200'
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex items-center justify-center space-x-1.5">
                            <button
                              onClick={() => setViewPayment(p)}
                              className="p-1.5 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
                              title="View Breakdown"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => handleDownloadReceipt(p.id, p.payment_number)}
                              className="p-1.5 rounded bg-emerald-50 text-emerald-600 hover:bg-emerald-100 transition"
                              title="Download Receipt PDF"
                            >
                              <Download className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: RECORD NEW PAYMENT */}
      {activeTab === 'new-payment' && (
        <form onSubmit={handleRecordPayment} className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-200 pb-4">
              <h3 className="text-base font-bold text-slate-900">Record Customer Receipt &amp; Allocate</h3>
              <p className="text-xs text-slate-500 mt-1">
                Post received payment to the customer ledger and allocate funds against outstanding GST sales invoices.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Customer / Debtor</label>
                <select
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
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
                <label className="block text-xs font-semibold text-slate-700 mb-1">Receipt Date</label>
                <input
                  type="date"
                  value={paymentDate}
                  onChange={(e) => setPaymentDate(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Total Payment Received (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  min="1"
                  value={paymentAmountRs}
                  onChange={(e) => setPaymentAmountRs(e.target.value)}
                  placeholder="e.g. 4000.00"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white font-mono font-bold text-emerald-700"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Payment Mode</label>
                <select
                  value={paymentMode}
                  onChange={(e) => setPaymentMode(e.target.value as PaymentMode)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white font-semibold"
                >
                  <option value="UPI">UPI (Google Pay / PhonePe / Paytm)</option>
                  <option value="NEFT">NEFT (Electronic Bank Transfer)</option>
                  <option value="RTGS">RTGS</option>
                  <option value="CHEQUE">Cheque / Demand Draft</option>
                  <option value="CASH">Cash</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Transaction Ref / UTR / Cheque #</label>
                <input
                  type="text"
                  value={referenceNumber}
                  onChange={(e) => setReferenceNumber(e.target.value)}
                  placeholder="e.g. UTR-HDFC-991244"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Bank Name</label>
                <input
                  type="text"
                  value={bankName}
                  onChange={(e) => setBankName(e.target.value)}
                  placeholder="e.g. HDFC Bank, ICICI Bank"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                />
              </div>

              <div className="md:col-span-3">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Remarks / Payment Notes</label>
                <input
                  type="text"
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  placeholder="e.g. Advance for Diwali Murukku dispatch"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                />
              </div>
            </div>

            {/* Unpaid Invoices Allocation Section */}
            {selectedCustomerId && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                      Outstanding Invoices for Allocation
                    </span>
                    <p className="text-[11px] text-slate-500">
                      Allocate payment partially or fully across unpaid posted invoices.
                    </p>
                  </div>
                  {unpaidInvoices.length > 0 && (
                    <button
                      type="button"
                      onClick={handleAutoAllocateFIFO}
                      className="px-2.5 py-1 text-xs bg-blue-50 text-blue-700 rounded border border-blue-200 font-semibold hover:bg-blue-100 transition"
                    >
                      Auto Allocate (FIFO)
                    </button>
                  )}
                </div>

                {unpaidInvoices.length === 0 ? (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 text-center">
                    No outstanding unpaid invoices for this customer. Payment will be recorded on account.
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-2.5 px-3">Invoice Number</th>
                          <th className="py-2.5 px-3">Invoice Date</th>
                          <th className="py-2.5 px-3 text-right">Invoice Total (₹)</th>
                          <th className="py-2.5 px-3 text-right">Already Paid (₹)</th>
                          <th className="py-2.5 px-3 text-right">Remaining Due (₹)</th>
                          <th className="py-2.5 px-3 text-center">Allocate Now (₹)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 font-mono">
                        {unpaidInvoices.map((inv) => {
                          const totalRs = inv.grand_total_paise / 100
                          const paidRs = inv.amount_paid_paise / 100
                          const remainingRs = inv.remaining_unpaid_paise / 100
                          const currentAlloc = parseFloat(allocations[inv.id] || '0')
                          const isExcess = currentAlloc > remainingRs

                          return (
                            <tr key={inv.id} className="hover:bg-slate-50 transition font-sans">
                              <td className="py-2.5 px-3 font-mono font-bold text-blue-600">{inv.invoice_number}</td>
                              <td className="py-2.5 px-3 text-slate-600">{inv.invoice_date}</td>
                              <td className="py-2.5 px-3 text-right font-mono font-medium">₹{totalRs.toFixed(2)}</td>
                              <td className="py-2.5 px-3 text-right font-mono text-emerald-600">₹{paidRs.toFixed(2)}</td>
                              <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                                ₹{remainingRs.toFixed(2)}
                              </td>
                              <td className="py-2.5 px-3 text-center">
                                <input
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  max={remainingRs}
                                  value={allocations[inv.id] || ''}
                                  onChange={(e) =>
                                    setAllocations({
                                      ...allocations,
                                      [inv.id]: e.target.value,
                                    })
                                  }
                                  className={`w-32 text-center text-xs p-1.5 rounded-lg border font-mono font-bold ${
                                    isExcess
                                      ? 'border-red-500 bg-red-50 text-red-700'
                                      : 'border-slate-300 bg-white text-slate-900'
                                  }`}
                                  placeholder="0.00"
                                />
                                {isExcess && (
                                  <span className="block text-[10px] text-red-600 font-semibold mt-0.5">
                                    Exceeds Due (₹{(currentAlloc - remainingRs).toFixed(2)})
                                  </span>
                                )}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Submit Action */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setActiveTab('payments')}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50 flex items-center space-x-1.5"
              >
                <Check className="h-4 w-4" />
                <span>{loading ? 'Recording...' : 'Record & Post Receipt'}</span>
              </button>
            </div>
          </div>
        </form>
      )}

      {/* TAB 3: CUSTOMER LEDGER STATEMENT */}
      {activeTab === 'ledger' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Statement of Customer Account</h3>
                <p className="text-xs text-slate-500">
                  Running balance ledger for tracking debits (sales invoices) and credits (receipts).
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Building2 className="h-4 w-4 text-slate-400" />
                <select
                  value={selectedLedgerCustomer}
                  onChange={(e) => setSelectedLedgerCustomer(e.target.value)}
                  className="text-xs p-2 rounded-lg border border-slate-300 bg-white font-medium"
                >
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.customer_name} ({c.customer_code})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {ledgerStatement && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Customer Profile</span>
                    <p className="text-sm font-bold text-slate-900 mt-1">{ledgerStatement.customer_name}</p>
                    <p className="text-xs text-slate-500">{ledgerStatement.gstin || 'Unregistered'}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Invoiced (Debit)</span>
                    <p className="text-sm font-bold text-blue-600 mt-1 font-mono">
                      ₹{(ledgerStatement.total_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Received (Credit)</span>
                    <p className="text-sm font-bold text-emerald-600 mt-1 font-mono">
                      ₹{(ledgerStatement.total_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Closing Balance (Due)</span>
                    <p
                      className={`text-sm font-bold mt-1 font-mono ${
                        ledgerStatement.closing_balance_paise > 0 ? 'text-amber-600' : 'text-slate-900'
                      }`}
                    >
                      ₹{(ledgerStatement.closing_balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>

                {/* Ledger Entries Table */}
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Date</th>
                        <th className="py-2.5 px-3">Type</th>
                        <th className="py-2.5 px-3">Reference #</th>
                        <th className="py-2.5 px-3">Description</th>
                        <th className="py-2.5 px-3 text-right">Debit (₹)</th>
                        <th className="py-2.5 px-3 text-right">Credit (₹)</th>
                        <th className="py-2.5 px-3 text-right">Running Balance (₹)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 font-mono">
                      {ledgerStatement.entries.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-6 text-center text-slate-500 font-sans">
                            No ledger transactions recorded for this customer yet.
                          </td>
                        </tr>
                      ) : (
                        ledgerStatement.entries.map((entry) => (
                          <tr key={entry.id} className="hover:bg-slate-50 transition font-sans">
                            <td className="py-2.5 px-3 text-slate-600 font-mono">{entry.entry_date}</td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  entry.entry_type === 'INVOICE'
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-emerald-100 text-emerald-800'
                                }`}
                              >
                                {entry.entry_type}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-mono font-medium text-slate-800">{entry.reference_number}</td>
                            <td className="py-2.5 px-3 text-slate-600">{entry.description || '-'}</td>
                            <td className="py-2.5 px-3 text-right font-mono text-blue-600">
                              {entry.debit_paise > 0
                                ? `₹${(entry.debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                                : '-'}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono text-emerald-600">
                              {entry.credit_paise > 0
                                ? `₹${(entry.credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                                : '-'}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                              ₹{(entry.running_balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: RECEIVABLES AGEING ANALYSIS */}
      {activeTab === 'ageing' && ageingReport && (
        <div className="space-y-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Total Receivables</span>
              <p className="text-base font-extrabold text-slate-900 mt-1 font-mono">
                ₹{(ageingReport.total_receivables_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Not Due Yet</span>
              <p className="text-base font-extrabold text-slate-600 mt-1 font-mono">
                ₹{(ageingReport.total_not_due_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-bold text-emerald-600 uppercase">0 - 30 Days</span>
              <p className="text-base font-extrabold text-emerald-700 mt-1 font-mono">
                ₹{(ageingReport.total_0_to_30_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-bold text-blue-600 uppercase">31 - 60 Days</span>
              <p className="text-base font-extrabold text-blue-700 mt-1 font-mono">
                ₹{(ageingReport.total_31_to_60_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-bold text-amber-600 uppercase">61 - 90 Days</span>
              <p className="text-base font-extrabold text-amber-700 mt-1 font-mono">
                ₹{(ageingReport.total_61_to_90_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-bold text-red-600 uppercase">&gt; 90 Days</span>
              <p className="text-base font-extrabold text-red-700 mt-1 font-mono">
                ₹{(ageingReport.total_over_90_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          {/* Ageing Table by Customer */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Debtor Ageing Schedule</h3>
                <p className="text-xs text-slate-500">As of {ageingReport.as_of_date}</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4">Customer Name</th>
                    <th className="py-2.5 px-4">Code</th>
                    <th className="py-2.5 px-4 text-right">Total Due (₹)</th>
                    <th className="py-2.5 px-4 text-right">Not Due</th>
                    <th className="py-2.5 px-4 text-right">0 - 30 Days</th>
                    <th className="py-2.5 px-4 text-right">31 - 60 Days</th>
                    <th className="py-2.5 px-4 text-right">61 - 90 Days</th>
                    <th className="py-2.5 px-4 text-right">&gt; 90 Days</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 font-mono">
                  {ageingReport.customers.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                        Zero outstanding receivables! All customer invoices are fully settled.
                      </td>
                    </tr>
                  ) : (
                    ageingReport.customers.map((c) => (
                      <tr key={c.customer_id} className="hover:bg-slate-50 transition font-sans">
                        <td className="py-3 px-4 font-medium text-slate-900">{c.customer_name}</td>
                        <td className="py-3 px-4 font-mono text-slate-500">{c.customer_code}</td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                          ₹{(c.total_outstanding_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-slate-500">
                          ₹{(c.not_due_paise / 100).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-emerald-600 font-medium">
                          ₹{(c.days_0_to_30_paise / 100).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-blue-600 font-medium">
                          ₹{(c.days_31_to_60_paise / 100).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-amber-600 font-medium">
                          ₹{(c.days_61_to_90_paise / 100).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-red-600 font-bold">
                          ₹{(c.days_over_90_paise / 100).toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Payment Details Modal */}
      {viewPayment && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <CreditCard className="h-4 w-4 text-emerald-600" />
                  <span>Receipt #{viewPayment.payment_number}</span>
                </h3>
                <span className="text-xs text-slate-500">{viewPayment.payment_date}</span>
              </div>
              <button
                onClick={() => setViewPayment(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg">
                <div>
                  <span className="text-slate-500 block">Customer</span>
                  <span className="font-bold text-slate-900">{viewPayment.customer_name}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Payment Mode</span>
                  <span className="font-bold text-slate-900">{viewPayment.payment_mode}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Amount</span>
                  <span className="font-bold text-emerald-700 text-sm font-mono">
                    ₹{(viewPayment.amount_paise / 100).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Reference</span>
                  <span className="font-mono text-slate-800">{viewPayment.reference_number || 'N/A'}</span>
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-2">Invoice Allocations</span>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2 px-3">Invoice Number</th>
                        <th className="py-2 px-3 text-right">Allocated Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 font-mono">
                      {viewPayment.allocations.map((a) => (
                        <tr key={a.id}>
                          <td className="py-2 px-3 text-blue-600">{a.invoice_number || 'Direct Invoice'}</td>
                          <td className="py-2 px-3 text-right font-bold text-slate-900">
                            ₹{(a.allocated_amount_paise / 100).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-200">
              <button
                onClick={() => handleDownloadReceipt(viewPayment.id, viewPayment.payment_number)}
                className="px-3 py-1.5 bg-emerald-600 text-white rounded text-xs font-semibold hover:bg-emerald-700 transition flex items-center space-x-1"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download PDF</span>
              </button>
              <button
                onClick={() => setViewPayment(null)}
                className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded text-xs font-semibold hover:bg-slate-50 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
