# OpsPilot — Live Demonstration Scenario & Walkthrough Script

This script is structured for live demonstration to project examiners, evaluators, or technical interviewers. It presents OpsPilot as **one unified operational story** rather than disconnected features.

---

## 🎭 Demonstration Personas

| Stage | Persona | Role | Credentials | Action |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1–4** | **Priya Nair** | L2 Systems Engineer | `priya.nair@opspilot.internal` / `Password123!` | Triage, Investigation, Action Request |
| **Stage 5–6** | **Rahul Sharma** | Incident Manager | `rahul.sharma@opspilot.internal` / `Password123!` | Risk Review, Human Approval Gate |
| **Stage 7–8** | **Priya Nair** | L2 Systems Engineer | `priya.nair@opspilot.internal` / `Password123!` | Safe Execution, Verification, Audit Review |

---

## 🎬 Step-by-Step Demonstration Walkthrough

### Act 1: The Alert & The Dashboard
1. Open OpsPilot UI at `http://localhost:8000/ui/` (or `http://localhost:5173/`).
2. Log in as **Priya Nair** (L2 Systems Engineer).
3. **Operations Dashboard:**
   - Note the real-time fleet health indicator: `DEGRADED`.
   - Point out active incident metrics: 1 Critical SEV-1 Incident, MTTD: 4.2 minutes.
   - Monitored Services fleet shows `payment-api` experiencing elevated error rate (~14.2%).
   - *Examiner Talking Point:* "The dashboard is not displaying static mocked data; it queries aggregated fleet telemetry and health summaries from PostgreSQL."

### Act 2: Incident Triage & Event Timeline
1. Navigate to **Incident Queue** and select **Incident #1: Payment API Database Connection Timeouts**.
2. Review the chronological incident event stream:
   - `00:00` — Latency spike on `/checkout` endpoint.
   - `00:05` — Connection pool utilization exceeded 95%.
   - `00:10` — HTTP 504 Gateway Timeouts reported.
3. *Examiner Talking Point:* "Incident events provide the empirical timeline that anchors our investigation."

### Act 3: Agentic LangGraph Investigation
1. Click **"⚡ Run LangGraph Investigation"**.
2. Observe multi-agent DAG execution:
   - Tool `get_incident_details` queries telemetry.
   - Tool `get_recent_deployments` finds commit `9f2c4a1` deployed 20 minutes prior by developer Arun.
   - Tool `search_knowledge` queries Pinecone with team context `platform`.
3. Investigation completes with 3 structured findings and grounded evidence persisted to PostgreSQL.

### Act 4: Inspect Grounded RAG Citations
1. Open the **RAG Evidence** section.
2. Observe retrieved chunks from `payment-service-runbook.md`:
   - Similarity score: `0.8500` (strictly above the calibrated threshold of `0.65`).
   - Runbook excerpt specifies: *"If connection pool timeouts spike following a deployment, verify pool timeout configuration or rollback to previous stable tag v1.4.1."*
3. *Examiner Talking Point:* "Every citation is validated against Pinecone. Cross-team isolation prevents leakage, and citation validity is 1.0000."

### Act 5: Incident Intelligence & Decision Engine
1. Click **"Synthesize AI Decision"**.
2. The Incident Intelligence Engine correlates all signals:
   - **Probable Root Cause:** `Commit 9f2c4a1 lowered connection pool timeout to 250ms` (Confidence: 88%).
   - **Blast Radius:** `Checkout transactions delayed for ~14% of users`.
   - **Recommended Action:** `DEPLOYMENT_ROLLBACK` to `v1.4.1`.
   - **Safety Invariant:** `requires_human_approval = True`.
3. Click **"Request Remediation"**.
4. The action is created in state **`PENDING_APPROVAL`**.
5. *Examiner Talking Point:* "OpsPilot adheres to the cardinal rule: AI recommends, Human approves. The operator cannot execute this action unilaterally."

### Act 6: Human-in-the-Loop Manager Approval
1. Log out of Priya's session.
2. Log in as **Rahul Sharma** (Incident Manager).
3. Navigate to **Human Approval Gate**.
4. Rahul reviews:
   - The proposed action: `DEPLOYMENT_ROLLBACK` on `payment-api`.
   - The blast radius and risk score.
   - Priya's rationale.
5. Rahul enters review comment: *"Approved rollback to v1.4.1. Verified blast radius is isolated."*
6. Click **"Approve Remediation"**.
7. Action transitions to **`APPROVED`**.

### Act 7: Safe Execution & Automated Verification
1. Log back in as **Priya Nair** (or execute as authorized operator).
2. Click **"Execute Remediation"**.
3. The platform:
   - Claims an atomic row lock: `APPROVED` ➔ `EXECUTING` (preventing concurrent duplicates).
   - Invokes the whitelisted `DeploymentRollbackAdapter` in safe dry-run mode.
   - Transitions action to **`COMPLETED`**.
4. Automated verification probes kick off immediately:
   - Service health probe: `HEALTHY`.
   - Readiness endpoint: `200 OK`.
   - Connection pool utilization: stabilized at `28%`.
5. Action status transitions to **`VERIFIED`**.
6. **Incident #1 status updates automatically to `MITIGATED`!**

### Act 8: Immutable Observability & Audit Trail
1. Navigate to **Audit & Observability**.
2. Inspect the immutable audit log table:
   - Chronological log of every single step: `INVESTIGATION_TRIGGERED`, `INTELLIGENCE_SYNTHESIZED`, `REMEDIATION_REQUESTED`, `REMEDIATION_APPROVED` (Actor: Rahul), `REMEDIATION_EXECUTED` (Actor: Priya), `REMEDIATION_VERIFIED`.
3. Check Prometheus metrics endpoint (`/metrics`) showing updated operational counters.
4. *Conclusion:* "From an unmitigated SEV-1 outage to full resolution, every step was grounded in empirical evidence, governed by human approval, and audited permanently."

---

## 💡 Anticipated Examiner Questions & Answers

**Q1: Why use LangGraph instead of a standard LangChain agent or custom script?**  
*Answer:* Standard ReAct agents can loop unpredictably or execute unconstrained actions. LangGraph provides a deterministic Directed Acyclic Graph (DAG) with explicit state transitions, strict node-level type definitions, and reliable fallback mechanisms.

**Q2: How do you prevent LLM hallucinations during investigations?**  
*Answer:* We enforce a fail-closed `IntelligenceSafetyGate`. Every claim must map to an empirical evidence ID in the database or an authorized Pinecone vector chunk with similarity >= 0.65. Any hallucinated ID is stripped before output.

**Q3: What prevents an operator from bypassing manager approval and executing a rollback directly?**  
*Answer:* Security is enforced at the database and API level via FastAPI RBAC dependencies (`ACTION_APPROVE` permission). Furthermore, the state machine strictly rejects executing any remediation that is not in `APPROVED` status.

**Q4: How does the system handle concurrent remediation requests?**  
*Answer:* The repository uses atomic check-and-set database transactions (`claim_execution_lock`). If two requests arrive simultaneously, only one claims the lock (`APPROVED` ➔ `EXECUTING`), and the second receives a `409 Conflict`.
