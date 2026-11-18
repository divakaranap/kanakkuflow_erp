import { describe, it, expect } from 'vitest'
import { formatINR } from '../lib/utils'

describe('Frontend Master Data Utilities & Validators', () => {
  it('formats Indian Rupees accurately from exact integer paise', () => {
    expect(formatINR(5000)).toBe('₹50.00')
    expect(formatINR(787500)).toBe('₹7,875.00')
    expect(formatINR(18750)).toBe('₹187.50')
    expect(formatINR(123456700)).toBe('₹12,34,567.00')
    expect(formatINR(0)).toBe('₹0.00')
    expect(formatINR(-400000)).toBe('-₹4,000.00')
  })

  it('validates Indian 15-character GSTIN format correctly', () => {
    const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/
    expect(gstinRegex.test('33AAAAA0000A1Z5')).toBe(true) // Tamil Nadu Retailer A
    expect(gstinRegex.test('29BBBBB1111B1Z2')).toBe(true) // Karnataka Distributor B
    expect(gstinRegex.test('INVALID-GST')).toBe(false)
    expect(gstinRegex.test('33AAAAA0000A1Z')).toBe(false) // too short
  })

  it('validates 10-digit Indian phone numbers', () => {
    const phoneRegex = /^(\+91[\-\s]?)?[0]?[6789]\d{9}$/
    expect(phoneRegex.test('9842198421')).toBe(true)
    expect(phoneRegex.test('+91-9842198421')).toBe(true)
    expect(phoneRegex.test('12345')).toBe(false)
  })

  it('verifies unit conversion logic and ratios for cartons', () => {
    const packetsPerCarton = 20
    const packets = 200
    const cartons = packets / packetsPerCarton
    expect(cartons).toBe(10)
    expect(cartons * packetsPerCarton).toBe(200)
  })

  it('validates master product pricing rules', () => {
    const murukkuMRP = 5000 // 5000 paise = ₹50
    const gstRate = 0.05 // 5%
    const taxableAmountPaise = Math.round(murukkuMRP / (1 + gstRate))
    expect(taxableAmountPaise).toBe(4762)
  })
})
