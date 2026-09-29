<div align="center">

# 🚀 OpsPilot
### Autonomous IT Operations & Incident Response Copilot
**AI-Powered Triaging, LangGraph Multi-Agent Investigation, Grounded RAG, Safe Human-in-the-Loop Remediation, and Immutable Auditing**

[![CI/CD Pipeline](https://github.com/Sanhith30/OpsPilot-AI-Powered-IT-Operations-Incident-Response-Copilot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Sanhith30/OpsPilot-AI-Powered-IT-Operations-Incident-Response-Copilot/actions/workflows/ci.yml)
[![Tests Passing](https://img.shields.io/badge/Tests-435%20Passed%20(100%25)-success?logo=pytest)](docs/TESTING_EVALUATION.md)
[![Live AWS EC2](https://img.shields.io/badge/AWS%20EC2-13.201.38.20%20(ap--south--1)-FF9900?logo=amazon-aws)](http://13.201.38.20)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose%20(6%20Containers)-2496ED?logo=docker)](https://www.docker.com/)

</div>

---

## 📌 Executive Overview

**OpsPilot** is an enterprise-grade AI Operations (AIOps) platform engineered to autonomously triage, investigate, and remediate complex cloud infrastructure and production incidents. 

Rather than relying on ungrounded generative AI chatbots that hallucinate or execute unsafe commands, OpsPilot combines:
1. **LangGraph Multi-Agent Orchestration:** Deterministic cyclic state machine coordinating specialized operational tools (event analysis, deployment correlation, LogHub log pattern search, and vector runbook retrieval).
2. **Grounded RAG with Team-Level Access Control:** Hybrid vector retrieval via Pinecone enforcing strict team ownership boundaries, empirical similarity thresholds (0.65), and citation validation with zero unsupported claims. Includes deterministic mock vector store for isolated CI testing.
3. **Incident Intelligence & Decision Engine:** Correlates disparate signals across microservices, calculates blast radius and impact, estimates escalation risk, and synthesizes root-cause hypotheses with confidence scoring.
4. **Human-in-the-Loop Remediation Gate:** Strict separation of duties between Operators and Incident Managers. Production changes require two-man approval, atomic execution locks, whitelisted safe adapters, and automated post-remediation health verification.
5. **Full Observability & Immutable Audit Trail:** Complete audit logging in PostgreSQL, OpenTelemetry distributed tracing, Prometheus metrics, and Grafana operational dashboards.

---

## 🌐 Live AWS Production Deployment

OpsPilot is actively deployed on **AWS EC2** in `ap-south-1` (Mumbai) running a multi-container Docker Compose stack:

| Component | Endpoint | Description |
| :--- | :--- | :--- |
| **Operations Dashboard** | [http://13.201.38.20/](http://13.201.38.20/) | React Vite SPA with real-time incident triaging & persona switching |
| **Backend REST API** | [http://13.201.38.20/health](http://13.201.38.20/health) | FastAPI core engine with health probes & Swagger docs |
| **Grafana Dashboards** | [http://13.201.38.20:3000/](http://13.201.38.20:3000/) | System metrics & service latency dashboards (`admin` / `admin`) |
| **Prometheus Server** | [http://13.201.38.20:9090/](http://13.201.38.20:9090/) | Time-series metric collection and alert query engine |
| **OpenTelemetry Collector**| `http://13.201.38.20:4318/` | OTLP HTTP/gRPC receiver for distributed traces & service logs |

---

## 🏗️ System Architecture

```text
                                  Internet
                                     │
                     ┌───────────────┴───────────────┐
                     │ Port 80 (HTTP) / Port 443 (TLS)│
                     └───────────────┬───────────────┘
                                     │
                 ┌───────────────────▼───────────────────┐
                 │       AWS EC2 c7i-flex.large          │
                 │   (13.201.38.20 / ap-south-1)         │
                 │                                       │
                 │   ┌───────────────────────────────┐   │
                 │   │     Nginx Reverse Proxy       │   │
                 │   │ (Let's Encrypt TLS / Port 80) │   │
                 │   └───┬───────────────────────┬───┘   │
                 │       │ /                     │ /api/ │
                 │   ┌───▼───────────────┐   ┌───▼───┴───┐
                 │   │ opspilot-frontend │   │ opspilot- │
                 │   │   (React Vite)    │   │  backend  │
                 │   │     Port 80       │   │ Port 8000 │
                 │   └───────────────────┘   └───┬───┬───┘
                 │                               │   │
                 │         ┌─────────────────────┘   │
                 │         ▼                         ▼
                 │   ┌───────────────┐        ┌──────────────┐
                 │   │opspilot-db    │        │  opspilot-   │
                 │   │(PostgreSQL 15)│        │otel-collector│
                 │   └───────────────┘        └──────┬───────┘
                 │                                   │
                 │                     ┌─────────────┴─────────────┐
                 │                     ▼                           ▼
                 │              ┌──────────────┐            ┌──────────────┐
                 │              │  prometheus  │            │   grafana    │
                 │              │ (Port 9090)  │            │ (Port 3000)  │
                 │              └──────────────┘            └──────────────┘
                 └───────────────────────────────────────────────────────┘
```

---

## 🌟 The End-to-End User Journey

OpsPilot tells one coherent operational story from initial telemetry alert to verified resolution:

```text
1. Login                 Operator logs in via JWT with RBAC persona (L1, L2, Manager, Admin).
   ↓
2. Operations Dashboard  Real-time KPI metrics, fleet health, active incidents, and MTTD.
   ↓
3. Incident Triage       Open SEV-1 incident: Payment API database connection timeouts.
   ↓
4. AI Investigation      Trigger LangGraph runner querying incident events, deployments & runbooks.
   ↓
5. Grounded RAG          Inspect Pinecone citations with verified similarity >= 0.65.
   ↓
6. Root Cause & Risk     Intelligence engine identifies rogue commit 9f2c4a1 and 88% escalation risk.
   ↓
7. Remediation Request   L2 Operator requests DEPLOYMENT_ROLLBACK (status: PENDING_APPROVAL).
   ↓
8. Manager Approval      Incident Manager reviews blast radius and approves action (APPROVED).
   ↓
9. Atomic Execution      Whitelisted adapter executes rollback in safe mode (COMPLETED).
   ↓
10. Automated Verify     Post-remediation probes confirm error rate < 0.01% (VERIFIED).
   ↓
11. Incident Resolved    PostgreSQL incident status transitions to MITIGATED.
   ↓
12. Audit Trail          Complete immutable record logged in core.audit_logs.
```

---

## 🔬 Core AI & Safety Invariants

| Invariant | Target | Measured Result | Verification Method |
| :--- | :--- | :--- | :--- |
| **Grounding Rate** | `1.0000` | **`1.0000`** | Every claim verified against retrieved chunks |
| **Citation Validity** | `1.0000` | **`1.0000`** | Hallucinated or non-existent chunk IDs rejected |
| **Unauthorized Leakage** | `0.0000` | **`0.0000`** | Cross-team runbook isolation enforced |
| **Unsupported Claims** | `0.0000` | **`0.0000`** | Non-grounded LLM statements rejected |
| **RAG Threshold** | `0.65` | **`0.65`** | Calibrated threshold sweep across operational runbooks |
| **State Machine Safety** | `STRICT` | **`STRICT`** | Unapproved executions strictly blocked |
| **Full Test Suite** | `435/435` | **`100% PASS`** | Automated pytest regression suite |
| **AWS Golden Path** | `9/9 Steps`| **`100% PASS`** | Live end-to-end production verification script |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.13+
- Node.js 20+
- PostgreSQL 15+

### 1. Clone & Set Up Backend
```bash
git clone https://github.com/Sanhith30/OpsPilot-AI-Powered-IT-Operations-Incident-Response-Copilot.git
cd OpsPilot-AI-Powered-IT-Operations-Incident-Response-Copilot/backend

# Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

### 2. Set Up Database Schema & Seed Data
```bash
python scripts/run_migrations.py
python scripts/seed_test_data.py
```

### 3. Run the Backend API
```bash
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Prometheus metrics: `http://localhost:8000/metrics`

### 4. Run the React Frontend (Dev Server)
```bash
cd ../frontend
npm install
npm run dev
```
- Frontend UI: `http://localhost:5173/`

---

## 🐳 Docker & Production Deployment

### Local Production Simulation (Docker Compose)
Run the entire production stack (PostgreSQL, Backend, Frontend Nginx, Prometheus, Grafana, OpenTelemetry):
```bash
docker compose up -d --build
```
Access points:
- **OpsPilot Frontend (Nginx):** `http://localhost/`
- **OpsPilot Backend (FastAPI):** `http://localhost:8000/`
- **Grafana Dashboards:** `http://localhost:3000/` (admin/admin)
- **Prometheus Metrics:** `http://localhost:9090/`

---

## ⚙️ CI/CD & Automated Deployment

### GitHub Actions Workflows
1. **Continuous Integration (`.github/workflows/ci.yml`)**:
   - Executes Flake8 linting and Bandit security AST scanner.
   - Runs full **435 pytest regression suite** with mock vector store and mock embeddings (zero external API dependencies).
   - Builds frontend SPA bundle with Node.js 20.
   - Builds backend and frontend Docker containers for syntax and build verification.

2. **Continuous Deployment (`.github/workflows/deploy-ec2.yml`)**:
   - Triggered automatically on `main` when CI passes.
   - Connects to AWS EC2 via SSH (`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`).
   - Pulls latest code, runs database migrations, and performs rolling restart via Docker Compose.
   - Validates live `/health` status.

---

## 🧪 Testing & Golden Path Verification

Run the consolidated 435-test regression suite locally:
```bash
cd backend
pytest -v
```

Run the live **AWS Golden Path Verification** against your cloud instance:
```bash
python scripts/aws_golden_path_verify.py --url http://13.201.38.20
```

Verification Output:
```text
====================================================================
         OpsPilot - AWS Production Golden Path Verification         
====================================================================
Step 1: System Health Probe (/health)                 [PASS] (216.0ms) App: OpsPilot
Step 2: Operator Authentication (/auth/login)         [PASS] (304.5ms) JWT token acquired
Step 3: Operator Persona & Context (/auth/me)         [PASS] (102.1ms) User: Arun Kumar
Step 4: Incident Pipeline (/incidents)                [PASS] (102.2ms) 1 active incidents found
Step 5: Incident #1 Events Timeline                   [PASS] (63.8ms) 5 timeline events
Step 6: AI Investigation Copilot (/chat)              [PASS] (1934.9ms) Answer: 1049 chars, 4 tools
Step 7: RAG Knowledge Catalog (/documents)            [PASS] (59.4ms) 4 operational runbooks
Step 8: Dashboard Summary (/dashboard/summary)        [PASS] (92.2ms) Active: 0, Resolved: 0
Step 9: Audit Trail Verification (/audit-logs)        [PASS] (50.2ms) 5 immutable audit records
--------------------------------------------------------------------
Total Steps: 9 | Passed: 9 | Failed: 0 | Avg Latency: 325.0ms
[OK] AWS Golden Path Verification PASSED completely!
```

---

## 👥 Demonstration Personas & Credentials

| Persona | Role | Email | Password | Permissions Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Arun Kumar** | L1 Triage Operator | `arun@opspilot.local` | `OpsPilot@123` | View incidents, search runbooks, view metrics |
| **Priya Sharma** | L2 Systems Engineer | `priya@opspilot.local` | `OpsPilot@123` | Trigger AI investigations, request remediation |
| **Rahul Verma** | Incident Manager | `rahul@opspilot.local` | `OpsPilot@123` | Approve/reject remediations, manage lifecycle |
| **Meena Rao** | Operations Admin | `meena@opspilot.local` | `OpsPilot@123` | Role management, user access, full system oversight |

*You can also switch personas instantly via the **Persona Switcher** dropdown in the top-right navigation bar of the web UI.*

---

## 📖 Comprehensive Documentation Index

| Document | Description |
| :--- | :--- |
| **[Architecture Guide](docs/ARCHITECTURE.md)** | C4 Container models, sequence diagrams, and subsystem design |
| **[Database & Schema](docs/DATABASE.md)** | PostgreSQL relational schema, 23 models, and migration strategy |
| **[AI & LangGraph](docs/AI_LANGGRAPH.md)** | Graph orchestration, tool registry, and decision synthesis |
| **[RAG & Vector Retrieval](docs/RAG.md)** | Pinecone indexing, similarity threshold calibration, and grounding evaluation |
| **[Security & RBAC](docs/SECURITY_RBAC.md)** | JWT auth, role permissions matrix, prompt injection defenses |
| **[API Documentation](docs/API.md)** | Interactive endpoints reference for all subsystems |
| **[Deployment Guide](infra/DEPLOYMENT.md)** | Docker Compose, AWS EC2, GitHub Actions CI/CD, SSL/Certbot, and rollback |
| **[Testing & Evaluation](docs/TESTING_EVALUATION.md)** | 435-test suite report, failure diagnostics, and safety benchmarks |
| **[Live Demo Scenario](docs/DEMO_SCENARIO.md)** | Step-by-step walkthrough script for evaluator presentations |
| **[Presentation Slides](docs/PRESENTATION.md)** | Complete slide deck content and speaker notes for viva |
| **[Setup Guide](docs/SETUP_GUIDE.md)** | Zero-to-running setup guide for Windows, Linux, and macOS |
| **[Final Project Summary](docs/FINAL_PROJECT_SUMMARY.md)** | Complete milestones review and project accomplishments |
| **[Resume & Portfolio](docs/RESUME_PROJECT_DESCRIPTION.md)** | Project bullet points and system design interview questions |

---

<div align="center">
  <sub>Built with ❤️ as an enterprise-grade AI Operations & Autonomous Incident Response Copilot.</sub>
</div>
