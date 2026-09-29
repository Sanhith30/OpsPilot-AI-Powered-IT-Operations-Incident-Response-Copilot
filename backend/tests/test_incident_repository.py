from app.repositories.incident_repository import IncidentRepository
def test_get_incident_by_number(db_session):
    x=IncidentRepository(db_session).get_by_number("INC-1042"); assert x is not None; assert x.incident_number=="INC-1042"
def test_missing_incident_returns_none(db_session): assert IncidentRepository(db_session).get_by_number("INC-DOES-NOT-EXIST") is None
