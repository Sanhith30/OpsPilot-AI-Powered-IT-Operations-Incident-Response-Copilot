-- Read-only audit validation.
SELECT audit_log_id,user_id,action,resource_type,resource_id,details,created_at FROM core.audit_logs ORDER BY audit_log_id DESC LIMIT 50;
SELECT action,COUNT(*) AS total FROM core.audit_logs GROUP BY action ORDER BY action;
