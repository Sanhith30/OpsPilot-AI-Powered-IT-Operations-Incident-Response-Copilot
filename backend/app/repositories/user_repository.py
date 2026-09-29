from sqlalchemy import select
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User
class UserRepository:
    def __init__(self, db): self.db=db
    def get_by_id(self,user_id): return self.db.scalars(select(User).where(User.user_id==user_id)).one_or_none()
    def get_by_email(self,email): return self.db.scalars(select(User).where(User.email==email)).one_or_none()
    def get_permissions(self,user_id):
        q=(select(Permission.permission_code).join(RolePermission,RolePermission.permission_id==Permission.permission_id).join(User,User.role_id==RolePermission.role_id).where(User.user_id==user_id).order_by(Permission.permission_code))
        return list(self.db.scalars(q).all())
    def has_permission(self,user_id,permission_code):
        q=(select(Permission.permission_id).join(RolePermission,RolePermission.permission_id==Permission.permission_id).join(User,User.role_id==RolePermission.role_id).where(User.user_id==user_id,Permission.permission_code==permission_code).limit(1))
        return self.db.scalar(q) is not None
