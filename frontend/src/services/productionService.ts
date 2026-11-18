import { api } from "./api"
import type {
  BOM,
  BOMCreate,
  BOMScalingResponse,
  BOMStatus,
  ProductionRun,
  ProductionRunCreate,
  ProductionRunUpdate,
  ProductionRunStatus,
  ProductionVarianceReport,
  ProductionCostingReport,
  ProductionSummary,
} from "../types/production"

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export const productionService = {
  // BOM Endpoints
  async getBOMs(params?: {
    product_id?: string
    status?: BOMStatus
    search?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResult<BOM>> {
    const res = await api.get<PaginatedResult<BOM>>("/boms", { params })
    return res.data
  },

  async getBOM(id: string): Promise<BOM> {
    const res = await api.get<BOM>(`/boms/${id}`)
    return res.data
  },

  async getActiveBOM(productId: string): Promise<BOM> {
    const res = await api.get<BOM>(`/boms/active/${productId}`)
    return res.data
  },

  async createBOM(data: BOMCreate): Promise<BOM> {
    const res = await api.post<BOM>("/boms", data)
    return res.data
  },

  async activateBOM(id: string): Promise<BOM> {
    const res = await api.post<BOM>(`/boms/${id}/activate`)
    return res.data
  },

  async archiveBOM(id: string): Promise<BOM> {
    const res = await api.post<BOM>(`/boms/${id}/archive`)
    return res.data
  },

  async scaleBOM(id: string, batches: number | string = 1): Promise<BOMScalingResponse> {
    const res = await api.get<BOMScalingResponse>(`/boms/${id}/scale`, {
      params: { batches },
    })
    return res.data
  },

  // Production Run Endpoints
  async getProductionRuns(params?: {
    product_id?: string
    status?: ProductionRunStatus
    search?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResult<ProductionRun>> {
    const res = await api.get<PaginatedResult<ProductionRun>>("/production-runs", { params })
    return res.data
  },

  async getProductionRun(id: string): Promise<ProductionRun> {
    const res = await api.get<ProductionRun>(`/production-runs/${id}`)
    return res.data
  },

  async createProductionRun(data: ProductionRunCreate): Promise<ProductionRun> {
    const res = await api.post<ProductionRun>("/production-runs", data)
    return res.data
  },

  async updateProductionRun(id: string, data: ProductionRunUpdate): Promise<ProductionRun> {
    const res = await api.patch<ProductionRun>(`/production-runs/${id}`, data)
    return res.data
  },

  async postProductionRun(id: string): Promise<ProductionRun> {
    const res = await api.post<ProductionRun>(`/production-runs/${id}/post`)
    return res.data
  },

  async getVarianceReport(runId: string): Promise<ProductionVarianceReport> {
    const res = await api.get<ProductionVarianceReport>(`/production-runs/${runId}/variance`)
    return res.data
  },

  async getCostingReport(runId: string): Promise<ProductionCostingReport> {
    const res = await api.get<ProductionCostingReport>(`/production-runs/${runId}/costing`)
    return res.data
  },

  async getProductionSummary(): Promise<ProductionSummary> {
    const res = await api.get<ProductionSummary>("/production/summary")
    return res.data
  },

  async getVarianceAlerts(): Promise<PaginatedResult<ProductionRun>> {
    const res = await api.get<PaginatedResult<ProductionRun>>("/production/variance-alerts")
    return res.data
  },
}
