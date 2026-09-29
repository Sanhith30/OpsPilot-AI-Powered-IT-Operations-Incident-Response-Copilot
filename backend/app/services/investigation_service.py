from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.ai.rag.validation.citation_validator import CitationValidator
from app.ai.risk.schemas import RiskPredictionResult
from app.ai.state.factory import create_initial_investigation_state
from app.core.exceptions import NotFoundError, ValidationError
from app.models.finding_evidence import FindingEvidence
from app.models.investigation import Investigation
from app.models.investigation_evidence import InvestigationEvidence
from app.models.investigation_finding import InvestigationFinding
from app.models.risk_prediction import RiskPrediction
from app.models.tool_call import ToolCall
from app.observability.metrics import (
    INVESTIGATIONS_TOTAL,
    RISK_PREDICTIONS_TOTAL,
)
from app.observability.tracing import get_tracer
from app.repositories.user_repository import UserRepository

tracer = get_tracer("opspilot.investigation")


class InvestigationService:
    def __init__(
        self,
        db,
        repository,
        incident_repository,
        audit_log_service,
        risk_prediction_service=None,
        citation_validator=None,
    ):
        self.db = db
        self.repository = repository
        self.incident_repository = incident_repository
        self.audit_log_service = audit_log_service
        self.risk_prediction_service = risk_prediction_service
        self.citation_validator = (
            citation_validator
            if citation_validator is not None
            else CitationValidator()
        )

    def get_all_investigations(self):
        return self.repository.get_all()

    def get_investigation_by_id(self, investigation_id: int):
        investigation = self.repository.get_by_id(investigation_id)
        if investigation is None:
            raise NotFoundError("Investigation not found.")
        return investigation

    def get_investigation_details(self, investigation_id: int):
        investigation = self.repository.get_by_id_with_details(investigation_id)
        if investigation is None:
            raise NotFoundError("Investigation not found.")
        return investigation

    def get_knowledge_evidence(self, investigation_id: int) -> list[dict[str, Any]]:
        investigation = self.repository.get_by_id_with_details(investigation_id)
        if investigation is None:
            raise NotFoundError("Investigation not found.")
        return investigation.knowledge_evidence

    def get_investigation_audit(
        self,
        investigation_id: int,
    ):
        investigation = self.repository.get_by_id(investigation_id)
        if investigation is None:
            raise NotFoundError(
                f"Investigation with id {investigation_id} not found"
            )

        return self.audit_log_service.get_by_resource(
            resource_type="INVESTIGATION",
            resource_id=investigation_id,
        )

    def get_investigations_by_incident(self, incident_id: int):
        if self.incident_repository.get_by_id(incident_id) is None:
            raise NotFoundError("Incident not found.")
        return self.repository.get_by_incident(incident_id)

    def get_investigations_by_status(self, status: str):
        return self.repository.get_by_status(status)

    def mark_running(
        self,
        *,
        investigation_id: int,
    ) -> Investigation:
        investigation = self.repository.get_by_id(investigation_id)

        if investigation is None:
            raise NotFoundError("Investigation not found.")

        investigation.status = "RUNNING"

        self.db.flush()
        self.db.commit()

        return investigation

    def mark_completed(
        self,
        *,
        investigation_id: int,
        final_summary: str | None = None,
    ) -> Investigation:
        investigation = self.repository.get_by_id(investigation_id)

        if investigation is None:
            raise NotFoundError("Investigation not found.")

        investigation.status = "COMPLETED"
        if final_summary is not None:
            investigation.final_summary = final_summary
        investigation.completed_at = datetime.now(timezone.utc)

        self.db.flush()
        self.db.commit()

        return investigation

    def mark_failed(
        self,
        *,
        investigation_id: int,
        error_message: str | None = None,
    ) -> Investigation:
        investigation = self.repository.get_by_id(investigation_id)

        if investigation is None:
            raise NotFoundError("Investigation not found.")

        investigation.status = "FAILED"
        if error_message is not None:
            investigation.final_summary = f"Investigation failed: {error_message}"
        investigation.completed_at = datetime.now(timezone.utc)

        self.db.flush()
        self.db.commit()

        return investigation

    def create_investigation(
        self,
        *,
        incident_id: int,
        investigation_type: str,
        question: str,
        actor_user_id: int | None,
        status: str = "STARTED",
    ) -> Investigation:
        try:
            if self.incident_repository.get_by_id(incident_id) is None:
                raise NotFoundError("Incident not found.")
            if not question.strip():
                raise ValidationError("Investigation question cannot be empty.")
            if actor_user_id is not None:
                user = UserRepository(self.db).get_by_id(actor_user_id)
                if user is None:
                    raise NotFoundError("Investigation starter not found.")
                if not user.is_active:
                    raise ValidationError("Investigation starter is inactive.")

            investigation = Investigation(
                incident_id=incident_id,
                started_by=actor_user_id,
                investigation_type=investigation_type,
                question=question.strip(),
                status=status,
            )
            self.repository.add(investigation)
            self.db.flush()

            self.audit_log_service.add_to_transaction(
                action="CREATE_INVESTIGATION",
                user_id=actor_user_id,
                actor_type=(
                    "USER"
                    if actor_user_id is not None
                    else "SYSTEM"
                ),
                action_result="SUCCESS",
                resource_type="INVESTIGATION",
                resource_id=investigation.investigation_id,
                incident_id=incident_id,
                investigation_id=investigation.investigation_id,
                details={
                    "incident_id": incident_id,
                    "investigation_type": investigation_type,
                    "status": status,
                },
            )
            self.db.commit()
            return investigation

        except Exception:
            self.db.rollback()
            raise

    def run_investigation(
        self,
        *,
        incident_id: int,
        question: str,
        actor_user_id: int | None = None,
        investigation_type: str = "ASSISTED",
        investigation_id: int | None = None,
        graph=None,
    ) -> Investigation:
        """
        Execute an end-to-end AI investigation via LangGraph,
        persisting the investigation record, tool calls, normalized evidence,
        findings, finding-evidence links, ML risk prediction, and audit trail.
        """
        if self.incident_repository.get_by_id(incident_id) is None:
            raise NotFoundError("Incident not found.")
        if not question.strip():
            raise ValidationError("Investigation question cannot be empty.")
        if actor_user_id is not None:
            user = UserRepository(self.db).get_by_id(actor_user_id)
            if user is None:
                raise NotFoundError("Investigation starter not found.")
            if not user.is_active:
                raise ValidationError("Investigation starter is inactive.")

        # 1. Use the existing investigation when provided.
        # Otherwise create one for backwards compatibility.

        if investigation_id is not None:
            investigation = self.repository.get_by_id(investigation_id)

            if investigation is None:
                raise NotFoundError("Investigation not found.")

            if investigation.incident_id != incident_id:
                raise ValidationError(
                    "Investigation does not belong to the specified incident."
                )

            investigation.status = "RUNNING"

            self.db.flush()
            self.db.commit()

        else:
            investigation = Investigation(
                incident_id=incident_id,
                started_by=actor_user_id,
                investigation_type=investigation_type,
                question=question.strip(),
                status="RUNNING",
            )

            self.repository.add(investigation)
            self.db.flush()

            self.audit_log_service.add_to_transaction(
                action="CREATE_INVESTIGATION",
                user_id=actor_user_id,
                actor_type=(
                    "USER"
                    if actor_user_id is not None
                    else "SYSTEM"
                ),
                action_result="SUCCESS",
                resource_type="INVESTIGATION",
                resource_id=investigation.investigation_id,
                incident_id=incident_id,
                investigation_id=investigation.investigation_id,
                details={
                    "incident_id": incident_id,
                    "investigation_type": investigation_type,
                    "status": "RUNNING",
                },
            )

            self.db.commit()

        # 2. Execute the AI LangGraph outside the DB transaction
        try:
            state = create_initial_investigation_state(
                incident_id=incident_id,
                user_question=question.strip(),
                investigation_id=investigation.investigation_id,
                investigation_type=investigation_type,
            )
            with tracer.start_as_current_span(
                "investigation.run"
            ) as span:
                span.set_attribute(
                    "opspilot.investigation_id",
                    investigation.investigation_id,
                )
                span.set_attribute(
                    "opspilot.incident_id",
                    incident_id,
                )
                span.set_attribute(
                    "opspilot.investigation_type",
                    investigation_type,
                )
                result = (
                    graph.graph.invoke(state)
                    if graph is not None
                    else state
                )
        except Exception as exc:
            self.mark_failed(
                investigation_id=investigation.investigation_id,
                error_message=str(exc),
            )
            INVESTIGATIONS_TOTAL.labels(status="FAILED").inc()

            try:
                self.audit_log_service.add_to_transaction(
                    action="INVESTIGATION_FAILED",
                    user_id=actor_user_id or investigation.started_by,
                    actor_type="USER",
                    action_result="FAILURE",
                    resource_type="INVESTIGATION",
                    resource_id=investigation.investigation_id,
                    incident_id=incident_id,
                    investigation_id=investigation.investigation_id,
                    details={
                        "status": "FAILED",
                        "error_message": str(exc),
                    },
                )
                self.db.commit()
            except Exception:
                self.db.rollback()

            raise

        # 3. Persist the investigation results in a new transaction
        try:
            status = result.get("status", "COMPLETED")
            grounding_status = result.get("rag_grounding_status")
            raw_findings = list(result.get("findings", []))
            rag_citations = result.get("rag_citations") or []

            # Deterministic citation validation gate before persistence
            validation = self.citation_validator.validate(
                findings=raw_findings,
                rag_citations=rag_citations,
            )

            if not validation.valid or grounding_status == "INVALID":
                status = "FAILED"
                raw_findings = []
                final_summary = result.get("final_summary")
                if not final_summary or "failed" not in final_summary.lower():
                    final_summary = (
                        f"Investigation failed citation validation: {validation.error_message}"
                    )
            else:
                final_summary = result.get("final_summary")

            investigation = self.repository.get_by_id(investigation.investigation_id)
            investigation.status = status
            investigation.final_summary = final_summary
            investigation.completed_at = datetime.now(timezone.utc)
            self.db.flush()

            # 4. Persist tool calls
            now = datetime.now(timezone.utc)
            search_knowledge_tool_call_id: int | None = None
            for tool_result in result.get("tool_results", []):
                tool_name = tool_result.get("tool_name", "tool")
                tc = ToolCall(
                    investigation_id=investigation.investigation_id,
                    tool_name=tool_name,
                    tool_type="AI_GRAPH_TOOL",
                    status=tool_result.get("status", "SUCCESS"),
                    input_payload=tool_result.get("input_payload"),
                    output_payload=tool_result.get("data"),
                    error_message=tool_result.get("error_message"),
                    started_at=now,
                    completed_at=now,
                )
                self.db.add(tc)
                self.db.flush()
                if tool_name == "search_knowledge" and tc.tool_call_id is not None:
                    search_knowledge_tool_call_id = tc.tool_call_id

            # 5. Persist evidence items (operational)
            evidence_map: dict[tuple[str, str], int] = {}
            for ev in result.get("evidence", []):
                source_type = ev.get("source_type") or ev.get("evidence_type") or "SYSTEM"
                if source_type.upper() not in ('INCIDENT', 'LOG', 'METRIC', 'DEPLOYMENT', 'RUNBOOK', 'TICKET', 'TRACE', 'ML_PREDICTION', 'SYSTEM', 'INCIDENT_EVENT', 'KNOWLEDGE_BASE'):
                    source_type = "SYSTEM"
                source_id = str(ev.get("source_id", ""))
                db_ev = InvestigationEvidence(
                    investigation_id=investigation.investigation_id,
                    evidence_type=source_type,
                    source=ev.get("title") or ev.get("source") or "",
                    source_reference=source_id,
                    content=ev.get("content", ""),
                    evidence_metadata=ev.get("metadata"),
                    collected_at=ev.get("timestamp") or datetime.now(timezone.utc),
                )
                self.db.add(db_ev)
                self.db.flush()
                evidence_map[(source_type, source_id)] = db_ev.evidence_id
                evidence_map[(source_type.upper(), source_id)] = db_ev.evidence_id

            # 5b. Persist RAG evidence
            rag_citations = result.get("rag_citations")
            rag_context = result.get("rag_context")
            rag_query = result.get("rag_query")
            citation_to_evidence_id: dict[str, int] = {}
            if rag_citations or (rag_context and not isinstance(rag_context, str)):
                citation_to_evidence_id = self.persist_rag_evidence(
                    investigation_id=investigation.investigation_id,
                    rag_context=rag_context if not isinstance(rag_context, str) else None,
                    rag_citations=rag_citations,
                    rag_query=rag_query,
                    tool_call_id=search_knowledge_tool_call_id,
                )
                for cit_id, ev_id in citation_to_evidence_id.items():
                    evidence_map[("KNOWLEDGE_BASE", cit_id)] = ev_id
                    evidence_map[("KNOWLEDGE", cit_id)] = ev_id
                    evidence_map[("RAG", cit_id)] = ev_id

            # 6. Persist findings & link to evidence
            for finding in raw_findings:
                finding_type = finding.get("confidence", "HIGH")
                finding_text = finding.get("finding", "")
                title = finding_text[:250] if len(finding_text) > 250 else (finding_text or "Finding")
                db_finding = InvestigationFinding(
                    investigation_id=investigation.investigation_id,
                    finding_type=finding_type,
                    title=title,
                    finding_text=finding_text,
                )
                self.db.add(db_finding)
                self.db.flush()

                linked_evidence_ids: set[int] = set()
                for ref in finding.get("evidence_refs", []):
                    ref_source_type = (ref.get("source_type") or "").upper()
                    ref_source_id = str(ref.get("source_id", ""))
                    ev_id = None
                    if ref_source_type in ("KNOWLEDGE_BASE", "KNOWLEDGE", "RAG"):
                        ev_id = citation_to_evidence_id.get(ref_source_id)
                        if ev_id is None:
                            ev_id = evidence_map.get((ref.get("source_type"), ref_source_id))
                        if ev_id is None:
                            ev_id = evidence_map.get(("KNOWLEDGE_BASE", ref_source_id))
                    else:
                        ref_key = (ref.get("source_type"), ref_source_id)
                        ev_id = evidence_map.get(ref_key)
                        if ev_id is None:
                            ev_id = evidence_map.get((ref_source_type, ref_source_id))

                    if ev_id is not None and ev_id not in linked_evidence_ids:
                        linked_evidence_ids.add(ev_id)
                        link = FindingEvidence(
                            finding_id=db_finding.finding_id,
                            evidence_id=ev_id,
                            relationship_type="SUPPORTS",
                        )
                        self.db.add(link)
            self.db.flush()

            # 7. Persist risk prediction
            rp = result.get("risk_prediction")
            if rp:
                if isinstance(rp, dict):
                    normalized_rp = {
                        "model_name": rp.get("model_name", "incident_risk_baseline"),
                        "model_version": rp.get("model_version", "1.0.0"),
                        "risk_score": Decimal(str(rp.get("risk_score", "0.50"))),
                        "risk_level": rp.get("risk_level", "MEDIUM"),
                        "features": (
                            rp.get("features")
                            if rp.get("features") is not None
                            else rp.get("factors", {})
                        ),
                        "explanation": (
                            rp.get("explanation")
                            if rp.get("explanation") is not None
                            else rp.get("prediction_explanation", "")
                        ),
                    }
                    prediction = RiskPredictionResult.model_validate(normalized_rp)
                else:
                    prediction = RiskPredictionResult.model_validate(rp)

                if self.risk_prediction_service is not None:
                    self.risk_prediction_service.create_from_prediction(
                        incident_id=incident_id,
                        investigation_id=investigation.investigation_id,
                        prediction=prediction,
                    )
                else:
                    db_rp = RiskPrediction(
                        incident_id=incident_id,
                        investigation_id=investigation.investigation_id,
                        model_name=prediction.model_name,
                        model_version=prediction.model_version,
                        prediction_type="INCIDENT_ESCALATION",
                        risk_score=Decimal(str(prediction.risk_score)),
                        risk_level=prediction.risk_level,
                        prediction_metadata=prediction.features,
                        prediction_explanation=prediction.explanation,
                        predicted_at=datetime.now(timezone.utc),
                    )
                    self.db.add(db_rp)
                    self.db.flush()

            # 7b. Persist incident intelligence (Step 18)
            intel = result.get("incident_intelligence")
            if intel:
                try:
                    from app.models.incident_intelligence import IncidentIntelligence
                    db_intel = IncidentIntelligence(
                        incident_id=incident_id,
                        investigation_id=investigation.investigation_id,
                        incident_summary=intel.get("incident_summary", "Incident analysis complete"),
                        correlated_signals=intel.get("correlated_signals", []),
                        probable_root_causes=intel.get("probable_root_causes", []),
                        impact_assessment=intel.get("impact_assessment", {}),
                        risk_assessment=intel.get("risk_assessment", {}),
                        recommended_actions=intel.get("recommended_actions", []),
                        operational_decision=intel.get("operational_decision", {}),
                        overall_confidence=Decimal(str(intel.get("confidence", "0.75"))),
                        model_name=intel.get("model_name", "opspilot-intelligence"),
                        model_version=intel.get("model_version", "1.0.0"),
                    )
                    self.db.add(db_intel)
                    self.db.flush()
                except Exception:
                    pass

            # 8. Record audit log entries
            user_id = actor_user_id or investigation.started_by
            actor_type = "USER" if user_id is not None else "SYSTEM"

            self.audit_log_service.add_to_transaction(
                action="EXECUTE_INVESTIGATION",
                user_id=user_id,
                actor_type=actor_type,
                action_result=(
                    "SUCCESS"
                    if investigation.status == "COMPLETED"
                    else "FAILURE"
                ),
                resource_type="INVESTIGATION",
                resource_id=investigation.investigation_id,
                incident_id=incident_id,
                investigation_id=investigation.investigation_id,
                details={
                    "incident_id": incident_id,
                    "status": investigation.status,
                    "findings_count": len(
                        result.get("findings", [])
                    ),
                    "risk_level": (
                        rp.get("risk_level")
                        if rp
                        else None
                    ),
                },
            )

            if investigation.status == "COMPLETED":
                self.audit_log_service.add_to_transaction(
                    action="INVESTIGATION_COMPLETED",
                    user_id=user_id,
                    actor_type=actor_type,
                    action_result="SUCCESS",
                    resource_type="INVESTIGATION",
                    resource_id=investigation.investigation_id,
                    incident_id=incident_id,
                    investigation_id=investigation.investigation_id,
                    details={
                        "status": "COMPLETED",
                        "final_summary": investigation.final_summary,
                    },
                )
            else:
                self.audit_log_service.add_to_transaction(
                    action="INVESTIGATION_FAILED",
                    user_id=user_id,
                    actor_type=actor_type,
                    action_result="FAILURE",
                    resource_type="INVESTIGATION",
                    resource_id=investigation.investigation_id,
                    incident_id=incident_id,
                    investigation_id=investigation.investigation_id,
                    details={
                        "status": investigation.status,
                        "errors": result.get("errors", []),
                    },
                )

            self.db.commit()

            INVESTIGATIONS_TOTAL.labels(
                status=investigation.status
            ).inc()

            # 9. Return fully populated investigation with details
            return self.repository.get_by_id_with_details(investigation.investigation_id)

        except Exception as exc:
            self.db.rollback()

            try:
                investigation = self.repository.get_by_id(
                    investigation.investigation_id
                )

                if investigation is not None:
                    investigation.status = "FAILED"
                    investigation.completed_at = datetime.now(timezone.utc)
                    investigation.final_summary = (
                        f"Investigation persistence failed: {exc}"
                    )
                    self.db.flush()

                    self.audit_log_service.add_to_transaction(
                        action="INVESTIGATION_FAILED",
                        user_id=actor_user_id or investigation.started_by,
                        actor_type="USER",
                        action_result="FAILURE",
                        resource_type="INVESTIGATION",
                        resource_id=investigation.investigation_id,
                        incident_id=incident_id,
                        investigation_id=investigation.investigation_id,
                        details={
                            "status": "FAILED",
                            "error_message": str(exc),
                            "phase": "PERSISTENCE",
                        },
                    )
                    self.db.commit()
                    INVESTIGATIONS_TOTAL.labels(status="FAILED").inc()
            except Exception:
                self.db.rollback()

            raise

    def persist_rag_evidence(
        self,
        *,
        investigation_id: int,
        rag_context: Any = None,
        rag_query: str | None = None,
        rag_citations: list[dict[str, Any]] | None = None,
        tool_call_id: int | None = None,
    ) -> dict[str, int]:
        """
        Persist retrieved RAG context items as InvestigationEvidence records.

        Returns a mapping of citation_id (e.g. 'KB-1') to evidence_id.
        Each citation_id and chunk_id is persisted at most once per investigation.
        """
        raw_items: list[Any] = []
        if rag_citations is not None:
            raw_items = list(rag_citations)
        elif rag_context is not None:
            if hasattr(rag_context, "items"):
                raw_items = list(rag_context.items)
                if rag_query is None and hasattr(rag_context, "query"):
                    rag_query = rag_context.query
            elif isinstance(rag_context, dict):
                raw_items = (
                    rag_context.get("items")
                    or rag_context.get("citations")
                    or []
                )
                if rag_query is None:
                    rag_query = rag_context.get("query")
            elif isinstance(rag_context, list):
                raw_items = list(rag_context)

        citation_to_evidence_id: dict[str, int] = {}
        seen_citations: set[str] = set()
        seen_chunks: set[str] = set()

        for idx, raw_item in enumerate(raw_items, start=1):
            if hasattr(raw_item, "model_dump"):
                item = raw_item.model_dump(mode="json")
            elif isinstance(raw_item, dict):
                item = raw_item
            else:
                item = vars(raw_item)

            citation_id = str(item.get("citation_id") or f"KB-{idx}")
            chunk_id = str(item.get("chunk_id") or f"chunk-{idx}")

            if citation_id in seen_citations or chunk_id in seen_chunks:
                continue

            seen_citations.add(citation_id)
            seen_chunks.add(chunk_id)

            title = str(
                item.get("title")
                or item.get("source_name")
                or "Knowledge Document"
            )
            content = str(item.get("content") or "")
            source_name = str(item.get("source_name") or "UNKNOWN")
            source_type = str(item.get("source_type") or "UNKNOWN")
            document_id = str(item.get("document_id") or "")
            version_number = int(item.get("version_number", 0))
            score = float(item.get("score", 0.0))

            metadata: dict[str, Any] = {
                "citation_id": citation_id,
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source_type": source_type,
                "source_name": source_name,
                "version_number": version_number,
                "score": score,
                "rag_query": rag_query,
            }

            if isinstance(item.get("metadata"), dict):
                for k, v in item["metadata"].items():
                    if k not in metadata:
                        metadata[k] = v

            db_ev = InvestigationEvidence(
                investigation_id=investigation_id,
                tool_call_id=tool_call_id,
                evidence_type="KNOWLEDGE_BASE",
                source=title[:150],
                source_reference=chunk_id[:255],
                content=content,
                evidence_metadata=metadata,
                collected_at=datetime.now(timezone.utc),
            )
            self.db.add(db_ev)
            self.db.flush()

            citation_to_evidence_id[citation_id] = db_ev.evidence_id

        return citation_to_evidence_id

