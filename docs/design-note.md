# FACTORYFLOW (kanakkuflow) – Engineering Design Note

## Production Engine, BOM Management, Variance Analysis & Costing (Phase 4)

### 1. Architectural Overview & Manufacturing Life Cycle
FACTORYFLOW connects the entire food manufacturing lifecycle with an immutable ledger-first architecture:
```
Product Definition ──> Active BOM (Recipe) ──> Scaling (Batch Multiplier)
                                                       │
                                                       ▼
Actual Consumption <── Production Run (Execution) <── Material Check
        │
        ├─ Good Finished Goods Output ────> Stock Movement (+PRODUCTION_OUTPUT)
        ├─ Consumed Raw/Packaging ────────> Stock Movement (-PRODUCTION_ISSUE)
        ├─ Damaged Packaging/Scrap ───────> Stock Movement (-PRODUCTION_SCRAP)
        │
        ▼
Variance Analysis Engine ─────────────────> Yield & Consumption Tolerance Checks (±3.00%)
        │
        ▼
Costing & Margin Engine ──────────────────> Weighted-Average Valuation + Direct Overheads
```

---

### 2. Bill of Materials (BOM) Architecture
- **Versioning & Single Active Constraint**:
  Each Product may have multiple versions of BOMs (e.g., v1, v2) for recipe experimentation and seasonal spice adjustments. However, at most **one BOM per product** may be in `ACTIVE` status at any given time.
- **BOM Snapshotting**:
  When a production run is created, a point-in-time JSON snapshot (`bom_snapshot`) of the active BOM structure, items, yields, and tolerances is captured in the `production_runs` table. If the product recipe is revised in the future, historical production runs remain immutable and auditable.
- **Linear Scaling**:
  For an arbitrary batch count $N$, planned material requirement is:
  $$\text{Planned Qty}_i = N \times \text{QuantityPerBatch}_i$$
  $$\text{Expected Output} = N \times \text{BatchYieldPackets}$$

---

### 3. Inventory Ledger Integration & Packaging Damage Treatment
Every production posting operates inside an **atomic PostgreSQL transaction** with row-level locks on `inventory_balances`:
1. **Raw Material & Normal Packaging Consumption**:
   Recorded as `movement_type = 'PRODUCTION_ISSUE'` with negative quantity $\Delta = -\text{consumed\_qty}$.
2. **Damaged Packaging Treatment**:
   In high-speed food packaging lines, pouch tearing or sealing defects occur. Damaged packaging is recorded as `movement_type = 'PRODUCTION_SCRAP'` with negative quantity $\Delta = -\text{damaged\_qty}$.
   - **Audit separation**: Normal consumption vs scrap are distinct ledger rows with independent audit trail markers.
   - **Net stock deduction**: Net packaging deducted from inventory is $\text{good\_qty} + \text{damaged\_qty}$.
   - **Cost absorption**: The financial cost of scrapped packaging is fully absorbed into the production cost of good packets produced.
3. **Finished Goods Output**:
   Recorded as `movement_type = 'PRODUCTION_OUTPUT'` with positive quantity $\Delta = +\text{actual\_good\_output}$.
4. **Negative Stock Prevention**:
   If available stock on hand < consumed quantity, the transaction raises `400 Bad Request` and rolls back atomically.

---

### 4. Moving Weighted-Average Valuation
To eliminate sub-paise truncation and floating-point errors:
1. `inventory_balances` maintains `cached_qty` (Decimal) and `total_value_paise` (Integer `BIGINT`).
2. Exact rate per unit is derived dynamically as:
   $$\text{Rate}_{\text{exact}} = \frac{\text{total\_value\_paise}}{\text{cached\_qty}}$$
3. Total line item material cost:
   $$\text{LineCost}_{\text{paise}} = \text{round}\left(\text{Rate}_{\text{exact}} \times \text{ConsumedQty}\right)$$

---

### 5. Variance Analysis Formulas & Threshold Logic
For every posted run:
1. **Material Consumption Variance %**:
   $$\text{Variance \%} = \frac{\text{Actual Qty} - \text{Planned Qty}}{\text{Planned Qty}} \times 100$$
   - A positive variance means excess material was used (over-consumption).
   - A negative variance means less material was used.
2. **Yield Variance %**:
   $$\text{Yield Variance \%} = \frac{\text{Actual Good Output} - \text{Expected Output}}{\text{Expected Output}} \times 100$$
   - A negative yield variance means production fell short of expected output.
3. **Tolerance Alert Classification**:
   - `NORMAL`: $|\text{Variance \%}| \le \text{Tolerance \%}$ (default $\le 3.00\%$).
   - `WARNING`: $|\text{Variance \%}| > \text{Tolerance \%}$ (triggers audit warning notification).

---

### 6. Production Costing & Margins
1. **Total Production Cost**:
   $$\text{Total Cost}_{\text{paise}} = \sum \text{LineCost}_{\text{materials}} + \sum \text{Overhead}_{\text{direct}}$$
2. **Cost per Good Packet**:
   $$\text{CostPerPacket}_{\text{paise}} = \left\lfloor \frac{\text{Total Cost}_{\text{paise}}}{\text{Actual Good Output}} \right\rfloor$$
   $$\text{CostPerPacket}_{\text{decimal}} = \frac{\text{Total Cost}_{\text{paise}}}{\text{Actual Good Output} \times 100} \text{ (Rupees)}$$
3. **Gross Margin per Packet**:
   $$\text{Gross Margin}_{\text{paise}} = \text{SellingPrice}_{\text{paise}} - \text{CostPerPacket}_{\text{paise}}$$
   $$\text{Gross Margin \%} = \frac{\text{Gross Margin}_{\text{paise}}}{\text{SellingPrice}_{\text{paise}}} \times 100$$

---

### 7. Phase 4 Benchmark Validation Results

The NIT Trichy Phase 4 benchmark test (`test_murukku_production_run_benchmark`) executes the complete Murukku 200g production cycle:

| Metric | Expected Benchmark | System Result | Status |
|---|---|---|---|
| **Flour Weighted Avg Cost** | 100 kg @ ₹42 + 60 kg @ ₹45 $\to$ ₹43.125/kg | 4312.5 paise/kg (₹43.125) | PASS |
| **Flour Consumption** | 40 kg @ ₹43.125 | 172,500 paise (₹1,725.00) | PASS |
| **Oil Consumption** | 10.5 L @ ₹140.00 | 147,000 paise (₹1,470.00) | PASS |
| **Spice Mix Consumption** | 1.2 kg @ ₹200.00 | 24,000 paise (₹240.00) | PASS |
| **Pouches Deduction** | 194 pcs (188 good + 6 damaged) @ ₹2.50 | 48,500 paise (₹485.00) | PASS |
| **Cartons Consumption** | 9 pcs @ ₹15.00 | 13,500 paise (₹135.00) | PASS |
| **Total Material Cost** | ₹4,055.00 | 405,500 paise | PASS |
| **Direct Overheads** | Labour ₹1,200 + Gas ₹600 = ₹1,800.00 | 180,000 paise | PASS |
| **Total Production Cost** | ₹5,855.00 | 585,500 paise (₹5,855.00) | PASS |
| **Good Packets Output** | 188 packets | 188 packets | PASS |
| **Damaged Pouches** | 6 pieces | 6 pieces | PASS |
| **Cost Per Good Packet** | ₹31.14 (3114 paise) | 3114 paise (₹31.14) | PASS |
| **Selling Price (MRP)** | ₹50.00 (5000 paise) | 5000 paise (₹50.00) | PASS |
| **Gross Margin / Packet** | ₹18.86 (1886 paise, 37.72%) | 1886 paise (37.72%) | PASS |
| **Yield Variance** | -6.00% (Shortfall of 12 pkts) | -6.00% | PASS (WARNING Alert) |
| **Oil Variance** | +5.00% (Excess 0.5 L) | +5.00% | PASS (WARNING Alert) |
| **Flour & Spice Variance**| 0.00% | 0.00% | PASS (NORMAL) |
| **Post-run Flour Stock** | 120.00 kg | 120.00 kg | PASS |
| **Post-run Oil Stock** | 19.50 L | 19.50 L | PASS |
| **Post-run Pouches Stock**| 306 pcs | 306 pcs | PASS |
| **Post-run Murukku FG** | 238 pkts (50 opening + 188 output) | 238 pkts | PASS |
