from datetime import datetime
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.ai.graph.analysis_parser import parse_investigation_analysis
from app.ai.graph.nodes.incident_intelligence import (
    build_incident_intelligence as build_incident_intelligence_node,
)
from app.ai.graph.prompts import build_investigation_prompt
from app.ai.intelligence.analyzer import IncidentIntelligenceAnalyzer
from app.ai.providers.base import LLMProvider
from app.ai.rag.context.builder import RAGContextBuilder
from app.ai.rag.schemas import RetrievalResult
from app.ai.rag.validation.citation_validator import CitationValidator
from app.ai.risk.base import RiskPredictor
from app.ai.risk.heuristic import HeuristicRiskPredictor
from app.ai.schemas.investigation_analysis import InvestigationAnalysis
from app.ai.state.evidence import add_evidence
from app.ai.state.investigation_state import InvestigationState
from app.ai.tools.registry import ToolRegistry
from app.observability.metrics import (
    RAG_CITATION_VALIDATIONS_TOTAL,
    RAG_INVALID_CITATIONS_TOTAL,
)
from app.observability.tracing import get_tracer

tracer = get_tracer("opspilot.ai.investigation_graph")


class InvestigationGraph:
    """
    LangGraph-based OpsPilot investigation workflow with grounded
    LLM reasoning and ML incident risk prediction.
    """

    def __init__(
        self,
        *,
        tool_registry: ToolRegistry,
        llm_provider: LLMProvider,
        risk_predictor: RiskPredictor | None = None,
        rag_context_builder: RAGContextBuilder | None = None,
        citation_validator: CitationValidator | None = None,
        analyzer: IncidentIntelligenceAnalyzer | None = None,
    ):
        self.tool_registry = tool_registry
        self.llm_provider = llm_provider
        self.risk_predictor = (
            risk_predictor
            if risk_predictor is not None
            else HeuristicRiskPredictor()
        )
        self.rag_context_builder = (
            rag_context_builder
            if rag_context_builder is not None
            else RAGContextBuilder()
        )
        self.citation_validator = (
            citation_validator
            if citation_validator is not None
            else CitationValidator()
        )
        self.incident_analyzer = (
            analyzer
            if analyzer is not None
            else IncidentIntelligenceAnalyzer(llm_provider=llm_provider)
        )

        self.graph = self._build_graph()

    # ========================================================
    # Node 1: Load Incident
    # ========================================================

    def load_incident(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Retrieve the incident using the get_incident tool.
        """

        result = self.tool_registry.execute(
            "get_incident",
            {
                "incident_id": state["incident_id"],
            },
        )

        result_data = result.model_dump(mode="json")

        if result.status != "SUCCESS":
            return {
                "status": "FAILED",
                "current_stage": "incident_load_failed",
                "tool_results": [result_data],
                "errors": [
                    {
                        "stage": "loading_incident",
                        "tool_name": result.tool_name,
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                ],
            }

        return {
            "status": "RUNNING",
            "current_stage": "incident_loaded",
            "tool_results": [result_data],
        }

    # ========================================================
    # Router after incident
    # ========================================================

    def route_after_incident(
        self,
        state: InvestigationState,
    ) -> Literal[
        "load_deployments",
        "handle_failure",
    ]:
        """
        Decide what happens after incident retrieval.
        """

        if state["status"] == "FAILED":
            return "handle_failure"

        return "load_deployments"

    # ========================================================
    # Node 2: Load Deployments
    # ========================================================

    def load_deployments(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Retrieve recent deployments using information
        obtained from the incident tool.
        """

        incident_results = [
            result
            for result in state["tool_results"]
            if result.get("tool_name") == "get_incident"
        ]

        if not incident_results:
            return {
                "status": "FAILED",
                "current_stage": "deployment_context_missing",
                "errors": [
                    {
                        "stage": "loading_deployments",
                        "tool_name": "get_recent_deployments",
                        "error_code": "MISSING_INCIDENT_RESULT",
                        "error_message": (
                            "Cannot retrieve deployments because "
                            "the incident result is missing."
                        ),
                    }
                ],
            }

        incident_data = incident_results[-1].get(
            "data",
            {},
        )

        service_id = incident_data.get("service_id")
        started_at = incident_data.get("started_at")

        if service_id is None or started_at is None:
            return {
                "status": "FAILED",
                "current_stage": "deployment_context_invalid",
                "errors": [
                    {
                        "stage": "loading_deployments",
                        "tool_name": "get_recent_deployments",
                        "error_code": "INVALID_INCIDENT_CONTEXT",
                        "error_message": (
                            "Incident result does not contain "
                            "service_id or started_at."
                        ),
                    }
                ],
            }

        result = self.tool_registry.execute(
            "get_recent_deployments",
            {
                "service_id": service_id,
                "before_time": started_at,
                "environment": "production",
                "limit": 5,
            },
        )

        result_data = result.model_dump(mode="json")

        # Deployment failure is deliberately non-fatal
        # at this stage. We want later investigation tools
        # to continue even if one evidence source fails.
        if result.status != "SUCCESS":
            return {
                "status": "RUNNING",
                "current_stage": "deployment_collection_failed",
                "tool_results": [result_data],
                "errors": [
                    {
                        "stage": "loading_deployments",
                        "tool_name": result.tool_name,
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                ],
            }

        deployments = result.data.get("deployments", [])

        new_evidence: list[dict[str, Any]] = []

        for deployment in deployments:
            started_at = deployment.get("started_at")

            timestamp = (
                datetime.fromisoformat(started_at)
                if started_at
                else None
            )

            new_evidence = add_evidence(
                new_evidence,
                source_type="deployment",
                source_id=str(deployment["deployment_id"]),
                timestamp=timestamp,
                title=(
                    f"Deployment {deployment['version']} "
                    f"to {deployment['environment']}"
                ),
                content=(
                    f"Deployment ID {deployment['deployment_id']} "
                    f"deployed version {deployment['version']} "
                    f"to {deployment['environment']} with status "
                    f"{deployment['status']}. "
                    f"Commit: {deployment.get('commit_hash')}. "
                    f"Deployment type: {deployment.get('deployment_type')}. "
                    f"Trigger type: {deployment.get('trigger_type')}. "
                    f"Started at: {deployment.get('started_at')}. "
                    f"Completed at: {deployment.get('completed_at')}."
                ),
                metadata={
                    "deployment_id": deployment["deployment_id"],
                    "service_id": deployment["service_id"],
                    "version": deployment["version"],
                    "environment": deployment["environment"],
                    "status": deployment["status"],
                    "commit_hash": deployment.get("commit_hash"),
                    "deployment_type": deployment.get("deployment_type"),
                    "trigger_type": deployment.get("trigger_type"),
                    "deployed_by": deployment.get("deployed_by"),
                },
            )

        return {
            "status": "RUNNING",
            "current_stage": "deployments_loaded",
            "tool_results": [result_data],
            "evidence": new_evidence,
        }

    # ========================================================
    # Node 3: Load Incident Events
    # ========================================================

    def load_incident_events(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Retrieve timeline events for the incident.
        Failure is non-fatal — investigation continues
        with whatever evidence was already collected.
        """

        result = self.tool_registry.execute(
            "search_incident_events",
            {
                "incident_id": state["incident_id"],
                "limit": 50,
            },
        )

        result_data = result.model_dump(mode="json")

        if result.status != "SUCCESS":
            return {
                "status": "RUNNING",
                "current_stage": "incident_events_collection_failed",
                "tool_results": [result_data],
                "errors": [
                    {
                        "stage": "load_incident_events",
                        "tool_name": result.tool_name,
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                ],
            }

        events = result.data.get("events", [])

        new_evidence: list[dict[str, Any]] = []

        for event in events:
            new_evidence = add_evidence(
                new_evidence,
                source_type="incident_event",
                source_id=str(event["event_id"]),
                timestamp=(
                    datetime.fromisoformat(event["event_time"])
                    if event.get("event_time")
                    else None
                ),
                title=event["event_type"],
                content=event["description"],
                metadata=event.get("metadata") or {},
            )

        return {
            "status": "RUNNING",
            "current_stage": "incident_events_loaded",
            "tool_results": [result_data],
            "evidence": new_evidence,
        }

    # ========================================================
    # Node 4: Prepare for next investigation stage
    # ========================================================

    def prepare_investigation(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Mark the investigation as ready for additional
        evidence collection.
        """

        return {
            "status": "RUNNING",
            "current_stage": (
                "ready_for_evidence_collection"
            ),
        }

    # ========================================================
    # Node 4a: Retrieve Knowledge (RAG)
    # ========================================================

    def retrieve_knowledge(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Query the knowledge base via the SearchKnowledgeTool.

        This node is non-fatal:
        - If the tool is not registered (no retrieval service
          was configured), the investigation proceeds without
          RAG context.
        - If the tool call fails (e.g. vector-store timeout),
          an error is recorded but the investigation continues.

        The query is composed from the incident title and the
        user question. The LLM does NOT choose the query.
        """

        incident_result = next(
            (
                r
                for r in state.get("tool_results", [])
                if (
                    r.get("tool_name") == "get_incident"
                    and r.get("status") == "SUCCESS"
                )
            ),
            None,
        )

        incident_title = (
            incident_result["data"].get("title", "")
            if incident_result
            else ""
        )
        user_question = state["user_question"]

        if incident_title:
            query = f"{incident_title}. {user_question}"
        else:
            query = user_question

        query = query.strip()

        try:
            result = self.tool_registry.execute(
                "search_knowledge",
                {"query": query, "top_k": 5},
            )
        except KeyError:
            # search_knowledge is not registered — RAG is not
            # configured for this investigation. Skip silently.
            return {
                "current_stage": "knowledge_retrieval_skipped",
                "rag_query": None,
            }

        result_data = result.model_dump(mode="json")

        if result.status != "SUCCESS":
            return {
                "current_stage": "knowledge_retrieval_failed",
                "rag_query": query,
                "tool_results": [result_data],
                "errors": [
                    {
                        "stage": "retrieve_knowledge",
                        "tool_name": result.tool_name,
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                    }
                ],
            }

        return {
            "current_stage": "knowledge_retrieved",
            "rag_query": query,
            "tool_results": [result_data],
        }

    # ========================================================
    # Node 4b: Build RAG Context
    # ========================================================

    def build_rag_context(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Convert raw retrieval results into a structured RAGContext.

        Reads the search_knowledge result from tool_results,
        reconstructs RetrievalResult objects, and calls
        RAGContextBuilder to produce the formatted context string
        and citation list.

        Returns empty context when retrieval was skipped or failed.
        """

        rag_query = state.get("rag_query")

        if not rag_query:
            return {
                "current_stage": "rag_context_skipped",
                "rag_context": None,
                "rag_citations": [],
            }

        search_result = next(
            (
                r
                for r in state.get("tool_results", [])
                if (
                    r.get("tool_name") == "search_knowledge"
                    and r.get("status") == "SUCCESS"
                )
            ),
            None,
        )

        if not search_result:
            return {
                "current_stage": "rag_context_skipped",
                "rag_context": None,
                "rag_citations": [],
            }

        raw_results = (
            search_result.get("data", {})
            .get("results", [])
        )

        retrieval_results = [
            RetrievalResult.model_validate(r)
            for r in raw_results
        ]

        rag_ctx = self.rag_context_builder.build(
            query=rag_query,
            results=retrieval_results,
        )

        return {
            "current_stage": "rag_context_built",
            "rag_context": rag_ctx.formatted_context,
            "rag_citations": [
                item.model_dump(mode="json")
                for item in rag_ctx.items
            ],
        }

    # ========================================================
    # Node 5: Analyze Investigation
    # ========================================================

    def analyze_investigation(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Build a prompt from incident data and unified evidence,
        call the LLM provider, then parse the structured response
        into investigation findings.
        """

        incident_result = next(
            (
                result
                for result in state["tool_results"]
                if result["tool_name"] == "get_incident"
                and result["status"] == "SUCCESS"
            ),
            None,
        )

        if incident_result is None:
            return {
                "status": "FAILED",
                "current_stage": "analysis",
                "errors": [
                    {
                        "stage": "analysis",
                        "error_code": "INCIDENT_DATA_UNAVAILABLE",
                        "error_message": (
                            "Incident data is unavailable for analysis."
                        ),
                    }
                ],
            }

        incident = incident_result["data"]

        prompt = build_investigation_prompt(
            incident=incident,
            evidence=state.get("evidence", []),
            user_question=state["user_question"],
            rag_context=state.get("rag_context"),
        )

        try:
            raw_response = self.llm_provider.generate(
                system_prompt=(
                    "You are an AI IT operations investigation assistant. "
                    "Analyze incidents using only supplied evidence."
                ),
                user_prompt=prompt,
                temperature=0.0,
                response_schema=InvestigationAnalysis,
            )

            analysis = parse_investigation_analysis(raw_response)

        except Exception as exc:
            return {
                "status": "FAILED",
                "current_stage": "analysis",
                "errors": [
                    {
                        "stage": "analysis",
                        "error_code": "LLM_ANALYSIS_FAILED",
                        "error_message": f"Investigation analysis failed: {exc}",
                    }
                ],
            }

        findings = [
            finding.model_dump()
            for finding in analysis.findings
        ]

        return {
            "status": "RUNNING",
            "current_stage": "analysis_completed",
            "findings": findings,
            "final_summary": analysis.summary,
        }

    # ========================================================
    # Node: Validate RAG Citations & Grounding Gate
    # ========================================================

    def validate_rag_citations(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Deterministic grounding gate for RAG citations.
        Validates all KNOWLEDGE_BASE references in findings against
        actually retrieved rag_citations.
        """
        if state.get("status") == "FAILED":
            return {}

        findings = state.get("findings", [])
        rag_citations = state.get("rag_citations", [])

        with tracer.start_as_current_span("rag.validate_citations") as span:
            result = self.citation_validator.validate(
                findings=findings,
                rag_citations=rag_citations,
            )

            total_citations = len(result.validated_citations) + len(result.invalid_citations)
            span.set_attribute("rag.citation_count", total_citations)
            span.set_attribute("rag.invalid_citation_count", len(result.invalid_citations))
            span.set_attribute("rag.grounding_status", result.grounding_status)

            RAG_CITATION_VALIDATIONS_TOTAL.labels(
                status=result.grounding_status.lower()
            ).inc()

            if result.invalid_citations:
                RAG_INVALID_CITATIONS_TOTAL.inc(len(result.invalid_citations))

            if not result.valid or result.grounding_status == "INVALID":
                invalid_list_str = ", ".join(result.invalid_citations)
                err_msg = f"Finding referenced unknown citation: {invalid_list_str}"
                return {
                    "status": "FAILED",
                    "current_stage": "citation_validation_failed",
                    "rag_grounding_status": "INVALID",
                    "findings": [],
                    "errors": [
                        {
                            "stage": "citation_validation",
                            "error_code": "INVALID_RAG_CITATION",
                            "error_message": err_msg,
                        }
                    ],
                }

            return {
                "current_stage": "citation_validation_completed",
                "rag_grounding_status": result.grounding_status,
            }

    # ========================================================
    # Node 6: Predict Incident Risk
    # ========================================================

    def predict_risk(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:

        if state.get("status") == "FAILED":
            return {}

        try:
            incident_result = next(
                (
                    item
                    for item in state.get("tool_results", [])
                    if (
                        item.get("tool_name") == "get_incident"
                        and item.get("status") == "SUCCESS"
                    )
                ),
                None,
            )

            if incident_result is None:
                raise RuntimeError(
                    "Successful incident retrieval result was not found."
                )

            incident = incident_result["data"]

            prediction = self.risk_predictor.predict(
                incident=incident,
                evidence=state.get("evidence", []),
            )

            return {
                "status": "RUNNING",
                "current_stage": "risk_predicted",
                "risk_prediction": prediction.model_dump(
                    mode="json"
                ),
            }

        except Exception as exc:

            return {
                "status": "FAILED",
                "current_stage": "risk_prediction_failed",
                "errors": [
                    {
                        "stage": "risk_prediction",
                        "error_code": "RISK_PREDICTION_ERROR",
                        "error_message": str(exc),
                    }
                ],
            }

    # ========================================================
    # Node 7: Build Incident Intelligence & Decision Engine
    # ========================================================

    def build_incident_intelligence(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Synthesize operational evidence, RAG context, and risk
        into correlated signals, multi-candidate root causes,
        impact assessment, and operational decision.
        """
        return build_incident_intelligence_node(
            state,
            analyzer=self.incident_analyzer,
        )

    # ========================================================
    # Failure Node
    # ========================================================

    def handle_failure(
        self,
        state: InvestigationState,
    ) -> dict[str, Any]:
        """
        Finalize an unrecoverable investigation failure.
        """

        return {
            "status": "FAILED",
            "current_stage": "investigation_failed",
        }

    # ========================================================
    # Build Graph
    # ========================================================

    def _build_graph(self):
        """
        Build and compile the LangGraph workflow.
        """

        builder = StateGraph(
            InvestigationState
        )

        builder.add_node(
            "load_incident",
            self.load_incident,
        )

        builder.add_node(
            "load_deployments",
            self.load_deployments,
        )

        builder.add_node(
            "load_incident_events",
            self.load_incident_events,
        )

        builder.add_node(
            "prepare_investigation",
            self.prepare_investigation,
        )

        builder.add_node(
            "analyze_investigation",
            self.analyze_investigation,
        )

        builder.add_node(
            "predict_risk",
            self.predict_risk,
        )

        builder.add_node(
            "handle_failure",
            self.handle_failure,
        )

        # START → load incident
        builder.add_edge(
            START,
            "load_incident",
        )

        # Incident result determines next node
        builder.add_conditional_edges(
            "load_incident",
            self.route_after_incident,
        )

        # Successful incident → deployments → events → prepare → analyze → predict_risk
        builder.add_edge(
            "load_deployments",
            "load_incident_events",
        )

        builder.add_edge(
            "load_incident_events",
            "prepare_investigation",
        )

        builder.add_node(
            "retrieve_knowledge",
            self.retrieve_knowledge,
        )

        builder.add_node(
            "build_rag_context",
            self.build_rag_context,
        )

        builder.add_edge(
            "prepare_investigation",
            "retrieve_knowledge",
        )

        builder.add_edge(
            "retrieve_knowledge",
            "build_rag_context",
        )

        builder.add_node(
            "validate_rag_citations",
            self.validate_rag_citations,
        )

        builder.add_edge(
            "build_rag_context",
            "analyze_investigation",
        )

        builder.add_edge(
            "analyze_investigation",
            "validate_rag_citations",
        )

        builder.add_edge(
            "validate_rag_citations",
            "predict_risk",
        )

        builder.add_node(
            "build_incident_intelligence",
            self.build_incident_intelligence,
        )

        builder.add_edge(
            "predict_risk",
            "build_incident_intelligence",
        )

        builder.add_edge(
            "build_incident_intelligence",
            END,
        )

        # Unrecoverable incident failure → END
        builder.add_edge(
            "handle_failure",
            END,
        )

        return builder.compile()