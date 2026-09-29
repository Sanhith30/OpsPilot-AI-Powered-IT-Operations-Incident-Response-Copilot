# OpsPilot — Security, Authentication & RBAC Architecture

## 1. Security Philosophy: Defense in Depth

OpsPilot is engineered to adhere to enterprise security standards, recognizing that an autonomous operations platform has access to sensitive telemetry and production execution adapters.

The platform enforces five layers of defense:
1. **Transport & Gateway Security:** OWASP headers, CORS controls, rate limiting.
2. **Cryptographic Identity & Authentication:** Argon2 password hashing, short-lived JWTs.
3. **Role-Based Access Control (RBAC):** Principle of least privilege with 19 granular permissions.
4. **Prompt & Input Sanitization:** Regex-based injection filters and XML breakout neutralization.
5. **Immutable Audit Trails:** Append-only transaction logging of all administrative and remediation actions.

---

## 2. Authentication & JWT Tokens

- **Password Hashing:** Passwords are hashed using the state-of-the-art **Argon2id** algorithm (`pwdlib[argon2]`), resilient against GPU-based cracking.
- **Access Tokens:** Signed using HMAC-SHA256 (`HS256`) with a 32-byte secret key.
  - Claims: `sub` (User ID), `iat` (Issued At), `exp` (Expires At).
  - Default expiration: 480 minutes (configurable).
  - Validated on every protected endpoint via `get_current_user` FastAPI dependency.

---

## 3. RBAC Persona & Permission Matrix

OpsPilot defines 4 standard operational roles across 19 permissions:

| Permission Code | Description | L1 Triage | L2 Operator | Incident Manager | Admin |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `INCIDENT_VIEW` | View incidents & details | ✅ | ✅ | ✅ | ✅ |
| `INCIDENT_SEARCH` | Search & filter incidents | ✅ | ✅ | ✅ | ✅ |
| `INCIDENT_ASSIGN` | Assign incidents to teams | ❌ | ✅ | ✅ | ✅ |
| `INCIDENT_UPDATE` | Update incident status | ❌ | ✅ | ✅ | ✅ |
| `LOG_VIEW` | View application logs | ✅ | ✅ | ✅ | ✅ |
| `LOG_SEARCH` | Search application logs | ✅ | ✅ | ✅ | ✅ |
| `METRICS_VIEW` | View fleet metrics | ✅ | ✅ | ✅ | ✅ |
| `DEPLOYMENT_VIEW` | View deployment history | ✅ | ✅ | ✅ | ✅ |
| `RUNBOOK_SEARCH` | Search operational runbooks | ✅ | ✅ | ✅ | ✅ |
| `TICKET_VIEW` | View associated tickets | ✅ | ✅ | ✅ | ✅ |
| `TICKET_CREATE` | Create issue tickets | ✅ | ✅ | ✅ | ✅ |
| `TICKET_UPDATE` | Update issue tickets | ❌ | ✅ | ✅ | ✅ |
| `TICKET_ASSIGN` | Assign issue tickets | ❌ | ✅ | ✅ | ✅ |
| `RISK_PREDICTION_VIEW`| View ML risk scores | ✅ | ✅ | ✅ | ✅ |
| `ACTION_REQUEST` | Request remediation action | ❌ | **✅** | ✅ | ✅ |
| `ACTION_APPROVE` | Approve/Reject remediation | ❌ | ❌ | **✅** | ✅ |
| `AUDIT_VIEW` | View immutable audit trail | ❌ | ❌ | ❌ | ✅ |
| `USER_MANAGE` | Create and manage users | ❌ | ❌ | ❌ | ✅ |
| `ROLE_MANAGE` | Assign roles & permissions | ❌ | ❌ | ❌ | ✅ |

### The Separation of Duties Rule
- **L2 Operators (`Priya`)** can trigger AI investigations, synthesize root causes, and **request** remediation (`ACTION_REQUEST`). They **cannot approve** their own remediation requests.
- **Incident Managers (`Rahul`)** have approval authority (`ACTION_APPROVE`). They review the risk, blast radius, and rationale before granting approval.

---

## 4. Prompt & Evidence Injection Defenses

Untrusted incident payloads (e.g. error strings from external users containing injection attacks) are neutralized via `app/core/sanitizer.py`:
- **Pattern Matching:** Detects strings such as `"ignore all instructions"`, `"system prompt override"`, `"you are now in developer mode"`, and `"reveal passwords"`.
- **Delimiter Neutralization:** Neutralizes XML breakout tags (`</incident>`, `<system>`) before strings are passed to LLM prompts.
- **Fail-Closed Evidence Check:** The `IntelligenceSafetyGate` verifies that all evidence IDs exist in PostgreSQL. Hallucinated IDs are pruned.

---

## 5. Sensitive Data Redaction & Error Masking

- **Sanitization Helper (`redact_sensitive_data`):** Automatically masks database passwords (`postgresql://***:***@`), Bearer tokens, and API keys.
- **Global Error Handler:** Unhandled server exceptions return a generic message:
  ```json
  {
    "error": "INTERNAL_SERVER_ERROR",
    "detail": "An internal server error occurred.",
    "request_id": "c7f93a12-..."
  }
  ```
  Internal stack traces and database credentials are never leaked to API clients.

---

## 6. Immutable Audit Trail (`core.audit_logs`)

All security and operational lifecycle actions generate append-only audit entries:
- Events recorded: `USER_LOGIN`, `INVESTIGATION_TRIGGERED`, `INTELLIGENCE_SYNTHESIZED`, `REMEDIATION_REQUESTED`, `REMEDIATION_APPROVED`, `REMEDIATION_EXECUTED`, `REMEDIATION_VERIFIED`, `REMEDIATION_VERIFICATION_FAILED`.
- Metadata stored: Actor user ID, target resource type and ID, action outcome (`SUCCESS`, `FAILURE`, `DENIED`), request UUID, and timestamp.
