# OpsPilot — Resume & Technical Interview Guide

This guide provides polished resume bullet points, portfolio summaries, and system design discussion points tailored for Site Reliability Engineering (SRE), DevOps, Backend Engineering, and AI Systems roles.

---

## 📄 Resume Bullet Points

### Option 1: AI / Backend Systems Engineer
- **Architected OpsPilot**, an enterprise autonomous incident response platform combining **FastAPI**, **LangGraph**, and **PostgreSQL**, reducing simulated Mean Time to Resolution (MTTR) by automating telemetry correlation, root-cause analysis, and safe remediation.
- Built a deterministic **LangGraph multi-agent DAG** with specialized tools for querying telemetry events, CI/CD releases, and vector runbooks, achieving **100% test pass rate across 349 test cases**.
- Implemented **Grounded RAG on Pinecone** with an empirical **0.65 similarity threshold sweep** and multi-tenant access control, ensuring a **1.0000 grounding rate** and **zero cross-team document leakage**.
- Engineered a **Human-in-the-Loop remediation workflow** with separation of duties, atomic concurrency locks, whitelisted execution adapters, and automated post-remediation health verification.
- Automated continuous delivery using **GitHub Actions**, **Docker multi-stage builds**, and **AWS Terraform** (ECS Fargate, RDS PostgreSQL Multi-AZ, ALB), including automated rollback on smoke test failures.

### Option 2: DevOps / SRE Focus
- Designed and deployed an end-to-end incident response copilot with **FastAPI**, **React 18**, and **PostgreSQL 15**, instrumented with **OpenTelemetry**, **Prometheus**, and **Grafana**.
- Developed infrastructure as code using **Terraform** provisioning a secure AWS VPC, private ECS Fargate tasks, encrypted RDS PostgreSQL, and an Application Load Balancer with zero public database exposure.
- Built a **resilient CI/CD deployment pipeline** in GitHub Actions featuring Bandit security AST scanning, multi-stage Docker builds, database schema migrations, and automated ECS rollback on probe failure.
- Implemented defense-in-depth security including **Argon2id password hashing**, cryptographic **JWT RBAC** (19 granular permissions across 4 roles), OWASP security headers, sliding-window rate limiting, and regex prompt-injection filters.

---

## 🎯 1-Minute Elevator Pitch / Portfolio Summary

> *"OpsPilot is an enterprise-grade autonomous IT operations and incident response copilot. In modern cloud environments, microservice outages trigger thousands of alerts that overwhelm operators. Rather than relying on naive chatbots that hallucinate or execute unsafe shell scripts, OpsPilot uses LangGraph to coordinate deterministic multi-agent investigations across telemetry, deployments, and Pinecone vector runbooks. It correlates disparate signals to pinpoint the root cause and blast radius, but enforces the strict rule: AI recommends, Human approves. Remediation actions require role-based manager approval, claim atomic execution locks, dispatch only whitelisted safe adapters, and verify recovery through automated health probes. The platform is backed by 349 automated tests with a 100% pass rate, packaged with multi-stage Docker builds, and deployed to AWS ECS Fargate via Terraform with automated rollback."*

---

## 🧠 System Design & Interview Discussion Points

### Q1: "How did you design the LangGraph multi-agent workflow to prevent infinite loops or erratic behavior?"
**Key Talking Points:**
- Replaced open-ended ReAct prompt loops with a strictly bounded Directed Acyclic Graph (DAG).
- Defined an immutable, typed `InvestigationState` object passed between nodes.
- Each node executes a specialized `BaseTool` subclass with Pydantic input validation.
- Unhandled tool crashes are encapsulated into `ToolResult(status="FAILED")` instead of crashing the pipeline.
- If external LLM calls time out or return unparseable output, the engine automatically falls back to a deterministic rules engine.

### Q2: "How did you ensure RAG grounding and prevent hallucinated runbook citations?"
**Key Talking Points:**
- Implemented a two-stage evaluation: empirical similarity threshold sweep and strict citation validation.
- Calibrated the similarity cutoff at **`0.65`** across a 16-case benchmark, eliminating irrelevant chunk noise while maintaining 0.95+ recall.
- Added a `CitationValidator` that verifies every cited chunk ID was physically present in the active retrieval result set.
- Built multi-tenant access filtering at the vector metadata layer, ensuring complete isolation across teams with `0.0000` unauthorized leakage.

### Q3: "How does the system ensure safety during remediation actions?"
**Key Talking Points:**
- **Separation of Duties:** Operators (`L2_OPERATOR`) can only request remediation; managers (`INCIDENT_MANAGER`) must approve.
- **Idempotency & Concurrency:** The database repository uses an atomic check-and-set query (`claim_execution_lock`) to transition `APPROVED` ➔ `EXECUTING`. A duplicate request receives a `409 Conflict`.
- **Whitelisted Adapters:** Arbitrary bash/shell execution is strictly disallowed; only registered Python adapters (`DeploymentRollbackAdapter`, etc.) can execute.
- **Automated Verification:** The action is not marked `VERIFIED` until automated probes confirm readiness endpoints and error rate stabilization. If probes fail, status becomes `VERIFICATION_FAILED` and the incident is not marked `MITIGATED`.

### Q4: "How does the CI/CD pipeline handle deployment failures?"
**Key Talking Points:**
- Before deploying, GitHub Actions captures the currently running ECS Task Definition revision as a rollback anchor.
- The workflow deploys new container images using a zero-downtime rolling update (`minimum_healthy_percent = 100`).
- Immediately after ECS service stabilization, an automated smoke verification script (`scripts/deploy_verify.py`) executes probes against `/health`, `/db-health`, `/metrics`, security headers, and `/ui/`.
- If any probe fails after retries, the workflow triggers `scripts/rollback_ecs.py`, which invokes the AWS ECS API to revert the service to the previous stable task definition revision.
