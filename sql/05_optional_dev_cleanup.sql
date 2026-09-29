-- DEVELOPMENT DATABASE ONLY. Preview first. This file defaults to ROLLBACK.
BEGIN;
SELECT ticket_id,ticket_number FROM core.tickets WHERE ticket_number IN ('TCK-DEV-001','TCK-API-001','TCK-ERR-TEST-001','TCK-AUTH-TEST-001','TCK-AUTH-TEST-002');
SELECT prediction_id,model_name,model_version FROM core.risk_predictions WHERE model_name IN ('pytest_model','test_xgboost');
SELECT tool_call_id,tool_name FROM core.tool_calls WHERE tool_name IN ('test_log_search_tool','test_timeout_tool');
ROLLBACK;
