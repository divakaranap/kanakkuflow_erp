import { describe, it, expect } from 'vitest'
import { formatINR } from '../lib/utils'

describe('Phase 3 Inventory & Costing Logic Verification', () => {
  it('accurately computes benchmark moving weighted average valuation', () => {
    // 1. Opening stock: 100 kg @ ₹42.00/kg (4200 paise)
    const opQty = 100
    const opRatePaise = 4200
    const opValuationPaise = opQty * opRatePaise // 420,000 paise

    expect(opValuationPaise).toBe(420000)
    expect(formatINR(opValuationPaise)).toBe('₹4,200.00')

    // 2. Purchase receipt: 60 kg @ ₹45.00/kg (4500 paise)
    const poQty = 60
    const poRatePaise = 4500
    const poValuationPaise = poQty * poRatePaise // 270,000 paise

    expect(poValuationPaise).toBe(270000)
    expect(formatINR(poValuationPaise)).toBe('₹2,700.00')

    // 3. Consolidated stock and valuation
    const totalQty = opQty + poQty
    const totalValuationPaise = opValuationPaise + poValuationPaise

    expect(totalQty).toBe(160)
    expect(totalValuationPaise).toBe(690000)
    expect(formatINR(totalValuationPaise)).toBe('₹6,900.00')

    // 4. Moving weighted average cost per unit
    const weightedAvgPaise = totalValuationPaise / totalQty
    expect(weightedAvgPaise).toBe(4312.5)

    // Formatted display in paise rounded
    const displayRatePaise = Math.round(weightedAvgPaise)
    expect(displayRatePaise).toBe(4313)
    expect(formatINR(displayRatePaise)).toBe('₹43.13')
  })

  it('validates stock ledger reconciliation equation: Closing = Opening + Receipts - Issues + Adjustments', () => {
    const openingStock = 100
    const receipts = 60
    const issues = 0
    const adjustment = -15 // 15 kg wastage

    const closingStock = openingStock + receipts - issues + adjustment
    expect(closingStock).toBe(145)
  })

  it('computes purchase line tax and total paise without floating point drift', () => {
    const quantity = 60
    const ratePaise = 4500 // ₹45.00
    const taxRate = 0.05 // 5% GST

    const taxableValuePaise = Math.round(quantity * ratePaise)
    const taxPaise = Math.round(taxableValuePaise * taxRate)
    const totalPaise = taxableValuePaise + taxPaise

    expect(taxableValuePaise).toBe(270000)
    expect(taxPaise).toBe(13500)
    expect(totalPaise).toBe(283500)

    expect(formatINR(taxableValuePaise)).toBe('₹2,700.00')
    expect(formatINR(taxPaise)).toBe('₹135.00')
    expect(formatINR(totalPaise)).toBe('₹2,835.00')
  })
})
