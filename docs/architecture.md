# FACTORYFLOW System Architecture & Technical Specifications

> **Product:** FACTORYFLOW (kanakkuflow)  
> **Tagline:** From Order to Production. From Stock to Audit.  
> **Evaluation:** Centre for Digital Infrastructure, National Institute of Technology Tiruchirappalli (NIT Trichy).

---

## 1. Executive Architecture Overview

FACTORYFLOW is an integrated, double-entry ERP management system engineered specifically for small-to-medium South Indian food manufacturing facilities (producing packaged snacks including Murukku, Mixture, Banana Chips, Potato Chips, and Traditional Sweets).

The system seamlessly unifies all eight core manufacturing cycles:
1. **Master Data & Tiered Pricing:** Customer, supplier, recipe BOM, and SKU catalogs with automatic price-list inheritance.
2. **Purchasing & GRN:** Supplier purchase orders, Goods Received Notes (GRN), and moving weighted-average inventory valuation.
3. **Recipe BOM & Material Issuance:** High-precision recipe requirements engine with standard batch yield scaling.
4. **Production Run & Variance Analysis:** Atomic floor execution recording actual good output, damaged packaging, wastage, and variance alerts.
5. **Sales Orders & GST Invoicing:** Multi-tier salesman order entry, approval workflows, and intra-state/inter-state GST invoice engine.
6. **Dispatch & Stock Reduction:** Physical finished goods stock reduction strictly deferred until physical delivery dispatch.
7. **Customer Payments & Receivables Ageing:** Multi-invoice allocation, FIFO/manual matching, and 0–30, 31–60, 61–90, >90 day ageing.
8. **Double-Entry General Ledger & Statutory Audit:** Real-time Chart of Accounts, auto-balancing journal entries, and 1-click GSTR-1, GSTR-2, Stock Ledger, and Trial Balance exports.

```
                    ┌─────────────────────────┐
                    │    Offline Mobile PWA   │
                    │   (Dexie / IndexedDB)   │
                    └────────────┬────────────┘
                                 │ Background Sync
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend API                           │
├────────────────────────────────────────────────────────────────────────┤
│  [Auth & RBAC]   [Sales & GST]    [Production & BOM]   [Accounting]   │
│  [Master Data]   [Dispatch Engine][Inventory Valuation][Report Engine] │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 16 Database                          │
├────────────────────────────────────────────────────────────────────────┤
│  • Immutable Stock Movements Ledger    • Chart of Accounts & Journals  │
│  • Sales Orders & GST Invoices         • Customer Balances & Ageing    │
│  • Recipe BOM & Production Runs        • Immutable Audit Trail Logs    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fundamental Architectural Invariants

### Invariant 1: Integer Currency Representation (`BIGINT` Paise)
Floating-point arithmetic is strictly prohibited across all financial calculations.
- Every currency amount in the database is stored as an integer representing paise (1 INR = 100 paise).
- Example: ₹7,875.00 is stored as `787500`.
- Conversions to rupees occur strictly at the presentation layer via `amount_paise / 100`.
- All rounding uses banker's rounding (`ROUND_HALF_UP`) with explicit Decimal precision.

### Invariant 2: High-Precision Quantity Representation (`NUMERIC(14,4)`)
Physical quantities for raw materials, bulk cooking oil, spices, and packaging are stored with 4 decimal digits of precision (`Numeric(14,4)` in PostgreSQL and Python `Decimal`).
- Grams, kilograms, millilitres, and litres are converted deterministically using exact conversion factors (e.g. 1 kg = 1000.0000 g).

### Invariant 3: Single Source of Truth Stock Movement Ledger
Inventory balances are **never manually overwritten or updated directly**.
- Physical stock is strictly computed from append-only `StockMovement` records.
- Movement types:
  - `OPENING_STOCK`: Initial stock initialization.
  - `PURCHASE_RECEIPT`: Inward GRN purchase voucher.
  - `PRODUCTION_ISSUE`: Raw materials and packaging consumed on the factory floor.
  - `PRODUCTION_RECEIPT`: Finished goods output added from completed production runs.
  - `INVOICE_DISPATCH`: Finished goods stock reduction upon verified physical dispatch.
  - `STOCK_ADJUSTMENT`: Cycle count reconciliation adjustments.

### Invariant 4: Commercial Invoicing vs Physical Stock Reduction
- Generating and posting a GST Sales Invoice **does NOT deduct physical inventory**.
- Inventory is deducted **exclusively when a Dispatch Note is posted**, preventing inventory desynchronization when orders are approved in advance of transport availability.

### Invariant 5: Strict Double-Entry Accounting Equality
Every business event generates a balanced Journal Entry where:
$$\sum \text{Debit Amounts} = \sum \text{Credit Amounts}$$
- Trial Balance automatically validates `grand_total_debit_paise == grand_total_credit_paise` and `difference_paise == 0`.

---

## 3. Technology Stack Specification

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Runtime** | Python | 3.12 / 3.14 | Modern async backend runtime |
| **API Framework** | FastAPI | 0.110.0 | High-performance OpenAPI REST endpoints |
| **ORM & Database** | SQLAlchemy | 2.0.28 | Declarative type-safe database mapping |
| **Database Engine** | PostgreSQL | 16-alpine | Enterprise relational storage with ACID guarantees |
| **Migrations** | Alembic | 1.13.1 | Version-controlled schema migrations |
| **Validation** | Pydantic | 2.6.0 | Strict request/response payload validation |
| **Frontend Framework** | React | 18.3.1 | Component-based reactive UI |
| **Build Tooling** | Vite | 5.2.11 | Fast ESM compilation and asset bundling |
| **Type Safety** | TypeScript | 5.4.5 | Static typing across full frontend code |
| **UI Styling** | Tailwind CSS | 3.4.3 | Utility-first responsive design |
| **Client Storage** | Dexie.js | 4.0.4 | IndexedDB wrapper for mobile offline PWA |
| **PWA Service** | vite-plugin-pwa | 0.20.5 | Service worker, manifest, and offline caching |
| **PDF Reporting** | ReportLab | 4.1.0 | Vector PDF invoice, challan, and ledger generation |
| **Spreadsheets** | openpyxl | 3.1.2 | Financial XLSX exports |
