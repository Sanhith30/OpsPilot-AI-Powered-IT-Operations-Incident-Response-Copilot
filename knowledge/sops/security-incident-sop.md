# Standard Operating Procedure for Security Compromise and Secret Revocation

## Scope
Mandatory procedure for responding to leaked credentials, unauthorized API access, compromised secrets, or security boundary violations.

## Initial Detection and Containment
1. If database passwords, API keys, or JWT private keys are detected in public code repositories, application logs, or third-party communications, treat immediately as SEV-1 Security Incident.
2. Isolate affected instances or revoke compromised credentials in HashiCorp Vault / AWS Secrets Manager immediately:
   - For database credentials: Create a new database role/password, update secret in Vault, and immediately alter/disable the compromised user account in PostgreSQL.
   - For API tokens: Revoke token ID via Redis revocation list and rotate signing secrets.
3. Terminate active sessions associated with the compromised identity.

## Forensic Evidence Preservation
1. Preserve all application access logs, WAF telemetry, and audit trail records before restarting or terminating instances.
2. Snapshot the current memory and disk state of suspect compute nodes for offline forensic inspection.
3. Review `core.audit_logs` and PostgreSQL query logs for unauthorized data extraction or privilege escalation attempts.

## Recovery and Post-Incident Security Actions
1. Validate that all microservices have reloaded new rotated credentials without connection dropouts.
2. Deploy WAF rate limiting and IP blocking rules for identified malicious origin addresses.
3. Conduct mandatory security review, rotate any secondary secrets that could have been laterally accessed, and file a formal compliance incident report.
