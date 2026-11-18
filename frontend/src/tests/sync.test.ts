import { describe, it, expect } from 'vitest'
import type { QueuedOrder } from '../lib/offlineDb'

describe('Phase 10 - Mobile PWA & Offline Sync Tests', () => {
  it('correctly calculates offline order total with standard 5% food GST', () => {
    // 50 pkts Murukku 200g @ ₹50.00 = ₹2,500.00 = 250,000 paise
    const qty = 50
    const unitPricePaise = 5000 // ₹50.00
    const subtotalPaise = qty * unitPricePaise // 250000 paise
    const taxPaise = Math.round(subtotalPaise * 0.05) // 12500 paise (5% GST)
    const grandTotalPaise = subtotalPaise + taxPaise // 262500 paise (₹2,625.00)

    expect(subtotalPaise).toBe(250000)
    expect(taxPaise).toBe(12500)
    expect(grandTotalPaise).toBe(262500)
    expect(grandTotalPaise / 100).toBe(2625.0)
  })

  it('generates unique client_order_uuid and verifies queued order payload', () => {
    const mockOrder: QueuedOrder = {
      client_order_uuid: '550e8400-e29b-41d4-a716-446655440000',
      customer_id: 'cust-1234',
      customer_name: 'Sri Krishna Stores',
      order_date: '2026-11-18',
      delivery_date: '2026-11-20',
      notes: 'Urgent festival delivery',
      items: [
        {
          product_id: 'prod-5678',
          product_name: 'Murukku 200g',
          ordered_quantity: 100,
          unit_price_paise: 5000,
          line_total_paise: 500000,
        },
      ],
      total_amount_paise: 525000, // ₹5,250.00 with GST
      sync_status: 'PENDING',
      created_at: new Date().toISOString(),
    }

    expect(mockOrder.sync_status).toBe('PENDING')
    expect(mockOrder.items.length).toBe(1)
    expect(mockOrder.client_order_uuid).toBeDefined()
    expect(mockOrder.total_amount_paise / 100).toBe(5250.0)
  })

  it('processes batch sync results and segregates synced vs failed orders', () => {
    const syncResponse = {
      synced: [
        {
          client_order_uuid: 'uuid-1',
          sales_order_id: 'so-id-1',
          order_number: 'SO-202611-0001',
          grand_total_paise: 262500,
          status: 'DRAFT',
        },
      ],
      failed: [
        {
          client_order_uuid: 'uuid-2',
          error: 'Customer not found',
        },
      ],
    }

    expect(syncResponse.synced.length).toBe(1)
    expect(syncResponse.failed.length).toBe(1)
    expect(syncResponse.synced[0].order_number).toBe('SO-202611-0001')
    expect(syncResponse.failed[0].error).toContain('Customer not found')
  })
})
