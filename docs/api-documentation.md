# FACTORYFLOW API Documentation & Endpoint Reference

All endpoints are served by FastAPI and automatically documented in interactive Swagger UI at `/docs` and ReDoc at `/redoc`.

---

## 1. Authentication & Users (`/auth`)

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `POST` | `/auth/login` | Public | Authenticates credentials and returns JWT access token. |
| `GET` | `/auth/me` | Authenticated | Returns current authenticated user profile and assigned role. |

---

## 2. Master Data Management

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `GET` / `POST` | `/customers` | Owner, Admin, Salesman | List active customers or create customer with GSTIN validation. |
| `GET` / `PUT` | `/customers/{id}` | Owner, Admin, Salesman | Retrieve or update customer details and credit limit. |
| `GET` / `POST` | `/suppliers` | Owner, Admin, Production | List suppliers or register a new material vendor. |
| `GET` / `POST` | `/products` | Owner, Admin, Production | List finished goods or create new snack SKU. |
| `GET` / `POST` | `/raw-materials` | Owner, Admin, Production | List raw materials or register new ingredients. |
| `GET` / `POST` | `/packaging` | Owner, Admin, Production | List packaging materials or register pouches/cartons. |
| `GET` / `POST` | `/price-lists` | Owner, Admin | Manage tiered pricing catalogs. |

---

## 3. Inventory & Purchase Management

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `POST` | `/inventory/opening-stock` | Owner, Admin | Initialize opening inventory balances with unit costs in paise. |
| `GET` | `/stock/summary/{item_type}/{item_id}` | All Roles | Query current on-hand stock balance. |
| `GET` | `/stock/valuation/{item_type}/{item_id}` | Owner, Admin, Auditor | Compute moving weighted-average valuation. |
| `GET` | `/stock/movements` | Owner, Admin, Auditor | Fetch immutable chronological inventory movement ledger. |
| `POST` | `/purchases` | Owner, Admin, Production | Create draft purchase order / GRN inward. |
| `POST` | `/purchases/{id}/post` | Owner, Admin, Production | Post purchase receipt: increases inventory and updates moving average cost. |

---

## 4. Recipe BOM & Manufacturing

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `GET` / `POST` | `/boms` | Owner, Admin, Production | List or create recipe BOM with batch yield and tolerance %. |
| `POST` | `/boms/{id}/activate` | Owner, Admin | Set BOM status to ACTIVE (one active BOM per product). |
| `POST` | `/production-runs` | Owner, Admin, Production | Record floor production batch with actual materials and good output. |
| `GET` | `/production-runs/{id}/variance` | Owner, Admin, Production | Compute yield and ingredient variance percentages with alert status. |
| `GET` | `/production-runs/{id}/costing` | Owner, Admin, Production | Calculate total production cost and unit cost per packet in paise. |
| `POST` | `/production-runs/{id}/post` | Owner, Admin, Production | Atomically deduct materials and increment finished goods stock. |

---

## 5. Sales, Dispatch & GST Invoicing

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `GET` | `/sales/check-stock` | All Roles | Check FG stock availability without deducting stock. |
| `POST` | `/sales/orders` | Owner, Admin, Salesman | Create Sales Order in `DRAFT` status. |
| `POST` | `/sales/orders/{id}/submit` | Owner, Admin, Salesman | Submit order for admin verification. |
| `POST` | `/sales/orders/{id}/approve` | Owner, Admin | Admin approval of order. |
| `POST` | `/sales/invoices` | Owner, Admin | Generate and post GST Tax Invoice (Intra/Inter state tax breakdown). |
| `GET` | `/sales/invoices/{id}/pdf` | All Roles | Download official GST Tax Invoice PDF. |
| `POST` | `/dispatches` | Owner, Admin, Production | Create delivery dispatch challan with vehicle details. |
| `POST` | `/dispatches/{id}/post` | Owner, Admin, Production | Post dispatch: atomically reduces finished goods stock. |
| `GET` | `/dispatches/{id}/pdf` | All Roles | Download official Delivery Challan PDF. |

---

## 6. Payments, Receivables & Customer Ledger

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `POST` | `/payments` | Owner, Admin, Salesman | Record customer payment and allocate against posted invoices. |
| `GET` | `/payments/ledger/{customer_id}` | All Roles | Generate customer running ledger statement with debit/credit balance. |
| `GET` | `/payments/receivables/ageing` | Owner, Admin, Auditor | Receivables ageing report (0-30, 31-60, 61-90, >90 days). |
| `GET` | `/payments/{id}/receipt` | All Roles | Download formal Payment Receipt PDF. |

---

## 7. Accounting, Audit & Report Exports

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `GET` | `/accounting/accounts` | All Roles | List full Chart of Accounts. |
| `GET` | `/accounting/trial-balance` | Owner, Admin, Auditor | Generate real-time Trial Balance with zero-difference validation. |
| `GET` | `/accounting/ledger/{account_id}` | Owner, Admin, Auditor | General Ledger account statement. |
| `GET` | `/accounting/audit-logs` | Owner, Admin, Auditor | Immutable audit log trail. |
| `GET` | `/analytics/dashboard-summary` | Owner, Admin | Executive KPI metrics across sales, production, inventory, and finance. |
| `GET` | `/reports/gstr1` | Owner, Admin, Auditor | Export GSTR-1 Sales Register (CSV, XLSX, PDF). |
| `GET` | `/reports/gstr2` | Owner, Admin, Auditor | Export GSTR-2 Purchase Register (CSV, XLSX, PDF). |
| `GET` | `/reports/stock-movement` | Owner, Admin, Auditor | Export Stock Movement Ledger (CSV, XLSX, PDF). |
| `GET` | `/reports/production-yield` | Owner, Admin, Auditor | Export Production Yield Variance Report (CSV, XLSX, PDF). |
| `GET` | `/reports/receivables-ageing` | Owner, Admin, Auditor | Export Receivables Ageing Analysis (CSV, XLSX, PDF). |
| `GET` | `/reports/trial-balance` | Owner, Admin, Auditor | Export Financial Trial Balance (CSV, XLSX, PDF). |

---

## 8. Mobile PWA & Offline Sync (`/sync`)

| Method | Endpoint | Allowed Roles | Description |
|---|---|---|---|
| `GET` | `/sync/reference-data` | Salesman, Admin, Owner | Download active customers and products for local IndexedDB caching. |
| `POST` | `/sync/orders` | Salesman, Admin, Owner | Synchronize queued offline orders with client UUID idempotency protection. |
