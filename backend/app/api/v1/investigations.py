from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_investigation_graph,
    get_investigation_service,
    require_permission,
)
from app.schemas.investigation import (
    AuditLogResponse,
    InvestigationCreate,
    InvestigationDetailResponse,
    InvestigationResponse,
    KnowledgeEvidenceResponse,
)

router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)


@router.get(
    "",
    response_model=list[InvestigationResponse],
)
def get_investigations(
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_all_investigations()


@router.get(
    "/incident/{incident_id}",
    response_model=list[InvestigationResponse],
)
def get_investigations_by_incident(
    incident_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_investigations_by_incident(incident_id)


@router.get(
    "/status/{status}",
    response_model=list[InvestigationResponse],
)
def get_investigations_by_status(
    status: str,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_investigations_by_status(status)


@router.get(
    "/{investigation_id}/details",
    response_model=InvestigationDetailResponse,
)
def get_investigation_details(
    investigation_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_investigation_details(investigation_id)


@router.get(
    "/{investigation_id}/rag-evidence",
    response_model=list[KnowledgeEvidenceResponse],
)
def get_investigation_rag_evidence(
    investigation_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    details = service.get_investigation_details(investigation_id)
    return getattr(details, "knowledge_evidence", [])



@router.get(
    "/{investigation_id}/audit",
    response_model=list[AuditLogResponse],
)
def get_investigation_audit(
    investigation_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_investigation_audit(investigation_id)


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
)
def get_investigation(
    investigation_id: int,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
):
    return service.get_investigation_by_id(investigation_id)


@router.post(
    "",
    response_model=InvestigationDetailResponse,
)
def create_investigation(
    request: InvestigationCreate,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
    graph=Depends(get_investigation_graph),
):
    investigation = service.create_investigation(
        incident_id=request.incident_id,
        investigation_type=request.investigation_type,
        question=request.question,
        actor_user_id=current_user.user_id,
    )

    return service.run_investigation(
        incident_id=request.incident_id,
        question=request.question,
        actor_user_id=current_user.user_id,
        investigation_type=request.investigation_type,
        investigation_id=investigation.investigation_id,
        graph=graph,
    )


@router.post(
    "/run",
    response_model=InvestigationDetailResponse,
)
def run_investigation(
    request: InvestigationCreate,
    current_user=Depends(require_permission("INCIDENT_VIEW")),
    service=Depends(get_investigation_service),
    graph=Depends(get_investigation_graph),
):
    investigation = service.create_investigation(
        incident_id=request.incident_id,
        investigation_type=request.investigation_type,
        question=request.question,
        actor_user_id=current_user.user_id,
    )

    return service.run_investigation(
        incident_id=request.incident_id,
        investigation_type=request.investigation_type,
        question=request.question,
        actor_user_id=current_user.user_id,
        investigation_id=investigation.investigation_id,
        graph=graph,
    )