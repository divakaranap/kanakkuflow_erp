export type SalesOrderStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "APPROVED"
  | "PARTIALLY_FULFILLED"
  | "FULFILLED"
  | "CANCELLED"

export type InvoiceStatus = "DRAFT" | "POSTED" | "CANCELLED"

export interface SalesOrderItem {
  id: string
  sales_order_id: string
  product_id: string
  product_name?: string
  product_sku?: string
  ordered_quantity: number | string
  fulfilled_quantity: number | string
  unit_price_paise: number
  discount_paise: number
  gst_rate: number | string
  taxable_amount_paise: number
  cgst_paise: number
  sgst_paise: number
  igst_paise: number
  line_total_paise: number
}

export interface SalesOrderItemCreate {
  product_id: string
  ordered_quantity: number | string
  unit_price_paise?: number
  discount_paise?: number
}

export interface SalesOrder {
  id: string
  order_number: string
  customer_id: string
  customer_name?: string
  customer_code?: string
  order_date: string
  delivery_date?: string
  place_of_supply_state_code: string
  customer_gstin?: string
  status: SalesOrderStatus
  subtotal_paise: number
  discount_paise: number
  taxable_amount_paise: number
  cgst_paise: number
  sgst_paise: number
  igst_paise: number
  total_tax_paise: number
  grand_total_paise: number
  notes?: string
  created_by: number
  creator_name?: string
  approved_by?: number
  approved_at?: string
  created_at: string
  updated_at: string
  items: SalesOrderItem[]
}

export interface SalesOrderCreate {
  customer_id: string
  delivery_date?: string
  notes?: string
  items: SalesOrderItemCreate[]
}

export interface SalesOrderUpdate {
  delivery_date?: string
  notes?: string
  items?: SalesOrderItemCreate[]
}

export interface SalesInvoiceItem {
  id: string
  invoice_id: string
  product_id?: string
  product_name: string
  hsn_code: string
  quantity: number | string
  unit: string
  unit_price_paise: number
  taxable_value_paise: number
  gst_rate: number | string
  cgst_paise: number
  sgst_paise: number
  igst_paise: number
  line_total_paise: number
}

export interface SalesInvoice {
  id: string
  invoice_number: string
  sales_order_id: string
  order_number?: string
  customer_id: string
  customer_name?: string
  customer_gstin?: string
  invoice_date: string
  place_of_supply_state_code: string
  seller_gstin: string
  buyer_gstin?: string
  taxable_amount_paise: number
  cgst_paise: number
  sgst_paise: number
  igst_paise: number
  total_tax_paise: number
  grand_total_paise: number
  status: InvoiceStatus
  pdf_path?: string
  cancellation_reason?: string
  created_by: number
  creator_name?: string
  posted_at?: string
  created_at: string
  items: SalesInvoiceItem[]
}

export interface SalesInvoiceCreate {
  sales_order_id: string
  invoice_date?: string
}

export interface ProductStockCheckResponse {
  product_id: string
  sku: string
  product_name: string
  requested_qty: number | string
  available_qty: number | string
  is_sufficient: boolean
  shortage_qty: number | string
}
