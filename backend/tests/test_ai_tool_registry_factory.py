from app.ai.tools.registry_factory import create_tool_registry


class FakeIncidentService:
    pass


class FakeDeploymentService:
    pass


class FakeIncidentEventService:
    pass


def test_create_tool_registry():
    registry = create_tool_registry(
        incident_service=FakeIncidentService(),
        deployment_service=FakeDeploymentService(),
        incident_event_service=FakeIncidentEventService(),
    )

    assert {t["name"] for t in registry.list_tools()} == {
        "get_incident",
        "get_recent_deployments",
        "search_incident_events",
    }