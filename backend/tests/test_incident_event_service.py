from datetime import datetime, timezone

from app.repositories.incident_event_repository import (
    IncidentEventRepository,
)
from app.services.incident_event_service import (
    IncidentEventService,
)


def make_service(db_session):
    repository = IncidentEventRepository(db_session)

    return IncidentEventService(
        db=db_session,
        repository=repository,
    )


def test_get_events_by_incident(db_session):
    service = make_service(db_session)

    events = service.get_events_by_incident(
        incident_id=1,
        limit=10,
    )

    assert isinstance(events, list)

    for event in events:
        assert event.incident_id == 1


def test_get_events_before_time(db_session):
    service = make_service(db_session)

    before_time = datetime(
        2026,
        9,
        26,
        12,
        0,
        tzinfo=timezone.utc,
    )

    events = service.get_events_by_incident(
        incident_id=1,
        before_time=before_time,
        limit=10,
    )

    assert isinstance(events, list)

    for event in events:
        assert event.event_time <= before_time