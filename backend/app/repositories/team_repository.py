from sqlalchemy import select
from app.models.team import Team
class TeamRepository:
    def __init__(self, db): self.db=db
    def get_by_id(self, team_id): return self.db.scalars(select(Team).where(Team.team_id==team_id)).one_or_none()
