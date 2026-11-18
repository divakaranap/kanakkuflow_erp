import type { InventoryItemType } from "./inventory"

export type BOMStatus = "DRAFT" | "ACTIVE" | "ARCHIVED"
export type ProductionRunStatus = "DRAFT" | "POSTED" | "CANCELLED"
export type OverheadExpenseType = "LABOUR" | "GAS" | "POWER" | "OTHER"
export type VarianceStatus = "NORMAL" | "WARNING" | "CRITICAL"

export interface BOMItem {
  id: string
  bom_id: string
  item_type: InventoryItemType
  item_id: string
  item_name?: string
  item_code?: string
  quantity_per_batch: number | string
  unit: string
  created_at: string
}

export interface BOMItemCreate {
  item_type: InventoryItemType
  item_id: string
  quantity_per_batch: number | string
  unit: string
}

export interface BOM {
  id: string
  bom_code: string
  product_id: string
  product_name?: string
  product_sku?: string
  version: number
  batch_yield_packets: number | string
  tolerance_pct: number | string
  description?: string
  status: BOMStatus
  effective_from: string
  effective_until?: string
  created_by: number
  created_at: string
  updated_at: string
  items: BOMItem[]
}

export interface BOMCreate {
  product_id: string
  batch_yield_packets?: number | string
  tolerance_pct?: number | string
  description?: string
  items: BOMItemCreate[]
}

export interface BOMPlannedItem {
  item_type: InventoryItemType
  item_id: string
  item_code: string
  item_name: string
  quantity_per_batch: number | string
  planned_quantity: number | string
  unit: string
  available_stock: number | string
  is_sufficient: boolean
}

export interface BOMScalingResponse {
  bom_id: string
  bom_code: string
  version: number
  product_id: string
  product_name: string
  product_sku: string
  number_of_batches: number | string
  batch_yield_packets: number | string
  expected_output_packets: number | string
  tolerance_pct: number | string
  items: BOMPlannedItem[]
}

export interface ProductionRunMaterial {
  id: string
  production_run_id: string
  item_type: InventoryItemType
  item_id: string
  item_name?: string
  item_code?: string
  planned_quantity: number | string
  issued_quantity: number | string
  consumed_quantity: number | string
  unit: string
  planned_unit_cost: number
  actual_unit_cost: number
  material_cost_paise: number
  consumption_variance_pct: number | string
}

export interface ProductionRunMaterialCreate {
  item_type: InventoryItemType
  item_id: string
  issued_quantity: number | string
  consumed_quantity?: number | string
  unit: string
}

export interface ProductionRunOverhead {
  id: string
  production_run_id: string
  expense_type: OverheadExpenseType
  amount_paise: number
  description?: string
  created_at: string
}

export interface ProductionRunOverheadCreate {
  expense_type: OverheadExpenseType
  amount_paise: number
  description?: string
}

export interface ProductionRun {
  id: string
  run_number: string
  product_id: string
  product_name?: string
  product_sku?: string
  bom_id: string
  bom_code?: string
  production_date: string
  batch_number: string
  number_of_batches: number | string
  expected_output: number | string
  actual_good_output: number | string
  damaged_packaging: number | string
  wastage_quantity: number | string
  status: ProductionRunStatus
  planned_material_cost_paise: number
  actual_material_cost_paise: number
  packaging_cost_paise: number
  labour_cost_paise: number
  utility_cost_paise: number
  total_production_cost_paise: number
  cost_per_packet_paise: number
  cost_per_packet_decimal: number | string
  variance_status: VarianceStatus
  notes?: string
  supervisor_id: number
  created_at: string
  posted_at?: string
  materials: ProductionRunMaterial[]
  overheads: ProductionRunOverhead[]
}

export interface ProductionRunCreate {
  product_id: string
  bom_id?: string
  batch_number: string
  number_of_batches?: number | string
  actual_good_output?: number | string
  damaged_packaging?: number | string
  wastage_quantity?: number | string
  production_date?: string
  notes?: string
  materials?: ProductionRunMaterialCreate[]
  overheads?: ProductionRunOverheadCreate[]
}

export interface ProductionRunUpdate {
  batch_number?: string
  number_of_batches?: number | string
  actual_good_output?: number | string
  damaged_packaging?: number | string
  wastage_quantity?: number | string
  production_date?: string
  notes?: string
  materials?: ProductionRunMaterialCreate[]
  overheads?: ProductionRunOverheadCreate[]
}

export interface VarianceItem {
  item_type: string
  item_id: string
  item_code: string
  item_name: string
  planned_quantity: number | string
  actual_quantity: number | string
  unit: string
  difference: number | string
  variance_pct: number | string
  tolerance_pct: number | string
  status: "OK" | "WARNING" | "CRITICAL"
}

export interface ProductionVarianceReport {
  production_run_id: string
  run_number: string
  expected_output: number | string
  actual_good_output: number | string
  yield_difference: number | string
  yield_variance_pct: number | string
  yield_status: string
  material_variances: VarianceItem[]
  has_alerts: boolean
  alerts: string[]
}

export interface ProductionCostingReport {
  production_run_id: string
  run_number: string
  actual_good_output: number | string
  raw_materials_cost_paise: number
  packaging_cost_paise: number
  total_material_cost_paise: number
  labour_cost_paise: number
  utility_cost_paise: number
  total_overheads_paise: number
  total_production_cost_paise: number
  cost_per_packet_paise: number
  cost_per_packet_decimal: number | string
  selling_price_paise: number
  gross_margin_paise: number
  gross_margin_pct: number | string
  material_breakdown: Array<{
    item_type: string
    item_id: string
    item_code: string
    item_name: string
    consumed_quantity: string
    unit: string
    unit_cost_paise: number
    line_cost_paise: number
  }>
}

export interface ProductionSummary {
  total_runs: number
  posted_runs: number
  total_good_packets_produced: number
  total_expected_packets: number
  overall_yield_pct: number
  total_production_cost_paise: number
  avg_cost_per_packet_paise: number
  runs_with_variance_alerts: number
}
