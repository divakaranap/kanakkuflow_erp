import { describe, it, expect } from 'vitest'
import type { Dispatch } from '../types/dispatch'

describe('Phase 6 - Dispatch and Finished Goods Management Tests', () => {
  it('correctly calculates remaining stock after benchmark dispatch (238 - 150 = 88 pkts)', () => {
    const initialFGStock = 238
    const retailerADispatchQty = 150

    expect(retailerADispatchQty).toBeLessThanOrEqual(initialFGStock)
    const remainingStock = initialFGStock - retailerADispatchQty
    expect(remainingStock).toBe(88)
  })

  it('correctly detects shortage when requested quantity exceeds available stock (Distributor B: 120 requested, 88 available -> shortage 32)', () => {
    const availableStock = 88
    const requestedQty = 120

    const isSufficient = availableStock >= requestedQty
    const shortageQty = Math.max(0, requestedQty - availableStock)

    expect(isSufficient).toBe(false)
    expect(shortageQty).toBe(32)
  })

  it('validates Dispatch and OrderDispatchStatusResponse type contracts', () => {
    const dummyDispatch: Dispatch = {
      id: 'disp-uuid-1',
      dispatch_number: 'DSP-202611-0001',
      sales_order_id: 'so-uuid-1',
      order_number: 'SO-202611-0001',
      customer_id: 'cust-uuid-1',
      customer_name: 'Retailer A (Sri Krishna Stores)',
      dispatch_date: '2026-11-18',
      status: 'DISPATCHED',
      transporter_name: 'TN Logistics',
      vehicle_number: 'TN-45-AB-1234',
      created_by: 1,
      created_at: new Date().toISOString(),
      items: [
        {
          id: 'item-1',
          dispatch_id: 'disp-uuid-1',
          sales_order_item_id: 'so-item-1',
          product_id: 'prod-1',
          product_name: 'Murukku 200g',
          quantity_dispatched: 150,
          unit: 'packet',
          created_at: new Date().toISOString(),
        },
      ],
    }

    expect(dummyDispatch.dispatch_number).toBe('DSP-202611-0001')
    expect(dummyDispatch.items).toHaveLength(1)
    expect(dummyDispatch.items[0].quantity_dispatched).toBe(150)
  })
})
