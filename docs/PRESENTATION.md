# OpsPilot — Capstone / Final-Year Viva Presentation Slides & Speaker Notes

This document provides a slide-by-slide guide for presenting OpsPilot during your final-year project defense, capstone review, or technical interview presentation.

---

## 📽️ Slide Deck Outline

### Slide 1: Title Slide
- **Title:** OpsPilot: Autonomous IT Operations & Incident Response Copilot
- **Subtitle:** Agentic Triaging, Grounded RAG, Safe Human-in-the-Loop Remediation & Immutable Observability
- **Presenter:** [Your Name / Team Members]
- **Advisors/Evaluators:** Department of Computer Science & Engineering
- **Technologies:** React, FastAPI, PostgreSQL, LangGraph, Pinecone, Docker, AWS Terraform
> **Speaker Notes:** "Good morning, respected professors and evaluators. Today, we are proud to present OpsPilot—an enterprise-grade autonomous IT operations and incident response copilot designed to dramatically reduce Mean Time to Resolution (MTTR) while enforcing strict safety, grounding, and human-in-the-loop controls."

---

### Slide 2: The Industry Problem
- **The Modern SRE Challenge:**
  - Microservice explosion: Thousands of alerts and telemetry streams daily.
  - Alert fatigue & slow MTTR: Operators take hours to correlate logs, metrics, and deployments.
  - Hallucinatory AI risks: Naive LLM chatbots invent non-existent commands or leak proprietary data.
  - Unsafe automation: Autonomous scripts that execute unvetted destructive actions against production clusters.
> **Speaker Notes:** "Cloud infrastructure complexity has outpaced human cognitive capacity during outages. However, handing automated control to ungrounded LLMs is dangerous—hallucinating a command in production can cause irreversible data loss. OpsPilot was engineered to solve this dilemma: combining the reasoning speed of AI with the deterministic safety of enterprise systems."

---

### Slide 3: The OpsPilot Solution
- **Core Pillars:**
  1. **LangGraph Agentic DAG:** Deterministic multi-agent coordination over an immutable state machine.
  2. **Grounded RAG with Team Isolation:** Dense vector retrieval on Pinecone with strict tenant isolation and calibrated similarity threshold (0.65).
  3. **Incident Intelligence Engine:** Multi-signal correlation, blast radius estimation, and root cause candidate ranking.
  4. **Human-in-the-Loop Safety Gate:** Separation of duties (L2 Operator requests, Incident Manager approves) with atomic execution locks.
  5. **Automated Verification & Audit:** Real-time readiness probes and immutable PostgreSQL audit trails.
> **Speaker Notes:** "OpsPilot bridges the gap between passive alerting and uncontrolled automation. Our cardinal rule is: AI recommends, Human approves. Every finding is grounded in empirical evidence, and every action is verified."

---

### Slide 4: High-Level System Architecture
- **Layered Architecture:**
  - **Presentation:** React 18 + Vite SPA (10 operational screens).
  - **Gateway:** FastAPI with OWASP headers and sliding-window rate limiting.
  - **Agentic Core:** LangGraph Directed Acyclic Graph coordinating specialized tools.
  - **Knowledge & Persistence:** PostgreSQL 15 relational core + Pinecone vector store.
  - **Telemetry:** OpenTelemetry Collector, Prometheus, and Grafana.
> **Speaker Notes:** "Here is our C4 container architecture. Notice how the frontend interacts exclusively with our hardened FastAPI gateway. State is distributed across PostgreSQL 15 for relational consistency and Pinecone for vector similarity, while OpenTelemetry captures distributed traces across the entire investigation."

---

### Slide 5: Agentic Investigation with LangGraph
- **Why LangGraph?**
  - Replaces erratic ReAct loops with deterministic state transitions.
  - Strongly-typed `InvestigationState`.
  - Node 1: Ingest Telemetry & Alerts.
  - Node 2: Correlate Deployment History (identifying rogue release commit 9f2c4a1).
  - Node 3: Query Pinecone Knowledge Base with tenant context.
  - Node 4: Synthesize Findings & Recommendations.
> **Speaker Notes:** "Instead of an open-ended chatbot, we modeled incident investigation as a deterministic Directed Acyclic Graph using LangGraph. Each node is a specialized operational agent with a strongly typed input and output contract."

---

### Slide 6: Grounded RAG & Multi-Tenant Isolation
- **Overcoming RAG Limitations:**
  - **Empirical Threshold Sweep:** Calibrated similarity threshold of 0.65 eliminates low-confidence noise.
  - **Multi-Team Isolation:** Document access policy strictly blocks cross-team leakage (Leakage Rate = 0.0000).
  - **Citation Validity:** Every claim is verified against retrieved chunks. Hallucinations are actively stripped.
  - **Chunk Deduplication:** SHA-256 chunk hashing prevents duplicate vector ingestion across document revisions.
> **Speaker Notes:** "In Step 17, we ran extensive threshold sweeps and answer-quality evaluations across 10 operational runbooks. We achieved a 1.0000 grounding rate and zero unauthorized document leakage."

---

### Slide 7: Incident Intelligence & Decision Engine
- **From Raw Signals to Actionable Intelligence:**
  - Correlates telemetry spikes with recent deployments.
  - Generates ranked root cause candidates with confidence scores.
  - Evaluates blast radius (e.g. 14% checkout degradation).
  - Generates prioritized actions with mandatory `requires_human_approval = True`.
  - Fail-closed `IntelligenceSafetyGate` enforces evidence validity before DB persistence.
> **Speaker Notes:** "The Decision Engine is what transforms OpsPilot from a search engine into an intelligent copilot. It correlates signals across time, identifies the exact commit causing the issue, and calculates customer blast radius."

---

### Slide 8: Human-in-the-Loop Remediation Workflow
- **State Machine Transitions:**
  - `PENDING_APPROVAL` ➔ `APPROVED` ➔ `EXECUTING` ➔ `COMPLETED` ➔ `VERIFIED`
- **Safety Mechanisms:**
  - **Separation of Duties:** Priya (L2) requests; Rahul (Manager) approves.
  - **Idempotent Concurrency:** Atomic database check-and-set locks prevent duplicate executions.
  - **Adapter Whitelist:** Only registered adapters (`DEPLOYMENT_ROLLBACK`, etc.) can execute; shell commands are impossible.
  - **Automated Verification:** Probes readiness and error rates. If probes fail, status transitions to `VERIFICATION_FAILED` and the incident is NOT mitigated.
> **Speaker Notes:** "This is our human-in-the-loop safety gate. Even if the AI is 100% confident in a rollback, production cannot be modified without manager authorization. Once approved, execution is atomic and validated by automated probes."

---

### Slide 9: Enterprise Security & RBAC
- **Hardened Security Features:**
  - **Argon2id** password hashing.
  - **Cryptographic JWTs** with 19 granular permissions across 4 personas.
  - **Prompt Injection Defense:** Regex filters and XML delimiter sanitization neutralizes jailbreak attempts.
  - **Sensitive Data Redaction:** Automatically masks database passwords and bearer tokens.
  - **Immutable Audit Trail:** All actions permanently logged in `core.audit_logs`.
> **Speaker Notes:** "Security was treated as a first-class citizen throughout the project. We validated 24 distinct security scenarios in Step 22, including RBAC bypasses, token tampering, rate-limit bursts, and prompt injection attempts."

---

### Slide 10: Production Cloud Deployment (AWS + Docker)
- **Production Architecture:**
  - **Multi-stage Docker Builds:** Lean images with dedicated non-root user `opspilot`.
  - **AWS ECS Fargate:** Multi-AZ container cluster with zero-downtime rolling updates.
  - **AWS RDS PostgreSQL 15:** Multi-AZ, private subnets, KMS encryption at rest.
  - **Application Load Balancer:** Health check targets at `/health`.
  - **Terraform IaC:** Complete automated provisioning in `infra/terraform/`.
> **Speaker Notes:** "OpsPilot is ready for real cloud deployment. We built multi-stage production Dockerfiles, Docker Compose for local environments, and 11 modular Terraform files to provision AWS ECS Fargate, RDS PostgreSQL, and ALBs."

---

### Slide 11: CI/CD Pipeline & Automated Rollback
- **GitHub Actions Workflows:**
  - `ci.yml`: Flake8 linting, Bandit security scanning, full 349-test suite, and Docker build verification.
  - `deploy.yml`: Pushes images to Amazon ECR, applies database migrations, updates ECS task definitions, and runs post-deployment smoke tests (`scripts/deploy_verify.py`).
  - **Automated Rollback:** If smoke verification fails, `scripts/rollback_ecs.py` automatically rolls back the ECS service to the previous stable revision.
> **Speaker Notes:** "Our continuous delivery pipeline doesn't deploy blindly. It executes automated smoke verification against the newly deployed containers. If any probe fails, our automated rollback script reverts the cluster to the last stable task definition."

---

### Slide 12: Empirical Evaluation & Benchmarks
- **Verification Metrics:**
  - **Total Tests:** 349 passed (100% pass rate in 27s).
  - **Regressions:** 0 across all 23 development steps.
  - **Grounding Rate:** 1.0000.
  - **Citation Validity:** 1.0000.
  - **Unauthorized Leakage:** 0.0000.
  - **Unsupported Claims:** 0.0000.
> **Speaker Notes:** "Every single engineering claim in this presentation is backed by empirical data and automated testing. All 349 tests pass in our continuous integration pipeline with zero regressions."

---

### Slide 13: Live Demonstration Recap
- **The End-to-End Walkthrough:**
  - Alert detected on `payment-api` ➔ Priya investigates via LangGraph ➔ Pinecone runbook retrieved (similarity: 0.85) ➔ Intelligence identifies rogue commit 9f2c4a1 ➔ Priya requests rollback ➔ Rahul approves ➔ Safe execution & verification pass ➔ Incident becomes `MITIGATED` ➔ Audit trail verified.
> **Speaker Notes:** "In our demonstration, you witnessed a complete operational lifecycle where the incident transitioned from critical degradation to full mitigation in minutes, with full accountability."

---

### Slide 14: Key Technical Contributions
1. First deterministic operational agent architecture combining LangGraph with empirical RAG calibration.
2. Production-grade human-in-the-loop state machine with atomic concurrency locks.
3. Multi-tenant document isolation model preventing vector store leakage.
4. Comprehensive cloud deployment package (Terraform, Docker Compose, CI/CD, Automated Rollback).
> **Speaker Notes:** "Our key contributions demonstrate how modern agentic AI can be deployed safely in high-stakes enterprise infrastructure environments without sacrificing reliability or control."

---

### Slide 15: Conclusion & Q&A
- **Summary:** OpsPilot is a complete, secure, and production-ready autonomous operations platform.
- **GitHub Repository:** `https://github.com/OpsPilot/OpsPilot`
- **Documentation:** Full architectural and API guides in `/docs`.
- **Open for Questions:** Thank you!
> **Speaker Notes:** "Thank you for your time and attention. We now welcome any questions or discussion."
