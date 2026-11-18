import { api } from "./api"
import type {
  Dispatch,
  DispatchCreate,
  DispatchStatus,
  OrderDispatchStatusResponse,
} from "../types/dispatch"

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export const dispatchService = {
  async getOrderDispatchStatus(orderId: string): Promise<OrderDispatchStatusResponse> {
    const res = await api.get<OrderDispatchStatusResponse>(`/dispatches/orders/${orderId}/status`)
    return res.data
  },

  async getDispatches(params?: {
    customer_id?: string
    sales_order_id?: string
    status?: DispatchStatus
    page?: number
    limit?: number
  }): Promise<PaginatedResult<Dispatch>> {
    const res = await api.get<PaginatedResult<Dispatch>>("/dispatches", { params })
    return res.data
  },

  async getDispatch(id: string): Promise<Dispatch> {
    const res = await api.get<Dispatch>(`/dispatches/${id}`)
    return res.data
  },

  async createDispatch(data: DispatchCreate): Promise<Dispatch> {
    const res = await api.post<Dispatch>("/dispatches", data)
    return res.data
  },

  async postDispatch(id: string): Promise<Dispatch> {
    const res = await api.post<Dispatch>(`/dispatches/${id}/post`)
    return res.data
  },

  async cancelDispatch(id: string): Promise<Dispatch> {
    const res = await api.post<Dispatch>(`/dispatches/${id}/cancel`)
    return res.data
  },

  async downloadChallanPdf(id: string, dispatchNumber: string): Promise<void> {
    const res = await api.get(`/dispatches/${id}/challan`, {
      responseType: "blob",
    })
    const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `Challan_${dispatchNumber}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  },
}
