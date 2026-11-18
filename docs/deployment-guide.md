# FACTORYFLOW Deployment & Operations Guide

This guide describes how to deploy, configure, run, and maintain FACTORYFLOW in local development and production environments using Docker Compose.

---

## 1. Quickstart with Docker Compose

Ensure Docker and Docker Compose are installed on your host machine.

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/your-username/kanakkuflow.git
cd kanakkuflow
cp .env.example .env
```

Review and adjust `.env` parameters if needed (database credentials, JWT secret key, and port assignments).

### Step 2: Build & Start Services
```bash
docker compose up -d --build
```

This starts:
1. `kanakkuflow-db`: PostgreSQL 16 on port `5432` with healthcheck.
2. `kanakkuflow-backend`: FastAPI application on port `8000`.
3. `kanakkuflow-frontend`: Vite React PWA served via Nginx on port `5173`.

### Step 3: Access Application
- **Frontend PWA:** [http://localhost:5173](http://localhost:5173)
- **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 2. Default Seeded Credentials

| Username | Password | Role | Responsibilities |
|---|---|---|---|
| `owner` | `demo123` | `OWNER` | Complete system access, audit review, and executive analytics |
| `admin` | `demo123` | `ADMIN` | Master data approval, price list updates, user management |
| `salesA` | `demo123` | `SALESMAN` | Order booking, customer onboarding, mobile offline sync |
| `prod` | `demo123` | `PRODUCTION` | BOM creation, material issuance, batch runs, dispatch execution |
| `auditor` | `demo123` | `AUDITOR` | Read-only ledger audit, GSTR-1/GSTR-2 verification, Trial Balance |

---

## 3. Database Migrations

Database schema migrations are managed with Alembic.
```bash
# Apply pending migrations
docker compose exec backend alembic upgrade head

# Generate a new migration
docker compose exec backend alembic revision --autogenerate -m "migration description"
```

---

## 4. Running Automated Tests

### Backend Test Suite (Pytest)
```bash
# Run all 45 automated backend tests
docker compose exec backend pytest backend/app/tests -v
```

### Frontend Test Suite (Vitest)
```bash
# Run all 29 automated frontend tests
cd frontend && npm test
```

---

## 5. Security & Production Hardening

1. **JWT Secret Key:** Replace `SECRET_KEY` in `.env` with a high-entropy 256-bit secret string in production.
2. **CORS Restrictions:** Restrict `CORS_ORIGINS` to trusted enterprise domain names.
3. **Database Security:** Store database passwords in a secret manager or encrypted environment file; do not expose port `5432` to the public internet.
4. **HTTPS / SSL:** Place an SSL reverse proxy (e.g. Traefik, AWS ALB, Cloudflare, or Nginx with Let's Encrypt) in front of the application for TLS termination.
