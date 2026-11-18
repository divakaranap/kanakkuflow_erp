import { api } from "./api"
import type {
  StockSummaryItem,
  StockMovement,
  StockValuationSummary,
  StockValuationItem,
  StockReconciliationReport,
  InventoryAdjustment,
  AdjustmentCreate,
  Purchase,
  PurchaseCreate,
  InventoryItemType,
  MovementType,
  PurchaseStatus,
  AdjustmentStatus,
} from "../types/inventory"

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export const inventoryService = {
  // Stock Summary
  async getStockSummary(params?: {
    item_type?: InventoryItemType
    search?: string
    low_stock_only?: boolean
  }): Promise<StockSummaryItem[]> {
    const res = await api.get<StockSummaryItem[]>("/stock/summary", { params })
    return res.data
  },

  async getItemSummary(itemType: InventoryItemType, itemId: string): Promise<StockSummaryItem> {
    const res = await api.get<StockSummaryItem>(`/stock/summary/${itemType}/${itemId}`)
    return res.data
  },

  // Stock Ledger
  async getStockLedger(params?: {
    item_type?: InventoryItemType
    item_id?: string
    movement_type?: MovementType
    from_date?: string
    to_date?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResult<StockMovement>> {
    const res = await api.get<PaginatedResult<StockMovement>>("/stock/ledger", { params })
    return res.data
  },

  // Inventory Valuation
  async getStockValuation(itemType?: InventoryItemType): Promise<StockValuationSummary> {
    const res = await api.get<StockValuationSummary>("/stock/valuation", {
      params: itemType ? { item_type: itemType } : {},
    })
    return res.data
  },

  async getItemValuation(itemType: InventoryItemType, itemId: string): Promise<StockValuationItem> {
    const res = await api.get<StockValuationItem>(`/stock/valuation/${itemType}/${itemId}`)
    return res.data
  },

  // Stock Reconciliation
  async getReconciliationReport(): Promise<StockReconciliationReport> {
    const res = await api.get<StockReconciliationReport>("/stock/reconciliation")
    return res.data
  },

  async runReconciliation(): Promise<StockReconciliationReport> {
    const res = await api.post<StockReconciliationReport>("/stock/reconciliation/run")
    return res.data
  },

  // Opening Stock
  async initializeOpeningStock(data: {
    item_type: InventoryItemType
    item_id: string
    quantity: number | string
    unit_cost_paise: number
    notes?: string
  }): Promise<StockMovement> {
    const res = await api.post<StockMovement>("/inventory/opening-stock", data)
    return res.data
  },

  // Adjustments
  async getAdjustments(params?: {
    item_type?: InventoryItemType
    status?: AdjustmentStatus
    page?: number
    limit?: number
  }): Promise<PaginatedResult<InventoryAdjustment>> {
    const res = await api.get<PaginatedResult<InventoryAdjustment>>("/inventory/adjustments", { params })
    return res.data
  },

  async createAdjustment(data: AdjustmentCreate): Promise<InventoryAdjustment> {
    const res = await api.post<InventoryAdjustment>("/inventory/adjustments", data)
    return res.data
  },

  async postAdjustment(id: string): Promise<InventoryAdjustment> {
    const res = await api.post<InventoryAdjustment>(`/inventory/adjustments/${id}/post`)
    return res.data
  },

  // Purchases
  async getPurchases(params?: {
    supplier_id?: string
    status?: PurchaseStatus
    search?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResult<Purchase>> {
    const res = await api.get<PaginatedResult<Purchase>>("/purchases", { params })
    return res.data
  },

  async getPurchase(id: string): Promise<Purchase> {
    const res = await api.get<Purchase>(`/purchases/${id}`)
    return res.data
  },

  async createPurchase(data: PurchaseCreate): Promise<Purchase> {
    const res = await api.post<Purchase>("/purchases", data)
    return res.data
  },

  async postPurchase(id: string): Promise<Purchase> {
    const res = await api.post<Purchase>(`/purchases/${id}/post`)
    return res.data
  },
}
