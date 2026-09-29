from sqlalchemy import select
from app.models.investigation_evidence import InvestigationEvidence


class EvidenceRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, evidence_id: int):
        return self.db.scalars(
            select(InvestigationEvidence).where(
                InvestigationEvidence.evidence_id == evidence_id
            )
        ).one_or_none()

    def get_by_investigation(self, investigation_id: int):
        return list(
            self.db.scalars(
                select(InvestigationEvidence)
                .where(
                    InvestigationEvidence.investigation_id == investigation_id
                )
                .order_by(InvestigationEvidence.evidence_id)
            ).all()
        )

    def get_knowledge_base_by_investigation(
        self, investigation_id: int
    ) -> list[InvestigationEvidence]:
        return list(
            self.db.scalars(
                select(InvestigationEvidence)
                .where(
                    InvestigationEvidence.investigation_id == investigation_id,
                    InvestigationEvidence.evidence_type == "KNOWLEDGE_BASE",
                )
                .order_by(InvestigationEvidence.evidence_id)
            ).all()
        )

    def get_by_tool_call(self, tool_call_id: int):
        return list(
            self.db.scalars(
                select(InvestigationEvidence)
                .where(
                    InvestigationEvidence.tool_call_id == tool_call_id
                )
                .order_by(InvestigationEvidence.evidence_id)
            ).all()
        )

    def add(self, evidence: InvestigationEvidence):
        self.db.add(evidence)
        return evidence


InvestigationEvidenceRepository = EvidenceRepository

