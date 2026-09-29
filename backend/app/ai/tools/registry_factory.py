from __future__ import annotations

from app.ai.tools.deployment_tools import GetRecentDeploymentsTool
from app.ai.tools.get_service_metrics import GetServiceMetricsTool
from app.ai.tools.incident_event_tools import SearchIncidentEventsTool
from app.ai.tools.incident_tools import GetIncidentTool
from app.ai.tools.query_tickets import QueryTicketsTool
from app.ai.tools.ticketing_tools import CreateTicketTool
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.search_knowledge import SearchKnowledgeTool
from app.ai.tools.search_logs import SearchLogsTool
from app.ai.tools.sql_tool import ReadOnlySqlTool
from app.repositories.app_log_repository import AppLogRepository
from app.repositories.service_metric_repository import ServiceMetricRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.deployment_service import DeploymentService
from app.services.incident_event_service import IncidentEventService
from app.services.incident_service import IncidentService


def create_tool_registry(
    *,
    incident_service: IncidentService,
    deployment_service: DeploymentService,
    incident_event_service: IncidentEventService,
    knowledge_retrieval_service=None,
    knowledge_access_context=None,
    # Phase B — new operational tools
    app_log_repository: AppLogRepository | None = None,
    service_metric_repository: ServiceMetricRepository | None = None,
    ticket_repository: TicketRepository | None = None,
    db=None,
) -> ToolRegistry:
    registry = ToolRegistry()

    # ------------------------------------------------------------------ #
    # Core Incident Tools                                                  #
    # ------------------------------------------------------------------ #
    registry.register(GetIncidentTool(incident_service=incident_service))
    registry.register(GetRecentDeploymentsTool(deployment_service=deployment_service))
    registry.register(SearchIncidentEventsTool(incident_event_service=incident_event_service))

    # ------------------------------------------------------------------ #
    # Knowledge / RAG                                                      #
    # ------------------------------------------------------------------ #
    if knowledge_retrieval_service is not None and knowledge_access_context is not None:
        registry.register(
            SearchKnowledgeTool(
                retrieval_service=knowledge_retrieval_service,
                access_context=knowledge_access_context,
            )
        )

    # ------------------------------------------------------------------ #
    # Phase B — Application Logs                                          #
    # ------------------------------------------------------------------ #
    if app_log_repository is not None:
        registry.register(SearchLogsTool(log_repository=app_log_repository))

    # ------------------------------------------------------------------ #
    # Phase B — Service Metrics                                           #
    # ------------------------------------------------------------------ #
    if service_metric_repository is not None:
        registry.register(GetServiceMetricsTool(metric_repository=service_metric_repository))

    # ------------------------------------------------------------------ #
    # Phase B — Ticketing                                                 #
    # ------------------------------------------------------------------ #
    if ticket_repository is not None:
        registry.register(QueryTicketsTool(ticket_repository=ticket_repository))

    # ------------------------------------------------------------------ #
    # Phase B — Create Ticket Tool                                        #
    # ------------------------------------------------------------------ #
    if db is not None:
        registry.register(CreateTicketTool(db=db))

    # ------------------------------------------------------------------ #
    # Phase B — Guarded Read-Only SQL Tool                                #
    # ------------------------------------------------------------------ #
    if db is not None:
        registry.register(ReadOnlySqlTool(db=db))

    return registry