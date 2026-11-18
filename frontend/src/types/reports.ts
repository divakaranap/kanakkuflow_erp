export interface SalesKpi {
  total_revenue_paise: number
  total_taxable_paise: number
  total_tax_paise: number
  invoices_count: number
  orders_count: number
}

export interface ProductionKpi {
  total_packets_produced: number
  completed_runs_count: number
  avg_yield_variance_pct: number
}

export interface InventoryKpi {
  total_valuation_paise: number
  raw_materials_paise: number
  packaging_paise: number
  finished_goods_paise: number
}

export interface FinanceKpi {
  total_receivables_paise: number
  total_collections_paise: number
  over_30_days_paise: number
}

export interface TopProduct {
  product_name: string
  total_quantity: number
  total_revenue_paise: number
}

export interface TopDebtor {
  customer_id: string
  customer_name: string
  outstanding_paise: number
  over_30_days_paise: number
}

export interface DashboardSummary {
  as_of_date: string
  sales: SalesKpi
  production: ProductionKpi
  inventory: InventoryKpi
  finance: FinanceKpi
  top_products: TopProduct[]
  top_debtors: TopDebtor[]
}
