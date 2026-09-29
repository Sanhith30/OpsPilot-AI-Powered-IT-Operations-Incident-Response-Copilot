# OpsPilot — REST API Specification (v1)

Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger UI: `http://localhost:8000/docs`  
OpenAPI Specification: `http://localhost:8000/openapi.json`

---

## 1. Authentication Endpoints

### `POST /auth/login`
Authenticates a user and issues a Bearer JWT token.
- **Request Body:**
  ```json
  {
    "email": "priya.nair@opspilot.internal",
    "password": "Password123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

### `GET /auth/me`
Returns current user profile, role, and authorized permissions.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "user_id": 2,
    "email": "priya.nair@opspilot.internal",
    "full_name": "Priya Nair",
    "role": "L2_OPERATOR",
    "permissions": ["INCIDENT_VIEW", "ACTION_REQUEST", "LOG_VIEW", "..."]
  }
  ```

---

## 2. Operations Dashboard Endpoints

### `GET /dashboard/summary`
Returns fleet-level health, system state, active alerts, and incident metrics.
- **Response (200 OK):**
  ```json
  {
    "fleet_status": "DEGRADED",
    "active_incidents_count": 1,
    "critical_incidents_count": 1,
    "mttd_minutes": 4.2,
    "mttr_minutes": 18.5,
    "services": [
      { "name": "payment-api", "status": "DEGRADED", "error_rate": 0.142 },
      { "name": "auth-service", "status": "HEALTHY", "error_rate": 0.001 }
    ]
  }
  ```

---

## 3. Incident Management Endpoints

### `GET /incidents`
Lists incidents with optional filtering by severity and status.

### `GET /incidents/{incident_id}`
Returns details of a specific incident.

### `GET /incidents/{incident_id}/events`
Returns chronological telemetry and alert stream for the incident.

---

## 4. Multi-Agent Investigation Endpoints

### `POST /investigations`
Dispatches a LangGraph multi-agent investigation session.
- **Request Body:**
  ```json
  {
    "incident_id": 1,
    "investigation_type": "AUTOMATED_TRIAGE"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "investigation_id": 12,
    "incident_id": 1,
    "status": "COMPLETED",
    "findings_count": 3
  }
  ```

### `GET /investigations/{investigation_id}/rag-evidence`
Returns grounded Pinecone RAG citations retrieved during the investigation.

---

## 5. Incident Intelligence & Decision Engine

### `POST /incidents/{incident_id}/intelligence/synthesize`
Correlates operational signals, identifies probable root cause, computes blast radius, and generates action recommendations.
- **Response (200 OK):**
  ```json
  {
    "incident_id": 1,
    "incident_summary": "payment-api degraded due to database connection pool exhaustion.",
    "probable_root_causes": [
      {
        "cause": "Rogue deployment commit 9f2c4a1 lowered connection pool timeout to 250ms.",
        "confidence": 0.88,
        "explanation": "Deployment timestamp matches latency surge and 504 timeouts."
      }
    ],
    "impact_assessment": {
      "severity": "HIGH",
      "customer_impact": "Checkout delayed for ~14% of transactions."
    },
    "recommended_actions": [
      {
        "action_id": "act-rollback-001",
        "action_type": "DEPLOYMENT_ROLLBACK",
        "title": "Rollback payment-api to v1.4.1",
        "priority": "HIGH",
        "requires_human_approval": true
      }
    ]
  }
  ```

---

## 6. Remediation & Approval Workflow

### `POST /incidents/{incident_id}/remediations`
Requests a human-approved remediation action (Permission: `ACTION_REQUEST`).
- **Status:** Initialized to `PENDING_APPROVAL`.

### `POST /remediations/{remediation_id}/approve`
Reviews and approves/rejects a remediation request (Permission: `ACTION_APPROVE`).
- **Request Body:**
  ```json
  {
    "decision": "APPROVE",
    "review_comment": "Approved rollback to v1.4.1 after reviewing blast radius."
  }
  ```

### `POST /remediations/{remediation_id}/execute`
Claims atomic lock and executes whitelisted remediation adapter in dry-run/safe mode.

### `POST /remediations/{remediation_id}/verify`
Executes automated health probes. If verified, marks remediation as `VERIFIED` and incident as `MITIGATED`.

---

## 7. Audit & Observability

### `GET /audit-logs`
Returns chronological, immutable audit log records.
- **Query Params:** `limit=50`, `resource_type=REMEDIATION_ACTION`

### `GET /health`
Returns system liveness probe: `{"status": "healthy"}`.

### `GET /db-health`
Returns PostgreSQL connectivity status.

### `GET /metrics`
Exposes Prometheus telemetry metrics (HTTP request durations, tool calls, remediation counts).
