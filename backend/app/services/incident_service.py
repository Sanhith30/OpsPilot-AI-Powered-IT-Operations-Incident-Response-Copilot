from app.core.exceptions import NotFoundError
class IncidentService:
    def __init__(self,db,repository): self.db=db; self.repository=repository
    def get_all_incidents(self): return self.repository.get_all()
    def get_incident_by_id(self,incident_id):
        x=self.repository.get_by_id(incident_id)
        if x is None: raise NotFoundError("Incident not found.")
        return x
    def get_incident_by_number(self,incident_number):
        x=self.repository.get_by_number(incident_number)
        if x is None: raise NotFoundError("Incident not found.")
        return x
    def get_incidents_by_status(self,status): return self.repository.get_by_status(status)
