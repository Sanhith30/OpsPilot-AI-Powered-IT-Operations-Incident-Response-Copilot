BEGIN;

--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: roles; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.roles OVERRIDING SYSTEM VALUE VALUES (1, 'L1_ENGINEER', 'First-level incident support', true, '2026-09-26 13:41:34.022876+05:30');
INSERT INTO core.roles OVERRIDING SYSTEM VALUE VALUES (2, 'L2_ENGINEER', 'Advanced incident investigation', true, '2026-09-26 13:42:00.694239+05:30');
INSERT INTO core.roles OVERRIDING SYSTEM VALUE VALUES (3, 'MANAGER', 'IT operations management', true, '2026-09-26 13:42:00.694239+05:30');
INSERT INTO core.roles OVERRIDING SYSTEM VALUE VALUES (4, 'ADMIN', 'System administration', true, '2026-09-26 13:42:00.694239+05:30');


--
-- Data for Name: teams; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.teams OVERRIDING SYSTEM VALUE VALUES (1, 'Payments Team', 'Responsible for payment processing services', true, '2026-09-26 13:58:58.336767+05:30', '2026-09-26 13:58:58.336767+05:30', NULL);
INSERT INTO core.teams OVERRIDING SYSTEM VALUE VALUES (2, 'Database Team', 'Responsible for database operations and reliability', true, '2026-09-26 13:58:58.336767+05:30', '2026-09-26 13:58:58.336767+05:30', NULL);
INSERT INTO core.teams OVERRIDING SYSTEM VALUE VALUES (3, 'Infrastructure Team', 'Responsible for compute, networking, and infrastructure', true, '2026-09-26 13:58:58.336767+05:30', '2026-09-26 13:58:58.336767+05:30', NULL);
INSERT INTO core.teams OVERRIDING SYSTEM VALUE VALUES (4, 'Security Team', 'Responsible for security operations and incident response', true, '2026-09-26 13:58:58.336767+05:30', '2026-09-26 13:58:58.336767+05:30', NULL);
INSERT INTO core.teams OVERRIDING SYSTEM VALUE VALUES (5, 'Platform Team', 'Responsible for shared platform and authentication services', true, '2026-09-26 13:58:58.336767+05:30', '2026-09-26 13:58:58.336767+05:30', NULL);


--
-- Data for Name: services; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.services OVERRIDING SYSTEM VALUE VALUES (1, 'Payment API', 'payment-api', 'Handles customer payment authorization and processing.', 'production', 'ACTIVE', 'CRITICAL', 1, '2026-09-26 14:06:47.092249+05:30', '2026-09-26 14:06:47.092249+05:30');
INSERT INTO core.services OVERRIDING SYSTEM VALUE VALUES (2, 'Order Service', 'order-service', 'Creates and manages customer orders.', 'production', 'ACTIVE', 'HIGH', 1, '2026-09-26 14:06:47.092249+05:30', '2026-09-26 14:06:47.092249+05:30');
INSERT INTO core.services OVERRIDING SYSTEM VALUE VALUES (3, 'Authentication Service', 'auth-service', 'Handles user authentication and access tokens.', 'production', 'ACTIVE', 'CRITICAL', 5, '2026-09-26 14:06:47.092249+05:30', '2026-09-26 14:06:47.092249+05:30');
INSERT INTO core.services OVERRIDING SYSTEM VALUE VALUES (4, 'Fraud Detection Service', 'fraud-service', 'Analyzes transactions for potential fraud.', 'production', 'ACTIVE', 'HIGH', 5, '2026-09-26 14:06:47.092249+05:30', '2026-09-26 14:06:47.092249+05:30');
INSERT INTO core.services OVERRIDING SYSTEM VALUE VALUES (5, 'Notification Service', 'notification-service', 'Handles email and notification delivery.', 'production', 'ACTIVE', 'MEDIUM', 5, '2026-09-26 14:06:47.092249+05:30', '2026-09-26 14:06:47.092249+05:30');
INSERT INTO core.services OVERRIDING SYSTEM VALUE VALUES (6, 'Product Catalog Service', 'catalog-service', 'Provides product catalog information.', 'production', 'ACTIVE', 'MEDIUM', 1, '2026-09-26 14:06:47.092249+05:30', '2026-09-26 14:06:47.092249+05:30');


--
-- Data for Name: users; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.users OVERRIDING SYSTEM VALUE VALUES (1, 'Arun Kumar', 'arun@opspilot.local', '$argon2id$v=19$m=65536,t=3,p=4$5JJh8h01+PPkIRqnxHWfnA$zxtrFgh/sGclzqYbxrXrBOij1L3mj5DKBBR4t6tz18k', 1, 1, true, NULL, '2026-09-26 14:00:37.623472+05:30', '2026-09-26 20:48:07.645229+05:30');
INSERT INTO core.users OVERRIDING SYSTEM VALUE VALUES (2, 'Priya Sharma', 'priya@opspilot.local', '$argon2id$v=19$m=65536,t=3,p=4$5JJh8h01+PPkIRqnxHWfnA$zxtrFgh/sGclzqYbxrXrBOij1L3mj5DKBBR4t6tz18k', 2, 2, true, NULL, '2026-09-26 14:00:37.623472+05:30', '2026-09-26 20:48:27.153256+05:30');
INSERT INTO core.users OVERRIDING SYSTEM VALUE VALUES (3, 'Rahul Verma', 'rahul@opspilot.local', '$argon2id$v=19$m=65536,t=3,p=4$5JJh8h01+PPkIRqnxHWfnA$zxtrFgh/sGclzqYbxrXrBOij1L3mj5DKBBR4t6tz18k', 3, 3, true, NULL, '2026-09-26 14:00:37.623472+05:30', '2026-09-26 20:48:40.865631+05:30');
INSERT INTO core.users OVERRIDING SYSTEM VALUE VALUES (4, 'Meena Rao', 'meena@opspilot.local', '$argon2id$v=19$m=65536,t=3,p=4$5JJh8h01+PPkIRqnxHWfnA$zxtrFgh/sGclzqYbxrXrBOij1L3mj5DKBBR4t6tz18k', 4, 4, true, NULL, '2026-09-26 14:00:37.623472+05:30', '2026-09-26 20:48:52.046487+05:30');


--
-- Data for Name: incidents; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.incidents OVERRIDING SYSTEM VALUE VALUES (1, 'INC-1042', 1, 'Payment API elevated error rate', 'The Payment API is experiencing elevated request failures and increased latency in production.', 'HIGH', 'INVESTIGATING', '2026-09-26 14:50:00+05:30', '2026-09-26 14:54:00+05:30', NULL, 1, 2, 'Customers may experience failed payment requests.', NULL, NULL, NULL, '2026-09-26 14:34:26.738569+05:30', '2026-09-26 14:34:26.738569+05:30');


--
-- Data for Name: investigations; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.investigations OVERRIDING SYSTEM VALUE VALUES (1, 1, 2, 'ASSISTED', 'Why is Payment API failing?', 'STARTED', '2026-09-26 15:13:43.650858+05:30', NULL, NULL, '2026-09-26 15:13:43.650858+05:30', '2026-09-27 17:28:30.136442+05:30');
INSERT INTO core.investigations OVERRIDING SYSTEM VALUE VALUES (2, 1, 4, 'ASSISTED', 'Step 8 authenticated investigation identity verification', 'STARTED', '2026-09-26 23:23:41.005165+05:30', NULL, NULL, '2026-09-26 23:23:41.005165+05:30', '2026-09-27 17:28:30.136442+05:30');
INSERT INTO core.investigations OVERRIDING SYSTEM VALUE VALUES (94, 1, 1, 'ASSISTED', 'Why is this incident happening? What evidence suggests the most likely cause, and what should the operations engineer check next?', 'COMPLETED', '2026-09-27 19:24:42.295907+05:30', '2026-09-27 19:24:54.239798+05:30', 'The Payment API is experiencing an elevated error rate and increased latency in production, leading to customer payment failures. The incident started immediately after the successful deployment of Payment API version 2.8.1 to production. Logs indicate repeated database connection timeout errors.', '2026-09-27 19:24:42.295907+05:30', '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigations OVERRIDING SYSTEM VALUE VALUES (145, 1, 1, 'ASSISTED', 'Check database latency and recent deployments.', 'COMPLETED', '2026-09-27 19:56:57.10415+05:30', '2026-09-27 19:57:25.785267+05:30', 'A high-severity incident affecting the Payment API started at 2026-09-26T14:50:00+05:30 and was detected at 2026-09-26T14:54:00+05:30 due to an elevated error rate. Subsequent observations confirmed the increased error rate and revealed repeated database connection timeout errors. This incident coincides precisely with the completion of a production deployment of Payment API version 2.8.1.', '2026-09-27 19:56:57.10415+05:30', '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigations OVERRIDING SYSTEM VALUE VALUES (13, 1, 1, 'ASSISTED', 'Why is this incident happening? What evidence suggests the most likely cause, and what should the operations engineer check next?', 'COMPLETED', '2026-09-27 17:53:43.61923+05:30', '2026-09-27 17:53:56.020947+05:30', 'The Payment API is experiencing an elevated error rate and increased latency, leading to failed payment requests for customers. The incident started at 2026-09-26T14:50:00+05:30, coinciding with the completion of a new deployment (version 2.8.1) to production. Logs indicate repeated database connection timeout errors.', '2026-09-27 17:53:43.61923+05:30', '2026-09-27 17:53:43.64689+05:30');


--
-- Data for Name: tickets; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.tickets OVERRIDING SYSTEM VALUE VALUES (1, 'TCK-5001', 1, 'Investigate Payment API database connection timeouts', 'Investigate repeated database connection timeout errors observed during incident INC-1042.', 'URGENT', 'IN_PROGRESS', 2, 2, 2, '2026-09-26 15:10:55.799258+05:30', '2026-09-26 15:58:29.797408+05:30', NULL, NULL);
INSERT INTO core.tickets OVERRIDING SYSTEM VALUE VALUES (5, 'TCK-AUTH-001', 1, 'Authenticated creator test', 'Step 8 authenticated identity verification', 'LOW', 'OPEN', NULL, NULL, 4, '2026-09-26 23:10:16.939596+05:30', '2026-09-26 23:10:16.939596+05:30', NULL, NULL);


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (1, 2, 'USER', 'INVESTIGATION_VIEW', 'INVESTIGATION', '1', 1, 1, NULL, 'SUCCESS', 'req-demo-001', NULL, NULL, '{"view": "investigation_details"}', '2026-09-26 15:31:32.078244+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (2, NULL, 'AI', 'TOOL_CALL', 'TOOL', 'log_search_tool', 1, 1, NULL, 'SUCCESS', 'req-demo-001', NULL, NULL, '{"tool_call_id": 1, "tool_version": "1.0"}', '2026-09-26 15:31:54.383877+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (3, 1, 'USER', 'ACTION_APPROVE', 'ACTION_REQUEST', '42', 1, 1, NULL, 'DENIED', 'req-demo-002', NULL, NULL, '{"reason": "User does not have permission to approve sensitive actions", "permission_required": "ACTION_APPROVE"}', '2026-09-26 15:32:02.376761+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (4, 4, 'USER', 'PERMISSION_CHANGE', 'ROLE', '1', NULL, NULL, NULL, 'SUCCESS', NULL, NULL, NULL, '{"operation": "ASSIGN_PERMISSION", "permission_id": 15, "permission_code": "ACTION_REQUEST"}', '2026-09-26 21:57:05.052491+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (5, 4, 'USER', 'PERMISSION_CHANGE', 'ROLE', '1', NULL, NULL, NULL, 'SUCCESS', NULL, NULL, NULL, '{"operation": "REVOKE_PERMISSION", "permission_id": 15, "permission_code": "ACTION_REQUEST"}', '2026-09-26 22:01:30.838744+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (6, 4, 'USER', 'CREATE_TICKET', 'TICKET', '5', NULL, NULL, NULL, 'SUCCESS', NULL, NULL, NULL, '{"title": "Authenticated creator test", "incident_id": 1, "ticket_number": "TCK-AUTH-001"}', '2026-09-26 23:10:16.939596+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (7, 4, 'USER', 'CREATE_INVESTIGATION', 'INVESTIGATION', '2', NULL, NULL, NULL, 'SUCCESS', NULL, NULL, NULL, '{"incident_id": 1, "investigation_type": "ASSISTED"}', '2026-09-26 23:23:41.005165+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (127, 1, 'USER', 'CREATE_INVESTIGATION', 'INVESTIGATION', '94', 1, 94, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "RUNNING", "incident_id": 1, "investigation_type": "ASSISTED"}', '2026-09-27 19:24:42.295907+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (128, 1, 'USER', 'EXECUTE_INVESTIGATION', 'INVESTIGATION', '94', 1, 94, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "COMPLETED", "risk_level": "HIGH", "incident_id": 1, "findings_count": 5}', '2026-09-27 19:24:54.31254+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (129, 1, 'USER', 'INVESTIGATION_COMPLETED', 'INVESTIGATION', '94', 1, 94, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "COMPLETED", "final_summary": "The Payment API is experiencing an elevated error rate and increased latency in production, leading to customer payment failures. The incident started immediately after the successful deployment of Payment API version 2.8.1 to production. Logs indicate repeated database connection timeout errors."}', '2026-09-27 19:24:54.31254+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (13, 1, 'USER', 'EXECUTE_INVESTIGATION', 'INVESTIGATION', '13', NULL, NULL, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "COMPLETED", "risk_level": "HIGH", "incident_id": 1, "findings_count": 5}', '2026-09-27 17:53:56.076415+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (240, 1, 'USER', 'CREATE_INVESTIGATION', 'INVESTIGATION', '145', 1, 145, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "STARTED", "incident_id": 1, "investigation_type": "ASSISTED"}', '2026-09-27 19:56:57.10415+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (241, 1, 'USER', 'EXECUTE_INVESTIGATION', 'INVESTIGATION', '145', 1, 145, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "COMPLETED", "risk_level": "HIGH", "incident_id": 1, "findings_count": 4}', '2026-09-27 19:57:25.850707+05:30');
INSERT INTO core.audit_logs OVERRIDING SYSTEM VALUE VALUES (242, 1, 'USER', 'INVESTIGATION_COMPLETED', 'INVESTIGATION', '145', 1, 145, NULL, 'SUCCESS', NULL, NULL, NULL, '{"status": "COMPLETED", "final_summary": "A high-severity incident affecting the Payment API started at 2026-09-26T14:50:00+05:30 and was detected at 2026-09-26T14:54:00+05:30 due to an elevated error rate. Subsequent observations confirmed the increased error rate and revealed repeated database connection timeout errors. This incident coincides precisely with the completion of a production deployment of Payment API version 2.8.1."}', '2026-09-27 19:57:25.850707+05:30');


--
-- Data for Name: deployments; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.deployments OVERRIDING SYSTEM VALUE VALUES (1, 1, '2.7.0', 'production', 'a1b2c3d4', 'NORMAL', 'CI_CD', 'SUCCESS', NULL, '2026-09-25 13:30:00+05:30', '2026-09-25 13:35:00+05:30', '2026-09-26 14:40:45.47781+05:30');
INSERT INTO core.deployments OVERRIDING SYSTEM VALUE VALUES (2, 1, '2.8.0', 'production', 'e5f6g7h8', 'NORMAL', 'CI_CD', 'SUCCESS', NULL, '2026-09-26 13:40:00+05:30', '2026-09-26 13:45:00+05:30', '2026-09-26 14:40:45.47781+05:30');
INSERT INTO core.deployments OVERRIDING SYSTEM VALUE VALUES (3, 1, '2.8.1', 'production', 'i9j0k1l2', 'NORMAL', 'CI_CD', 'SUCCESS', NULL, '2026-09-26 14:45:00+05:30', '2026-09-26 14:50:00+05:30', '2026-09-26 14:40:45.47781+05:30');
INSERT INTO core.deployments OVERRIDING SYSTEM VALUE VALUES (4, 2, '4.1.0', 'production', 'm3n4o5p6', 'NORMAL', 'CI_CD', 'SUCCESS', NULL, '2026-09-26 13:00:00+05:30', '2026-09-26 13:05:00+05:30', '2026-09-26 14:40:55.872102+05:30');
INSERT INTO core.deployments OVERRIDING SYSTEM VALUE VALUES (5, 3, '3.4.2', 'production', 'q7r8s9t0', 'HOTFIX', 'MANUAL', 'SUCCESS', 3, '2026-09-26 12:00:00+05:30', '2026-09-26 12:08:00+05:30', '2026-09-26 14:40:55.872102+05:30');
INSERT INTO core.deployments OVERRIDING SYSTEM VALUE VALUES (6, 4, '1.9.0', 'production', 'u1v2w3x4', 'NORMAL', 'CI_CD', 'SUCCESS', NULL, '2026-09-26 12:30:00+05:30', '2026-09-26 12:34:00+05:30', '2026-09-26 14:40:55.872102+05:30');


--
-- Data for Name: investigation_steps; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.investigation_steps OVERRIDING SYSTEM VALUE VALUES (1, 1, 1, 'INCIDENT_QUERY', 'Retrieve incident details and current status.', 'COMPLETED', '2026-09-26 15:14:47.557051+05:30', NULL, NULL, '2026-09-26 15:14:47.557051+05:30', 'Step');
INSERT INTO core.investigation_steps OVERRIDING SYSTEM VALUE VALUES (2, 1, 2, 'LOG_SEARCH', 'Search Payment API logs for errors around incident start time.', 'COMPLETED', '2026-09-26 15:14:55.284519+05:30', NULL, NULL, '2026-09-26 15:14:55.284519+05:30', 'Step');
INSERT INTO core.investigation_steps OVERRIDING SYSTEM VALUE VALUES (3, 1, 3, 'METRIC_QUERY', 'Check error rate and latency metrics around the incident window.', 'COMPLETED', '2026-09-26 15:15:02.209616+05:30', NULL, NULL, '2026-09-26 15:15:02.209616+05:30', 'Step');
INSERT INTO core.investigation_steps OVERRIDING SYSTEM VALUE VALUES (4, 1, 4, 'DEPLOYMENT_QUERY', 'Check recent Payment API deployments before incident start.', 'COMPLETED', '2026-09-26 15:15:14.688418+05:30', NULL, NULL, '2026-09-26 15:15:14.688418+05:30', 'Step');
INSERT INTO core.investigation_steps OVERRIDING SYSTEM VALUE VALUES (5, 1, 5, 'RUNBOOK_SEARCH', 'Search operational runbooks for database connection timeout handling.', 'COMPLETED', '2026-09-26 15:15:24.241059+05:30', NULL, NULL, '2026-09-26 15:15:24.241059+05:30', 'Step');
INSERT INTO core.investigation_steps OVERRIDING SYSTEM VALUE VALUES (6, 1, 6, 'SYNTHESIS', 'Combine retrieved evidence into observations, hypotheses, and recommendations.', 'COMPLETED', '2026-09-26 15:15:31.992276+05:30', NULL, NULL, '2026-09-26 15:15:31.992276+05:30', 'Step');


--
-- Data for Name: tool_calls; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (1, 1, 2, 'log_search_tool', '1.0', '{"service": "payment-api", "end_time": "2026-09-26T09:35:00Z", "keywords": ["timeout", "database"], "start_time": "2026-09-26T09:20:00Z", "environment": "production"}', 'Found repeated database connection timeout messages during the incident window.', 'SUCCESS', '2026-09-26 15:02:00+05:30', '2026-09-26 15:02:01+05:30', 1000, NULL, NULL, '2026-09-26 15:17:46.978289+05:30', 'AI_GRAPH_TOOL', NULL);
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (2, 1, 3, 'metrics_query_tool', '1.0', '{"metric": "http_error_rate", "service": "payment-api", "environment": "production"}', 'Metrics source did not return data within the configured timeout.', 'TIMEOUT', '2026-09-26 15:03:00+05:30', '2026-09-26 15:03:10+05:30', 10000, 'METRICS_TIMEOUT', 'Prometheus query exceeded 10 second timeout.', '2026-09-26 15:18:00.201883+05:30', 'AI_GRAPH_TOOL', NULL);
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (11, 13, NULL, 'get_incident', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 17:53:56.024905+05:30', '2026-09-27 17:53:56.024905+05:30', NULL, NULL, NULL, '2026-09-27 17:53:43.64689+05:30', 'AI_GRAPH_TOOL', '{"title": "Payment API elevated error rate", "status": "INVESTIGATING", "severity": "HIGH", "root_cause": null, "service_id": 1, "started_at": "2026-09-26T14:50:00+05:30", "description": "The Payment API is experiencing elevated request failures and increased latency in production.", "detected_at": "2026-09-26T14:54:00+05:30", "incident_id": 1, "resolved_at": null, "impact_summary": "Customers may experience failed payment requests.", "incident_number": "INC-1042", "assigned_team_id": 1, "assigned_user_id": 2}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (12, 13, NULL, 'get_recent_deployments', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 17:53:56.024905+05:30', '2026-09-27 17:53:56.024905+05:30', NULL, NULL, NULL, '2026-09-27 17:53:43.64689+05:30', 'AI_GRAPH_TOOL', '{"service_id": 1, "before_time": "2026-09-26T14:50:00+05:30", "deployments": [{"status": "SUCCESS", "version": "2.8.1", "service_id": 1, "started_at": "2026-09-26T14:45:00+05:30", "commit_hash": "i9j0k1l2", "deployed_by": null, "environment": "production", "completed_at": "2026-09-26T14:50:00+05:30", "trigger_type": "CI_CD", "deployment_id": 3, "deployment_type": "NORMAL"}, {"status": "SUCCESS", "version": "2.8.0", "service_id": 1, "started_at": "2026-09-26T13:40:00+05:30", "commit_hash": "e5f6g7h8", "deployed_by": null, "environment": "production", "completed_at": "2026-09-26T13:45:00+05:30", "trigger_type": "CI_CD", "deployment_id": 2, "deployment_type": "NORMAL"}, {"status": "SUCCESS", "version": "2.7.0", "service_id": 1, "started_at": "2026-09-25T13:30:00+05:30", "commit_hash": "a1b2c3d4", "deployed_by": null, "environment": "production", "completed_at": "2026-09-25T13:35:00+05:30", "trigger_type": "CI_CD", "deployment_id": 1, "deployment_type": "NORMAL"}], "environment": "production"}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (13, 13, NULL, 'search_incident_events', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 17:53:56.024905+05:30', '2026-09-27 17:53:56.024905+05:30', NULL, NULL, NULL, '2026-09-27 17:53:43.64689+05:30', 'AI_GRAPH_TOOL', '{"events": [{"event_id": 5, "metadata": {"version": "2.8.1", "deployment_id": 2}, "created_by": null, "event_time": "2026-09-26T15:01:00+05:30", "event_type": "DEPLOYMENT_DETECTED", "description": "A recent Payment API deployment was identified before the incident.", "incident_id": 1}, {"event_id": 4, "metadata": {"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}, "created_by": null, "event_time": "2026-09-26T14:59:00+05:30", "event_type": "LOG_ANOMALY_DETECTED", "description": "Repeated database connection timeout errors were detected in Payment API logs.", "incident_id": 1}, {"event_id": 3, "metadata": {"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}, "created_by": null, "event_time": "2026-09-26T14:57:00+05:30", "event_type": "METRIC_THRESHOLD_EXCEEDED", "description": "Payment API error rate exceeded the configured operational threshold.", "incident_id": 1}, {"event_id": 2, "metadata": {"assigned_user_id": 2}, "created_by": 2, "event_time": "2026-09-26T14:55:00+05:30", "event_type": "ENGINEER_ASSIGNED", "description": "Incident assigned to Priya Sharma for investigation.", "incident_id": 1}, {"event_id": 1, "metadata": {"source": "monitoring", "error_rate": 13.7}, "created_by": null, "event_time": "2026-09-26T14:54:00+05:30", "event_type": "INCIDENT_CREATED", "description": "Payment API error rate exceeded the configured threshold and an incident was created.", "incident_id": 1}], "event_count": 5, "incident_id": 1}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (38, 94, NULL, 'get_incident', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 19:24:54.24331+05:30', '2026-09-27 19:24:54.24331+05:30', NULL, NULL, NULL, '2026-09-27 19:24:42.340369+05:30', 'AI_GRAPH_TOOL', '{"title": "Payment API elevated error rate", "status": "INVESTIGATING", "severity": "HIGH", "root_cause": null, "service_id": 1, "started_at": "2026-09-26T14:50:00+05:30", "description": "The Payment API is experiencing elevated request failures and increased latency in production.", "detected_at": "2026-09-26T14:54:00+05:30", "incident_id": 1, "resolved_at": null, "impact_summary": "Customers may experience failed payment requests.", "incident_number": "INC-1042", "assigned_team_id": 1, "assigned_user_id": 2}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (39, 94, NULL, 'get_recent_deployments', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 19:24:54.24331+05:30', '2026-09-27 19:24:54.24331+05:30', NULL, NULL, NULL, '2026-09-27 19:24:42.340369+05:30', 'AI_GRAPH_TOOL', '{"service_id": 1, "before_time": "2026-09-26T14:50:00+05:30", "deployments": [{"status": "SUCCESS", "version": "2.8.1", "service_id": 1, "started_at": "2026-09-26T14:45:00+05:30", "commit_hash": "i9j0k1l2", "deployed_by": null, "environment": "production", "completed_at": "2026-09-26T14:50:00+05:30", "trigger_type": "CI_CD", "deployment_id": 3, "deployment_type": "NORMAL"}, {"status": "SUCCESS", "version": "2.8.0", "service_id": 1, "started_at": "2026-09-26T13:40:00+05:30", "commit_hash": "e5f6g7h8", "deployed_by": null, "environment": "production", "completed_at": "2026-09-26T13:45:00+05:30", "trigger_type": "CI_CD", "deployment_id": 2, "deployment_type": "NORMAL"}, {"status": "SUCCESS", "version": "2.7.0", "service_id": 1, "started_at": "2026-09-25T13:30:00+05:30", "commit_hash": "a1b2c3d4", "deployed_by": null, "environment": "production", "completed_at": "2026-09-25T13:35:00+05:30", "trigger_type": "CI_CD", "deployment_id": 1, "deployment_type": "NORMAL"}], "environment": "production"}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (40, 94, NULL, 'search_incident_events', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 19:24:54.24331+05:30', '2026-09-27 19:24:54.24331+05:30', NULL, NULL, NULL, '2026-09-27 19:24:42.340369+05:30', 'AI_GRAPH_TOOL', '{"events": [{"event_id": 5, "metadata": {"version": "2.8.1", "deployment_id": 2}, "created_by": null, "event_time": "2026-09-26T15:01:00+05:30", "event_type": "DEPLOYMENT_DETECTED", "description": "A recent Payment API deployment was identified before the incident.", "incident_id": 1}, {"event_id": 4, "metadata": {"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}, "created_by": null, "event_time": "2026-09-26T14:59:00+05:30", "event_type": "LOG_ANOMALY_DETECTED", "description": "Repeated database connection timeout errors were detected in Payment API logs.", "incident_id": 1}, {"event_id": 3, "metadata": {"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}, "created_by": null, "event_time": "2026-09-26T14:57:00+05:30", "event_type": "METRIC_THRESHOLD_EXCEEDED", "description": "Payment API error rate exceeded the configured operational threshold.", "incident_id": 1}, {"event_id": 2, "metadata": {"assigned_user_id": 2}, "created_by": 2, "event_time": "2026-09-26T14:55:00+05:30", "event_type": "ENGINEER_ASSIGNED", "description": "Incident assigned to Priya Sharma for investigation.", "incident_id": 1}, {"event_id": 1, "metadata": {"source": "monitoring", "error_rate": 13.7}, "created_by": null, "event_time": "2026-09-26T14:54:00+05:30", "event_type": "INCIDENT_CREATED", "description": "Payment API error rate exceeded the configured threshold and an incident was created.", "incident_id": 1}], "event_count": 5, "incident_id": 1}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (56, 145, NULL, 'get_incident', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 19:57:25.787648+05:30', '2026-09-27 19:57:25.787648+05:30', NULL, NULL, NULL, '2026-09-27 19:56:58.105181+05:30', 'AI_GRAPH_TOOL', '{"title": "Payment API elevated error rate", "status": "INVESTIGATING", "severity": "HIGH", "root_cause": null, "service_id": 1, "started_at": "2026-09-26T14:50:00+05:30", "description": "The Payment API is experiencing elevated request failures and increased latency in production.", "detected_at": "2026-09-26T14:54:00+05:30", "incident_id": 1, "resolved_at": null, "impact_summary": "Customers may experience failed payment requests.", "incident_number": "INC-1042", "assigned_team_id": 1, "assigned_user_id": 2}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (57, 145, NULL, 'get_recent_deployments', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 19:57:25.787648+05:30', '2026-09-27 19:57:25.787648+05:30', NULL, NULL, NULL, '2026-09-27 19:56:58.105181+05:30', 'AI_GRAPH_TOOL', '{"service_id": 1, "before_time": "2026-09-26T14:50:00+05:30", "deployments": [{"status": "SUCCESS", "version": "2.8.1", "service_id": 1, "started_at": "2026-09-26T14:45:00+05:30", "commit_hash": "i9j0k1l2", "deployed_by": null, "environment": "production", "completed_at": "2026-09-26T14:50:00+05:30", "trigger_type": "CI_CD", "deployment_id": 3, "deployment_type": "NORMAL"}, {"status": "SUCCESS", "version": "2.8.0", "service_id": 1, "started_at": "2026-09-26T13:40:00+05:30", "commit_hash": "e5f6g7h8", "deployed_by": null, "environment": "production", "completed_at": "2026-09-26T13:45:00+05:30", "trigger_type": "CI_CD", "deployment_id": 2, "deployment_type": "NORMAL"}, {"status": "SUCCESS", "version": "2.7.0", "service_id": 1, "started_at": "2026-09-25T13:30:00+05:30", "commit_hash": "a1b2c3d4", "deployed_by": null, "environment": "production", "completed_at": "2026-09-25T13:35:00+05:30", "trigger_type": "CI_CD", "deployment_id": 1, "deployment_type": "NORMAL"}], "environment": "production"}');
INSERT INTO core.tool_calls OVERRIDING SYSTEM VALUE VALUES (58, 145, NULL, 'search_incident_events', NULL, 'null', NULL, 'SUCCESS', '2026-09-27 19:57:25.787648+05:30', '2026-09-27 19:57:25.787648+05:30', NULL, NULL, NULL, '2026-09-27 19:56:58.105181+05:30', 'AI_GRAPH_TOOL', '{"events": [{"event_id": 5, "metadata": {"version": "2.8.1", "deployment_id": 2}, "created_by": null, "event_time": "2026-09-26T15:01:00+05:30", "event_type": "DEPLOYMENT_DETECTED", "description": "A recent Payment API deployment was identified before the incident.", "incident_id": 1}, {"event_id": 4, "metadata": {"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}, "created_by": null, "event_time": "2026-09-26T14:59:00+05:30", "event_type": "LOG_ANOMALY_DETECTED", "description": "Repeated database connection timeout errors were detected in Payment API logs.", "incident_id": 1}, {"event_id": 3, "metadata": {"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}, "created_by": null, "event_time": "2026-09-26T14:57:00+05:30", "event_type": "METRIC_THRESHOLD_EXCEEDED", "description": "Payment API error rate exceeded the configured operational threshold.", "incident_id": 1}, {"event_id": 2, "metadata": {"assigned_user_id": 2}, "created_by": 2, "event_time": "2026-09-26T14:55:00+05:30", "event_type": "ENGINEER_ASSIGNED", "description": "Incident assigned to Priya Sharma for investigation.", "incident_id": 1}, {"event_id": 1, "metadata": {"source": "monitoring", "error_rate": 13.7}, "created_by": null, "event_time": "2026-09-26T14:54:00+05:30", "event_type": "INCIDENT_CREATED", "description": "Payment API error rate exceeded the configured threshold and an incident was created.", "incident_id": 1}], "event_count": 5, "incident_id": 1}');


--
-- Data for Name: investigation_evidence; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (1, 1, 1, 'LOG', 'Loki', 'payment-api/log-search/2026-09-26-09-29', 'Repeated database connection timeout errors were observed in Payment API logs during the incident window.', '{"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT", "environment": "production", "last_observed": "2026-09-26T09:34:00Z", "first_observed": "2026-09-26T09:29:00Z"}', '2026-09-26 14:59:00+05:30', 0.9600, true, '2026-09-26 15:19:54.153939+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (2, 1, NULL, 'DEPLOYMENT', 'PostgreSQL', 'deployment:3', 'Payment API version 2.8.1 completed deployment immediately before the incident start time.', '{"service": "payment-api", "version": "2.8.1", "environment": "production", "completed_at": "2026-09-26T09:20:00Z", "deployment_id": 3, "deployment_status": "SUCCESS"}', '2026-09-26 14:50:00+05:30', 0.9100, true, '2026-09-26 15:20:12.313839+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (3, 1, NULL, 'INCIDENT', 'PostgreSQL', 'incident_event:3', 'Payment API error rate reached 14.2%, exceeding the configured 10.0% threshold.', '{"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}', '2026-09-26 14:57:00+05:30', 0.9700, true, '2026-09-26 15:20:18.593357+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (11, 13, NULL, 'deployment', 'Deployment 2.8.1 to production', '3', 'Deployment ID 3 deployed version 2.8.1 to production with status SUCCESS. Commit: i9j0k1l2. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-26T14:45:00+05:30. Completed at: 2026-09-26T14:50:00+05:30.', '{"status": "SUCCESS", "version": "2.8.1", "service_id": 1, "commit_hash": "i9j0k1l2", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 3, "deployment_type": "NORMAL"}', '2026-09-26 14:45:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (12, 13, NULL, 'deployment', 'Deployment 2.8.0 to production', '2', 'Deployment ID 2 deployed version 2.8.0 to production with status SUCCESS. Commit: e5f6g7h8. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-26T13:40:00+05:30. Completed at: 2026-09-26T13:45:00+05:30.', '{"status": "SUCCESS", "version": "2.8.0", "service_id": 1, "commit_hash": "e5f6g7h8", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 2, "deployment_type": "NORMAL"}', '2026-09-26 13:40:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (13, 13, NULL, 'deployment', 'Deployment 2.7.0 to production', '1', 'Deployment ID 1 deployed version 2.7.0 to production with status SUCCESS. Commit: a1b2c3d4. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-25T13:30:00+05:30. Completed at: 2026-09-25T13:35:00+05:30.', '{"status": "SUCCESS", "version": "2.7.0", "service_id": 1, "commit_hash": "a1b2c3d4", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 1, "deployment_type": "NORMAL"}', '2026-09-25 13:30:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (14, 13, NULL, 'incident_event', 'DEPLOYMENT_DETECTED', '5', 'A recent Payment API deployment was identified before the incident.', '{"version": "2.8.1", "deployment_id": 2}', '2026-09-26 15:01:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (15, 13, NULL, 'incident_event', 'LOG_ANOMALY_DETECTED', '4', 'Repeated database connection timeout errors were detected in Payment API logs.', '{"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}', '2026-09-26 14:59:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (16, 13, NULL, 'incident_event', 'METRIC_THRESHOLD_EXCEEDED', '3', 'Payment API error rate exceeded the configured operational threshold.', '{"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}', '2026-09-26 14:57:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (17, 13, NULL, 'incident_event', 'ENGINEER_ASSIGNED', '2', 'Incident assigned to Priya Sharma for investigation.', '{"assigned_user_id": 2}', '2026-09-26 14:55:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (18, 13, NULL, 'incident_event', 'INCIDENT_CREATED', '1', 'Payment API error rate exceeded the configured threshold and an incident was created.', '{"source": "monitoring", "error_rate": 13.7}', '2026-09-26 14:54:00+05:30', NULL, false, '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (43, 94, NULL, 'deployment', 'Deployment 2.8.1 to production', '3', 'Deployment ID 3 deployed version 2.8.1 to production with status SUCCESS. Commit: i9j0k1l2. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-26T14:45:00+05:30. Completed at: 2026-09-26T14:50:00+05:30.', '{"status": "SUCCESS", "version": "2.8.1", "service_id": 1, "commit_hash": "i9j0k1l2", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 3, "deployment_type": "NORMAL"}', '2026-09-26 14:45:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (44, 94, NULL, 'deployment', 'Deployment 2.8.0 to production', '2', 'Deployment ID 2 deployed version 2.8.0 to production with status SUCCESS. Commit: e5f6g7h8. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-26T13:40:00+05:30. Completed at: 2026-09-26T13:45:00+05:30.', '{"status": "SUCCESS", "version": "2.8.0", "service_id": 1, "commit_hash": "e5f6g7h8", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 2, "deployment_type": "NORMAL"}', '2026-09-26 13:40:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (45, 94, NULL, 'deployment', 'Deployment 2.7.0 to production', '1', 'Deployment ID 1 deployed version 2.7.0 to production with status SUCCESS. Commit: a1b2c3d4. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-25T13:30:00+05:30. Completed at: 2026-09-25T13:35:00+05:30.', '{"status": "SUCCESS", "version": "2.7.0", "service_id": 1, "commit_hash": "a1b2c3d4", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 1, "deployment_type": "NORMAL"}', '2026-09-25 13:30:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (46, 94, NULL, 'incident_event', 'DEPLOYMENT_DETECTED', '5', 'A recent Payment API deployment was identified before the incident.', '{"version": "2.8.1", "deployment_id": 2}', '2026-09-26 15:01:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (47, 94, NULL, 'incident_event', 'LOG_ANOMALY_DETECTED', '4', 'Repeated database connection timeout errors were detected in Payment API logs.', '{"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}', '2026-09-26 14:59:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (48, 94, NULL, 'incident_event', 'METRIC_THRESHOLD_EXCEEDED', '3', 'Payment API error rate exceeded the configured operational threshold.', '{"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}', '2026-09-26 14:57:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (49, 94, NULL, 'incident_event', 'ENGINEER_ASSIGNED', '2', 'Incident assigned to Priya Sharma for investigation.', '{"assigned_user_id": 2}', '2026-09-26 14:55:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (50, 94, NULL, 'incident_event', 'INCIDENT_CREATED', '1', 'Payment API error rate exceeded the configured threshold and an incident was created.', '{"source": "monitoring", "error_rate": 13.7}', '2026-09-26 14:54:00+05:30', NULL, false, '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (66, 145, NULL, 'deployment', 'Deployment 2.8.1 to production', '3', 'Deployment ID 3 deployed version 2.8.1 to production with status SUCCESS. Commit: i9j0k1l2. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-26T14:45:00+05:30. Completed at: 2026-09-26T14:50:00+05:30.', '{"status": "SUCCESS", "version": "2.8.1", "service_id": 1, "commit_hash": "i9j0k1l2", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 3, "deployment_type": "NORMAL"}', '2026-09-26 14:45:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (67, 145, NULL, 'deployment', 'Deployment 2.8.0 to production', '2', 'Deployment ID 2 deployed version 2.8.0 to production with status SUCCESS. Commit: e5f6g7h8. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-26T13:40:00+05:30. Completed at: 2026-09-26T13:45:00+05:30.', '{"status": "SUCCESS", "version": "2.8.0", "service_id": 1, "commit_hash": "e5f6g7h8", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 2, "deployment_type": "NORMAL"}', '2026-09-26 13:40:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (68, 145, NULL, 'deployment', 'Deployment 2.7.0 to production', '1', 'Deployment ID 1 deployed version 2.7.0 to production with status SUCCESS. Commit: a1b2c3d4. Deployment type: NORMAL. Trigger type: CI_CD. Started at: 2026-09-25T13:30:00+05:30. Completed at: 2026-09-25T13:35:00+05:30.', '{"status": "SUCCESS", "version": "2.7.0", "service_id": 1, "commit_hash": "a1b2c3d4", "deployed_by": null, "environment": "production", "trigger_type": "CI_CD", "deployment_id": 1, "deployment_type": "NORMAL"}', '2026-09-25 13:30:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (69, 145, NULL, 'incident_event', 'DEPLOYMENT_DETECTED', '5', 'A recent Payment API deployment was identified before the incident.', '{"version": "2.8.1", "deployment_id": 2}', '2026-09-26 15:01:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (70, 145, NULL, 'incident_event', 'LOG_ANOMALY_DETECTED', '4', 'Repeated database connection timeout errors were detected in Payment API logs.', '{"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}', '2026-09-26 14:59:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (71, 145, NULL, 'incident_event', 'METRIC_THRESHOLD_EXCEEDED', '3', 'Payment API error rate exceeded the configured operational threshold.', '{"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}', '2026-09-26 14:57:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (72, 145, NULL, 'incident_event', 'ENGINEER_ASSIGNED', '2', 'Incident assigned to Priya Sharma for investigation.', '{"assigned_user_id": 2}', '2026-09-26 14:55:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.investigation_evidence OVERRIDING SYSTEM VALUE VALUES (73, 145, NULL, 'incident_event', 'INCIDENT_CREATED', '1', 'Payment API error rate exceeded the configured threshold and an incident was created.', '{"source": "monitoring", "error_rate": 13.7}', '2026-09-26 14:54:00+05:30', NULL, false, '2026-09-27 19:56:58.105181+05:30');


--
-- Data for Name: investigation_findings; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (1, 1, 'OBSERVATION', 'Database connection timeouts detected', 'Repeated database connection timeout errors were observed in Payment API logs during the incident window.', 0.9700, 'PROPOSED', '2026-09-26 15:21:49.43902+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (2, 1, 'HYPOTHESIS', 'Recent deployment temporally associated with incident', 'Payment API version 2.8.1 completed immediately before the incident began. The timing makes the deployment a candidate factor requiring further investigation, but the evidence does not establish causation.', 0.7800, 'PROPOSED', '2026-09-26 15:21:57.664973+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (3, 1, 'RECOMMENDATION', 'Review connection-pool and deployment changes', 'Compare database connection-pool behavior and relevant configuration changes introduced by Payment API version 2.8.1 before considering rollback or other production actions.', 0.8800, 'PROPOSED', '2026-09-26 15:22:06.023848+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (10, 13, 'HIGH', 'The Payment API is experiencing an elevated error rate and increased latency in production, impacting customer payment requests.', 'The Payment API is experiencing an elevated error rate and increased latency in production, impacting customer payment requests.', NULL, 'PROPOSED', '2026-09-27 17:53:43.64689+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (11, 13, 'HIGH', 'The incident started at 2026-09-26T14:50:00+05:30 and was detected at 2026-09-26T14:54:00+05:30 when the error rate exceeded the configured threshold (13.7%).', 'The incident started at 2026-09-26T14:50:00+05:30 and was detected at 2026-09-26T14:54:00+05:30 when the error rate exceeded the configured threshold (13.7%).', NULL, 'PROPOSED', '2026-09-27 17:53:43.64689+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (12, 13, 'HIGH', 'The Payment API error rate continued to exceed the operational threshold, reaching 14.2% by 2026-09-26T14:57:00+05:30.', 'The Payment API error rate continued to exceed the operational threshold, reaching 14.2% by 2026-09-26T14:57:00+05:30.', NULL, 'PROPOSED', '2026-09-27 17:53:43.64689+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (13, 13, 'HIGH', 'Repeated database connection timeout errors have been detected in the Payment API logs.', 'Repeated database connection timeout errors have been detected in the Payment API logs.', NULL, 'PROPOSED', '2026-09-27 17:53:43.64689+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (14, 13, 'HIGH', 'A new version (2.8.1) of the Payment API was successfully deployed to production, completing at 2026-09-26T14:50:00+05:30, which directly correlates with the incident''s start time.', 'A new version (2.8.1) of the Payment API was successfully deployed to production, completing at 2026-09-26T14:50:00+05:30, which directly correlates with the incident''s start time.', NULL, 'PROPOSED', '2026-09-27 17:53:43.64689+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (39, 94, 'HIGH', 'The Payment API is experiencing an elevated error rate and increased latency.', 'The Payment API is experiencing an elevated error rate and increased latency.', NULL, 'PROPOSED', '2026-09-27 19:24:42.340369+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (40, 94, 'HIGH', 'The incident started at 2026-09-26T14:50:00+05:30 and was detected at 2026-09-26T14:54:00+05:30.', 'The incident started at 2026-09-26T14:50:00+05:30 and was detected at 2026-09-26T14:54:00+05:30.', NULL, 'PROPOSED', '2026-09-27 19:24:42.340369+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (41, 94, 'HIGH', 'The Payment API error rate exceeded the configured operational threshold, reaching 13.7% at detection and 14.2% shortly after.', 'The Payment API error rate exceeded the configured operational threshold, reaching 13.7% at detection and 14.2% shortly after.', NULL, 'PROPOSED', '2026-09-27 19:24:42.340369+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (42, 94, 'HIGH', 'Repeated database connection timeout errors have been detected in Payment API logs.', 'Repeated database connection timeout errors have been detected in Payment API logs.', NULL, 'PROPOSED', '2026-09-27 19:24:42.340369+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (43, 94, 'HIGH', 'Payment API version 2.8.1 was successfully deployed to production, completing at 2026-09-26T14:50:00+05:30.', 'Payment API version 2.8.1 was successfully deployed to production, completing at 2026-09-26T14:50:00+05:30.', NULL, 'PROPOSED', '2026-09-27 19:24:42.340369+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (59, 145, 'HIGH', 'An incident was created for the Payment API at 2026-09-26T14:54:00+05:30 because its error rate exceeded the configured threshold, with an initial detected error rate of 13.7%.', 'An incident was created for the Payment API at 2026-09-26T14:54:00+05:30 because its error rate exceeded the configured threshold, with an initial detected error rate of 13.7%.', NULL, 'PROPOSED', '2026-09-27 19:56:58.105181+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (60, 145, 'HIGH', 'The Payment API''s error rate further increased to 14.2%, exceeding the 10.0% operational threshold by 2026-09-26T14:57:00+05:30.', 'The Payment API''s error rate further increased to 14.2%, exceeding the 10.0% operational threshold by 2026-09-26T14:57:00+05:30.', NULL, 'PROPOSED', '2026-09-27 19:56:58.105181+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (61, 145, 'HIGH', 'Repeated database connection timeout errors were detected in Payment API logs starting at 2026-09-26T14:59:00+05:30.', 'Repeated database connection timeout errors were detected in Payment API logs starting at 2026-09-26T14:59:00+05:30.', NULL, 'PROPOSED', '2026-09-27 19:56:58.105181+05:30', 'AI');
INSERT INTO core.investigation_findings OVERRIDING SYSTEM VALUE VALUES (62, 145, 'HIGH', 'Payment API version 2.8.1 was successfully deployed to production, completing at 2026-09-26T14:50:00+05:30.', 'Payment API version 2.8.1 was successfully deployed to production, completing at 2026-09-26T14:50:00+05:30.', NULL, 'PROPOSED', '2026-09-27 19:56:58.105181+05:30', 'AI');


--
-- Data for Name: finding_evidence; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.finding_evidence VALUES (1, 1, 'SUPPORTS', '2026-09-26 15:22:54.696231+05:30');
INSERT INTO core.finding_evidence VALUES (1, 3, 'SUPPORTS', '2026-09-26 15:22:54.696231+05:30');
INSERT INTO core.finding_evidence VALUES (2, 2, 'SUPPORTS', '2026-09-26 15:22:54.696231+05:30');
INSERT INTO core.finding_evidence VALUES (2, 3, 'CONTEXT', '2026-09-26 15:22:54.696231+05:30');
INSERT INTO core.finding_evidence VALUES (3, 1, 'SUPPORTS', '2026-09-26 15:22:54.696231+05:30');
INSERT INTO core.finding_evidence VALUES (3, 2, 'CONTEXT', '2026-09-26 15:22:54.696231+05:30');
INSERT INTO core.finding_evidence VALUES (11, 18, 'SUPPORTS', '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.finding_evidence VALUES (12, 16, 'SUPPORTS', '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.finding_evidence VALUES (13, 15, 'SUPPORTS', '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.finding_evidence VALUES (14, 11, 'SUPPORTS', '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.finding_evidence VALUES (40, 50, 'SUPPORTS', '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.finding_evidence VALUES (41, 50, 'SUPPORTS', '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.finding_evidence VALUES (41, 48, 'SUPPORTS', '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.finding_evidence VALUES (42, 47, 'SUPPORTS', '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.finding_evidence VALUES (43, 43, 'SUPPORTS', '2026-09-27 19:24:42.340369+05:30');
INSERT INTO core.finding_evidence VALUES (59, 73, 'SUPPORTS', '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.finding_evidence VALUES (60, 71, 'SUPPORTS', '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.finding_evidence VALUES (61, 70, 'SUPPORTS', '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.finding_evidence VALUES (62, 66, 'SUPPORTS', '2026-09-27 19:56:58.105181+05:30');


--
-- Data for Name: incident_events; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.incident_events OVERRIDING SYSTEM VALUE VALUES (1, 1, 'INCIDENT_CREATED', 'Payment API error rate exceeded the configured threshold and an incident was created.', '2026-09-26 14:54:00+05:30', NULL, '{"source": "monitoring", "error_rate": 13.7}', '2026-09-26 14:37:17.060503+05:30');
INSERT INTO core.incident_events OVERRIDING SYSTEM VALUE VALUES (2, 1, 'ENGINEER_ASSIGNED', 'Incident assigned to Priya Sharma for investigation.', '2026-09-26 14:55:00+05:30', 2, '{"assigned_user_id": 2}', '2026-09-26 14:37:26.969863+05:30');
INSERT INTO core.incident_events OVERRIDING SYSTEM VALUE VALUES (3, 1, 'METRIC_THRESHOLD_EXCEEDED', 'Payment API error rate exceeded the configured operational threshold.', '2026-09-26 14:57:00+05:30', NULL, '{"unit": "percent", "value": 14.2, "metric": "error_rate", "threshold": 10.0}', '2026-09-26 14:37:36.543919+05:30');
INSERT INTO core.incident_events OVERRIDING SYSTEM VALUE VALUES (4, 1, 'LOG_ANOMALY_DETECTED', 'Repeated database connection timeout errors were detected in Payment API logs.', '2026-09-26 14:59:00+05:30', NULL, '{"service": "payment-api", "error_type": "DATABASE_CONNECTION_TIMEOUT"}', '2026-09-26 14:37:46.294038+05:30');
INSERT INTO core.incident_events OVERRIDING SYSTEM VALUE VALUES (5, 1, 'DEPLOYMENT_DETECTED', 'A recent Payment API deployment was identified before the incident.', '2026-09-26 15:01:00+05:30', NULL, '{"version": "2.8.1", "deployment_id": 2}', '2026-09-26 14:37:55.401092+05:30');


--
-- Data for Name: investigation_feedback; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.investigation_feedback OVERRIDING SYSTEM VALUE VALUES (1, 1, NULL, 2, 'OVERALL', 4, true, 'The investigation was useful because it quickly surfaced the database timeout evidence and recent deployment information.', '2026-09-26 15:27:37.137003+05:30');
INSERT INTO core.investigation_feedback OVERRIDING SYSTEM VALUE VALUES (2, 1, 2, 2, 'FINDING', 4, true, 'The deployment hypothesis was useful as a lead, but it should remain explicitly unconfirmed because the evidence only establishes temporal association.', '2026-09-26 15:27:46.087471+05:30');
INSERT INTO core.investigation_feedback OVERRIDING SYSTEM VALUE VALUES (3, 1, NULL, 2, 'EVIDENCE', 5, true, 'The log evidence was directly relevant to the investigation and matched the observed incident symptoms.', '2026-09-26 15:27:54.130134+05:30');
INSERT INTO core.investigation_feedback OVERRIDING SYSTEM VALUE VALUES (4, 1, NULL, 2, 'RECOMMENDATION', 4, true, 'The recommendation provided a useful investigation path without immediately recommending an irreversible production action.', '2026-09-26 15:28:01.493667+05:30');


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (1, 'INCIDENT_VIEW', 'View incident details', 'INCIDENT', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (2, 'INCIDENT_SEARCH', 'Search and filter incidents', 'INCIDENT', 'SEARCH', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (3, 'INCIDENT_ASSIGN', 'Assign incidents to teams or engineers', 'INCIDENT', 'ASSIGN', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (4, 'INCIDENT_UPDATE', 'Update incident information', 'INCIDENT', 'UPDATE', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (5, 'LOG_VIEW', 'View application logs', 'LOG', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (6, 'LOG_SEARCH', 'Search application logs', 'LOG', 'SEARCH', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (7, 'METRICS_VIEW', 'View service metrics', 'METRICS', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (8, 'DEPLOYMENT_VIEW', 'View deployment history', 'DEPLOYMENT', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (9, 'RUNBOOK_SEARCH', 'Search operational runbooks', 'RUNBOOK', 'SEARCH', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (10, 'TICKET_VIEW', 'View tickets', 'TICKET', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (11, 'TICKET_CREATE', 'Create tickets', 'TICKET', 'CREATE', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (12, 'TICKET_UPDATE', 'Update tickets', 'TICKET', 'UPDATE', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (13, 'TICKET_ASSIGN', 'Assign tickets', 'TICKET', 'ASSIGN', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (14, 'RISK_PREDICTION_VIEW', 'View incident risk predictions', 'RISK_PREDICTION', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (15, 'ACTION_REQUEST', 'Request a sensitive operational action', 'ACTION', 'REQUEST', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (16, 'ACTION_APPROVE', 'Approve a sensitive operational action', 'ACTION', 'APPROVE', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (17, 'AUDIT_VIEW', 'View audit records', 'AUDIT', 'VIEW', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (18, 'USER_MANAGE', 'Manage application users', 'USER', 'MANAGE', true, '2026-09-26 13:49:14.125095+05:30');
INSERT INTO core.permissions OVERRIDING SYSTEM VALUE VALUES (19, 'ROLE_MANAGE', 'Manage application roles', 'ROLE', 'MANAGE', true, '2026-09-26 13:49:14.125095+05:30');


--
-- Data for Name: risk_predictions; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.risk_predictions OVERRIDING SYSTEM VALUE VALUES (1, 1, 1, 'incident_risk_xgboost', '0.1.0-dev', 'INCIDENT_ESCALATION', 0.8700, 'CRITICAL', '{"error_rate": 14.2, "recent_deployment": true, "service_criticality": "CRITICAL", "unhealthy_instances": 1}', 'Development sample prediction based on elevated error rate, critical service classification, an unhealthy instance, and recent deployment activity.', '2026-09-26 15:25:08.760232+05:30', '2026-09-26 15:25:08.760232+05:30');
INSERT INTO core.risk_predictions OVERRIDING SYSTEM VALUE VALUES (188, 145, 1, 'incident_risk_baseline', '1.0.0', 'INCIDENT_ESCALATION', 0.7000, 'HIGH', '{"status": "INVESTIGATING", "severity": "HIGH", "event_count": 5, "timeout_count": 1, "recent_deployment": true, "error_rate_percent": 13.7}', 'High incident severity. A timeout-related event was observed. Error rate exceeded 10%. A recent deployment was associated with the incident timeline.', '2026-09-27 19:57:25.842597+05:30', '2026-09-27 19:56:58.105181+05:30');
INSERT INTO core.risk_predictions OVERRIDING SYSTEM VALUE VALUES (76, 13, 1, 'incident_risk_baseline', '1.0.0', 'INCIDENT_ESCALATION', 0.7000, 'HIGH', '{"status": "INVESTIGATING", "severity": "HIGH", "event_count": 5, "timeout_count": 1, "recent_deployment": true, "error_rate_percent": 13.7}', 'High incident severity. A timeout-related event was observed. Error rate exceeded 10%. A recent deployment was associated with the incident timeline.', '2026-09-27 17:53:56.068937+05:30', '2026-09-27 17:53:43.64689+05:30');
INSERT INTO core.risk_predictions OVERRIDING SYSTEM VALUE VALUES (147, 94, 1, 'incident_risk_baseline', '1.0.0', 'INCIDENT_ESCALATION', 0.7000, 'HIGH', '{"status": "INVESTIGATING", "severity": "HIGH", "event_count": 5, "timeout_count": 1, "recent_deployment": true, "error_rate_percent": 13.7}', 'High incident severity. A timeout-related event was observed. Error rate exceeded 10%. A recent deployment was associated with the incident timeline.', '2026-09-27 19:24:54.30335+05:30', '2026-09-27 19:24:42.340369+05:30');


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.role_permissions VALUES (1, 1, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 2, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 5, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 6, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 7, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 8, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 9, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 10, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 11, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (1, 14, '2026-09-26 13:52:48.812991+05:30');
INSERT INTO core.role_permissions VALUES (2, 1, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 2, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 3, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 4, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 5, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 6, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 7, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 8, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 9, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 10, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 11, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 12, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 13, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 14, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (2, 15, '2026-09-26 13:53:50.381477+05:30');
INSERT INTO core.role_permissions VALUES (3, 1, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 2, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 3, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 4, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 5, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 6, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 7, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 8, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 9, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 10, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 11, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 12, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 13, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 14, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 15, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (3, 16, '2026-09-26 13:54:00.714231+05:30');
INSERT INTO core.role_permissions VALUES (4, 1, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 2, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 3, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 4, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 5, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 6, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 7, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 8, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 9, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 10, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 11, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 12, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 13, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 14, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 15, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 16, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 17, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 18, '2026-09-26 13:54:15.025307+05:30');
INSERT INTO core.role_permissions VALUES (4, 19, '2026-09-26 13:54:15.025307+05:30');


--
-- Data for Name: servers; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.servers OVERRIDING SYSTEM VALUE VALUES (1, 'ops-prod-01', '10.0.1.10', 'production', 'ap-south-1', 't3.large', 'Ubuntu 24.04', 'RUNNING', '2026-09-26 14:22:26.853395+05:30', '2026-09-26 14:22:26.853395+05:30');
INSERT INTO core.servers OVERRIDING SYSTEM VALUE VALUES (2, 'ops-prod-02', '10.0.1.11', 'production', 'ap-south-1', 't3.large', 'Ubuntu 24.04', 'RUNNING', '2026-09-26 14:22:26.853395+05:30', '2026-09-26 14:22:26.853395+05:30');
INSERT INTO core.servers OVERRIDING SYSTEM VALUE VALUES (3, 'ops-prod-03', '10.0.1.12', 'production', 'ap-south-1', 'c7i.large', 'Ubuntu 24.04', 'RUNNING', '2026-09-26 14:22:26.853395+05:30', '2026-09-26 14:22:26.853395+05:30');
INSERT INTO core.servers OVERRIDING SYSTEM VALUE VALUES (4, 'ops-staging-01', '10.0.2.10', 'staging', 'ap-south-1', 't3.medium', 'Ubuntu 24.04', 'RUNNING', '2026-09-26 14:22:26.853395+05:30', '2026-09-26 14:22:26.853395+05:30');


--
-- Data for Name: service_dependencies; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.service_dependencies OVERRIDING SYSTEM VALUE VALUES (1, 1, 3, 'API', 'CRITICAL', true, '2026-09-26 14:29:47.849064+05:30');
INSERT INTO core.service_dependencies OVERRIDING SYSTEM VALUE VALUES (2, 1, 4, 'API', 'HIGH', true, '2026-09-26 14:29:47.849064+05:30');
INSERT INTO core.service_dependencies OVERRIDING SYSTEM VALUE VALUES (3, 2, 3, 'API', 'CRITICAL', true, '2026-09-26 14:29:47.849064+05:30');
INSERT INTO core.service_dependencies OVERRIDING SYSTEM VALUE VALUES (4, 2, 6, 'API', 'HIGH', true, '2026-09-26 14:29:47.849064+05:30');
INSERT INTO core.service_dependencies OVERRIDING SYSTEM VALUE VALUES (5, 5, 3, 'API', 'MEDIUM', true, '2026-09-26 14:29:47.849064+05:30');


--
-- Data for Name: service_instances; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (1, 1, 1, 'payment-api-01', 8080, 'RUNNING', '2026-09-26 13:30:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (2, 1, 2, 'payment-api-02', 8080, 'RUNNING', '2026-09-26 13:35:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (3, 1, 3, 'payment-api-03', 8080, 'UNHEALTHY', '2026-09-26 13:40:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (4, 2, 1, 'order-service-01', 8081, 'RUNNING', '2026-09-26 13:00:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (5, 2, 2, 'order-service-02', 8081, 'RUNNING', '2026-09-26 13:05:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (6, 3, 2, 'auth-service-01', 8082, 'RUNNING', '2026-09-26 12:30:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (7, 4, 3, 'fraud-service-01', 8083, 'RUNNING', '2026-09-26 12:45:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');
INSERT INTO core.service_instances OVERRIDING SYSTEM VALUE VALUES (8, 5, 3, 'notification-service-01', 8084, 'RUNNING', '2026-09-26 12:50:00+05:30', NULL, '2026-09-26 14:25:00.376075+05:30');


--
-- Data for Name: ticket_comments; Type: TABLE DATA; Schema: core; Owner: -
--

INSERT INTO core.ticket_comments OVERRIDING SYSTEM VALUE VALUES (1, 1, 2, 'Initial review shows repeated database connection timeout errors in Payment API logs.', '2026-09-26 15:11:05.71298+05:30');
INSERT INTO core.ticket_comments OVERRIDING SYSTEM VALUE VALUES (2, 1, 3, 'Database team is checking connection pool utilization and recent configuration changes.', '2026-09-26 15:11:05.71298+05:30');
INSERT INTO core.ticket_comments OVERRIDING SYSTEM VALUE VALUES (3, 1, 2, 'Deployment history is also being reviewed because version 2.8.1 completed immediately before the incident started.', '2026-09-26 15:11:05.71298+05:30');


--
-- Name: audit_logs_audit_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.audit_logs_audit_id_seq', 891, true);


--
-- Name: deployments_deployment_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.deployments_deployment_id_seq', 6, true);


--
-- Name: incident_events_event_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.incident_events_event_id_seq', 6, true);


--
-- Name: incidents_incident_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.incidents_incident_id_seq', 2, true);


--
-- Name: investigation_evidence_evidence_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.investigation_evidence_evidence_id_seq', 208, true);


--
-- Name: investigation_feedback_feedback_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.investigation_feedback_feedback_id_seq', 4, true);


--
-- Name: investigation_findings_finding_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.investigation_findings_finding_id_seq', 142, true);


--
-- Name: investigation_steps_step_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.investigation_steps_step_id_seq', 6, true);


--
-- Name: investigations_investigation_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.investigations_investigation_id_seq', 375, true);


--
-- Name: knowledge_document_versions_version_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.knowledge_document_versions_version_id_seq', 363, true);


--
-- Name: knowledge_documents_document_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.knowledge_documents_document_id_seq', 310, true);


--
-- Name: permissions_permission_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.permissions_permission_id_seq', 19, true);


--
-- Name: risk_predictions_prediction_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.risk_predictions_prediction_id_seq', 310, true);


--
-- Name: roles_role_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.roles_role_id_seq', 6, true);


--
-- Name: servers_server_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.servers_server_id_seq', 4, true);


--
-- Name: service_dependencies_dependency_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.service_dependencies_dependency_id_seq', 6, true);


--
-- Name: service_instances_instance_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.service_instances_instance_id_seq', 12, true);


--
-- Name: services_service_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.services_service_id_seq', 12, true);


--
-- Name: teams_team_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.teams_team_id_seq', 5, true);


--
-- Name: ticket_comments_comment_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.ticket_comments_comment_id_seq', 4, true);


--
-- Name: tickets_ticket_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.tickets_ticket_id_seq', 5, true);


--
-- Name: tool_calls_tool_call_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.tool_calls_tool_call_id_seq', 174, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: core; Owner: -
--

SELECT pg_catalog.setval('core.users_user_id_seq', 7, true);


--
-- PostgreSQL database dump complete
--



COMMIT;
