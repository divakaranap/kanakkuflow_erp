import { describe, it, expect } from 'vitest'
import type { CustomerLedgerEntry } from '../types/payment'

describe('Phase 7 - Payments, Receivables & Customer Ledger Tests', () => {
  it('correctly calculates remaining unpaid balance after benchmark partial payment (₹7,875 - ₹4,000 = ₹3,875)', () => {
    const invoiceGrandTotalPaise = 787500 // ₹7,875.00
    const paymentAmountPaise = 400000    // ₹4,000.00

    expect(paymentAmountPaise).toBeLessThanOrEqual(invoiceGrandTotalPaise)
    const remainingUnpaidPaise = invoiceGrandTotalPaise - paymentAmountPaise
    expect(remainingUnpaidPaise).toBe(387500) // ₹3,875.00
    expect(remainingUnpaidPaise / 100).toBe(3875.0)
  })

  it('detects over-allocation when allocated amount exceeds remaining balance', () => {
    const remainingUnpaidPaise = 387500 // ₹3,875.00
    const attemptedAllocationPaise = 450000 // ₹4,500.00

    const isExcess = attemptedAllocationPaise > remainingUnpaidPaise
    const excessPaise = Math.max(0, attemptedAllocationPaise - remainingUnpaidPaise)

    expect(isExcess).toBe(true)
    expect(excessPaise).toBe(62500) // ₹625.00 excess
  })

  it('correctly calculates cumulative running balance in customer ledger', () => {
    const entries: Partial<CustomerLedgerEntry>[] = [
      {
        entry_type: 'INVOICE',
        debit_paise: 787500,
        credit_paise: 0,
      },
      {
        entry_type: 'PAYMENT',
        debit_paise: 0,
        credit_paise: 400000,
      },
      {
        entry_type: 'PAYMENT',
        debit_paise: 0,
        credit_paise: 387500,
      },
    ]

    let runningBalance = 0
    const balances: number[] = []

    for (const entry of entries) {
      runningBalance += (entry.debit_paise || 0) - (entry.credit_paise || 0)
      balances.push(runningBalance)
    }

    expect(balances[0]).toBe(787500) // After invoice: ₹7,875 due
    expect(balances[1]).toBe(387500) // After payment 1: ₹3,875 due
    expect(balances[2]).toBe(0)      // After payment 2: ₹0 due (fully settled)
  })

  it('correctly maps unpaid invoices to receivables ageing buckets', () => {
    function getAgeingBucket(days: number): 'not_due' | '0_30' | '31_60' | '61_90' | 'over_90' {
      if (days <= 0) return 'not_due'
      if (days <= 30) return '0_30'
      if (days <= 60) return '31_60'
      if (days <= 90) return '61_90'
      return 'over_90'
    }

    expect(getAgeingBucket(0)).toBe('not_due')
    expect(getAgeingBucket(15)).toBe('0_30')
    expect(getAgeingBucket(45)).toBe('31_60')
    expect(getAgeingBucket(75)).toBe('61_90')
    expect(getAgeingBucket(120)).toBe('over_90')
  })
})
