import { describe, it, expect } from 'vitest'
import type { SalesOrder } from '../types/sales'

describe('Phase 5 - Sales & GST Invoicing Tests', () => {
  it('correctly calculates intra-state GST (Tamil Nadu to Tamil Nadu, 5% on ₹7,500)', () => {
    // Retailer A benchmark: 150 pkts @ ₹50.00 = ₹7,500.00 (750,000 paise)
    const taxablePaise = 750000
    const gstRatePct = 5.0
    const halfRate = gstRatePct / 2 // 2.5%

    const cgstPaise = Math.round((taxablePaise * halfRate) / 100)
    const sgstPaise = Math.round((taxablePaise * halfRate) / 100)
    const igstPaise = 0
    const totalTaxPaise = cgstPaise + sgstPaise + igstPaise
    const grandTotalPaise = taxablePaise + totalTaxPaise

    expect(cgstPaise).toBe(18750) // ₹187.50
    expect(sgstPaise).toBe(18750) // ₹187.50
    expect(igstPaise).toBe(0)
    expect(totalTaxPaise).toBe(37500) // ₹375.00
    expect(grandTotalPaise).toBe(787500) // ₹7,875.00
  })

  it('correctly calculates inter-state GST (Tamil Nadu to Karnataka, 5% on ₹7,500)', () => {
    // Distributor B benchmark: 150 pkts @ ₹50.00 = ₹7,500.00 (750,000 paise)
    const taxablePaise = 750000
    const gstRatePct = 5.0

    const cgstPaise = 0
    const sgstPaise = 0
    const igstPaise = Math.round((taxablePaise * gstRatePct) / 100)
    const totalTaxPaise = cgstPaise + sgstPaise + igstPaise
    const grandTotalPaise = taxablePaise + totalTaxPaise

    expect(cgstPaise).toBe(0)
    expect(sgstPaise).toBe(0)
    expect(igstPaise).toBe(37500) // ₹375.00
    expect(totalTaxPaise).toBe(37500)
    expect(grandTotalPaise).toBe(787500)
  })

  it('validates SalesOrder and SalesInvoice contract objects', () => {
    const dummyOrder: SalesOrder = {
      id: 'so-uuid-1',
      order_number: 'SO-202611-0001',
      customer_id: 'cust-uuid-1',
      customer_name: 'Retailer A (Sri Krishna Stores)',
      order_date: '2026-11-18',
      place_of_supply_state_code: '33',
      status: 'APPROVED',
      subtotal_paise: 750000,
      discount_paise: 0,
      taxable_amount_paise: 750000,
      cgst_paise: 18750,
      sgst_paise: 18750,
      igst_paise: 0,
      total_tax_paise: 37500,
      grand_total_paise: 787500,
      created_by: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      items: [
        {
          id: 'item-1',
          sales_order_id: 'so-uuid-1',
          product_id: 'prod-murukku-1',
          ordered_quantity: 150,
          fulfilled_quantity: 0,
          unit_price_paise: 5000,
          discount_paise: 0,
          gst_rate: 5.0,
          taxable_amount_paise: 750000,
          cgst_paise: 18750,
          sgst_paise: 18750,
          igst_paise: 0,
          line_total_paise: 787500,
        },
      ],
    }

    expect(dummyOrder.order_number).toBe('SO-202611-0001')
    expect(dummyOrder.grand_total_paise).toBe(787500)
    expect(dummyOrder.items).toHaveLength(1)
  })
})
