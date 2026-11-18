# FACTORYFLOW (kanakkuflow)

**Integrated Order-to-Audit Management System for a Small Food Manufacturer**  
*Internship Challenge – Centre for Digital Infrastructure, National Institute of Technology Tiruchirappalli (NIT Trichy)*

[![Backend Tests](https://img.shields.io/badge/pytest-45%20passed-brightgreen.svg)](backend/app/tests)
[![Frontend Tests](https://img.shields.io/badge/vitest-29%20passed-brightgreen.svg)](frontend/src/tests)
[![Benchmark](https://img.shields.io/badge/NIT%20Trichy%20Benchmark-Verified%20100%25-blue.svg)](docs/benchmark-results.md)
[![PWA](https://img.shields.io/badge/PWA-Offline%20Ready-orange.svg)](frontend)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-blue.svg)](docker-compose.yml)

---

## 1. Project Vision & Architecture
FACTORYFLOW is a production-grade, double-entry ERP platform engineered specifically for South Indian snack and traditional food manufacturing (producing Murukku, Mixture, Banana Chips, Potato Chips, and Traditional Sweets).

The system connects the entire operational business lifecycle:
$$\text{Master Data} \longrightarrow \text{Purchasing} \longrightarrow \text{Inventory} \longrightarrow \text{BOM} \longrightarrow \text{Production} \longrightarrow \text{Sales} \longrightarrow \text{GST Invoices} \longrightarrow \text{Dispatch} \longrightarrow \text{Payments} \longrightarrow \text{Accounting} \longrightarrow \text{Audit} \longrightarrow \text{Reports}$$

### Core Operational Cycles
1. **Sales & Dispatch Cycle:**  
   Salesman Booking (Mobile PWA) $\rightarrow$ Order Placement $\rightarrow$ Admin Review $\rightarrow$ GST Tax Invoice (Intra/Inter state) $\rightarrow$ Physical Dispatch Challan $\rightarrow$ Atomic Stock Reduction.
2. **Manufacturing & Costing Cycle:**  
   Supplier Purchase (GRN) $\rightarrow$ Moving Weighted-Average Valuation $\rightarrow$ Recipe BOM $\rightarrow$ Material Issuance $\rightarrow$ Floor Batch Execution $\rightarrow$ Actual Good Output & Waste $\rightarrow$ Yield Variance Analysis (Tolerance Warning) $\rightarrow$ Unit Cost per Packet.
3. **Double-Entry Financial & Audit Cycle:**  
   Automated Journal Entries $\rightarrow$ Customer Ledger Running Balances $\rightarrow$ Receivables Ageing (0-30, 31-60, 61-90, >90 days) $\rightarrow$ Real-time Balanced Trial Balance $\rightarrow$ 1-Click Audit Exports (GSTR-1, GSTR-2, Stock Ledger, Trial Balance in CSV, Excel, PDF).

---

## 2. Non-Negotiable Engineering Rules & Invariants

- **Integer Currency Representation (`BIGINT` Paise):** Stored strictly as integer paise. Zero floating-point rounding errors.
- **High-Precision Quantities (`NUMERIC(14,4)`):** Raw materials, cooking oil, spices, and packaging track 4 decimal places of precision using Python `Decimal`.
- **Single Source of Truth Stock Ledger:** Physical stock balances are never manually updated; they are derived from append-only `StockMovement` records.
- **Invoicing vs Dispatch Separation:** Generating a commercial GST invoice does **not** deduct physical inventory. Inventory is deducted **exclusively upon physical dispatch**.
- **Double-Entry Accounting Equality:** Every transaction automatically enforces:
  $$\sum \text{Debit Amounts} = \sum \text{Credit Amounts}$$
- **Offline-First PWA:** Salesmen can book customer orders in rural areas without network connectivity. Orders are persisted in IndexedDB (Dexie) and synchronized via background idempotency keys.

---

## 3. Technology Stack

- **Backend:** Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Alembic / PostgreSQL 16 / Pydantic v2 / bcrypt / JWT / ReportLab / openpyxl / pytest
- **Frontend:** React 18 / Vite 5 / TypeScript / Tailwind CSS / TanStack Query / React Hook Form / Zod / Lucide React / Recharts / Dexie.js / vite-plugin-pwa / Vitest
- **Infrastructure:** Docker / Docker Compose / Nginx Reverse Proxy / PostgreSQL 16-alpine

---

## 4. NIT Trichy Benchmark Verification Summary

The benchmark scenario is fully automated and verified in `backend/app/tests/test_e2e_benchmark_workflow.py`:

| Stage | Benchmark Operation | System Output / Assertion | Status |
|---|---|---|:---:|
| **Step A** | Raw Material Purchases (Flour, Oil, Spices, Pouches, Boxes) | Positive ledger balance & weighted average rate | **PASSED** |
| **Step B** | Murukku 200g BOM Recipe (250 pkts target) | Verified standard recipe requirements | **PASSED** |
| **Step C** | Floor Batch Execution with Actual Yield | **238 packets output**, -4.8% yield variance (`WARNING`) | **PASSED** |
| **Step D** | Sales Order & GST Invoice (Retailer A: 150 pkts @ ₹50) | Taxable ₹7,500 + 5% GST (₹375) = **₹7,875 total**; FG stock remains 238 | **PASSED** |
| **Step E** | Delivery Dispatch Execution | Stock atomically drops $238 - 150 =$ **88 packets** | **PASSED** |
| **Step F** | Stock Shortage Detection (Distributor B: 120 pkts) | Shortage of **32 pkts** detected; fulfilled 88 pkts; stock = **0 pkts** | **PASSED** |
| **Step G** | Partial Payment (Retailer A: ₹4,000 paid) | Customer Ledger closing balance = **₹3,875 outstanding** (0-30 days) | **PASSED** |
| **Step H** | Double-Entry Trial Balance & Audit Trail | Debits = Credits = **₹12,495.00** (`is_balanced = True`, 0 diff) | **PASSED** |

---

## 5. Quick Start & Execution

### Option A: Docker Compose (Production Ready)
```bash
# 1. Clone repository
git clone https://github.com/your-username/kanakkuflow.git
cd kanakkuflow

# 2. Copy environment file
cp .env.example .env

# 3. Build & start all containers
docker compose up -d --build
```
- **Web App (Frontend PWA):** [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

### Option B: Local Development

```bash
# Backend
python -m venv backend/venv
.\backend\venv\Scripts\activate      # On Windows
pip install -r backend/requirements.txt
pytest backend/app/tests            # Run all 45 backend tests
uvicorn backend.app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm test                            # Run all 29 frontend tests
npm run dev                         # Starts Vite dev server at http://localhost:5173
```

---

## 6. Seeded Demo Accounts & Permissions

| Username | Password | Role | Description |
|---|---|---|---|
| `owner` | `demo123` | `OWNER` | Complete system visibility, executive analytics, statutory reports |
| `admin` | `demo123` | `ADMIN` | Master data administration, price lists, order approval, invoicing |
| `salesA` | `demo123` | `SALESMAN` | Mobile PWA ordering, customer onboarding, offline sync (Tamil Nadu) |
| `salesB` | `demo123` | `SALESMAN` | Mobile PWA ordering, customer onboarding, offline sync (Karnataka) |
| `prod` | `demo123` | `PRODUCTION` | Recipe BOMs, production batch execution, material issue, dispatch |
| `auditor` | `demo123` | `AUDITOR` | Read-only ledger audit, GSTR-1 & GSTR-2 exports, Trial Balance |

---

## 7. Documentation Index

- [System Architecture & Invariants](docs/architecture.md)
- [Database Schema & ER Diagrams](docs/database-schema.md)
- [Comprehensive API Reference](docs/api-documentation.md)
- [NIT Trichy Master Benchmark Results](docs/benchmark-results.md)
- [Production Deployment & Hardening Guide](docs/deployment-guide.md)
