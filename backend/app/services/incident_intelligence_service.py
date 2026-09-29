from __future__ import annotations

import time
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.ai.intelligence.actions import ActionRecommendationEngine
from app.ai.intelligence.analyzer import IncidentIntelligenceAnalyzer
from app.ai.intelligence.correlation import IncidentCorrelationEngine
from app.ai.intelligence.decision import OperationalDecisionEngine
from app.ai.intelligence.impact import ImpactAssessmentEngine
from app.ai.intelligence.root_cause import RootCauseEngine
from app.ai.intelligence.safety import IntelligenceSafetyGate
from app.ai.intelligence.schemas import IncidentIntelligenceResult
from app.ai.providers.base import LLMProvider
from app.core.exceptions import NotFoundError, ValidationError
from app.models.incident_intelligence import IncidentIntelligence
from app.observability.metrics import (
    INCIDENT_INTELLIGENCE_DURATION_SECONDS,
    INCIDENT_INTELLIGENCE_TOTAL,
    INTELLIGENCE_DECISIONS_TOTAL,
    INTELLIGENCE_SAFETY_REJECTIONS_TOTAL,
    ROOT_CAUSE_CANDIDATES_TOTAL,
)
from app.observability.tracing import get_tracer
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.incident_event_repository import IncidentEventRepository
from app.repositories.incident_intelligence_repository import IncidentIntelligenceRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.services.audit_log_service import AuditLogService

tracer = get_tracer("opspilot.incident.intelligence")


class IncidentIntelligenceService:
    def __init__(
        self,
        db: Session,
        intelligence_repository: IncidentIntelligenceRepository,
        incident_repository: IncidentRepository,
        investigation_repository: InvestigationRepository,
        audit_log_service: AuditLogService,
        event_repository: IncidentEventRepository | None = None,
        deployment_repository: DeploymentRepository | None = None,
        risk_prediction_repository: RiskPredictionRepository | None = None,
        llm_provider: LLMProvider | None = None,
        safety_gate: IntelligenceSafetyGate | None = None,
        correlation_engine: IncidentCorrelationEngine | None = None,
        root_cause_engine: RootCauseEngine | None = None,
        impact_engine: ImpactAssessmentEngine | None = None,
        action_engine: ActionRecommendationEngine | None = None,
        decision_engine: OperationalDecisionEngine | None = None,
    ) -> None:
        self.db = db
        self.intelligence_repository = intelligence_repository
        self.incident_repository = incident_repository
        self.investigation_repository = investigation_repository
        self.audit_log_service = audit_log_service
        self.event_repository = event_repository
        self.deployment_repository = deployment_repository
        self.risk_prediction_repository = risk_prediction_repository
        self.safety_gate = safety_gate or IntelligenceSafetyGate()

        self.analyzer = IncidentIntelligenceAnalyzer(
            llm_provider=llm_provider,
            correlation_engine=correlation_engine,
            root_cause_engine=root_cause_engine,
            impact_engine=impact_engine,
            action_engine=action_engine,
            decision_engine=decision_engine,
        )

    def get_latest_by_incident(self, incident_id: int) -> IncidentIntelligenceResult | None:
        incident = self.incident_repository.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError("Incident not found.")
        record = self.intelligence_repository.get_latest_by_incident(incident_id)
        if record is None:
            return None
        return self._to_result(record)

    def get_latest_by_investigation(self, investigation_id: int) -> IncidentIntelligenceResult | None:
        investigation = self.investigation_repository.get_by_id(investigation_id)
        if investigation is None:
            raise NotFoundError("Investigation not found.")
        record = self.intelligence_repository.get_latest_by_investigation(investigation_id)
        if record is None:
            return None
        return self._to_result(record)

    def generate(
        self,
        *,
        incident_id: int,
        investigation_id: int,
        user_id: int,
        request_id: str | None = None,
    ) -> IncidentIntelligenceResult:
        start_time = time.perf_counter()

        with tracer.start_as_current_span("incident.intelligence") as span:
            span.set_attribute("incident_id", incident_id)
            span.set_attribute("investigation_id", investigation_id)

            # 1. Load incident
            incident = self.incident_repository.get_by_id(incident_id)
            if incident is None:
                raise NotFoundError("Incident not found.")

            # 2. Load investigation
            investigation = self.investigation_repository.get_by_id_with_details(investigation_id)
            if investigation is None:
                raise NotFoundError("Investigation not found.")

            # 3. Load events
            raw_events: list[dict[str, Any]] = []
            if self.event_repository:
                db_events = self.event_repository.get_by_incident(incident_id=incident_id)
                raw_events = [
                    {
                        "event_id": getattr(e, "incident_event_id", getattr(e, "event_id", 0)),
                        "event_type": e.event_type,
                        "summary": getattr(e, "description", getattr(e, "summary", "")),
                        "message": getattr(e, "description", getattr(e, "message", "")),
                        "details": getattr(e, "event_metadata", getattr(e, "details", {})),
                        "timestamp": (
                            e.event_time.isoformat()
                            if hasattr(e, "event_time") and e.event_time
                            else (e.created_at.isoformat() if e.created_at else None)
                        ),
                    }
                    for e in db_events
                ]
            elif hasattr(incident, "events") and incident.events:
                raw_events = [
                    {
                        "event_id": getattr(e, "incident_event_id", getattr(e, "event_id", 0)),
                        "event_type": e.event_type,
                        "summary": getattr(e, "description", getattr(e, "summary", "")),
                        "message": getattr(e, "description", getattr(e, "message", "")),
                        "details": getattr(e, "event_metadata", getattr(e, "details", {})),
                        "timestamp": (
                            e.event_time.isoformat()
                            if hasattr(e, "event_time") and e.event_time
                            else (e.created_at.isoformat() if e.created_at else None)
                        ),
                    }
                    for e in incident.events
                ]

            # 4. Load deployments
            raw_deployments: list[dict[str, Any]] = []
            if self.deployment_repository:
                try:
                    now = datetime.now(timezone.utc)
                    db_deployments = self.deployment_repository.get_recent_by_service(
                        service_id=incident.service_id,
                        environment="production",
                        before_time=now,
                        limit=5,
                    )
                except Exception:
                    db_deployments = []
                raw_deployments = [
                    {
                        "deployment_id": d.deployment_id,
                        "service": getattr(d, "service_name", getattr(d, "service", "")),
                        "status": d.status,
                        "version": d.version,
                        "deployed_at": (
                            d.started_at.isoformat()
                            if hasattr(d, "started_at") and d.started_at
                            else (d.created_at.isoformat() if hasattr(d, "created_at") and d.created_at else None)
                        ),
                    }
                    for d in db_deployments
                ]

            # 5. Load findings
            raw_findings: list[dict[str, Any]] = []
            for f in getattr(investigation, "findings", []):
                linked_ids = [
                    fe.evidence_id
                    for fe in getattr(f, "finding_evidence_links", [])
                ]
                raw_findings.append(
                    {
                        "finding_id": f.finding_id,
                        "finding_text": f.finding_text,
                        "confidence": f.finding_type,
                        "evidence_ids": linked_ids,
                    }
                )

            # 6. Load investigation evidence & 7. Separate operational evidence and knowledge evidence
            raw_evidence: list[dict[str, Any]] = []
            operational_evidence: list[dict[str, Any]] = []
            knowledge_evidence: list[dict[str, Any]] = []
            valid_evidence_ids: set[int] = set()

            for ev in getattr(investigation, "evidence", []):
                valid_evidence_ids.add(ev.evidence_id)
                ev_dict = {
                    "evidence_id": ev.evidence_id,
                    "evidence_type": ev.evidence_type,
                    "source": ev.source,
                    "source_reference": ev.source_reference,
                    "content": ev.content,
                    "metadata": ev.evidence_metadata,
                    "timestamp": ev.collected_at.isoformat() if ev.collected_at else None,
                }
                raw_evidence.append(ev_dict)
                if (ev.evidence_type or "").upper() == "KNOWLEDGE_BASE":
                    knowledge_evidence.append(ev_dict)
                else:
                    operational_evidence.append(ev_dict)

            # Risk prediction
            risk_prediction_dict: dict[str, Any] | None = None
            if self.risk_prediction_repository:
                rp = self.risk_prediction_repository.get_latest_by_investigation(investigation_id)
                if rp:
                    risk_prediction_dict = {
                        "score": float(rp.risk_score),
                        "level": rp.risk_level,
                        "model": rp.model_name,
                    }

            service_title = getattr(incident.service, "service_name", "Core Services") if hasattr(incident, "service") and incident.service else "Core Services"

            incident_dict = {
                "incident_id": incident.incident_id,
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "status": incident.status,
                "service": service_title,
                "started_at": incident.started_at.isoformat() if incident.started_at else None,
            }

            # 8-14. Run correlation, root cause, impact, action, decision via analyzer
            with tracer.start_as_current_span("incident.correlation"):
                pass
            with tracer.start_as_current_span("incident.root_cause"):
                pass
            with tracer.start_as_current_span("incident.impact"):
                pass
            with tracer.start_as_current_span("incident.actions"):
                pass
            with tracer.start_as_current_span("incident.decision"):
                pass

            result = self.analyzer.analyze(
                incident_id=incident_id,
                investigation_id=investigation_id,
                incident=incident_dict,
                events=raw_events,
                deployments=raw_deployments,
                findings=raw_findings,
                knowledge_evidence=knowledge_evidence,
                risk_prediction=risk_prediction_dict,
                evidence_items=raw_evidence,
                valid_evidence_ids=valid_evidence_ids,
            )

            # 15. Run safety gate
            with tracer.start_as_current_span("incident.safety"):
                safety_val = self.safety_gate.validate(
                    result=result,
                    valid_evidence_ids=valid_evidence_ids,
                    has_incident=True,
                    has_investigation=True,
                )

            if not safety_val.is_valid:
                INTELLIGENCE_SAFETY_REJECTIONS_TOTAL.labels(
                    reason="safety_violation"
                ).inc()
                INCIDENT_INTELLIGENCE_TOTAL.labels(status="FAILED").inc()

                # Audit log failure
                self.audit_log_service.add_to_transaction(
                    action="INCIDENT_INTELLIGENCE_FAILED",
                    user_id=user_id,
                    resource_type="INCIDENT_INTELLIGENCE",
                    resource_id=None,
                    action_result="FAILURE",
                    incident_id=incident_id,
                    investigation_id=investigation_id,
                    request_id=request_id,
                    details={
                        "error": safety_val.error_message,
                        "violations": safety_val.violations,
                    },
                )
                self.db.commit()
                raise ValidationError(
                    f"Incident intelligence failed safety validation: {safety_val.error_message}"
                )

            # 16. Persist result
            db_model = IncidentIntelligence(
                incident_id=incident_id,
                investigation_id=investigation_id,
                incident_summary=result.incident_summary,
                correlated_signals=[s.model_dump(mode="json") for s in result.correlated_signals],
                probable_root_causes=[c.model_dump(mode="json") for c in result.probable_root_causes],
                impact_assessment=result.impact_assessment.model_dump(mode="json"),
                risk_assessment=result.risk_assessment,
                recommended_actions=[a.model_dump(mode="json") for a in result.recommended_actions],
                operational_decision=result.operational_decision.model_dump(mode="json"),
                overall_confidence=result.confidence,
                model_name=result.model_name,
                model_version=result.model_version,
            )
            self.intelligence_repository.add(db_model)

            # 17. Write audit log
            self.audit_log_service.add_to_transaction(
                action="INCIDENT_INTELLIGENCE_GENERATED",
                user_id=user_id,
                resource_type="INCIDENT_INTELLIGENCE",
                resource_id=str(db_model.intelligence_id),
                action_result="SUCCESS",
                incident_id=incident_id,
                investigation_id=investigation_id,
                request_id=request_id,
                details={
                    "decision": result.operational_decision.decision,
                    "confidence": str(result.confidence),
                    "model": result.model_name,
                    "root_causes_count": len(result.probable_root_causes),
                    "actions_count": len(result.recommended_actions),
                },
            )
            self.db.commit()

            # Record telemetry
            elapsed = time.perf_counter() - start_time
            INCIDENT_INTELLIGENCE_DURATION_SECONDS.observe(elapsed)
            INCIDENT_INTELLIGENCE_TOTAL.labels(status="SUCCESS").inc()
            INTELLIGENCE_DECISIONS_TOTAL.labels(decision=result.operational_decision.decision).inc()
            for c in result.probable_root_causes:
                ROOT_CAUSE_CANDIDATES_TOTAL.labels(cause=c.cause[:50]).inc()

            span.set_attribute("decision", result.operational_decision.decision)
            span.set_attribute("risk_level", str(result.impact_assessment.severity))
            span.set_attribute("root_cause_count", len(result.probable_root_causes))
            span.set_attribute("action_count", len(result.recommended_actions))

            return result

    def _to_result(self, record: IncidentIntelligence) -> IncidentIntelligenceResult:
        from app.ai.intelligence.schemas import (
            CorrelatedSignal,
            ImpactAssessment,
            OperationalDecision,
            RecommendedAction,
            RootCauseCandidate,
        )

        signals = [CorrelatedSignal.model_validate(s) for s in (record.correlated_signals or [])]
        causes = [RootCauseCandidate.model_validate(c) for c in (record.probable_root_causes or [])]
        impact = ImpactAssessment.model_validate(record.impact_assessment)
        actions = [RecommendedAction.model_validate(a) for a in (record.recommended_actions or [])]
        decision = OperationalDecision.model_validate(record.operational_decision)

        return IncidentIntelligenceResult(
            incident_id=record.incident_id,
            investigation_id=record.investigation_id,
            incident_summary=record.incident_summary,
            correlated_signals=signals,
            probable_root_causes=causes,
            impact_assessment=impact,
            risk_assessment=record.risk_assessment or {},
            recommended_actions=actions,
            operational_decision=decision,
            confidence=record.overall_confidence,
            model_name=record.model_name,
            model_version=record.model_version,
        )
