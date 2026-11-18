# NIT Tiruchirappalli Challenge – Master Benchmark Verification Report

This report presents the verified end-to-end mathematical and operational results from executing the complete 8-stage manufacturing ERP benchmark challenge.

**Test Suite:** `backend/app/tests/test_e2e_benchmark_workflow.py`  
**Status:** **PASSED (100% verified)**

---

## 1. Stage-by-Stage Verification Summary

### Step A: Raw Material Inward & Initial Inventory Valuation
- **Supplier:** Madurai Agro Commodities (GSTIN: `33AABCM1234D1Z5`).
- **Materials Received:**
  - Rice Flour: 100.0000 kg @ ₹40.00/kg = ₹4,000.00 (400,000 paise)
  - Cooking Oil: 50.0000 L @ ₹120.00/L = ₹6,000.00 (600,000 paise)
  - Spice Mix: 10.0000 kg @ ₹150.00/kg = ₹1,500.00 (150,000 paise)
  - Packaging Pouches (200g): 1,000 pcs @ ₹1.50/pc = ₹1,500.00 (150,000 paise)
  - Corrugated Shipping Boxes: 100 pcs @ ₹15.00/box = ₹1,500.00 (150,000 paise)
- **Initial Murukku 200g Stock:** 0 packets.
- **Verification:** All inventory movements booked into immutable `StockMovement` ledger; on-hand balances match purchase quantities.

---

### Step B: Standard BOM Recipe (Murukku 200g)
- **Standard Batch Yield:** 250 packets (50.0000 kg net finished output).
- **Material Standards per Batch:**
  - Rice Flour: 35.0000 kg
  - Cooking Oil: 5.0000 litres
  - Spice Mix: 1.0000 kg
  - Printed Pouches: 250 pieces
  - Corrugated Box: 12.5 pieces (20 pkts/box)
- **BOM Status:** `ACTIVE` (Strictly 1 active BOM per product SKU).

---

### Step C: Production Run with Yield Variance Analysis
- **Batch Executed:** `BATCH-E2E-BENCHMARK-01` (1 Batch).
- **Actual Good Output:** **238 packets** of 200g (Target: 250 packets).
- **Damaged Packaging:** 12 pouches.
- **Yield Variance Calculation:**
  $$\text{Yield Variance \%} = \frac{238 - 250}{250} \times 100 = -4.80\%$$
- **Variance Status:** `WARNING` (Exceeds acceptable floor tolerance).
- **Floor Issuance Stock Deductions:**
  - Rice Flour: $100 - 35 = 65.0000\text{ kg}$
  - Cooking Oil: $50 - 5 = 45.0000\text{ L}$
  - Spice Mix: $10 - 1 = 9.0000\text{ kg}$
  - Printed Pouches: $1000 - 250 = 750\text{ pcs}$
  - Corrugated Boxes: $100 - 12 = 88\text{ boxes}$
- **Finished Goods Stock:** Increased atomically from 0 to **238 packets**.

---

### Step D: Sales Order & GST Invoicing for Retailer A
- **Customer:** Sri Krishna Stores, Madurai (GSTIN: `33AAAAA0000A1Z5`, Intra-state Tamil Nadu).
- **Ordered:** 150 packets @ ₹50.00/packet.
- **GST Calculation (Intra-state 5%):**
  - Taxable Value: $150 \times ₹50.00 = ₹7,500.00$ ($750,000$ paise)
  - CGST (2.5%): $₹187.50$ ($18,750$ paise)
  - SGST (2.5%): $₹187.50$ ($18,750$ paise)
  - IGST: $₹0.00$
  - Total GST: $₹375.00$ ($37,500$ paise)
  - Grand Total: $₹7,875.00$ ($787,500$ paise)
- **Commercial Invariance Verified:** Finished Goods inventory remained at **238 packets** after invoice posting (stock is NOT deducted by invoicing).

---

### Step E: Physical Dispatch & Stock Reduction
- **Dispatch Voucher:** Generated with vehicle number `TN-59-AB-1234` and transporter details.
- **Quantity Dispatched:** 150 packets.
- **Stock Reduction:**
  $$238\text{ packets} - 150\text{ packets} = 88\text{ packets remaining}$$
- **Finished Goods Inventory:** Verified on-hand balance drops to exactly **88 packets**.

---

### Step F: Shortage Prevention & Partial Fulfillment (Distributor B)
- **Customer:** Bengaluru Distributors, Karnataka (State Code 29, Inter-state).
- **Attempted Request:** 120 packets.
- **Shortage Detection:**
  - Available Finished Goods: 88 packets
  - Requested Quantity: 120 packets
  - `is_sufficient = False`
  - Shortage Prevented: **32 packets**
- **Partial Fulfillment:** Order placed and approved for available 88 packets.
- **Dispatch:** Dispatched 88 packets.
- **Final Finished Goods Stock:** Drops from 88 to **0 packets** (zero negative inventory allowed).

---

### Step G: Customer Payment & Receivables Ageing
- **Total Due from Retailer A:** ₹7,875.00 (787,500 paise).
- **Payment Recorded:** ₹4,000.00 (400,000 paise) via NEFT Bank Transfer.
- **Customer Ledger Running Balance:**
  $$\text{Closing Balance} = ₹7,875.00 - ₹4,000.00 = ₹3,875.00\text{ outstanding}$$
- **Invoice Paid Amount:** Updated to ₹4,000.00 with status `PARTIAL`.
- **Receivables Ageing Verification:**
  - Total Outstanding: ₹3,875.00
  - Current (0–30 Days): ₹3,875.00

---

### Step H: Double-Entry Balancing & Audit Trail
- **Trial Balance:**
  - Total Debits: ₹12,495.00 (1,249,500 paise)
  - Total Credits: ₹12,495.00 (1,249,500 paise)
  - Difference: **0 paise**
  - Balance Status: **BALANCED (`is_balanced = True`)**
- **Audit Logs:** Immutable audit records logged with user IDs, timestamps, and entity references.
