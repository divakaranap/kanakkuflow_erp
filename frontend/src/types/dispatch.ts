export type DispatchStatus = "DRAFT" | "READY" | "DISPATCHED" | "CANCELLED"

export interface DispatchItem {
  id: string
  dispatch_id: string
  sales_order_item_id: string
  product_id: string
  product_name?: string
  product_sku?: string
  quantity_dispatched: number | string
  batch_reference?: string
  unit: string
  created_at: string
}

export interface DispatchItemCreate {
  sales_order_item_id: string
  product_id: string
  quantity_dispatched: number | string
  batch_reference?: string
}

export interface Dispatch {
  id: string
  dispatch_number: string
  sales_order_id: string
  order_number?: string
  invoice_id?: string
  invoice_number?: string
  customer_id: string
  customer_name?: string
  dispatch_date: string
  status: DispatchStatus
  transporter_name?: string
  vehicle_number?: string
  tracking_reference?: string
  notes?: string
  created_by: number
  creator_name?: string
  dispatched_by?: number
  dispatched_at?: string
  created_at: string
  items: DispatchItem[]
}

export interface DispatchCreate {
  sales_order_id: string
  invoice_id?: string
  dispatch_date?: string
  transporter_name?: string
  vehicle_number?: string
  tracking_reference?: string
  notes?: string
  items: DispatchItemCreate[]
}

export interface OrderItemDispatchStatus {
  sales_order_item_id: string
  product_id: string
  product_name: string
  ordered_quantity: number | string
  fulfilled_quantity: number | string
  pending_quantity: number | string
  available_stock_quantity: number | string
  has_sufficient_stock: boolean
}

export interface OrderDispatchStatusResponse {
  sales_order_id: string
  order_number: string
  customer_id: string
  customer_name: string
  order_status: string
  items: OrderItemDispatchStatus[]
  can_dispatch: boolean
}
