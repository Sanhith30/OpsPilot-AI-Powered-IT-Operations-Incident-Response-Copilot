# OpsPilot — Comprehensive System Architecture

## 1. System Vision & Design Philosophy

OpsPilot is an AI-powered autonomous operations and incident response platform designed to assist Site Reliability Engineers (SREs), DevOps teams, and Incident Responders.

The design is governed by three foundational tenets:
1. **Deterministic Multi-Agent Coordination:** Large Language Models (LLMs) are used for synthesis, semantic correlation, and contextual reasoning, while state transitions, data fetching, and tool executions are strictly deterministic.
2. **Fail-Closed Evidence Grounding:** An AI recommendation is never trusted without empirical proof. Every factual claim must cite an empirical evidence ID or grounded runbook chunk. Hallucinations are actively filtered by an automated safety gate.
3. **Strict Separation of Operational Duties (Human-in-the-Loop):** Autonomous actions that alter production state (rollbacks, pod restarts, configuration overrides) are gated by role-based human approval and atomic idempotency locks.

---

## 2. High-Level C4 Container Architecture

```mermaid
graph TD
    User([SRE / Incident Responder]) -->|HTTPS / Port 80/443| UI[React 18 + Vite SPA]
    UI -->|REST / JSON| Gateway[FastAPI Application Gateway]
    
    subgraph Core Platform
        Gateway --> Auth[JWT & RBAC Module]
        Gateway --> Incidents[Incident Management Service]
        Gateway --> InvService[Investigation Service]
        Gateway --> IntelService[Incident Intelligence Engine]
        Gateway --> Remediation[Remediation & Approval Engine]
        Gateway --> Audit[Immutable Audit Service]
    end

    subgraph Data & Vector Persistence
        Incidents --> PG[(PostgreSQL 15 RDS)]
        InvService --> PG
        Remediation --> PG
        Audit --> PG
        IntelService --> Pinecone[(Pinecone Vector DB)]
    end

    subgraph Agentic Intelligence
        InvService --> LangGraph[LangGraph Multi-Agent Runner]
        LangGraph --> Tools[Tool Registry]
        Tools --> Tool1[Incident Query Tool]
        Tools --> Tool2[Deployment History Tool]
        Tools --> Tool3[RAG Runbook Search Tool]
        Tools --> Tool4[Metric Query Tool]
        LangGraph --> Gemini[Google Gemini LLM]
    end

    subgraph Observability Stack
        Gateway --> OTel[OpenTelemetry Collector]
        OTel --> Prom[Prometheus]
        OTel --> Jaeger[Jaeger Distributed Tracing]
        OTel --> Loki[Loki Log Aggregator]
        Prom --> Grafana[Grafana Dashboards]
    end
```

---

## 3. End-to-End Incident Lifecycle Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Operator as L2 Operator (Priya)
    actor Manager as Incident Manager (Rahul)
    participant UI as OpsPilot React UI
    participant API as FastAPI Gateway
    participant LG as LangGraph Runner
    participant RAG as Pinecone Vector DB
    participant Engine as Intelligence Engine
    participant DB as PostgreSQL 15
    participant Remed as Remediation Engine

    Operator->>UI: Open Active Incident (SEV-1)
    UI->>API: GET /api/v1/incidents/1
    API->>DB: Fetch Incident & Events
    DB-->>UI: Payment API Connection Timeouts

    Operator->>UI: Click "Run AI Investigation"
    UI->>API: POST /api/v1/investigations
    API->>LG: Dispatch Investigation Graph
    LG->>DB: Query Recent Deployments (SHA 9f2c4a1)
    LG->>RAG: Search Runbooks (query: payment timeout)
    RAG-->>LG: Chunk doc-payment-runbook (Score: 0.85 >= 0.65)
    LG->>DB: Persist Investigation Findings
    DB-->>UI: Investigation Complete

    Operator->>UI: Synthesize AI Intelligence
    UI->>API: POST /api/v1/incidents/1/intelligence/synthesize
    API->>Engine: Correlate Signals & Assess Risk
    Engine->>Engine: Probable Root Cause: Rogue Commit 9f2c4a1 (0.88)
    Engine->>Engine: Safety Gate: Verify Citations & requires_human_approval=True
    Engine->>DB: Persist Intelligence Result
    DB-->>UI: Display Root Cause, Blast Radius & Recommendations

    Operator->>UI: Request Remediation Action (DEPLOYMENT_ROLLBACK)
    UI->>API: POST /api/v1/incidents/1/remediations
    API->>DB: Status: PENDING_APPROVAL
    DB-->>UI: Action Awaiting Manager Approval

    Manager->>UI: Review Incident & Blast Radius
    Manager->>UI: Click "Approve Remediation"
    UI->>API: POST /api/v1/remediations/1/approve
    API->>DB: Status: APPROVED

    Operator->>UI: Execute Remediation
    UI->>API: POST /api/v1/remediations/1/execute
    API->>Remed: Claim Atomic Lock (APPROVED -> EXECUTING)
    Remed->>Remed: Execute Safe Adapter (dry_run=True)
    Remed->>Remed: Trigger Automated Verification Probes
    Remed->>DB: Status: VERIFIED & Incident: MITIGATED
    Remed->>DB: Write Immutable Audit Log
    DB-->>UI: Incident MITIGATED, Service Restored
```

---

## 4. Subsystem Specifications

### 4.1 FastAPI Application Gateway
- **Middleware Pipeline:**
  - `RequestObservabilityMiddleware`: Injects correlation UUID (`X-Request-ID`), traces latency, and records Prometheus HTTP request counts.
  - `SecurityHeadersMiddleware`: Enforces `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Strict-Transport-Security`.
  - `RateLimitMiddleware`: Sliding window in-memory limiter guarding against brute-force and request abuse.
  - `CORSMiddleware`: Whitelisted cross-origin resource sharing.
- **Exception Sanitization:** Global exception handlers mask passwords, database URLs, and API tokens from all API outputs.

### 4.2 LangGraph Multi-Agent Orchestration
- **State Definition (`InvestigationState`):** Strongly typed state object tracking incident metadata, accumulated evidence IDs, tool call traces, and agent findings.
- **Node Execution Flow:**
  1. `analyze_incident`: Ingests initial telemetry and events.
  2. `collect_deployments`: Queries CI/CD and deployment logs within the incident time window.
  3. `search_runbooks`: Queries Pinecone with verified team access context.
  4. `synthesize_findings`: Generates structured operational findings.
- **Deterministic Tool Registry:** Every tool inherits from `BaseTool`, validates inputs with Pydantic schemas, and encapsulates unhandled tool crashes in `ToolResult(status="FAILED")`.

### 4.3 Incident Intelligence & Decision Engine
- **Correlation Engine:** Computes temporal and semantic alignment across alerts, events, deployments, and runbooks.
- **Root Cause Engine:** Generates ranked candidate root causes with confidence scores, supporting evidence, and contradicting signals.
- **Impact Assessment:** Evaluates service degradation, operational scope, and customer impact.
- **Operational Decision Engine:** Recommends prioritized actions with strict human approval flags.
- **Fail-Closed Safety Gate:** Validates evidence grounding, strips hallucinated IDs, and rejects any action attempting to bypass human approval.

### 4.4 Remediation & Verification State Machine
- **State Lifecycle:**
  `PENDING_APPROVAL` ➔ `APPROVED` ➔ `EXECUTING` ➔ `COMPLETED` ➔ `VERIFIED`
- **Idempotent Concurrency:** Atomic database check-and-set locks prevent duplicate execution claims.
- **Adapter Whitelist:** Only predefined adapters (`DEPLOYMENT_ROLLBACK`, `RESTART_SERVICE_INSTANCE`, `ADJUST_POOL_LIMITS`, `RUNBOOK_STEP_EXECUTION`) can be dispatched. Shell injections are impossible.
- **Automated Verification:** Probes readiness endpoints and error rate metrics. If probes fail, status transitions to `VERIFICATION_FAILED` and the incident is NOT mitigated.
