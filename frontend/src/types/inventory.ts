export type InventoryItemType = "RAW" | "PACKAGING" | "FG"

export type MovementType =
  | "OPENING"
  | "PURCHASE_RECEIPT"
  | "PURCHASE_RETURN"
  | "PRODUCTION_ISSUE"
  | "PRODUCTION_OUTPUT"
  | "PRODUCTION_SCRAP"
  | "INVOICE_DISPATCH"
  | "CREDIT_NOTE"
  | "ADJUSTMENT"

export type AdjustmentType = "INCREASE" | "DECREASE"
export type AdjustmentStatus = "DRAFT" | "POSTED"

export type PurchaseStatus = "DRAFT" | "POSTED" | "CANCELLED"
export type PurchaseItemType = "RAW" | "PACKAGING"

export interface StockSummaryItem {
  item_type: InventoryItemType
  item_id: string
  item_code: string
  item_name: string
  category?: string
  base_unit: string
  current_stock: number | string
  reorder_level: number | string
  is_low_stock: boolean
  weighted_avg_rate_paise: number
  total_valuation_paise: number
  last_updated?: string
}

export interface StockMovement {
  id: string
  item_type: InventoryItemType
  item_id: string
  item_name?: string
  item_code?: string
  batch_id?: string
  movement_type: MovementType
  qty_delta: number | string
  unit_cost_paise?: number
  total_value_paise?: number
  source_type: string
  source_id: string
  reference_number?: string
  notes?: string
  created_by?: number
  created_at: string
}

export interface StockValuationItem {
  item_type: InventoryItemType
  item_id: string
  item_code: string
  item_name: string
  base_unit: string
  quantity: number | string
  weighted_avg_rate_paise: number
  total_value_paise: number
}

export interface StockValuationSummary {
  total_valuation_paise: number
  total_items: number
  raw_materials_valuation_paise: number
  packaging_valuation_paise: number
  finished_goods_valuation_paise: number
  items: StockValuationItem[]
}

export interface StockReconciliationItem {
  item_type: InventoryItemType
  item_id: string
  item_code: string
  item_name: string
  base_unit: string
  ledger_qty: number | string
  cached_qty: number | string
  difference: number | string
  status: "MATCHED" | "MISMATCH"
}

export interface StockReconciliationReport {
  reconciled_at: string
  total_items: number
  matched_items: number
  mismatched_items: number
  is_fully_reconciled: boolean
  items: StockReconciliationItem[]
}

export interface InventoryAdjustment {
  id: string
  adjustment_number: string
  item_type: InventoryItemType
  item_id: string
  item_name?: string
  item_code?: string
  adjustment_type: AdjustmentType
  quantity: number | string
  reason: string
  reference_number?: string
  status: AdjustmentStatus
  created_by: number
  approved_by?: number
  posted_at?: string
  created_at: string
  updated_at: string
}

export interface AdjustmentCreate {
  item_type: InventoryItemType
  item_id: string
  adjustment_type: AdjustmentType
  quantity: number | string
  reason: string
  reference_number?: string
}

export interface PurchaseLine {
  id: string
  purchase_id: string
  item_type: PurchaseItemType
  item_id: string
  item_name?: string
  item_code?: string
  quantity: number | string
  unit: string
  normalized_quantity: number | string
  unit_rate_paise: number
  taxable_value_paise: number
  tax_rate: number | string
  tax_paise: number
  line_total_paise: number
  batch_number?: string
  manufacturing_date?: string
  expiry_date?: string
}

export interface PurchaseLineCreate {
  item_type: PurchaseItemType
  item_id: string
  quantity: number | string
  unit: string
  unit_rate_paise: number
  tax_rate?: number | string
  batch_number?: string
  manufacturing_date?: string
  expiry_date?: string
}

export interface Purchase {
  id: string
  purchase_number: string
  supplier_id: string
  supplier_name?: string
  supplier_invoice_number: string
  purchase_date: string
  status: PurchaseStatus
  subtotal_paise: number
  tax_paise: number
  total_paise: number
  notes?: string
  created_by: number
  posted_by?: number
  posted_at?: string
  created_at: string
  updated_at: string
  lines: PurchaseLine[]
}

export interface PurchaseCreate {
  supplier_id: string
  supplier_invoice_number: string
  purchase_date?: string
  notes?: string
  lines: PurchaseLineCreate[]
}
