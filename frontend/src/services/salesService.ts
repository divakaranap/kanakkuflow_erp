import { api } from "./api"
import type {
  SalesOrder,
  SalesOrderCreate,
  SalesOrderUpdate,
  SalesOrderStatus,
  SalesInvoice,
  SalesInvoiceCreate,
  InvoiceStatus,
  ProductStockCheckResponse,
} from "../types/sales"

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export const salesService = {
  // Stock availability check
  async checkStock(productId: string, quantity: number | string): Promise<ProductStockCheckResponse> {
    const res = await api.get<ProductStockCheckResponse>("/sales/check-stock", {
      params: { product_id: productId, quantity },
    })
    return res.data
  },

  // Sales Orders
  async getSalesOrders(params?: {
    customer_id?: string
    status?: SalesOrderStatus
    page?: number
    limit?: number
  }): Promise<PaginatedResult<SalesOrder>> {
    const res = await api.get<PaginatedResult<SalesOrder>>("/sales/orders", { params })
    return res.data
  },

  async getSalesOrder(id: string): Promise<SalesOrder> {
    const res = await api.get<SalesOrder>(`/sales/orders/${id}`)
    return res.data
  },

  async createSalesOrder(data: SalesOrderCreate): Promise<SalesOrder> {
    const res = await api.post<SalesOrder>("/sales/orders", data)
    return res.data
  },

  async updateSalesOrder(id: string, data: SalesOrderUpdate): Promise<SalesOrder> {
    const res = await api.patch<SalesOrder>(`/sales/orders/${id}`, data)
    return res.data
  },

  async submitSalesOrder(id: string): Promise<SalesOrder> {
    const res = await api.post<SalesOrder>(`/sales/orders/${id}/submit`)
    return res.data
  },

  async approveSalesOrder(id: string): Promise<SalesOrder> {
    const res = await api.post<SalesOrder>(`/sales/orders/${id}/approve`)
    return res.data
  },

  async cancelSalesOrder(id: string): Promise<SalesOrder> {
    const res = await api.post<SalesOrder>(`/sales/orders/${id}/cancel`)
    return res.data
  },

  // Invoices
  async getSalesInvoices(params?: {
    customer_id?: string
    status?: InvoiceStatus
    page?: number
    limit?: number
  }): Promise<PaginatedResult<SalesInvoice>> {
    const res = await api.get<PaginatedResult<SalesInvoice>>("/sales/invoices", { params })
    return res.data
  },

  async getSalesInvoice(id: string): Promise<SalesInvoice> {
    const res = await api.get<SalesInvoice>(`/sales/invoices/${id}`)
    return res.data
  },

  async createSalesInvoice(data: SalesInvoiceCreate): Promise<SalesInvoice> {
    const res = await api.post<SalesInvoice>("/sales/invoices", data)
    return res.data
  },

  async cancelSalesInvoice(id: string, cancellationReason: string): Promise<SalesInvoice> {
    const res = await api.post<SalesInvoice>(`/sales/invoices/${id}/cancel`, {
      cancellation_reason: cancellationReason,
    })
    return res.data
  },

  async downloadInvoicePdf(id: string, invoiceNumber: string): Promise<void> {
    const res = await api.get(`/sales/invoices/${id}/pdf`, {
      responseType: "blob",
    })
    const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `Invoice_${invoiceNumber}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  },
}
