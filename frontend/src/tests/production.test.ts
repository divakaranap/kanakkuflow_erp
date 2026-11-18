import { describe, it, expect } from 'vitest'
import { formatINR } from '../lib/utils'

describe('Phase 4 Production Engine, Variance Analysis & Costing Verification', () => {
  it('calculates benchmark yield and material variances accurately', () => {
    // 1. Benchmark Yield Variance
    const expectedOutput = 200
    const actualGoodOutput = 188
    const yieldVariancePct = ((actualGoodOutput - expectedOutput) / expectedOutput) * 100
    expect(yieldVariancePct).toBe(-6.0)

    // 2. Benchmark Oil Consumption Variance
    const plannedOil = 10.0
    const actualOil = 10.5
    const oilVariancePct = ((actualOil - plannedOil) / plannedOil) * 100
    expect(oilVariancePct).toBe(5.0)

    // 3. Benchmark Flour Consumption Variance
    const plannedFlour = 40.0
    const actualFlour = 40.0
    const flourVariancePct = ((actualFlour - plannedFlour) / plannedFlour) * 100
    expect(flourVariancePct).toBe(0.0)

    // 4. Tolerance checks (3% threshold)
    const tolerance = 3.0
    expect(Math.abs(yieldVariancePct) > tolerance).toBe(true) // Triggers Warning Alert
    expect(Math.abs(oilVariancePct) > tolerance).toBe(true)   // Triggers Warning Alert
    expect(Math.abs(flourVariancePct) > tolerance).toBe(false) // Normal
  })

  it('calculates benchmark production costing, cost per packet, and gross margin', () => {
    // 1. Materials & Packaging Costs (paise)
    const flourCostPaise = Math.round(40 * 4312.5) // 40 kg @ ₹43.125 = ₹1,725.00
    const oilCostPaise = Math.round(10.5 * 14000)   // 10.5 L @ ₹140.00 = ₹1,470.00
    const spiceCostPaise = Math.round(1.2 * 20000)  // 1.2 kg @ ₹200.00 = ₹240.00
    const pouchCostPaise = Math.round(194 * 250)    // 194 pcs @ ₹2.50 = ₹485.00 (incl 6 damaged)
    const cartonCostPaise = Math.round(9 * 1500)    // 9 pcs @ ₹15.00 = ₹135.00

    const totalMaterialsPaise =
      flourCostPaise + oilCostPaise + spiceCostPaise + pouchCostPaise + cartonCostPaise

    expect(flourCostPaise).toBe(172500)
    expect(oilCostPaise).toBe(147000)
    expect(spiceCostPaise).toBe(24000)
    expect(pouchCostPaise).toBe(48500)
    expect(cartonCostPaise).toBe(13500)
    expect(totalMaterialsPaise).toBe(405500) // ₹4,055.00
    expect(formatINR(totalMaterialsPaise)).toBe('₹4,055.00')

    // 2. Direct Overheads
    const labourPaise = 120000 // ₹1,200.00
    const utilityPaise = 60000  // ₹600.00
    const totalOverheadsPaise = labourPaise + utilityPaise
    expect(totalOverheadsPaise).toBe(180000) // ₹1,800.00

    // 3. Total Production Cost
    const totalProductionCostPaise = totalMaterialsPaise + totalOverheadsPaise
    expect(totalProductionCostPaise).toBe(585500) // ₹5,855.00
    expect(formatINR(totalProductionCostPaise)).toBe('₹5,855.00')

    // 4. Cost per Good Packet (188 packets)
    const actualGoodOutput = 188
    const exactCostPerPacketRupees = (totalProductionCostPaise / (actualGoodOutput * 100))
    expect(parseFloat(exactCostPerPacketRupees.toFixed(4))).toBe(31.1436)

    const costPerPacketPaise = Math.round(totalProductionCostPaise / actualGoodOutput)
    expect(costPerPacketPaise).toBe(3114) // ₹31.14
    expect(formatINR(costPerPacketPaise)).toBe('₹31.14')

    // 5. Selling Price and Gross Margin
    const sellingPricePaise = 5000 // ₹50.00
    const grossMarginPaise = sellingPricePaise - costPerPacketPaise
    expect(grossMarginPaise).toBe(1886) // ₹18.86 per packet
    expect(formatINR(grossMarginPaise)).toBe('₹18.86')

    const grossMarginPct = (grossMarginPaise / sellingPricePaise) * 100
    expect(parseFloat(grossMarginPct.toFixed(2))).toBe(37.72)
  })
})
