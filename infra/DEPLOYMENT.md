# OpsPilot — Production Infrastructure & Deployment Architecture

This document defines the deployment architecture, container configuration, AWS Terraform setup, and CI/CD pipelines for OpsPilot.

---

## 1. High-Level Architecture Topology

```text
                            Internet
                               │
                               ▼
               ┌───────────────────────────────┐
               │   Application Load Balancer   │ (Public Subnets, Port 80/443)
               └───────────────┬───────────────┘
                               │ HTTPS / Health Checks (/health)
                               ▼
               ┌───────────────────────────────┐
               │    AWS ECS Fargate Cluster    │ (Private Subnets, Multi-AZ)
               │                               │
               │   ┌───────────────────────┐   │
               │   │    OpsPilot Backend   │   │
               │   │  (FastAPI + LangGraph)│   │
               │   │     Port 8000         │   │
               │   └───────────┬───────────┘   │
               └───────────────┼───────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 ┌───────────────────────┐             ┌─────────────────────┐
 │  RDS PostgreSQL 15    │             │ Pinecone Vector DB  │
 │ (Multi-AZ, KMS GP3,   │             │ (HTTPS via NAT GW)  │
 │  Private DB Subnets)  │             └─────────────────────┘
 └───────────────────────┘                        │
            │                                     ▼
            ▼                          ┌─────────────────────┐
 ┌───────────────────────┐             │   Google Gemini     │
 │  AWS Secrets Manager  │             │ (HTTPS via NAT GW)  │
 │  (Credentials/Keys)   │             └─────────────────────┘
 └───────────────────────┘
```

---

## 2. Containerization Strategy

OpsPilot utilizes multi-stage Docker builds to ensure lean images, minimal attack surfaces, and strict non-root runtime environments.

### Backend Container (`backend/Dockerfile`)
- **Base image:** `python:3.13-slim`
- **Builder Stage:** Compiles C-extensions and pre-builds wheels for `psycopg` and `pwdlib`.
- **Frontend Builder Stage:** Node.js 20 builds the React/Vite SPA bundle.
- **Runtime Stage:** 
  - Non-root user `opspilot` (UID 10001).
  - Built frontend assets served natively under `/ui` by FastAPI.
  - Native healthcheck probing `http://localhost:8000/health`.

### Frontend Container (`frontend/Dockerfile`)
- **Base image:** `nginx:1.27-alpine`
- **Reverse Proxy:** Proxies `/api/` to `http://backend:8000/api/`.
- **Security:** Static asset caching, gzip compression, and OWASP security headers.

---

## 3. Local Production Simulation (`docker-compose.yml`)

To run the complete production-identical stack locally:

```bash
docker-compose up -d --build
```

Services initialized:
- `postgres`: PostgreSQL 15 with automated migrations mount.
- `backend`: FastAPI API + LangGraph runner (port 8000).
- `frontend`: React SPA on Nginx (port 80).
- `otel-collector`: OpenTelemetry OTLP receiver (ports 4317/4318).
- `prometheus`: Scrapes metrics from `/metrics` (port 9090).
- `grafana`: Pre-provisioned dashboards (port 3000).

---

## 4. AWS Infrastructure as Code (Terraform)

Located in `infra/terraform/`:

| Module | Description |
| :--- | :--- |
| `vpc.tf` | Multi-AZ VPC across 2 AZs with public, private app, and private DB subnets. |
| `security_groups.tf` | Strict ingress rules (ALB -> ECS Tasks -> RDS). Zero public DB exposure. |
| `rds.tf` | AWS RDS PostgreSQL 15, KMS encryption at rest, storage auto-scaling, automated backups. |
| `alb.tf` | Application Load Balancer with target group health check at `/health`. |
| `ecs.tf` | ECS Fargate Cluster, Task Definitions, and Service with 100%-200% rolling deployment. |
| `secrets.tf` | Secrets Manager configuration for database credentials and API keys. |
| `cloudwatch.tf` | 30-day log group retention with CPU and memory alarms. |

### Provisioning Steps
```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

---

## 5. Automated CI/CD & Zero-Downtime Rollback

### GitHub Actions Workflows
1. **Continuous Integration (`.github/workflows/ci.yml`)**:
   - Executes flake8 linting and Bandit security AST scanner.
   - Runs full 340+ pytest backend regression suite against PostgreSQL service container.
   - Executes `npm run build` on frontend SPA.
   - Builds backend and frontend Docker images for syntax and build verification.

2. **Continuous Deployment (`.github/workflows/deploy.yml`)**:
   - Authenticates to AWS using OpenID Connect (OIDC).
   - Builds and tags Docker images with Git commit SHA and pushes to Amazon ECR.
   - Executes database schema migrations via `scripts/run_migrations.py`.
   - Records currently active task definition as rollback anchor.
   - Updates ECS Fargate Service with zero-downtime rolling update.
   - Executes automated smoke verification script: `scripts/deploy_verify.py`.
   - **Automated Rollback:** If smoke verification fails, `scripts/rollback_ecs.py` is automatically invoked to revert the service to the previous stable revision.

---

## 6. Disaster Recovery & Secrets Rotation

- **Database Snapshots:** RDS automated daily snapshots retained for 7 days.
- **Secret Rotation:** App secrets stored in AWS Secrets Manager with KMS encryption.
- **Rollback Runbook:** If rollback is needed manually:
  ```bash
  python scripts/rollback_ecs.py --cluster opspilot-production-cluster --service opspilot-production-service --target-task-def opspilot-production-app:PREVIOUS_REVISION
  ```
