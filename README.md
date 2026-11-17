# FACTORYFLOW (kanakkuflow)

**Integrated Order-to-Audit Management System for Small Food Manufacturers**  
*Internship Challenge – Centre for Digital Infrastructure, National Institute of Technology Tiruchirappalli (NIT Trichy)*

---

## 1. Project Vision & Architecture
FACTORYFLOW is a full-stack ERP platform engineered specifically for South Indian snack and traditional food manufacturing (producing Murukku, Mixture, Banana Chips, Potato Chips, and Traditional Sweets).

The system seamlessly unifies three critical operational cycles:
1. **Sales Workflow**: Salesman &rarr; Order Placement &rarr; Admin Review &rarr; GST Invoice &rarr; Dispatch &rarr; Finished Stock Deduction &rarr; Payment &rarr; Receivables Ageing.
2. **Production Workflow**: Supplier Purchase &rarr; Raw Material & Packaging Inventory &rarr; Bill of Materials (BOM) &rarr; Material Issue & Batch Production &rarr; Good Output & Damage Recording &rarr; Yield & Material Variance &rarr; Weighted-Average Costing per Packet.
3. **Audit Workflow**: Immutable Stock Movements + Posted Sales & Purchases + GST Returns + Batch Yields &rarr; Auditor Export Centre (PDF, Excel, CSV).

---

## 2. Technology Stack

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Alembic / PostgreSQL / Pydantic v2 / bcrypt / JWT / pytest
- **Frontend**: React 18 / Vite / TypeScript / Tailwind CSS / TanStack Query / React Hook Form / Zod / Lucide React / Recharts / Dexie.js
- **Document Generation**: ReportLab / openpyxl / Python CSV
- **Infrastructure**: Docker / Docker Compose / PostgreSQL 16

---

## 3. Demo Accounts & Role Permissions

| Username | Password | Role | Responsibilities |
|---|---|---|---|
| `owner` | `demo123` | `OWNER` | Complete executive dashboard, financial margins, production analytics, all reports |
| `admin` | `demo123` | `ADMIN` | Orders inbox, pricing, inventory approval, purchases, GST invoicing, dispatch |
| `salesA` | `demo123` | `SALESMAN` | Mobile PWA ordering, customer catalog, order status (Tamil Nadu territory) |
| `salesB` | `demo123` | `SALESMAN` | Mobile PWA ordering, customer catalog, order status (Karnataka territory) |
| `prod` | `demo123` | `PRODUCTION` | BOM management, production run posting, material issue, yield variance tracking |
| `auditor` | `demo123` | `AUDITOR` | Read-only ledger, GST summaries, sales/purchase registers, audit export centre |

---

## 4. Quick Start & Execution

### Option A: Docker Compose (Recommended)
```bash
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API & Interactive Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Option B: Local Development
```bash
# Backend Setup
python -m venv backend/venv
.\backend\venv\Scripts\activate
pip install -r backend/requirements.txt
pytest backend/app/tests

# Run Backend
uvicorn backend.app.main:app --reload --port 8000

# Frontend Setup
cd frontend
npm install
npm run dev
```

---

## 5. Non-Negotiable Engineering Rules
- **Money Calculations**: Stored strictly as integer paise using `BIGINT`. Never floating-point.
- **Quantity Calculations**: High-precision `NUMERIC(14,4)` and Python `Decimal`.
- **Stock Ledger**: Immutable transaction ledger (`stock_movements`). Balances are always computed from `SUM(qty_delta)`.
- **Traceability**: Every stock delta must be tied to a source document ID.
- **Atomic Operations**: Invoicing, production posting, and stock movements are wrapped inside atomic transactions with zero negative stock violations.
