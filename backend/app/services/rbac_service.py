from app.core.exceptions import ConflictError,NotFoundError
from app.models.role_permission import RolePermission
class RBACService:
    def __init__(self,db,role_repository,permission_repository,user_repository,audit_log_service): self.db=db; self.role_repository=role_repository; self.permission_repository=permission_repository; self.user_repository=user_repository; self.audit_log_service=audit_log_service
    def get_roles(self): return self.role_repository.get_all()
    def get_permissions(self): return self.permission_repository.get_all()
    def get_user_permissions(self,user_id):
        if self.user_repository.get_by_id(user_id) is None: raise NotFoundError("User not found.")
        return self.user_repository.get_permissions(user_id)
    def assign_permission_to_role(self,*,actor_user_id,role_id,permission_id):
        try:
            if self.role_repository.get_by_id(role_id) is None: raise NotFoundError("Role not found.")
            p=self.permission_repository.get_by_id(permission_id)
            if p is None: raise NotFoundError("Permission not found.")
            if any(x.permission_id==permission_id for x in self.role_repository.get_permission_links(role_id)): raise ConflictError("Permission is already assigned to this role.")
            link=RolePermission(role_id=role_id,permission_id=permission_id); self.role_repository.add_permission_link(link); self.db.flush()
            self.audit_log_service.add_to_transaction(action="PERMISSION_CHANGE",user_id=actor_user_id,resource_type="ROLE",resource_id=role_id,details={"operation":"ASSIGN_PERMISSION","permission_id":permission_id,"permission_code":p.permission_code})
            self.db.commit(); return link
        except Exception:
            self.db.rollback(); raise
    def revoke_permission_from_role(self,*,actor_user_id,role_id,permission_id):
        try:
            if self.role_repository.get_by_id(role_id) is None: raise NotFoundError("Role not found.")
            p=self.permission_repository.get_by_id(permission_id)
            if p is None: raise NotFoundError("Permission not found.")
            if not self.role_repository.delete_permission_link(role_id,permission_id): raise NotFoundError("Permission is not assigned to this role.")
            self.db.flush()
            self.audit_log_service.add_to_transaction(action="PERMISSION_CHANGE",user_id=actor_user_id,resource_type="ROLE",resource_id=role_id,details={"operation":"REVOKE_PERMISSION","permission_id":permission_id,"permission_code":p.permission_code})
            self.db.commit()
        except Exception:
            self.db.rollback(); raise
