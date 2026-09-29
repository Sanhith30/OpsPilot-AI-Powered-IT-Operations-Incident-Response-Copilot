from sqlalchemy import select
from app.models.role import Role
from app.models.role_permission import RolePermission
class RoleRepository:
    def __init__(self,db): self.db=db
    def get_by_id(self,role_id): return self.db.scalars(select(Role).where(Role.role_id==role_id)).one_or_none()
    def get_all(self): return list(self.db.scalars(select(Role).order_by(Role.role_id)).all())
    def get_permission_links(self,role_id): return list(self.db.scalars(select(RolePermission).where(RolePermission.role_id==role_id).order_by(RolePermission.permission_id)).all())
    def add_permission_link(self,link): self.db.add(link); return link
    def delete_permission_link(self,role_id,permission_id):
        link=self.db.scalars(select(RolePermission).where(RolePermission.role_id==role_id,RolePermission.permission_id==permission_id)).one_or_none()
        if link is None: return False
        self.db.delete(link); return True
