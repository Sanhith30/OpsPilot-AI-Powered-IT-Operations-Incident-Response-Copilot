# Standard Operating Procedure for Incident Severity and Escalation Management

## Objective
Defines incident severity classifications, escalation triggers, role assignments, and executive communication cadences for production incidents across OpsPilot systems.

## Severity Classifications
- **SEV-1 (Critical)**: Total customer-facing service outage, critical revenue impact, data integrity loss, or security compromise. Requires immediate 24/7 all-hands response.
- **SEV-2 (Major)**: Partial degradation of core functionality (e.g., elevated checkout latency, payment timeouts), affecting a substantial subset of users with no immediate workaround.
- **SEV-3 (Minor)**: Moderate issue with workaround available, non-critical background job failures, or internal tooling impairment.
- **SEV-4 (Low)**: Minor cosmetic defect, non-urgent bug, or informational alert.

## Escalation Triggers and Timelines
1. If a SEV-2 incident remains unmitigated after 15 minutes, it must be automatically escalated to SEV-1.
2. If root cause is unknown after 20 minutes of investigation, page domain tech leads and principal engineers.
3. If database or cloud infrastructure stability is threatened, immediately engage the Database Operations and Platform Infrastructure on-call teams.

## Escalation Roles and Responsibilities
- **Incident Commander (IC)**: Leads the response, coordinates investigation tasks, and has final authority over mitigation decisions (such as rollbacks or failovers).
- **Communications Lead**: Posts updates to public status pages and executive stakeholders every 15 minutes for SEV-1 and every 30 minutes for SEV-2.
- **Operations Lead**: Executes direct triage, telemetry analysis, and remediation commands on infrastructure.

## Incident Closure
An incident is declared mitigated only after all core health indicators remain within SLA thresholds for at least 30 consecutive minutes.
