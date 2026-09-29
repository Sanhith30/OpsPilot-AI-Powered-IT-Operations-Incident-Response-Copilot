from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.graph.chat_graph import ConversationalChatGraph
from app.ai.graph.investigation_graph import InvestigationGraph
from app.ai.providers.base import LLMProvider
from app.ai.providers.config import LLMConfig
from app.ai.providers.factory import create_llm_provider
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.registry_factory import create_tool_registry
from app.ai.risk.base import RiskPredictor
from app.ai.risk.factory import create_risk_predictor

from app.core.exceptions import ForbiddenError
from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.repositories.incident_event_repository import IncidentEventRepository
from app.repositories.app_log_repository import AppLogRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.incident_repository import IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.risk_prediction_repository import RiskPredictionRepository
from app.repositories.incident_intelligence_repository import (
    IncidentIntelligenceRepository,
)
from app.repositories.remediation_repository import RemediationRepository
from app.repositories.service_metric_repository import ServiceMetricRepository
from app.repositories.ticket_comment_repository import TicketCommentRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)
from app.repositories.knowledge_document_version_repository import (
    KnowledgeDocumentVersionRepository,
)

from app.ai.rag.access.policy import KnowledgeAccessContext
from app.ai.rag.retrieval.service import (
    KnowledgeRetrievalService,
)
from app.ai.rag.retrieval.factory import (
    create_knowledge_retrieval_service,
)
from app.ai.rag.ingestion.service import (
    KnowledgeIngestionService,
)
from app.ai.rag.ingestion.factory import (
    create_knowledge_ingestion_service,
)

from app.services.audit_log_service import AuditLogService
from app.services.deployment_service import DeploymentService
from app.services.incident_event_service import IncidentEventService
from app.services.incident_service import IncidentService
from app.services.incident_intelligence_service import IncidentIntelligenceService
from app.services.investigation_service import InvestigationService
from app.services.rbac_service import RBACService
from app.services.remediation_service import RemediationService
from app.services.risk_prediction_service import RiskPredictionService
from app.services.ticket_service import TicketService
from app.services.knowledge_document_service import (
    KnowledgeDocumentService,
)


# ============================================================
# Repository Dependencies
# ============================================================

def get_user_repository(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_audit_log_repository(
    db: Session = Depends(get_db),
) -> AuditLogRepository:
    return AuditLogRepository(db)


def get_incident_repository(
    db: Session = Depends(get_db),
) -> IncidentRepository:
    return IncidentRepository(db)


def get_investigation_repository(
    db: Session = Depends(get_db),
) -> InvestigationRepository:
    return InvestigationRepository(db)


def get_ticket_repository(
    db: Session = Depends(get_db),
) -> TicketRepository:
    return TicketRepository(db)


def get_team_repository(
    db: Session = Depends(get_db),
) -> TeamRepository:
    return TeamRepository(db)


def get_ticket_comment_repository(
    db: Session = Depends(get_db),
) -> TicketCommentRepository:
    return TicketCommentRepository(db)


def get_role_repository(
    db: Session = Depends(get_db),
) -> RoleRepository:
    return RoleRepository(db)


def get_permission_repository(
    db: Session = Depends(get_db),
) -> PermissionRepository:
    return PermissionRepository(db)


def get_deployment_repository(
    db: Session = Depends(get_db),
) -> DeploymentRepository:
    return DeploymentRepository(db)


def get_incident_event_repository(
    db: Session = Depends(get_db),
) -> IncidentEventRepository:
    return IncidentEventRepository(db)


def get_knowledge_document_repository(
    db: Session = Depends(get_db),
) -> KnowledgeDocumentRepository:
    return KnowledgeDocumentRepository(db)


def get_knowledge_document_version_repository(
    db: Session = Depends(get_db),
) -> KnowledgeDocumentVersionRepository:
    return KnowledgeDocumentVersionRepository(db)


def get_risk_prediction_repository(
    db: Session = Depends(get_db),
) -> RiskPredictionRepository:
    return RiskPredictionRepository(db)


def get_incident_intelligence_repository(
    db: Session = Depends(get_db),
) -> IncidentIntelligenceRepository:
    return IncidentIntelligenceRepository(db)


def get_remediation_repository(
    db: Session = Depends(get_db),
) -> RemediationRepository:
    return RemediationRepository(db)


# ============================================================
# Service Dependencies
# ============================================================

def get_audit_log_service(
    db: Session = Depends(get_db),
    repository: AuditLogRepository = Depends(
        get_audit_log_repository
    ),
    user_repository: UserRepository = Depends(
        get_user_repository
    ),
) -> AuditLogService:
    return AuditLogService(
        db,
        repository,
        user_repository,
    )


def get_incident_service(
    db: Session = Depends(get_db),
    repository: IncidentRepository = Depends(
        get_incident_repository
    ),
) -> IncidentService:
    return IncidentService(
        db,
        repository,
    )




def get_ticket_service(
    db: Session = Depends(get_db),
    ticket_repository: TicketRepository = Depends(
        get_ticket_repository
    ),
    incident_repository: IncidentRepository = Depends(
        get_incident_repository
    ),
    team_repository: TeamRepository = Depends(
        get_team_repository
    ),
    user_repository: UserRepository = Depends(
        get_user_repository
    ),
    ticket_comment_repository: TicketCommentRepository = Depends(
        get_ticket_comment_repository
    ),
    audit_log_service: AuditLogService = Depends(
        get_audit_log_service
    ),
) -> TicketService:
    return TicketService(
        db,
        ticket_repository,
        incident_repository,
        team_repository,
        user_repository,
        ticket_comment_repository,
        audit_log_service,
    )


def get_rbac_service(
    db: Session = Depends(get_db),
    role_repository: RoleRepository = Depends(
        get_role_repository
    ),
    permission_repository: PermissionRepository = Depends(
        get_permission_repository
    ),
    user_repository: UserRepository = Depends(
        get_user_repository
    ),
    audit_log_service: AuditLogService = Depends(
        get_audit_log_service
    ),
) -> RBACService:
    return RBACService(
        db,
        role_repository,
        permission_repository,
        user_repository,
        audit_log_service,
    )


def get_deployment_service(
    db: Session = Depends(get_db),
    repository: DeploymentRepository = Depends(
        get_deployment_repository
    ),
) -> DeploymentService:
    return DeploymentService(
        db,
        repository,
    )


def get_incident_event_service(
    db: Session = Depends(get_db),
    repository: IncidentEventRepository = Depends(
        get_incident_event_repository
    ),
) -> IncidentEventService:
    return IncidentEventService(
        db=db,
        repository=repository,
    )


def get_risk_prediction_repository(
    db: Session = Depends(get_db),
) -> RiskPredictionRepository:
    return RiskPredictionRepository(db)


def get_risk_prediction_service(
    db: Session = Depends(get_db),
    repository: RiskPredictionRepository = Depends(
        get_risk_prediction_repository
    ),
    incident_repository: IncidentRepository = Depends(
        get_incident_repository
    ),
    investigation_repository: InvestigationRepository = Depends(
        get_investigation_repository
    ),
) -> RiskPredictionService:
    return RiskPredictionService(
        db,
        repository,
        incident_repository,
        investigation_repository,
    )


def get_investigation_service(
    db: Session = Depends(get_db),
    repository: InvestigationRepository = Depends(
        get_investigation_repository
    ),
    incident_repository: IncidentRepository = Depends(
        get_incident_repository
    ),
    audit_log_service: AuditLogService = Depends(
        get_audit_log_service
    ),
    risk_prediction_service: RiskPredictionService = Depends(
        get_risk_prediction_service
    ),
) -> InvestigationService:
    return InvestigationService(
        db=db,
        repository=repository,
        incident_repository=incident_repository,
        audit_log_service=audit_log_service,
        risk_prediction_service=risk_prediction_service,
    )


def get_incident_intelligence_service(
    db: Session = Depends(get_db),
    intelligence_repository: IncidentIntelligenceRepository = Depends(
        get_incident_intelligence_repository
    ),
    incident_repository: IncidentRepository = Depends(
        get_incident_repository
    ),
    investigation_repository: InvestigationRepository = Depends(
        get_investigation_repository
    ),
    audit_log_service: AuditLogService = Depends(
        get_audit_log_service
    ),
    event_repository: IncidentEventRepository = Depends(
        get_incident_event_repository
    ),
    deployment_repository: DeploymentRepository = Depends(
        get_deployment_repository
    ),
    risk_prediction_repository: RiskPredictionRepository = Depends(
        get_risk_prediction_repository
    ),
) -> IncidentIntelligenceService:
    return IncidentIntelligenceService(
        db=db,
        intelligence_repository=intelligence_repository,
        incident_repository=incident_repository,
        investigation_repository=investigation_repository,
        audit_log_service=audit_log_service,
        event_repository=event_repository,
        deployment_repository=deployment_repository,
        risk_prediction_repository=risk_prediction_repository,
    )


def get_remediation_service(
    db: Session = Depends(get_db),
    repository: RemediationRepository = Depends(
        get_remediation_repository
    ),
    incident_repository: IncidentRepository = Depends(
        get_incident_repository
    ),
    investigation_repository: InvestigationRepository = Depends(
        get_investigation_repository
    ),
    audit_log_service: AuditLogService = Depends(
        get_audit_log_service
    ),
) -> RemediationService:
    return RemediationService(
        db=db,
        repository=repository,
        incident_repository=incident_repository,
        investigation_repository=investigation_repository,
        audit_log_service=audit_log_service,
    )


def get_knowledge_retrieval_service(
    repository: KnowledgeDocumentRepository = Depends(
        get_knowledge_document_repository
    ),
) -> KnowledgeRetrievalService:
    return create_knowledge_retrieval_service(
        document_repository=repository,
    )


def get_knowledge_ingestion_service(
    db: Session = Depends(get_db),
    document_repository: KnowledgeDocumentRepository = Depends(
        get_knowledge_document_repository
    ),
    version_repository: KnowledgeDocumentVersionRepository = Depends(
        get_knowledge_document_version_repository
    ),
) -> KnowledgeIngestionService:
    return create_knowledge_ingestion_service(
        db=db,
        document_repository=document_repository,
        version_repository=version_repository,
    )


def get_knowledge_document_service(
    db: Session = Depends(get_db),
    document_repository: KnowledgeDocumentRepository = Depends(
        get_knowledge_document_repository
    ),
    version_repository: KnowledgeDocumentVersionRepository = Depends(
        get_knowledge_document_version_repository
    ),
    ingestion_service: KnowledgeIngestionService = Depends(
        get_knowledge_ingestion_service
    ),
    audit_log_service: AuditLogService = Depends(
        get_audit_log_service
    ),
) -> KnowledgeDocumentService:
    return KnowledgeDocumentService(
        db=db,
        document_repository=document_repository,
        version_repository=version_repository,
        ingestion_service=ingestion_service,
        audit_log_service=audit_log_service,
    )


# ============================================================
# Phase B Repository Dependencies
# ============================================================

def get_app_log_repository(
    db: Session = Depends(get_db),
) -> AppLogRepository:
    return AppLogRepository(db)


def get_service_metric_repository(
    db: Session = Depends(get_db),
) -> ServiceMetricRepository:
    return ServiceMetricRepository(db)


# ============================================================
# AI Tool Registry
# ============================================================

def get_tool_registry(
    db: Session = Depends(get_db),
    incident_service: IncidentService = Depends(
        get_incident_service
    ),
    deployment_service: DeploymentService = Depends(
        get_deployment_service
    ),
    incident_event_service: IncidentEventService = Depends(
        get_incident_event_service
    ),
    app_log_repository: AppLogRepository = Depends(
        get_app_log_repository
    ),
    service_metric_repository: ServiceMetricRepository = Depends(
        get_service_metric_repository
    ),
    ticket_repository: TicketRepository = Depends(
        get_ticket_repository
    ),
    knowledge_retrieval_service: KnowledgeRetrievalService = Depends(
        get_knowledge_retrieval_service
    ),
) -> ToolRegistry:
    return create_tool_registry(
        incident_service=incident_service,
        deployment_service=deployment_service,
        incident_event_service=incident_event_service,
        knowledge_retrieval_service=knowledge_retrieval_service,
        knowledge_access_context=KnowledgeAccessContext(user_id=1, team_id=None),
        app_log_repository=app_log_repository,
        service_metric_repository=service_metric_repository,
        ticket_repository=ticket_repository,
        db=db,
    )


def get_llm_provider() -> LLMProvider:
    config = LLMConfig(
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout_seconds=settings.llm_timeout_seconds,
        api_key=settings.gemini_api_key,
    )

    return create_llm_provider(config)


def get_risk_predictor() -> RiskPredictor:
    return create_risk_predictor("ml")


def get_investigation_graph(
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    risk_predictor: RiskPredictor = Depends(get_risk_predictor),
) -> InvestigationGraph:
    return InvestigationGraph(
        tool_registry=tool_registry,
        llm_provider=llm_provider,
        risk_predictor=risk_predictor,
    )


def get_chat_repository(db: Session = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)


def get_chat_graph(
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    risk_predictor: RiskPredictor = Depends(get_risk_predictor),
) -> ConversationalChatGraph:
    return ConversationalChatGraph(
        tool_registry=tool_registry,
        llm_provider=llm_provider,
        risk_predictor=risk_predictor,
    )


def get_chat_service(
    db: Session = Depends(get_db),
    chat_repository: ChatRepository = Depends(get_chat_repository),
    chat_graph: ConversationalChatGraph = Depends(get_chat_graph),
    audit_log_service=Depends(get_audit_log_service),
):
    from app.services.chat_service import ChatService
    return ChatService(
        db=db,
        chat_repository=chat_repository,
        chat_graph=chat_graph,
        audit_log_service=audit_log_service,
    )


# ============================================================
# Authorization Dependency
# ============================================================

def require_permission(permission_code: str):
    def dependency(
        current_user=Depends(get_current_user),
        user_repository: UserRepository = Depends(
            get_user_repository
        ),
    ):
        target_codes = [permission_code]
        if permission_code == "INCIDENT_READ":
            target_codes.extend(["INCIDENT_VIEW"])
        elif permission_code == "INCIDENT_ANALYZE":
            target_codes.extend(["INCIDENT_VIEW", "INCIDENT_UPDATE"])

        has_permission = any(
            user_repository.has_permission(
                current_user.user_id,
                code,
            )
            for code in target_codes
        )

        if not has_permission:
            raise ForbiddenError(
                "You do not have permission to perform this action: "
                f"{permission_code}"
            )

        return current_user

    return dependency