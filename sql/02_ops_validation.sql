-- Read-only operational validation. Run against database: opspilot
SELECT incident_id,incident_number,title,severity,status,started_at,detected_at FROM core.incidents ORDER BY incident_id;
SELECT ticket_id,ticket_number,incident_id,priority,status,assigned_team_id,assigned_user_id,created_by FROM core.tickets ORDER BY ticket_id;
SELECT investigation_id,incident_id,started_by,investigation_type,question,status FROM core.investigations ORDER BY investigation_id;
SELECT investigation_id,COUNT(*) AS step_count FROM core.investigation_steps GROUP BY investigation_id ORDER BY investigation_id;
SELECT investigation_id,COUNT(*) AS tool_call_count FROM core.tool_calls GROUP BY investigation_id ORDER BY investigation_id;
SELECT investigation_id,COUNT(*) AS evidence_count FROM core.investigation_evidence GROUP BY investigation_id ORDER BY investigation_id;
SELECT investigation_id,COUNT(*) AS finding_count FROM core.investigation_findings GROUP BY investigation_id ORDER BY investigation_id;
SELECT investigation_id,COUNT(*) AS prediction_count FROM core.risk_predictions GROUP BY investigation_id ORDER BY investigation_id;
