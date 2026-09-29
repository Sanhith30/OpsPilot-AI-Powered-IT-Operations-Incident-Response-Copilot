<div align="center">

# 🚀 OpsPilot
### Autonomous IT Operations & Incident Response Copilot
**AI-Powered Triaging, LangGraph Multi-Agent Investigation, Grounded RAG, Safe Human-in-the-Loop Remediation, and Immutable Auditing**

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?logo=github-actions)](https://github.com/OpsPilot/OpsPilot)
[![Tests Passing](https://img.shields.io/badge/Tests-349%20Passed%20(100%25)-success?logo=pytest)](docs/TESTING_EVALUATION.md)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Multi--stage-2496ED?logo=docker)](https://www.docker.com/)
[![AWS Fargate](https://img.shields.io/badge/AWS-ECS%20Fargate%20%2B%20Terraform-FF9900?logo=amazon-aws)](https://aws.amazon.com/)

</div>

---

## 📌 Executive Overview

**OpsPilot** is an enterprise-grade AI Operations platform engineered to autonomously triage, investigate, and remediate complex cloud infrastructure and production incidents. 

Rather than relying on ungrounded generative AI chatbots that hallucinate or execute unsafe commands, OpsPilot combines:
1. **LangGraph Multi-Agent Orchestration:** Deterministic state machine coordinating specialized operational tools (event analysis, deployment correlation, and vector runbook retrieval).
2. **Grounded RAG with Team-Level Access Control:** Vector retrieval via Pinecone enforcing strict team ownership boundaries, empirical similarity thresholds (0.65), and citation validation with zero unsupported claims.
3. **Incident Intelligence & Decision Engine:** Correlates disparate signals, calculates blast radius and impact, estimates escalation risk, and synthesizes root-cause hypotheses.
4. **Human-in-the-Loop Remediation Gate:** Strict separation of duties between Operators and Incident Managers. Production changes require human approval, atomic execution locks, whitelisted safe adapters, and automated post-remediation health verification.
5. **Full Observability & Immutable Audit Trail:** Complete audit logging in PostgreSQL, OpenTelemetry distributed tracing, Prometheus metrics, and Grafana dashboards.

---

## 🏗️ System Architecture

```text
                                     React 18 + Vite Frontend
                                 (Dashboard, Triage, Remediation)
                                                │
                                                ▼
                                    FastAPI Application Gateway
                              (OWASP Security Headers, Rate Limiting)
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
      JWT Authentication / RBAC       PostgreSQL 15 (Relational)    OpenTelemetry & Prometheus
     (L1, L2, Manager, Admin)        (Core Incidents, Audit Logs)    (Metrics, Tracing, Logs)
                 │
                 ▼
     LangGraph Investigation Graph
     ├── Incident Context Node
     ├── Deployment Correlation Node
     └── Pinecone Vector RAG Node
                 │
                 ▼
     Incident Intelligence Engine
     ├── Multi-Signal Correlation
     ├── Probable Root Cause Analysis
     └── Risk & Blast Radius Assessment
                 │
                 ▼
     Human Approval Safety Gate
     ├── Role Check (INCIDENT_MANAGER)
     └── Atomic Transition Lock
                 │
                 ▼
     Remediation Execution Engine
     ├── Whitelisted Adapters (Rollback, Restart, Pool Limit)
     └── Dry-Run / Safe Execution
                 │
                 ▼
     Automated Health Verification
     └── Service Probes -> Incident MITIGATED -> Immutable Audit
```

---

## 🌟 The End-to-End User Journey

OpsPilot tells one coherent operational story from alert to resolution:

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
9. Atomic Execution      Whitelisted adapter executes rollback in dry-run/safe mode (COMPLETED).
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
| **RAG Threshold** | `0.65` | **`0.65`** | Calibrated threshold sweep across 10 runbooks |
| **State Machine Safety** | `STRICT` | **`STRICT`** | Unapproved executions strictly blocked |
| **Full Test Suite** | `349/349` | **`100% PASS`** | Automated pytest regression suite |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.13+
- Node.js 20+
- PostgreSQL 15+

### 1. Clone & Set Up Backend
```bash
git clone https://github.com/OpsPilot/OpsPilot.git
cd OpsPilot/backend

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
```

### 3. Run the Backend API
```bash
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- OpsPilot UI: `http://localhost:8000/ui/`
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
docker-compose up -d --build
```
Access points:
- **OpsPilot Frontend (Nginx):** `http://localhost/`
- **OpsPilot Backend (FastAPI):** `http://localhost:8000/`
- **Grafana Dashboards:** `http://localhost:3000/` (admin/admin)
- **Prometheus Metrics:** `http://localhost:9090/`

### AWS Cloud Deployment (Terraform)
Automated Infrastructure as Code located in `infra/terraform/`:
- **AWS ECS Fargate:** Multi-AZ container cluster with zero-downtime rolling deployment.
- **AWS RDS PostgreSQL 15:** Private subnet, KMS encrypted at rest, Multi-AZ.
- **Application Load Balancer:** Health check targets at `/health`.
- **AWS Secrets Manager:** Secure storage for database credentials and API keys.

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

---

## 🧪 Testing & Verification

Run the consolidated 349-test regression suite:
```bash
cd backend
pytest -v
```
Run the automated deployment smoke test:
```bash
python scripts/deploy_verify.py --url http://localhost:8000
```
Run the end-to-end interactive terminal demo:
```bash
python scripts/demo_walkthrough.py
```

---

## 📖 Comprehensive Documentation Index

| Document | Description |
| :--- | :--- |
| **[Architecture Guide](docs/ARCHITECTURE.md)** | C4 Container models, sequence diagrams, and subsystem design |
| **[Database & Schema](docs/DATABASE.md)** | PostgreSQL relational schema, 23 models, and migration strategy |
| **[AI & LangGraph](docs/AI_LANGGRAPH.md)** | Graph orchestration, tool registry, and decision synthesis |
| **[RAG & Vector Retrieval](docs/RAG.md)** | Pinecone indexing, similarity threshold calibration, and grounding evaluation |
| **[Security & RBAC](docs/SECURITY_RBAC.md)** | JWT auth, role permissions matrix, prompt injection defenses |
| **[API Documentation](docs/API.md)** | Interactive endpoints reference for all 10 subsystems |
| **[Deployment Guide](docs/DEPLOYMENT.md)** | Docker, AWS Terraform, GitHub Actions CI/CD, and rollback runbook |
| **[Testing & Evaluation](docs/TESTING_EVALUATION.md)** | 349-test suite report, failure diagnostics, and safety benchmarks |
| **[Live Demo Scenario](docs/DEMO_SCENARIO.md)** | Step-by-step walkthrough script for evaluator presentations |
| **[Presentation Slides](docs/PRESENTATION.md)** | Complete slide deck content and speaker notes for viva |
| **[Setup Guide](docs/SETUP_GUIDE.md)** | Zero-to-running setup guide for Windows, Linux, and macOS |
| **[Final Project Summary](docs/FINAL_PROJECT_SUMMARY.md)** | Complete milestones review and project accomplishments |
| **[Resume & Portfolio](docs/RESUME_PROJECT_DESCRIPTION.md)** | Project bullet points and system design interview questions |

---

## 👥 Default Demonstration Personas

| Persona | Role | Email | Permissions Scope |
| :--- | :--- | :--- | :--- |
| **Arun Kumar** | L1 Triage Operator | `arun.kumar@opspilot.internal` | View incidents, search runbooks, view metrics |
| **Priya Nair** | L2 Systems Engineer | `priya.nair@opspilot.internal` | Trigger AI investigations, request remediation actions |
| **Rahul Sharma** | Incident Manager | `rahul.sharma@opspilot.internal` | Approve/reject remediations, manage incident lifecycle |
| **Meena Patel** | Operations Admin | `meena.patel@opspilot.internal` | Role management, user access, full system oversight |

*Default demonstration password for all personas: `Password123!`*

---

<div align="center">
  <sub>Built with ❤️ as a production-grade Capstone / Final-Year Engineering Project.</sub>
</div>
