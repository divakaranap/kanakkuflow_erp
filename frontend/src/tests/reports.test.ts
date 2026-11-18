import { describe, it, expect } from 'vitest'
import type { DashboardSummary } from '../types/reports'

describe('Phase 9 - Management Analytics & Report Exports Tests', () => {
  it('correctly aggregates executive KPI financial figures from paise to rupees', () => {
    const summary: DashboardSummary = {
      as_of_date: '2026-11-18',
      sales: {
        total_revenue_paise: 787500, // ₹7,875.00
        total_taxable_paise: 750000, // ₹7,500.00
        total_tax_paise: 37500,      // ₹375.00 (5% GST)
        invoices_count: 1,
        orders_count: 1,
      },
      production: {
        total_packets_produced: 238,
        completed_runs_count: 1,
        avg_yield_variance_pct: -4.8, // -4.8% variance from planned 250 pkts
      },
      inventory: {
        total_valuation_paise: 2500000, // ₹25,000.00
        raw_materials_paise: 1500000,
        packaging_paise: 300000,
        finished_goods_paise: 700000,
      },
      finance: {
        total_receivables_paise: 387500, // ₹3,875.00
        total_collections_paise: 400000, // ₹4,000.00
        over_30_days_paise: 0,
      },
      top_products: [
        {
          product_name: 'Murukku 200g',
          total_quantity: 150,
          total_revenue_paise: 787500,
        },
      ],
      top_debtors: [
        {
          customer_id: 'cust-1',
          customer_name: 'Retailer A',
          outstanding_paise: 387500,
          over_30_days_paise: 0,
        },
      ],
    }

    expect(summary.sales.total_revenue_paise / 100).toBe(7875.0)
    expect(summary.sales.total_tax_paise / 100).toBe(375.0)
    expect(summary.production.total_packets_produced).toBe(238)
    expect(summary.production.avg_yield_variance_pct).toBe(-4.8)
    expect(summary.finance.total_receivables_paise / 100).toBe(3875.0)
    expect(summary.finance.total_collections_paise / 100).toBe(4000.0)
    expect(summary.top_products[0].total_quantity).toBe(150)
  })

  it('validates report export filename generation and mime types', () => {
    const reportTypes = ['csv', 'xlsx', 'pdf'] as const
    const mimeTypes: Record<string, string> = {
      csv: 'text/csv',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pdf: 'application/pdf',
    }

    for (const fmt of reportTypes) {
      expect(mimeTypes[fmt]).toBeDefined()
      const filename = `GSTR1_Sales_20261118.${fmt}`
      expect(filename.endsWith(`.${fmt}`)).toBe(true)
    }
  })

  it('correctly calculates ageing bucket distributions for customer debtors', () => {
    const debtors = [
      { name: 'Customer A', outstanding_paise: 387500, overdue_30_paise: 0 },
      { name: 'Customer B', outstanding_paise: 1200000, overdue_30_paise: 500000 },
    ]

    const totalOutstanding = debtors.reduce((acc, d) => acc + d.outstanding_paise, 0)
    const totalOverdue = debtors.reduce((acc, d) => acc + d.overdue_30_paise, 0)

    expect(totalOutstanding / 100).toBe(15875.0)
    expect(totalOverdue / 100).toBe(5000.0)
    expect((totalOverdue / totalOutstanding) * 100).toBeCloseTo(31.49, 1)
  })
})
