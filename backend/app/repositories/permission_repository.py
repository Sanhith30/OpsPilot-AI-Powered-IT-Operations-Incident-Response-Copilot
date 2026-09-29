from sqlalchemy import select
from app.models.permission import Permission
class PermissionRepository:
    def __init__(self,db): self.db=db
    def get_by_id(self,permission_id): return self.db.scalars(select(Permission).where(Permission.permission_id==permission_id)).one_or_none()
    def get_all(self): return list(self.db.scalars(select(Permission).order_by(Permission.permission_id)).all())
