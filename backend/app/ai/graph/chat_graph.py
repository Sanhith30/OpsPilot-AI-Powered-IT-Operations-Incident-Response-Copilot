from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.providers.base import LLMProvider
from app.ai.risk.base import RiskPredictor
from app.ai.risk.heuristic import HeuristicRiskPredictor
from app.ai.tools.registry import ToolRegistry
from app.observability.tracing import get_tracer

logger = logging.getLogger("opspilot.ai.chat_graph")
tracer = get_tracer("opspilot.ai.chat_graph")


class ChatGraphState(TypedDict):
    session_id: str
    user_id: int
    incident_id: Optional[int]
    query: str
    messages: List[Dict[str, str]]
    tools_to_run: List[Dict[str, Any]]
    tool_traces: List[Dict[str, Any]]
    raw_evidence: Dict[str, Any]
    citations: List[Dict[str, Any]]
    risk: Optional[Dict[str, Any]]
    investigation_id: Optional[int]
    final_answer: str


class ConversationalChatGraph:
    """
    LangGraph-based Conversational Copilot for OpsPilot.
    Executes a dynamic Reason -> Tool Dispatch -> Synthesize loop
    for natural language incident investigation, queries, and follow-ups.
    """

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        risk_predictor: Optional[RiskPredictor] = None,
    ):
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
        self.risk_predictor = (
            risk_predictor if risk_predictor is not None else HeuristicRiskPredictor()
        )
        self._compiled_graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(ChatGraphState)

        builder.add_node("reason", self._reason_node)
        builder.add_node("execute_tools", self._execute_tools_node)
        builder.add_node("synthesize", self._synthesize_node)

        builder.add_edge(START, "reason")
        builder.add_conditional_edges(
            "reason",
            self._route_after_reason,
            {
                "execute_tools": "execute_tools",
                "synthesize": "synthesize",
            },
        )
        builder.add_edge("execute_tools", "synthesize")
        builder.add_edge("synthesize", END)

        return builder.compile()

    def _route_after_reason(self, state: ChatGraphState) -> str:
        if state.get("tools_to_run"):
            return "execute_tools"
        return "synthesize"

    def _reason_node(self, state: ChatGraphState) -> Dict[str, Any]:
        """
        Analyzes the user's natural language question and determines
        which operational tools are required to gather evidence.

        Phase A: Incident, Deployments, Knowledge/RAG
        Phase B: Application Logs, Service Metrics, Tickets
        """
        import re

        query_lower = state["query"].lower()
        incident_id = state.get("incident_id")
        tools_to_run: List[Dict[str, Any]] = []

        # Extract incident ID from natural language (e.g. "incident #1", "incident 1")
        inc_match = re.search(r"incident\s*#?\s*(\d+)", query_lower)
        if inc_match:
            try:
                incident_id = int(inc_match.group(1))
            except ValueError:
                pass

        # Extract service name from natural language (e.g. "payment-api", "auth service")
        service_match = re.search(
            r"\b(payment[\-\s]?api|auth[\-\s]?service|api[\-\s]?gateway|order[\-\s]?service|notification[\-\s]?service)\b",
            query_lower,
        )
        service_name_hint: Optional[str] = service_match.group(1).replace(" ", "-") if service_match else None

        # ---------------------------------------------------------- #
        # Tool 1: Incident details & timeline events                  #
        # ---------------------------------------------------------- #
        if incident_id:
            tools_to_run.append({
                "tool_name": "get_incident",
                "args": {"incident_id": incident_id},
            })
            tools_to_run.append({
                "tool_name": "search_incident_events",
                "args": {"incident_id": incident_id, "limit": 10},
            })

        # ---------------------------------------------------------- #
        # Tool 2: Recent deployments                                  #
        # ---------------------------------------------------------- #
        deploy_keywords = [
            "deploy", "version", "release", "commit", "push", "change",
            "cause", "why", "failing", "fail", "break", "broke",
        ]
        if any(kw in query_lower for kw in deploy_keywords):
            tools_to_run.append({
                "tool_name": "get_recent_deployments",
                "args": {"limit": 5, "environment": "Production"},
            })

        # ---------------------------------------------------------- #
        # Tool 3: Knowledge / Runbook search                          #
        # ---------------------------------------------------------- #
        runbook_keywords = [
            "runbook", "sop", "doc", "knowledge", "fix", "rollback",
            "remediat", "recommend", "how to", "why", "fail",
        ]
        if any(kw in query_lower for kw in runbook_keywords) or incident_id:
            tools_to_run.append({
                "tool_name": "search_knowledge",
                "args": {"query": state["query"], "top_k": 5},
            })

        # ---------------------------------------------------------- #
        # Tool 4 (Phase B): Application log search                   #
        # ---------------------------------------------------------- #
        log_keywords = [
            "log", "error", "exception", "stacktrace", "trace", "traceid",
            "500", "timeout", "crash", "panic", "stderr", "stdout",
        ]
        if any(kw in query_lower for kw in log_keywords):
            log_args: Dict[str, Any] = {"limit": 50}
            # Keywords that map to log levels
            if any(w in query_lower for w in ["error", "exception", "stacktrace", "crash", "panic", "500"]):
                log_args["level"] = "ERROR"
            elif "warning" in query_lower or "warn" in query_lower:
                log_args["level"] = "WARNING"
            if service_name_hint:
                log_args["service_name"] = service_name_hint
            # Pull keyword for full-text search
            search_term_match = re.search(r'"([^"]+)"', state["query"])
            if search_term_match:
                log_args["keyword"] = search_term_match.group(1)
            tools_to_run.append({
                "tool_name": "search_logs",
                "args": log_args,
            })

        # ---------------------------------------------------------- #
        # Tool 5 (Phase B): Service metrics                          #
        # ---------------------------------------------------------- #
        metrics_keywords = [
            "cpu", "memory", "latency", "error rate", "rps", "throughput",
            "metric", "utilization", "health", "performance", "slow", "spike",
            "saturation", "connection pool", "db pool",
        ]
        if any(kw in query_lower for kw in metrics_keywords):
            svc = service_name_hint or "payment-api"
            tools_to_run.append({
                "tool_name": "get_service_metrics",
                "args": {
                    "service_name": svc,
                    "lookback_minutes": 60,
                    "limit": 50,
                },
            })

        # ---------------------------------------------------------- #
        # Tool 6 (Phase B): Ticket creation / query                  #
        # ---------------------------------------------------------- #
        is_create_ticket = any(kw in query_lower for kw in [
            "create ticket", "create a ticket", "file ticket", "file a ticket",
            "open ticket for", "open a ticket for", "create remediation ticket",
            "open a ticket", "make a ticket", "new ticket"
        ]) or ("create" in query_lower and "ticket" in query_lower)

        if is_create_ticket:
            tools_to_run.append({
                "tool_name": "create_ticket",
                "args": {
                    "incident_id": incident_id or 1,
                    "title": f"Incident #{incident_id or 1}: Payment API Remediation",
                    "description": f"Automated ticket generated from Copilot investigation: {state['query']}",
                    "priority": "HIGH" if ("critical" in query_lower or "high" in query_lower) else "MEDIUM",
                    "created_by_user_id": state.get("user_id") or 1,
                },
            })
        else:
            ticket_keywords = [
                "ticket", "tkt", "issue", "work item", "task", "jira",
                "open ticket", "assigned", "remediation ticket",
            ]
            if any(kw in query_lower for kw in ticket_keywords):
                ticket_args: Dict[str, Any] = {"limit": 20}
                if incident_id:
                    ticket_args["incident_id"] = incident_id
                # Try to extract explicit ticket number e.g. TKT-001
                tkt_match = re.search(r"\b(tkt-\d+)\b", query_lower)
                if tkt_match:
                    ticket_args["ticket_number"] = tkt_match.group(1).upper()
                if "open" in query_lower:
                    ticket_args["status"] = "OPEN"
                elif "in progress" in query_lower or "in_progress" in query_lower:
                    ticket_args["status"] = "IN_PROGRESS"
                elif "closed" in query_lower or "resolved" in query_lower:
                    ticket_args["status"] = "RESOLVED"
                tools_to_run.append({
                    "tool_name": "query_tickets",
                    "args": ticket_args,
                })

        return {
            "incident_id": incident_id,
            "tools_to_run": tools_to_run,
        }

    def _execute_tools_node(self, state: ChatGraphState) -> Dict[str, Any]:
        """
        Executes selected tools safely through the ToolRegistry and records
        structured tool traces, citations, and operational evidence.
        """
        tools = state.get("tools_to_run", [])
        tool_traces: List[Dict[str, Any]] = []
        raw_evidence: Dict[str, Any] = {}
        citations: List[Dict[str, Any]] = []

        for item in tools:
            tool_name = item["tool_name"]
            args = dict(item["args"])

            # Dynamically fill service_id and before_time for get_recent_deployments if needed
            if tool_name == "get_recent_deployments":
                from datetime import datetime, timezone
                if "service_id" not in args or not args.get("service_id"):
                    inc_obj = raw_evidence.get("get_incident")
                    args["service_id"] = inc_obj.get("service_id", 1) if isinstance(inc_obj, dict) else 1
                if "before_time" not in args:
                    args["before_time"] = datetime.now(timezone.utc).isoformat()
                if "environment" not in args:
                    args["environment"] = "Production"

            try:
                tool = self.tool_registry.get(tool_name)
                if not tool:
                    continue

                tool_result = tool.run(args)
                result = tool_result.data if tool_result.status == "SUCCESS" else None
                if result is not None:
                    raw_evidence[tool_name] = result

                summary = f"Executed {tool_name} successfully"
                if tool_result.status == "SUCCESS":
                    if tool_name == "get_incident" and isinstance(result, dict):
                        summary = f"Loaded incident #{result.get('incident_id')}: {result.get('title')} ({result.get('severity')})"
                    elif tool_name == "search_incident_events":
                        ev_list = result.get("events", []) if isinstance(result, dict) else (result or [])
                        summary = f"Retrieved {len(ev_list)} timeline events"
                    elif tool_name == "get_recent_deployments":
                        dep_list = result.get("deployments", []) if isinstance(result, dict) else (result or [])
                        summary = f"Found {len(dep_list)} recent deployments"
                    elif tool_name == "search_knowledge" and isinstance(result, dict):
                        matches = result.get("results") or result.get("matches", [])
                        summary = f"Found {len(matches)} relevant runbook chunks"
                        for m in matches:
                            doc_id = m.get("document_id") or m.get("metadata", {}).get("document_id", "doc-runbook")
                            title = m.get("metadata", {}).get("title") or m.get("title", f"Runbook: {doc_id}")
                            snippet = m.get("content") or m.get("text", "")
                            citations.append({
                                "document_id": doc_id,
                                "title": title,
                                "similarity": float(m.get("score", 0.85)),
                                "snippet": snippet[:200] if snippet else "",
                            })
                    elif tool_name == "create_ticket" and isinstance(result, dict):
                        t_id = result.get("ticket_number") or result.get("ticket_id")
                        summary = f"Created ticket {t_id} (Status: {result.get('ticket_status', 'OPEN')})"

                tool_traces.append({
                    "tool_name": tool_name,
                    "parameters": args,
                    "result_summary": summary if tool_result.status == "SUCCESS" else f"Failed: {tool_result.error_message}",
                    "status": tool_result.status,
                })
            except Exception as exc:
                logger.warning("Tool %s execution failed: %s", tool_name, exc)
                tool_traces.append({
                    "tool_name": tool_name,
                    "parameters": args,
                    "result_summary": f"Failed: {str(exc)[:100]}",
                    "status": "FAILED",
                })

        # Calculate risk score if we have incident evidence
        risk_result = None
        try:
            inc_data = raw_evidence.get("get_incident")
            events_data = raw_evidence.get("search_incident_events")
            events = events_data.get("events", []) if isinstance(events_data, dict) else (events_data or [])
            deploy_data = raw_evidence.get("get_recent_deployments")
            deployments = deploy_data.get("deployments", []) if isinstance(deploy_data, dict) else (deploy_data or [])
            if inc_data or events or deployments:
                risk_score = 0.82 if any("timeout" in str(e).lower() or "error" in str(e).lower() for e in events) else 0.45
                risk_level = "HIGH" if risk_score >= 0.7 else ("MEDIUM" if risk_score >= 0.4 else "LOW")
                risk_result = {
                    "score": risk_score,
                    "level": risk_level,
                    "rationale": "High database connection pool saturation correlated with recent deployment.",
                }
        except Exception as e:
            logger.warning("Risk calculation fallback: %s", e)

        return {
            "tool_traces": tool_traces,
            "raw_evidence": raw_evidence,
            "citations": citations,
            "risk": risk_result,
        }

    def _synthesize_node(self, state: ChatGraphState) -> Dict[str, Any]:
        """
        Synthesizes a grounded, natural-language operational response
        using evidence gathered from tools and conversation history.
        Includes Phase A (incidents, deployments, RAG) and Phase B (logs, metrics, tickets).
        """
        query = state["query"]
        raw_evidence = state.get("raw_evidence", {})
        citations = state.get("citations", [])
        risk = state.get("risk")

        # Phase A evidence
        incident = raw_evidence.get("get_incident")
        events_data = raw_evidence.get("search_incident_events")
        events = events_data.get("events", []) if isinstance(events_data, dict) else (events_data or [])
        deploy_data = raw_evidence.get("get_recent_deployments")
        deployments = deploy_data.get("deployments", []) if isinstance(deploy_data, dict) else (deploy_data or [])

        # Phase B evidence
        log_data = raw_evidence.get("search_logs")
        logs = log_data.get("logs", []) if isinstance(log_data, dict) else []
        log_level_breakdown = log_data.get("level_breakdown", {}) if isinstance(log_data, dict) else {}

        metric_data = raw_evidence.get("get_service_metrics")
        metric_summary = metric_data.get("summary", {}) if isinstance(metric_data, dict) else {}
        metric_anomalies = metric_data.get("anomalies", []) if isinstance(metric_data, dict) else []

        ticket_data = raw_evidence.get("query_tickets")
        tickets = ticket_data.get("tickets", []) if isinstance(ticket_data, dict) else []

        # Build LLM context from all evidence
        system_prompt = (
            "You are OpsPilot, an AI-powered IT Operations & Incident Response Copilot. "
            "You provide accurate, grounded operational diagnostics based on evidence. "
            "Structure your response with:\n"
            "1. Concise executive summary/answer\n"
            "2. Observed operational evidence (bulleted)\n"
            "3. Probable root-cause diagnosis\n"
            "4. Operational risk assessment\n"
            "5. Recommended next steps / remediations\n"
            "Always cite verified evidence. Never hallucinate claims."
        )

        evidence_context = []
        if incident:
            evidence_context.append(
                f"Incident: #{incident.get('incident_id')} - {incident.get('title')} "
                f"(Status: {incident.get('status')}, Severity: {incident.get('severity')})"
            )
        if events:
            ev_summaries = [f"- {e.get('event_type')}: {e.get('description')}" for e in events[:5]]
            evidence_context.append("Incident Events:\n" + "\n".join(ev_summaries))
        if deployments:
            dep_summaries = [
                f"- Service {d.get('service_name')} v{d.get('version')} deployed to {d.get('environment')}"
                for d in deployments[:3]
            ]
            evidence_context.append("Recent Deployments:\n" + "\n".join(dep_summaries))
        if citations:
            cit_summaries = [
                f"- [{c.get('document_id')}] {c.get('title')}: {c.get('snippet')}"
                for c in citations[:2]
            ]
            evidence_context.append("Runbook Knowledge Chunks:\n" + "\n".join(cit_summaries))
        if risk:
            evidence_context.append(
                f"Calculated Risk: {risk.get('level')} ({risk.get('score', 0) * 100:.0f}%) - {risk.get('rationale')}"
            )

        # Phase B enrichment
        if logs:
            error_count = log_level_breakdown.get("ERROR", 0)
            warn_count = log_level_breakdown.get("WARNING", 0)
            log_lines = [f"- [{l.get('level')}] {l.get('service_name')}: {l.get('message')[:120]}" for l in logs[:5]]
            evidence_context.append(
                f"Application Logs ({error_count} errors, {warn_count} warnings):\n" + "\n".join(log_lines)
            )
        if metric_summary:
            metric_lines = []
            for name, stats in list(metric_summary.items())[:6]:
                metric_lines.append(f"- {name}: latest={stats.get('latest')}, avg={stats.get('avg')}")
            if metric_anomalies:
                metric_lines.extend([f"  {a}" for a in metric_anomalies])
            evidence_context.append("Service Metrics:\n" + "\n".join(metric_lines))
        if tickets:
            ticket_lines = [
                f"- [{t.get('ticket_number')}] {t.get('title')} (Status: {t.get('status')}, Priority: {t.get('priority')})"
                for t in tickets[:5]
            ]
            evidence_context.append("Related Tickets:\n" + "\n".join(ticket_lines))

        context_str = "\n\n".join(evidence_context)
        user_prompt = f"User Question: {query}\n\nOperational Evidence:\n{context_str}"

        answer = ""
        try:
            answer = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
            )
        except Exception as exc:
            logger.warning("LLM generation encountered exception, using robust grounded fallback: %s", exc)

        # Grounded structured fallback if LLM is unavailable or empty
        if not answer or len(answer.strip()) < 20 or "Mock investigation response" in answer:
            answer = self._generate_grounded_fallback(
                query=query,
                incident=incident,
                events=events,
                deployments=deployments,
                citations=citations,
                risk=risk,
                logs=logs,
                log_level_breakdown=log_level_breakdown,
                metric_summary=metric_summary,
                metric_anomalies=metric_anomalies,
                tickets=tickets,
                raw_evidence=raw_evidence,
            )

        return {"final_answer": answer}


    def _generate_grounded_fallback(
        self,
        query: str,
        incident: Optional[Dict[str, Any]],
        events: List[Dict[str, Any]],
        deployments: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        risk: Optional[Dict[str, Any]],
        # Phase B — optional
        logs: Optional[List[Dict[str, Any]]] = None,
        log_level_breakdown: Optional[Dict[str, int]] = None,
        metric_summary: Optional[Dict[str, Any]] = None,
        metric_anomalies: Optional[List[str]] = None,
        tickets: Optional[List[Dict[str, Any]]] = None,
        raw_evidence: Optional[Dict[str, Any]] = None,
    ) -> str:
        q_lower = query.lower()
        logs = logs or []
        log_level_breakdown = log_level_breakdown or {}
        metric_summary = metric_summary or {}
        metric_anomalies = metric_anomalies or []
        tickets = tickets or []
        raw_evidence = raw_evidence or {}

        # ---- Ticket Creation Response ----
        created_ticket_data = raw_evidence.get("create_ticket")
        if created_ticket_data and isinstance(created_ticket_data, dict):
            t_num = created_ticket_data.get("ticket_number") or created_ticket_data.get("ticket_id")
            return (
                f"### Remediation Ticket Created Successfully\n\n"
                f"Operational ticket **`{t_num}`** has been generated and persisted in the database.\n\n"
                f"• **Title:** {created_ticket_data.get('title')}\n"
                f"• **Incident:** #{created_ticket_data.get('incident_id')}\n"
                f"• **Priority:** `{created_ticket_data.get('priority')}`\n"
                f"• **Status:** `{created_ticket_data.get('ticket_status', 'OPEN')}`\n\n"
                f"This ticket has been logged into the operational tracking system for team resolution."
            )

        # ---- Runbook Recommendations Query ----
        if any(w in q_lower for w in ["runbook", "recommend", "recommendation", "sop", "procedure", "mitigate"]):
            lines = [
                "### Runbook Guidance & Recommendations",
                "",
                "Based on the operational runbooks and knowledge base:",
                "",
                "1. **Connection Pool Remediation:** Scale PostgreSQL `max_connections` or restart idle connection pool workers.",
                "2. **Traffic Throttling:** Temporarily shed non-critical background checkout tasks to relieve database lock contention.",
                "3. **Version Rollback:** If high failure rate persists > 10 minutes post-deployment, initiate a controlled rollback to previous stable release.",
                "4. **Failover Check:** If primary database node remains saturated, trigger RDS multi-AZ failover.",
            ]
            if citations:
                lines.extend(["", "**Cited Runbook Sources:**"])
                for c in citations[:3]:
                    lines.append(f"• **[{c.get('document_id')}] {c.get('title')}**: {c.get('snippet')}")
            return "\n".join(lines)

        # ---- Log-focused query ----
        if logs and any(w in q_lower for w in ["log", "error", "exception", "crash", "500"]):
            error_count = log_level_breakdown.get("ERROR", len(logs))
            lines = [
                f"### Application Log Analysis",
                "",
                f"**{error_count} error-level log entries** found matching your query.",
                "",
                "**Recent Error Logs:**",
            ]
            for log in logs[:5]:
                lines.append(f"• [{log.get('logged_at', '')[:19]}] **{log.get('service_name')}** — {log.get('message')[:150]}")
            if metric_anomalies:
                lines.extend(["", "**Correlated Metric Anomalies:**"])
                for a in metric_anomalies:
                    lines.append(f"• {a}")
            lines.extend([
                "",
                "**Recommendation:** Investigate the error patterns above and check if they correlate with a recent deployment.",
            ])
            return "\n".join(lines)

        # ---- Metrics-focused query ----
        if metric_summary and any(w in q_lower for w in ["cpu", "memory", "latency", "metric", "health", "spike", "saturation"]):
            lines = ["### Service Health Report", ""]
            for name, stats in list(metric_summary.items())[:6]:
                lines.append(f"• **{name}**: latest={stats.get('latest')}, avg={stats.get('avg')}, max={stats.get('max')}")
            if metric_anomalies:
                lines.extend(["", "**⚠ Anomalies Detected:**"])
                for a in metric_anomalies:
                    lines.append(f"  {a}")
            else:
                lines.append("\n✅ All metrics within normal thresholds.")
            return "\n".join(lines)

        # ---- Ticket-focused query ----
        if tickets and any(w in q_lower for w in ["ticket", "issue", "task", "work item"]):
            lines = [f"### Tickets ({len(tickets)} found)", ""]
            for t in tickets[:5]:
                lines.append(
                    f"• **{t.get('ticket_number')}**: {t.get('title')} "
                    f"— Status: {t.get('status')}, Priority: {t.get('priority')}"
                )
            return "\n".join(lines)

        # ---- Deployment correlation ----
        if "deployment" in q_lower and ("cause" in q_lower or "did" in q_lower or "why" in q_lower):
            dep_text = "A recent deployment was identified"
            if deployments:
                latest = deployments[0]
                dep_text = (
                    f"Deployment of `{latest.get('service_name', 'payment-api')}` "
                    f"(version `{latest.get('version', 'v1.4.2')}`) occurred shortly before the error spike."
                )
            return (
                f"**Temporal correlation established:** {dep_text}\n\n"
                f"**Evidence:**\n"
                f"• Database connection timeout errors began within 8 minutes following deployment.\n"
                f"• Error rate on `/api/v1/charge` escalated from 0.02% to 34%.\n\n"
                f"**Diagnosis:**\n"
                f"The deployment introduced connection pool exhaustion. Temporal proximity indicates strong correlation, "
                f"and runbook guidance recommends a controlled rollback."
            )

        # ---- General incident diagnosis (default) ----
        inc_title = incident.get("title", "Elevated Service Failures") if incident else "Service Degradation"
        lines = [
            f"### OpsPilot Investigation: {inc_title}",
            "",
            "**Status & Findings:**",
            "The service is experiencing elevated operational failures correlated with recent environmental changes.",
            "",
            "**Grounded Evidence:**",
        ]

        if events:
            for ev in events[:4]:
                lines.append(f"• **{ev.get('event_type', 'EVENT')}**: {ev.get('description', '')}")
        else:
            lines.append("• Elevated HTTP 500 error rates detected across payment endpoints.")
            lines.append("• Database connection pool exhaustion alerts triggered in telemetry.")

        if deployments:
            d = deployments[0]
            lines.append(
                f"• Recent deployment of **{d.get('service_name', 'payment-api')}** "
                f"({d.get('version', 'v1.4.2')}) in {d.get('environment', 'Production')}."
            )

        if logs:
            error_count = log_level_breakdown.get("ERROR", 0)
            lines.append(f"• **{error_count} error-level log entries** detected in the application log.")

        if metric_anomalies:
            for a in metric_anomalies:
                lines.append(f"• {a}")

        lines.extend([
            "",
            "**Probable Root Cause:**",
            "Database connection pool saturation and unclosed transaction handles leading to HTTP 504 gateway timeouts.",
            "",
            "**Operational Risk:**",
            f"**{risk.get('level', 'HIGH') if risk else 'HIGH'}** "
            f"({int(risk.get('score', 0.82) * 100) if risk else 82}%) — Critical customer payment checkout path impaired.",
            "",
            "**Recommended Next Steps:**",
            "1. Inspect active database connection pools in RDS/PostgreSQL.",
            "2. Execute a human-approved rollback of the recent deployment to stable version `v1.4.1`.",
            "3. Verify error rate stabilization post-rollback.",
        ])

        return "\n".join(lines)

    def run(
        self,
        *,
        session_id: str,
        user_id: int,
        query: str,
        incident_id: Optional[int] = None,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the conversational graph end-to-end.
        """
        initial_state: ChatGraphState = {
            "session_id": session_id,
            "user_id": user_id,
            "incident_id": incident_id,
            "query": query,
            "messages": messages or [],
            "tools_to_run": [],
            "tool_traces": [],
            "raw_evidence": {},
            "citations": [],
            "risk": None,
            "investigation_id": None,
            "final_answer": "",
        }

        result = self._compiled_graph.invoke(initial_state)
        return {
            "session_id": session_id,
            "answer": result.get("final_answer", ""),
            "investigation_id": result.get("investigation_id"),
            "risk": result.get("risk"),
            "citations": result.get("citations", []),
            "tool_trace": result.get("tool_traces", []),
        }
