export type CustomerType = 'RETAILER' | 'DISTRIBUTOR'

export interface Customer {
  id: string
  customer_code: string
  customer_name: string
  customer_type: CustomerType
  contact_person?: string | null
  phone: string
  email?: string | null
  gstin: string
  billing_address: string
  shipping_address: string
  city: string
  district?: string | null
  state: string
  state_code: string
  pincode: string
  price_list_id?: string | null
  credit_limit_paise: number
  assigned_salesman_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Supplier {
  id: string
  supplier_code: string
  supplier_name: string
  contact_person?: string | null
  phone: string
  email?: string | null
  gstin: string
  address: string
  city: string
  state: string
  state_code: string
  pincode: string
  payment_terms?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ProductCategory = 'MURUKKU' | 'MIXTURE' | 'CHIPS' | 'SWEETS' | 'OTHER'

export interface Product {
  id: string
  sku: string
  product_name: string
  category: ProductCategory
  description?: string | null
  pack_size: number | string
  pack_size_unit: string
  hsn_code: string
  gst_rate: number | string
  selling_price_paise: number
  base_unit: string
  packets_per_carton: number
  reorder_level: number | string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type RawMaterialCategory = 'FLOUR' | 'OIL' | 'SPICE' | 'OTHER'

export interface RawMaterial {
  id: string
  material_code: string
  material_name: string
  category: RawMaterialCategory
  base_unit: string
  reorder_level: number | string
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type PackagingCategory = 'POUCH' | 'CARTON' | 'LABEL' | 'TAPE' | 'OTHER'

export interface PackagingItem {
  id: string
  packaging_code: string
  packaging_name: string
  category: PackagingCategory
  base_unit: string
  reorder_level: number | string
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type PriceListCustomerType = 'RETAILER' | 'DISTRIBUTOR' | 'ALL'

export interface PriceListItem {
  id: string
  price_list_id: string
  product_id: string
  selling_price_paise: number
  valid_from?: string | null
  valid_until?: string | null
  product_sku?: string
  product_name?: string
  created_at: string
  updated_at: string
}

export interface PriceList {
  id: string
  name: string
  description?: string | null
  customer_type: PriceListCustomerType
  is_active: boolean
  items: PriceListItem[]
  created_at: string
  updated_at: string
}

export interface EffectivePrice {
  product_id: string
  sku: string
  product_name: string
  selling_price_paise: number
  source: string
  price_list_id?: string | null
  price_list_name?: string | null
}

export interface UnitConversionResult {
  original_quantity: string
  converted_quantity: string
  from_unit: string
  to_unit: string
  packets_per_carton?: number | null
}
