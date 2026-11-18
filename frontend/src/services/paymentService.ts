import { api } from './api'
import type {
  CustomerPayment,
  CustomerPaymentCreate,
  CustomerLedgerStatement,
  ReceivablesAgeingSummary,
  UnpaidInvoiceSummary,
} from '../types/payment'

export const paymentService = {
  async getPayments(customerId?: string): Promise<CustomerPayment[]> {
    const params = customerId ? { customer_id: customerId } : {}
    const response = await api.get<CustomerPayment[]>('/payments', { params })
    return response.data
  },

  async getPayment(paymentId: string): Promise<CustomerPayment> {
    const response = await api.get<CustomerPayment>(`/payments/${paymentId}`)
    return response.data
  },

  async recordPayment(data: CustomerPaymentCreate): Promise<CustomerPayment> {
    const response = await api.post<CustomerPayment>('/payments', data)
    return response.data
  },

  async getUnpaidInvoices(customerId: string): Promise<UnpaidInvoiceSummary[]> {
    const response = await api.get<UnpaidInvoiceSummary[]>(`/payments/unpaid-invoices/${customerId}`)
    return response.data
  },

  async getCustomerLedger(
    customerId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<CustomerLedgerStatement> {
    const params: Record<string, string> = {}
    if (fromDate) params.from_date = fromDate
    if (toDate) params.to_date = toDate
    const response = await api.get<CustomerLedgerStatement>(`/payments/ledger/${customerId}`, { params })
    return response.data
  },

  async getReceivablesAgeing(asOf?: string): Promise<ReceivablesAgeingSummary> {
    const params = asOf ? { as_of: asOf } : {}
    const response = await api.get<ReceivablesAgeingSummary>('/payments/receivables/ageing', { params })
    return response.data
  },

  async downloadReceiptPdf(paymentId: string, receiptNumber: string): Promise<void> {
    const response = await api.get(`/payments/${paymentId}/receipt`, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Receipt_${receiptNumber}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
