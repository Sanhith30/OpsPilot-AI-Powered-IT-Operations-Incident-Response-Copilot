BEGIN;

--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
-- SET transaction_timeout = 0; (PostgreSQL 17+ only)
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_owner') THEN
        CREATE ROLE opspilot_owner;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_agent_ro') THEN
        CREATE ROLE opspilot_agent_ro;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'opspilot_app') THEN
        CREATE ROLE opspilot_app;
    END IF;
END
$$;

--
-- Name: core; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS core;


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: core; Owner: -
--

CREATE FUNCTION core.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_logs; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.audit_logs (
    audit_id bigint NOT NULL,
    actor_user_id bigint,
    actor_type character varying(20) NOT NULL,
    action character varying(100) NOT NULL,
    resource_type character varying(50),
    resource_id character varying(100),
    incident_id bigint,
    investigation_id bigint,
    ticket_id bigint,
    action_result character varying(20) NOT NULL,
    request_id character varying(100),
    ip_address inet,
    user_agent text,
    details jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_audit_logs_action_result CHECK (((action_result)::text = ANY ((ARRAY['SUCCESS'::character varying, 'FAILURE'::character varying, 'DENIED'::character varying])::text[]))),
    CONSTRAINT ck_audit_logs_actor_type CHECK (((actor_type)::text = ANY ((ARRAY['USER'::character varying, 'AI'::character varying, 'SYSTEM'::character varying])::text[])))
);


--
-- Name: audit_logs_audit_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.audit_logs ALTER COLUMN audit_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.audit_logs_audit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: deployments; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.deployments (
    deployment_id bigint NOT NULL,
    service_id bigint NOT NULL,
    version character varying(50) NOT NULL,
    environment character varying(30) NOT NULL,
    commit_hash character varying(100),
    deployment_type character varying(30) NOT NULL,
    trigger_type character varying(30) NOT NULL,
    status character varying(30) NOT NULL,
    deployed_by bigint,
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_deployments_environment CHECK (((environment)::text = ANY ((ARRAY['development'::character varying, 'staging'::character varying, 'production'::character varying])::text[]))),
    CONSTRAINT chk_deployments_status CHECK (((status)::text = ANY ((ARRAY['IN_PROGRESS'::character varying, 'SUCCESS'::character varying, 'FAILED'::character varying, 'CANCELLED'::character varying])::text[]))),
    CONSTRAINT chk_deployments_time CHECK (((completed_at IS NULL) OR (completed_at >= started_at))),
    CONSTRAINT chk_deployments_trigger CHECK (((trigger_type)::text = ANY ((ARRAY['MANUAL'::character varying, 'CI_CD'::character varying, 'AUTOMATED'::character varying])::text[]))),
    CONSTRAINT chk_deployments_type CHECK (((deployment_type)::text = ANY ((ARRAY['NORMAL'::character varying, 'HOTFIX'::character varying, 'ROLLBACK'::character varying, 'EMERGENCY'::character varying])::text[])))
);


--
-- Name: deployments_deployment_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.deployments ALTER COLUMN deployment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.deployments_deployment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: finding_evidence; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.finding_evidence (
    finding_id bigint NOT NULL,
    evidence_id bigint NOT NULL,
    relationship_type character varying(30) DEFAULT 'SUPPORTS'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_finding_evidence_relationship CHECK (((relationship_type)::text = ANY ((ARRAY['SUPPORTS'::character varying, 'CONTRADICTS'::character varying, 'CONTEXT'::character varying])::text[])))
);


--
-- Name: incident_events; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.incident_events (
    event_id bigint NOT NULL,
    incident_id bigint NOT NULL,
    event_type character varying(50) NOT NULL,
    event_message text NOT NULL,
    event_timestamp timestamp with time zone NOT NULL,
    created_by bigint,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_incident_events_type CHECK (((event_type)::text = ANY ((ARRAY['INCIDENT_CREATED'::character varying, 'ENGINEER_ASSIGNED'::character varying, 'SEVERITY_CHANGED'::character varying, 'STATUS_CHANGED'::character varying, 'METRIC_THRESHOLD_EXCEEDED'::character varying, 'LOG_ANOMALY_DETECTED'::character varying, 'DEPLOYMENT_DETECTED'::character varying, 'MITIGATION_APPLIED'::character varying, 'APPROVAL_REQUESTED'::character varying, 'APPROVAL_GRANTED'::character varying, 'APPROVAL_REJECTED'::character varying, 'INCIDENT_RESOLVED'::character varying])::text[])))
);


--
-- Name: incident_events_event_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.incident_events ALTER COLUMN event_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.incident_events_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: incidents; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.incidents (
    incident_id bigint NOT NULL,
    incident_number character varying(30) NOT NULL,
    service_id bigint NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    severity character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    started_at timestamp with time zone NOT NULL,
    detected_at timestamp with time zone NOT NULL,
    resolved_at timestamp with time zone,
    assigned_team_id bigint NOT NULL,
    assigned_user_id bigint,
    impact_summary text,
    root_cause text,
    root_cause_confirmed_by bigint,
    root_cause_confirmed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_incidents_detection_time CHECK ((detected_at >= started_at)),
    CONSTRAINT chk_incidents_resolution_time CHECK (((resolved_at IS NULL) OR (resolved_at >= started_at))),
    CONSTRAINT chk_incidents_root_cause_confirmation CHECK ((((root_cause_confirmed_by IS NULL) AND (root_cause_confirmed_at IS NULL)) OR ((root_cause_confirmed_by IS NOT NULL) AND (root_cause_confirmed_at IS NOT NULL)))),
    CONSTRAINT chk_incidents_severity CHECK (((severity)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT chk_incidents_status CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'INVESTIGATING'::character varying, 'MITIGATED'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying])::text[])))
);


--
-- Name: incidents_incident_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.incidents ALTER COLUMN incident_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.incidents_incident_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: investigation_evidence; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.investigation_evidence (
    evidence_id bigint NOT NULL,
    investigation_id bigint NOT NULL,
    tool_call_id bigint,
    evidence_type character varying(30) NOT NULL,
    source_name character varying(100) NOT NULL,
    source_reference character varying(255),
    evidence_text text NOT NULL,
    structured_data jsonb,
    observed_at timestamp with time zone,
    relevance_score numeric(5,4),
    is_selected boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_investigation_evidence_relevance CHECK (((relevance_score IS NULL) OR ((relevance_score >= (0)::numeric) AND (relevance_score <= (1)::numeric)))),
    CONSTRAINT ck_investigation_evidence_type CHECK ((upper((evidence_type)::text) = ANY (ARRAY['INCIDENT'::text, 'LOG'::text, 'METRIC'::text, 'DEPLOYMENT'::text, 'RUNBOOK'::text, 'TICKET'::text, 'TRACE'::text, 'ML_PREDICTION'::text, 'SYSTEM'::text, 'INCIDENT_EVENT'::text])))
);


--
-- Name: investigation_evidence_evidence_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.investigation_evidence ALTER COLUMN evidence_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.investigation_evidence_evidence_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: investigation_feedback; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.investigation_feedback (
    feedback_id bigint NOT NULL,
    investigation_id bigint NOT NULL,
    finding_id bigint,
    submitted_by bigint NOT NULL,
    feedback_type character varying(30) NOT NULL,
    rating smallint,
    is_helpful boolean,
    feedback_text text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_investigation_feedback_rating CHECK (((rating IS NULL) OR ((rating >= 1) AND (rating <= 5)))),
    CONSTRAINT ck_investigation_feedback_type CHECK (((feedback_type)::text = ANY ((ARRAY['OVERALL'::character varying, 'FINDING'::character varying, 'EVIDENCE'::character varying, 'RECOMMENDATION'::character varying])::text[])))
);


--
-- Name: investigation_feedback_feedback_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.investigation_feedback ALTER COLUMN feedback_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.investigation_feedback_feedback_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: investigation_findings; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.investigation_findings (
    finding_id bigint NOT NULL,
    investigation_id bigint NOT NULL,
    finding_type character varying(30) NOT NULL,
    title character varying(200) NOT NULL,
    finding_text text NOT NULL,
    confidence_score numeric(5,4),
    status character varying(30) DEFAULT 'PROPOSED'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(30) DEFAULT 'AI'::character varying NOT NULL,
    CONSTRAINT ck_investigation_findings_confidence CHECK (((confidence_score IS NULL) OR ((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric)))),
    CONSTRAINT ck_investigation_findings_created_by CHECK (((created_by)::text = ANY ((ARRAY['AI'::character varying, 'USER'::character varying, 'SYSTEM'::character varying])::text[]))),
    CONSTRAINT ck_investigation_findings_status CHECK (((status)::text = ANY ((ARRAY['PROPOSED'::character varying, 'ACCEPTED'::character varying, 'REJECTED'::character varying, 'CONFIRMED'::character varying])::text[]))),
    CONSTRAINT ck_investigation_findings_type CHECK ((upper((finding_type)::text) = ANY (ARRAY['OBSERVATION'::text, 'HYPOTHESIS'::text, 'RECOMMENDATION'::text, 'ROOT_CAUSE'::text, 'HIGH'::text, 'MEDIUM'::text, 'LOW'::text])))
);


--
-- Name: investigation_findings_finding_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.investigation_findings ALTER COLUMN finding_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.investigation_findings_finding_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: investigation_steps; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.investigation_steps (
    step_id bigint NOT NULL,
    investigation_id bigint NOT NULL,
    step_number integer NOT NULL,
    step_type character varying(50) NOT NULL,
    description text,
    status character varying(30) NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    title character varying(255) DEFAULT 'Step'::character varying,
    CONSTRAINT ck_investigation_steps_completed_at CHECK (((completed_at IS NULL) OR (completed_at >= started_at))),
    CONSTRAINT ck_investigation_steps_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'RUNNING'::character varying, 'COMPLETED'::character varying, 'FAILED'::character varying, 'SKIPPED'::character varying])::text[]))),
    CONSTRAINT ck_investigation_steps_type CHECK (((step_type)::text = ANY ((ARRAY['INCIDENT_QUERY'::character varying, 'LOG_SEARCH'::character varying, 'METRIC_QUERY'::character varying, 'DEPLOYMENT_QUERY'::character varying, 'RUNBOOK_SEARCH'::character varying, 'RISK_PREDICTION'::character varying, 'TICKET_ACTION'::character varying, 'SYNTHESIS'::character varying])::text[])))
);


--
-- Name: investigation_steps_step_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.investigation_steps ALTER COLUMN step_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.investigation_steps_step_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: investigations; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.investigations (
    investigation_id bigint NOT NULL,
    incident_id bigint NOT NULL,
    initiated_by bigint,
    investigation_type character varying(30) NOT NULL,
    user_question text NOT NULL,
    status character varying(30) NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    final_summary text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT ck_investigations_completed_at CHECK (((completed_at IS NULL) OR (completed_at >= started_at))),
    CONSTRAINT ck_investigations_status CHECK (((status)::text = ANY ((ARRAY['STARTED'::character varying, 'RUNNING'::character varying, 'COMPLETED'::character varying, 'FAILED'::character varying, 'CANCELLED'::character varying])::text[]))),
    CONSTRAINT ck_investigations_type CHECK (((investigation_type)::text = ANY ((ARRAY['MANUAL'::character varying, 'ASSISTED'::character varying, 'AUTOMATED'::character varying])::text[])))
);


--
-- Name: investigations_investigation_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.investigations ALTER COLUMN investigation_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.investigations_investigation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: knowledge_document_versions_version_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.knowledge_document_versions_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: knowledge_documents_document_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

CREATE SEQUENCE core.knowledge_documents_document_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: permissions; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.permissions (
    permission_id bigint NOT NULL,
    permission_code character varying(100) NOT NULL,
    description text,
    resource character varying(50) NOT NULL,
    action character varying(50) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: permissions_permission_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.permissions ALTER COLUMN permission_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.permissions_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: risk_predictions; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.risk_predictions (
    prediction_id bigint NOT NULL,
    investigation_id bigint NOT NULL,
    incident_id bigint NOT NULL,
    model_name character varying(100) NOT NULL,
    model_version character varying(50) NOT NULL,
    prediction_type character varying(50) NOT NULL,
    risk_score numeric(5,4) NOT NULL,
    risk_level character varying(20) NOT NULL,
    input_features jsonb,
    prediction_explanation text,
    predicted_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_risk_predictions_level CHECK (((risk_level)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT ck_risk_predictions_score CHECK (((risk_score >= (0)::numeric) AND (risk_score <= (1)::numeric))),
    CONSTRAINT ck_risk_predictions_type CHECK (((prediction_type)::text = ANY ((ARRAY['INCIDENT_ESCALATION'::character varying, 'SERVICE_FAILURE'::character varying, 'CUSTOM'::character varying])::text[])))
);


--
-- Name: risk_predictions_prediction_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.risk_predictions ALTER COLUMN prediction_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.risk_predictions_prediction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: role_permissions; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.role_permissions (
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: roles; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.roles (
    role_id bigint NOT NULL,
    role_name character varying(50) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: roles_role_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.roles ALTER COLUMN role_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.roles_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: servers; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.servers (
    server_id bigint NOT NULL,
    hostname character varying(100) NOT NULL,
    ip_address inet NOT NULL,
    environment character varying(30) NOT NULL,
    region character varying(50) NOT NULL,
    instance_type character varying(50),
    os_name character varying(100) NOT NULL,
    status character varying(30) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_servers_environment CHECK (((environment)::text = ANY ((ARRAY['development'::character varying, 'staging'::character varying, 'production'::character varying])::text[]))),
    CONSTRAINT chk_servers_status CHECK (((status)::text = ANY ((ARRAY['RUNNING'::character varying, 'STOPPED'::character varying, 'DEGRADED'::character varying, 'MAINTENANCE'::character varying])::text[])))
);


--
-- Name: servers_server_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.servers ALTER COLUMN server_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.servers_server_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: service_dependencies; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.service_dependencies (
    dependency_id bigint NOT NULL,
    service_id bigint NOT NULL,
    depends_on_service_id bigint NOT NULL,
    dependency_type character varying(30) NOT NULL,
    criticality character varying(20) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_service_dependency_criticality CHECK (((criticality)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT chk_service_dependency_not_self CHECK ((service_id <> depends_on_service_id)),
    CONSTRAINT chk_service_dependency_type CHECK (((dependency_type)::text = ANY ((ARRAY['API'::character varying, 'DATABASE'::character varying, 'MESSAGE_QUEUE'::character varying, 'CACHE'::character varying, 'EXTERNAL_SERVICE'::character varying, 'STORAGE'::character varying])::text[])))
);


--
-- Name: service_dependencies_dependency_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.service_dependencies ALTER COLUMN dependency_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.service_dependencies_dependency_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: service_instances; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.service_instances (
    instance_id bigint NOT NULL,
    service_id bigint NOT NULL,
    server_id bigint NOT NULL,
    instance_name character varying(100) NOT NULL,
    port integer NOT NULL,
    status character varying(30) NOT NULL,
    started_at timestamp with time zone NOT NULL,
    stopped_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_service_instances_port CHECK (((port >= 1) AND (port <= 65535))),
    CONSTRAINT chk_service_instances_status CHECK (((status)::text = ANY ((ARRAY['RUNNING'::character varying, 'STOPPED'::character varying, 'UNHEALTHY'::character varying, 'STARTING'::character varying])::text[]))),
    CONSTRAINT chk_service_instances_time CHECK (((stopped_at IS NULL) OR (stopped_at >= started_at)))
);


--
-- Name: service_instances_instance_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.service_instances ALTER COLUMN instance_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.service_instances_instance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: services; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.services (
    service_id bigint NOT NULL,
    service_name character varying(100) NOT NULL,
    service_code character varying(50) NOT NULL,
    description text,
    environment character varying(30) NOT NULL,
    status character varying(30) NOT NULL,
    criticality character varying(20) NOT NULL,
    owner_team_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_services_criticality CHECK (((criticality)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT chk_services_environment CHECK (((environment)::text = ANY ((ARRAY['development'::character varying, 'staging'::character varying, 'production'::character varying])::text[]))),
    CONSTRAINT chk_services_status CHECK (((status)::text = ANY ((ARRAY['ACTIVE'::character varying, 'DEGRADED'::character varying, 'DOWN'::character varying, 'MAINTENANCE'::character varying])::text[])))
);


--
-- Name: services_service_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.services ALTER COLUMN service_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.services_service_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: teams; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.teams (
    team_id bigint NOT NULL,
    team_name character varying(100) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    manager_user_id bigint
);


--
-- Name: teams_team_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.teams ALTER COLUMN team_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.teams_team_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ticket_comments; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.ticket_comments (
    comment_id bigint NOT NULL,
    ticket_id bigint NOT NULL,
    author_id bigint NOT NULL,
    comment_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ticket_comments_comment_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.ticket_comments ALTER COLUMN comment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.ticket_comments_comment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tickets; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.tickets (
    ticket_id bigint NOT NULL,
    ticket_number character varying(30) NOT NULL,
    incident_id bigint,
    title character varying(200) NOT NULL,
    description text,
    priority character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    assigned_team_id bigint,
    assigned_user_id bigint,
    created_by bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    resolution_notes text,
    CONSTRAINT ck_tickets_priority CHECK (((priority)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'URGENT'::character varying])::text[]))),
    CONSTRAINT ck_tickets_resolved_at CHECK (((resolved_at IS NULL) OR (resolved_at >= created_at))),
    CONSTRAINT ck_tickets_status CHECK (((status)::text = ANY ((ARRAY['OPEN'::character varying, 'IN_PROGRESS'::character varying, 'BLOCKED'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying])::text[])))
);


--
-- Name: tickets_ticket_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.tickets ALTER COLUMN ticket_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.tickets_ticket_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tool_calls; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.tool_calls (
    tool_call_id bigint NOT NULL,
    investigation_id bigint NOT NULL,
    step_id bigint,
    tool_name character varying(100) NOT NULL,
    tool_version character varying(30),
    input_payload jsonb,
    output_summary text,
    status character varying(30) NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    duration_ms integer,
    error_code character varying(50),
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    tool_type character varying(50) DEFAULT 'AI_GRAPH_TOOL'::character varying,
    output_payload jsonb,
    CONSTRAINT ck_tool_calls_completed_at CHECK (((completed_at IS NULL) OR (completed_at >= started_at))),
    CONSTRAINT ck_tool_calls_duration CHECK (((duration_ms IS NULL) OR (duration_ms >= 0))),
    CONSTRAINT ck_tool_calls_status CHECK (((status)::text = ANY ((ARRAY['SUCCESS'::character varying, 'FAILED'::character varying, 'TIMEOUT'::character varying, 'DENIED'::character varying])::text[])))
);


--
-- Name: tool_calls_tool_call_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.tool_calls ALTER COLUMN tool_call_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.tool_calls_tool_call_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: users; Type: TABLE; Schema: core; Owner: -
--

CREATE TABLE core.users (
    user_id bigint NOT NULL,
    full_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role_id bigint NOT NULL,
    team_id bigint,
    is_active boolean DEFAULT true NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: core; Owner: -
--

ALTER TABLE core.users ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME core.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: audit_logs pk_audit_logs; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.audit_logs
    ADD CONSTRAINT pk_audit_logs PRIMARY KEY (audit_id);


--
-- Name: deployments pk_deployments; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.deployments
    ADD CONSTRAINT pk_deployments PRIMARY KEY (deployment_id);


--
-- Name: finding_evidence pk_finding_evidence; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.finding_evidence
    ADD CONSTRAINT pk_finding_evidence PRIMARY KEY (finding_id, evidence_id);


--
-- Name: incident_events pk_incident_events; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incident_events
    ADD CONSTRAINT pk_incident_events PRIMARY KEY (event_id);


--
-- Name: incidents pk_incidents; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incidents
    ADD CONSTRAINT pk_incidents PRIMARY KEY (incident_id);


--
-- Name: investigation_evidence pk_investigation_evidence; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_evidence
    ADD CONSTRAINT pk_investigation_evidence PRIMARY KEY (evidence_id);


--
-- Name: investigation_feedback pk_investigation_feedback; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_feedback
    ADD CONSTRAINT pk_investigation_feedback PRIMARY KEY (feedback_id);


--
-- Name: investigation_findings pk_investigation_findings; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_findings
    ADD CONSTRAINT pk_investigation_findings PRIMARY KEY (finding_id);


--
-- Name: investigation_steps pk_investigation_steps; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_steps
    ADD CONSTRAINT pk_investigation_steps PRIMARY KEY (step_id);


--
-- Name: investigations pk_investigations; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigations
    ADD CONSTRAINT pk_investigations PRIMARY KEY (investigation_id);


--
-- Name: permissions pk_permissions; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.permissions
    ADD CONSTRAINT pk_permissions PRIMARY KEY (permission_id);


--
-- Name: risk_predictions pk_risk_predictions; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.risk_predictions
    ADD CONSTRAINT pk_risk_predictions PRIMARY KEY (prediction_id);


--
-- Name: role_permissions pk_role_permissions; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.role_permissions
    ADD CONSTRAINT pk_role_permissions PRIMARY KEY (role_id, permission_id);


--
-- Name: roles pk_roles; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.roles
    ADD CONSTRAINT pk_roles PRIMARY KEY (role_id);


--
-- Name: servers pk_servers; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.servers
    ADD CONSTRAINT pk_servers PRIMARY KEY (server_id);


--
-- Name: service_dependencies pk_service_dependencies; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_dependencies
    ADD CONSTRAINT pk_service_dependencies PRIMARY KEY (dependency_id);


--
-- Name: service_instances pk_service_instances; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_instances
    ADD CONSTRAINT pk_service_instances PRIMARY KEY (instance_id);


--
-- Name: services pk_services; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.services
    ADD CONSTRAINT pk_services PRIMARY KEY (service_id);


--
-- Name: teams pk_teams; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.teams
    ADD CONSTRAINT pk_teams PRIMARY KEY (team_id);


--
-- Name: ticket_comments pk_ticket_comments; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.ticket_comments
    ADD CONSTRAINT pk_ticket_comments PRIMARY KEY (comment_id);


--
-- Name: tickets pk_tickets; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tickets
    ADD CONSTRAINT pk_tickets PRIMARY KEY (ticket_id);


--
-- Name: tool_calls pk_tool_calls; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tool_calls
    ADD CONSTRAINT pk_tool_calls PRIMARY KEY (tool_call_id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.users
    ADD CONSTRAINT pk_users PRIMARY KEY (user_id);


--
-- Name: incidents uq_incidents_number; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incidents
    ADD CONSTRAINT uq_incidents_number UNIQUE (incident_number);


--
-- Name: investigation_steps uq_investigation_step_number; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_steps
    ADD CONSTRAINT uq_investigation_step_number UNIQUE (investigation_id, step_number);


--
-- Name: permissions uq_permissions_code; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.permissions
    ADD CONSTRAINT uq_permissions_code UNIQUE (permission_code);


--
-- Name: roles uq_roles_role_name; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.roles
    ADD CONSTRAINT uq_roles_role_name UNIQUE (role_name);


--
-- Name: servers uq_servers_hostname; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.servers
    ADD CONSTRAINT uq_servers_hostname UNIQUE (hostname);


--
-- Name: service_dependencies uq_service_dependency; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_dependencies
    ADD CONSTRAINT uq_service_dependency UNIQUE (service_id, depends_on_service_id, dependency_type);


--
-- Name: service_instances uq_service_instances_name; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_instances
    ADD CONSTRAINT uq_service_instances_name UNIQUE (instance_name);


--
-- Name: services uq_services_code_environment; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.services
    ADD CONSTRAINT uq_services_code_environment UNIQUE (service_code, environment);


--
-- Name: teams uq_teams_team_name; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.teams
    ADD CONSTRAINT uq_teams_team_name UNIQUE (team_name);


--
-- Name: tickets uq_tickets_ticket_number; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tickets
    ADD CONSTRAINT uq_tickets_ticket_number UNIQUE (ticket_number);


--
-- Name: users uq_users_email; Type: CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.users
    ADD CONSTRAINT uq_users_email UNIQUE (email);


--
-- Name: idx_audit_logs_action; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_audit_logs_action ON core.audit_logs USING btree (action, created_at);


--
-- Name: idx_audit_logs_actor; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_audit_logs_actor ON core.audit_logs USING btree (actor_user_id, created_at);


--
-- Name: idx_audit_logs_created_at; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_audit_logs_created_at ON core.audit_logs USING btree (created_at);


--
-- Name: idx_audit_logs_incident; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_audit_logs_incident ON core.audit_logs USING btree (incident_id, created_at);


--
-- Name: idx_audit_logs_investigation; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_audit_logs_investigation ON core.audit_logs USING btree (investigation_id, created_at);


--
-- Name: idx_deployments_service_env_completed; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_deployments_service_env_completed ON core.deployments USING btree (service_id, environment, completed_at);


--
-- Name: idx_investigation_feedback_finding; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigation_feedback_finding ON core.investigation_feedback USING btree (finding_id, created_at);


--
-- Name: idx_investigation_feedback_investigation; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigation_feedback_investigation ON core.investigation_feedback USING btree (investigation_id, created_at);


--
-- Name: idx_investigation_findings_investigation; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigation_findings_investigation ON core.investigation_findings USING btree (investigation_id, finding_type);


--
-- Name: idx_investigation_findings_status; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigation_findings_status ON core.investigation_findings USING btree (status);


--
-- Name: idx_investigation_steps_investigation; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigation_steps_investigation ON core.investigation_steps USING btree (investigation_id, step_number);


--
-- Name: idx_investigations_incident; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigations_incident ON core.investigations USING btree (incident_id);


--
-- Name: idx_investigations_initiated_by; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_investigations_initiated_by ON core.investigations USING btree (initiated_by);


--
-- Name: idx_risk_predictions_incident; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_risk_predictions_incident ON core.risk_predictions USING btree (incident_id, predicted_at);


--
-- Name: idx_risk_predictions_investigation; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_risk_predictions_investigation ON core.risk_predictions USING btree (investigation_id, predicted_at);


--
-- Name: idx_risk_predictions_model; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_risk_predictions_model ON core.risk_predictions USING btree (model_name, model_version);


--
-- Name: idx_ticket_comments_ticket_created; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_ticket_comments_ticket_created ON core.ticket_comments USING btree (ticket_id, created_at);


--
-- Name: idx_tickets_assigned_team; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tickets_assigned_team ON core.tickets USING btree (assigned_team_id);


--
-- Name: idx_tickets_assigned_user; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tickets_assigned_user ON core.tickets USING btree (assigned_user_id);


--
-- Name: idx_tickets_incident; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tickets_incident ON core.tickets USING btree (incident_id);


--
-- Name: idx_tickets_status; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tickets_status ON core.tickets USING btree (status);


--
-- Name: idx_tool_calls_investigation; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tool_calls_investigation ON core.tool_calls USING btree (investigation_id, started_at);


--
-- Name: idx_tool_calls_step; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tool_calls_step ON core.tool_calls USING btree (step_id);


--
-- Name: idx_tool_calls_tool_name_status; Type: INDEX; Schema: core; Owner: -
--

CREATE INDEX idx_tool_calls_tool_name_status ON core.tool_calls USING btree (tool_name, status);


--
-- Name: incidents trg_incidents_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_incidents_updated_at BEFORE UPDATE ON core.incidents FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: investigations trg_investigations_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_investigations_updated_at BEFORE UPDATE ON core.investigations FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: servers trg_servers_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_servers_updated_at BEFORE UPDATE ON core.servers FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: services trg_services_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_services_updated_at BEFORE UPDATE ON core.services FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: teams trg_teams_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_teams_updated_at BEFORE UPDATE ON core.teams FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: tickets trg_tickets_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_tickets_updated_at BEFORE UPDATE ON core.tickets FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: users trg_users_updated_at; Type: TRIGGER; Schema: core; Owner: -
--

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON core.users FOR EACH ROW EXECUTE FUNCTION core.set_updated_at();


--
-- Name: audit_logs fk_audit_logs_actor; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.audit_logs
    ADD CONSTRAINT fk_audit_logs_actor FOREIGN KEY (actor_user_id) REFERENCES core.users(user_id) ON DELETE SET NULL;


--
-- Name: audit_logs fk_audit_logs_incident; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.audit_logs
    ADD CONSTRAINT fk_audit_logs_incident FOREIGN KEY (incident_id) REFERENCES core.incidents(incident_id) ON DELETE SET NULL;


--
-- Name: audit_logs fk_audit_logs_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.audit_logs
    ADD CONSTRAINT fk_audit_logs_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE SET NULL;


--
-- Name: audit_logs fk_audit_logs_ticket; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.audit_logs
    ADD CONSTRAINT fk_audit_logs_ticket FOREIGN KEY (ticket_id) REFERENCES core.tickets(ticket_id) ON DELETE SET NULL;


--
-- Name: deployments fk_deployments_deployed_by; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.deployments
    ADD CONSTRAINT fk_deployments_deployed_by FOREIGN KEY (deployed_by) REFERENCES core.users(user_id);


--
-- Name: deployments fk_deployments_service; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.deployments
    ADD CONSTRAINT fk_deployments_service FOREIGN KEY (service_id) REFERENCES core.services(service_id);


--
-- Name: finding_evidence fk_finding_evidence_evidence; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.finding_evidence
    ADD CONSTRAINT fk_finding_evidence_evidence FOREIGN KEY (evidence_id) REFERENCES core.investigation_evidence(evidence_id) ON DELETE CASCADE;


--
-- Name: finding_evidence fk_finding_evidence_finding; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.finding_evidence
    ADD CONSTRAINT fk_finding_evidence_finding FOREIGN KEY (finding_id) REFERENCES core.investigation_findings(finding_id) ON DELETE CASCADE;


--
-- Name: incident_events fk_incident_events_created_by; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incident_events
    ADD CONSTRAINT fk_incident_events_created_by FOREIGN KEY (created_by) REFERENCES core.users(user_id);


--
-- Name: incident_events fk_incident_events_incident; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incident_events
    ADD CONSTRAINT fk_incident_events_incident FOREIGN KEY (incident_id) REFERENCES core.incidents(incident_id) ON DELETE CASCADE;


--
-- Name: incidents fk_incidents_root_cause_user; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incidents
    ADD CONSTRAINT fk_incidents_root_cause_user FOREIGN KEY (root_cause_confirmed_by) REFERENCES core.users(user_id);


--
-- Name: incidents fk_incidents_service; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incidents
    ADD CONSTRAINT fk_incidents_service FOREIGN KEY (service_id) REFERENCES core.services(service_id);


--
-- Name: incidents fk_incidents_team; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incidents
    ADD CONSTRAINT fk_incidents_team FOREIGN KEY (assigned_team_id) REFERENCES core.teams(team_id);


--
-- Name: incidents fk_incidents_user; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.incidents
    ADD CONSTRAINT fk_incidents_user FOREIGN KEY (assigned_user_id) REFERENCES core.users(user_id);


--
-- Name: investigation_evidence fk_investigation_evidence_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_evidence
    ADD CONSTRAINT fk_investigation_evidence_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE CASCADE;


--
-- Name: investigation_evidence fk_investigation_evidence_tool_call; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_evidence
    ADD CONSTRAINT fk_investigation_evidence_tool_call FOREIGN KEY (tool_call_id) REFERENCES core.tool_calls(tool_call_id) ON DELETE SET NULL;


--
-- Name: investigation_feedback fk_investigation_feedback_finding; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_feedback
    ADD CONSTRAINT fk_investigation_feedback_finding FOREIGN KEY (finding_id) REFERENCES core.investigation_findings(finding_id) ON DELETE SET NULL;


--
-- Name: investigation_feedback fk_investigation_feedback_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_feedback
    ADD CONSTRAINT fk_investigation_feedback_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE CASCADE;


--
-- Name: investigation_feedback fk_investigation_feedback_user; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_feedback
    ADD CONSTRAINT fk_investigation_feedback_user FOREIGN KEY (submitted_by) REFERENCES core.users(user_id);


--
-- Name: investigation_findings fk_investigation_findings_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_findings
    ADD CONSTRAINT fk_investigation_findings_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE CASCADE;


--
-- Name: investigation_steps fk_investigation_steps_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigation_steps
    ADD CONSTRAINT fk_investigation_steps_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE CASCADE;


--
-- Name: investigations fk_investigations_incident; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigations
    ADD CONSTRAINT fk_investigations_incident FOREIGN KEY (incident_id) REFERENCES core.incidents(incident_id);


--
-- Name: investigations fk_investigations_initiated_by; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.investigations
    ADD CONSTRAINT fk_investigations_initiated_by FOREIGN KEY (initiated_by) REFERENCES core.users(user_id);


--
-- Name: risk_predictions fk_risk_predictions_incident; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.risk_predictions
    ADD CONSTRAINT fk_risk_predictions_incident FOREIGN KEY (incident_id) REFERENCES core.incidents(incident_id);


--
-- Name: risk_predictions fk_risk_predictions_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.risk_predictions
    ADD CONSTRAINT fk_risk_predictions_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE CASCADE;


--
-- Name: role_permissions fk_role_permissions_permission; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.role_permissions
    ADD CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES core.permissions(permission_id);


--
-- Name: role_permissions fk_role_permissions_role; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.role_permissions
    ADD CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES core.roles(role_id) ON DELETE CASCADE;


--
-- Name: service_dependencies fk_service_dependencies_depends_on; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_dependencies
    ADD CONSTRAINT fk_service_dependencies_depends_on FOREIGN KEY (depends_on_service_id) REFERENCES core.services(service_id);


--
-- Name: service_dependencies fk_service_dependencies_service; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_dependencies
    ADD CONSTRAINT fk_service_dependencies_service FOREIGN KEY (service_id) REFERENCES core.services(service_id);


--
-- Name: service_instances fk_service_instances_server; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_instances
    ADD CONSTRAINT fk_service_instances_server FOREIGN KEY (server_id) REFERENCES core.servers(server_id);


--
-- Name: service_instances fk_service_instances_service; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.service_instances
    ADD CONSTRAINT fk_service_instances_service FOREIGN KEY (service_id) REFERENCES core.services(service_id);


--
-- Name: services fk_services_owner_team; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.services
    ADD CONSTRAINT fk_services_owner_team FOREIGN KEY (owner_team_id) REFERENCES core.teams(team_id);


--
-- Name: teams fk_teams_manager; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.teams
    ADD CONSTRAINT fk_teams_manager FOREIGN KEY (manager_user_id) REFERENCES core.users(user_id);


--
-- Name: ticket_comments fk_ticket_comments_author; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.ticket_comments
    ADD CONSTRAINT fk_ticket_comments_author FOREIGN KEY (author_id) REFERENCES core.users(user_id);


--
-- Name: ticket_comments fk_ticket_comments_ticket; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.ticket_comments
    ADD CONSTRAINT fk_ticket_comments_ticket FOREIGN KEY (ticket_id) REFERENCES core.tickets(ticket_id) ON DELETE CASCADE;


--
-- Name: tickets fk_tickets_assigned_team; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tickets
    ADD CONSTRAINT fk_tickets_assigned_team FOREIGN KEY (assigned_team_id) REFERENCES core.teams(team_id);


--
-- Name: tickets fk_tickets_assigned_user; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tickets
    ADD CONSTRAINT fk_tickets_assigned_user FOREIGN KEY (assigned_user_id) REFERENCES core.users(user_id);


--
-- Name: tickets fk_tickets_created_by; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tickets
    ADD CONSTRAINT fk_tickets_created_by FOREIGN KEY (created_by) REFERENCES core.users(user_id);


--
-- Name: tickets fk_tickets_incident; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tickets
    ADD CONSTRAINT fk_tickets_incident FOREIGN KEY (incident_id) REFERENCES core.incidents(incident_id);


--
-- Name: tool_calls fk_tool_calls_investigation; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tool_calls
    ADD CONSTRAINT fk_tool_calls_investigation FOREIGN KEY (investigation_id) REFERENCES core.investigations(investigation_id) ON DELETE CASCADE;


--
-- Name: tool_calls fk_tool_calls_step; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.tool_calls
    ADD CONSTRAINT fk_tool_calls_step FOREIGN KEY (step_id) REFERENCES core.investigation_steps(step_id) ON DELETE CASCADE;


--
-- Name: users fk_users_role; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.users
    ADD CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES core.roles(role_id);


--
-- Name: users fk_users_team; Type: FK CONSTRAINT; Schema: core; Owner: -
--

ALTER TABLE ONLY core.users
    ADD CONSTRAINT fk_users_team FOREIGN KEY (team_id) REFERENCES core.teams(team_id);


--
-- Name: SCHEMA core; Type: ACL; Schema: -; Owner: -
--

GRANT USAGE ON SCHEMA core TO opspilot_agent_ro;
GRANT USAGE ON SCHEMA core TO opspilot_app;


--
-- Name: TABLE audit_logs; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.audit_logs TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.audit_logs TO opspilot_app;


--
-- Name: SEQUENCE audit_logs_audit_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.audit_logs_audit_id_seq TO opspilot_app;


--
-- Name: TABLE deployments; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.deployments TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.deployments TO opspilot_app;


--
-- Name: SEQUENCE deployments_deployment_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.deployments_deployment_id_seq TO opspilot_app;


--
-- Name: TABLE finding_evidence; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.finding_evidence TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.finding_evidence TO opspilot_app;


--
-- Name: TABLE incident_events; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.incident_events TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.incident_events TO opspilot_app;


--
-- Name: SEQUENCE incident_events_event_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.incident_events_event_id_seq TO opspilot_app;


--
-- Name: TABLE incidents; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.incidents TO opspilot_agent_ro;
GRANT SELECT,INSERT,UPDATE ON TABLE core.incidents TO opspilot_app;


--
-- Name: SEQUENCE incidents_incident_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.incidents_incident_id_seq TO opspilot_app;


--
-- Name: TABLE investigation_evidence; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.investigation_evidence TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.investigation_evidence TO opspilot_app;


--
-- Name: SEQUENCE investigation_evidence_evidence_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.investigation_evidence_evidence_id_seq TO opspilot_app;


--
-- Name: TABLE investigation_feedback; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.investigation_feedback TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.investigation_feedback TO opspilot_app;


--
-- Name: SEQUENCE investigation_feedback_feedback_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.investigation_feedback_feedback_id_seq TO opspilot_app;


--
-- Name: TABLE investigation_findings; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.investigation_findings TO opspilot_agent_ro;
GRANT SELECT,INSERT,UPDATE ON TABLE core.investigation_findings TO opspilot_app;


--
-- Name: SEQUENCE investigation_findings_finding_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.investigation_findings_finding_id_seq TO opspilot_app;


--
-- Name: TABLE investigation_steps; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.investigation_steps TO opspilot_agent_ro;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE core.investigation_steps TO opspilot_app;


--
-- Name: SEQUENCE investigation_steps_step_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.investigation_steps_step_id_seq TO opspilot_app;


--
-- Name: TABLE investigations; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.investigations TO opspilot_agent_ro;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE core.investigations TO opspilot_app;


--
-- Name: SEQUENCE investigations_investigation_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.investigations_investigation_id_seq TO opspilot_app;


--
-- Name: SEQUENCE knowledge_document_versions_version_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.knowledge_document_versions_version_id_seq TO opspilot_app;


--
-- Name: SEQUENCE knowledge_documents_document_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.knowledge_documents_document_id_seq TO opspilot_app;


--
-- Name: TABLE permissions; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.permissions TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.permissions TO opspilot_app;


--
-- Name: SEQUENCE permissions_permission_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.permissions_permission_id_seq TO opspilot_app;


--
-- Name: TABLE risk_predictions; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.risk_predictions TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.risk_predictions TO opspilot_app;


--
-- Name: SEQUENCE risk_predictions_prediction_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.risk_predictions_prediction_id_seq TO opspilot_app;


--
-- Name: TABLE role_permissions; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.role_permissions TO opspilot_agent_ro;
GRANT SELECT,INSERT,DELETE ON TABLE core.role_permissions TO opspilot_app;


--
-- Name: TABLE roles; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.roles TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.roles TO opspilot_app;


--
-- Name: SEQUENCE roles_role_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.roles_role_id_seq TO opspilot_app;


--
-- Name: TABLE servers; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.servers TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.servers TO opspilot_app;


--
-- Name: SEQUENCE servers_server_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.servers_server_id_seq TO opspilot_app;


--
-- Name: TABLE service_dependencies; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.service_dependencies TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.service_dependencies TO opspilot_app;


--
-- Name: SEQUENCE service_dependencies_dependency_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.service_dependencies_dependency_id_seq TO opspilot_app;


--
-- Name: TABLE service_instances; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.service_instances TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.service_instances TO opspilot_app;


--
-- Name: SEQUENCE service_instances_instance_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.service_instances_instance_id_seq TO opspilot_app;


--
-- Name: TABLE services; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.services TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.services TO opspilot_app;


--
-- Name: SEQUENCE services_service_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.services_service_id_seq TO opspilot_app;


--
-- Name: TABLE teams; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.teams TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.teams TO opspilot_app;


--
-- Name: SEQUENCE teams_team_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.teams_team_id_seq TO opspilot_app;


--
-- Name: TABLE ticket_comments; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.ticket_comments TO opspilot_agent_ro;
GRANT SELECT,INSERT ON TABLE core.ticket_comments TO opspilot_app;


--
-- Name: SEQUENCE ticket_comments_comment_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.ticket_comments_comment_id_seq TO opspilot_app;


--
-- Name: TABLE tickets; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.tickets TO opspilot_agent_ro;
GRANT SELECT,INSERT,UPDATE ON TABLE core.tickets TO opspilot_app;


--
-- Name: SEQUENCE tickets_ticket_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.tickets_ticket_id_seq TO opspilot_app;


--
-- Name: TABLE tool_calls; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.tool_calls TO opspilot_agent_ro;
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE core.tool_calls TO opspilot_app;


--
-- Name: SEQUENCE tool_calls_tool_call_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.tool_calls_tool_call_id_seq TO opspilot_app;


--
-- Name: TABLE users; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT ON TABLE core.users TO opspilot_agent_ro;
GRANT SELECT ON TABLE core.users TO opspilot_app;


--
-- Name: SEQUENCE users_user_id_seq; Type: ACL; Schema: core; Owner: -
--

GRANT SELECT,USAGE ON SEQUENCE core.users_user_id_seq TO opspilot_app;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: core; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE opspilot_owner IN SCHEMA core GRANT SELECT,USAGE ON SEQUENCES TO opspilot_app;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: core; Owner: -
--

ALTER DEFAULT PRIVILEGES FOR ROLE opspilot_owner IN SCHEMA core GRANT SELECT ON TABLES TO opspilot_agent_ro;


--
-- PostgreSQL database dump complete
--



COMMIT;
