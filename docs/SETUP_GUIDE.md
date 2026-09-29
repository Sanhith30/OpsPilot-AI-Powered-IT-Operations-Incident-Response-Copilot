# OpsPilot — Complete Setup & Installation Guide

This guide provides step-by-step instructions to set up, configure, run, and test OpsPilot on Windows, macOS, Linux, and Docker.

---

## 1. Prerequisites

Ensure the following tools are installed on your machine:
- **Python:** 3.13 or newer (`python --version`)
- **Node.js:** 20.x or newer & npm (`node -v`, `npm -v`)
- **PostgreSQL:** 15.x or newer (local service or via Docker)
- **Git:** 2.40+
- **Docker & Docker Compose:** (Optional, for containerized run)

---

## 2. Option A: Local Native Development Setup

### Step 2.1: Clone the Repository
```bash
git clone https://github.com/OpsPilot/OpsPilot.git
cd OpsPilot
```

### Step 2.2: Backend Virtual Environment & Dependencies
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment:
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Upgrade pip and install all required packages
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.3: Configure Environment Variables
Copy the example environment configuration into `.env`:
```bash
cp .env.example .env
```
Open `.env` and verify/update your local PostgreSQL connection string:
```ini
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/opspilot
JWT_SECRET_KEY=change_this_to_a_long_random_secret_key_at_least_32_bytes_long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Optional API Keys (OpsPilot uses deterministic fallbacks if omitted)
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=opspilot-knowledge
```

### Step 2.4: Database Initialization & Migrations
Ensure your PostgreSQL server is running and create the `opspilot` database if it does not already exist:
```bash
# Example using psql:
psql -U postgres -c "CREATE DATABASE opspilot;"
```
Run the automated sequential migration runner:
```bash
python scripts/run_migrations.py
```
This applies all 6 sequential migrations from `db/migrations/`:
- `001_core_schema.sql`
- `002_core_seed_data.sql`
- `017_knowledge_base.sql`
- `018_investigation_evidence_knowledge_base.sql`
- `019_incident_intelligence.sql`
- `020_remediation_actions.sql`

### Step 2.5: Build and Run Frontend
```bash
cd ../frontend
npm install
npm run build
```
*(Optional) If running the Vite hot-reloading development server:*
```bash
npm run dev
```
Accessible at: `http://localhost:5173/`

### Step 2.6: Launch the Backend Server
```bash
cd ../backend
uvicorn app.main:app --reload --port 8000
```
- **OpsPilot Web UI (Built bundle):** `http://localhost:8000/ui/`
- **Interactive Swagger API Docs:** `http://localhost:8000/docs`
- **Health Check Endpoint:** `http://localhost:8000/health`
- **Prometheus Metrics:** `http://localhost:8000/metrics`

---

## 3. Option B: Complete Docker Compose Setup

Run the entire production stack (PostgreSQL, Backend API, Frontend Nginx, Prometheus, Grafana, OpenTelemetry) with a single command:

```bash
docker-compose up -d --build
```

### Accessing Docker Services
- **Web UI (Nginx):** `http://localhost/`
- **FastAPI Backend:** `http://localhost:8000/`
- **Grafana Dashboards:** `http://localhost:3000/` (Login: `admin` / `admin`)
- **Prometheus:** `http://localhost:9090/`

To view logs or stop the stack:
```bash
docker-compose logs -f
docker-compose down
```

---

## 4. Verification & Testing

### Run Automated Backend Regression Suite (349 Tests)
```bash
cd backend
pytest -v
```
All 349 tests should pass with 100% pass rate.

### Run Automated Smoke Verification Probe
```bash
python scripts/deploy_verify.py --url http://localhost:8000
```

### Run Interactive Terminal Demo
```bash
python scripts/demo_walkthrough.py
```

---

## 5. Troubleshooting Common Issues

### Issue 1: `psycopg.OperationalError: connection to server at "localhost", port 5432 failed`
- **Cause:** PostgreSQL is not running or the password in `.env` is incorrect.
- **Fix:** Start your local PostgreSQL service (`pg_ctl start` or Windows Services), verify you can connect via `psql -U postgres`, and verify `DATABASE_URL` in `.env`.

### Issue 2: `Port 8000 or 5432 already in use`
- **Cause:** Another process or background container is occupying the port.
- **Fix:** Terminate the occupying process or change `PORT=8001` in `.env`.

### Issue 3: `Frontend build fails with npm ERR!`
- **Cause:** Incompatible Node.js version.
- **Fix:** Ensure you are using Node.js 20+ (`node -v`). Delete `frontend/node_modules` and run `npm ci`.
