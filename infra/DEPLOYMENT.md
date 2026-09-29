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

## 5. Production AWS EC2 Architecture & Topology

OpsPilot is currently deployed and active on AWS EC2 in `ap-south-1` (Mumbai):

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
                 │   │ (Let's Encrypt TLS / Port 443)│   │
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

### Running Services on Live Instance
- **Backend API:** `http://13.201.38.20:8000/health`
- **Frontend SPA:** `http://13.201.38.20/`
- **Prometheus:** `http://13.201.38.20:9090/`
- **Grafana:** `http://13.201.38.20:3000/`

---

## 6. Automated GitHub Actions → EC2 Continuous Deployment

The `.github/workflows/ci.yml` pipeline includes the automated `deploy-ec2` job, which triggers automatically on pushes to `main` once all tests pass:

1. **Lint & Security:** Flake8 and Bandit AST security scans.
2. **Backend Regression:** All 435 pytest test suites executed with PostgreSQL service container.
3. **Frontend Compilation:** Node.js 20 builds the production React Vite bundle.
4. **Docker Container Builds:** Validates backend and frontend container buildability.
5. **EC2 Deployment:** Authenticates via SSH, pulls `origin/main`, applies migrations, rebuilds containers, and validates `/health`.

### Configuring GitHub Repository Secrets
To connect your repository to the live EC2 instance, configure the following repository secrets under **Settings → Secrets and variables → Actions**:

| Secret Name | Value | Description |
| :--- | :--- | :--- |
| `EC2_HOST` | `13.201.38.20` | Public IPv4 address or Elastic IP of the EC2 instance. |
| `EC2_USER` | `ubuntu` | SSH login username (default `ubuntu` for Ubuntu AMIs). |
| `EC2_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | Private key (`.pem`) used to launch the EC2 instance. |

---

## 7. HTTPS & Custom Domain Setup (Nginx + Let's Encrypt)

To secure the EC2 instance with SSL/TLS and your custom domain:

1. **DNS Record:** Create an `A` record pointing your domain (e.g. `opspilot.yourcompany.com`) to `13.201.38.20`.
2. **Execute Automated SSL Setup:**
   SSH into the instance and run the one-command setup script:
   ```bash
   ssh -i your-key.pem ubuntu@13.201.38.20
   cd ~/opspilot
   sudo bash infra/scripts/setup_ssl_ec2.sh opspilot.yourcompany.com admin@yourcompany.com
   ```
   This script:
   - Installs Certbot and Nginx.
   - Generates 2048-bit Diffie-Hellman parameters.
   - Issues Let's Encrypt certificates.
   - Deploys the production Nginx TLS configuration (`infra/nginx/nginx-ssl.conf`) with HSTS, modern ciphers, and rate limiting.
   - Configures automatic certificate renewal.

---

## 8. AWS Golden Path End-to-End Verification

OpsPilot includes an automated 9-step production verification suite in `scripts/aws_golden_path_verify.py`.

### Execution Command
```bash
python scripts/aws_golden_path_verify.py --url http://13.201.38.20
```

### Verification Checklist & Results
| Step | Pipeline Component | Target Endpoint | Status |
| :--- | :--- | :--- | :--- |
| 1 | System Health Probe | `GET /health` | **PASS** |
| 2 | Operator Authentication | `POST /api/v1/auth/login` | **PASS** |
| 3 | Operator Persona & RBAC | `GET /api/v1/auth/me` | **PASS** |
| 4 | Incident Pipeline | `GET /api/v1/incidents` | **PASS** |
| 5 | Telemetry Timeline | `GET /api/v1/incidents/{id}/events` | **PASS** |
| 6 | Conversational AI Agent | `POST /api/v1/chat` | **PASS** (1049 chars, 4 tools dispatched) |
| 7 | RAG Knowledge Catalog | `GET /api/v1/knowledge/documents` | **PASS** (4 runbooks indexed) |
| 8 | Operational Dashboard | `GET /api/v1/dashboard/summary` | **PASS** |
| 9 | Immutable Audit Trail | `GET /api/v1/audit-logs` | **PASS** |

