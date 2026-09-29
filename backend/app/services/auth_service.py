from app.core.exceptions import ForbiddenError
from app.core.security import create_access_token,verify_password
class AuthService:
    def __init__(self,db,user_repository): self.db=db; self.user_repository=user_repository
    def authenticate_user(self,email,password):
        u=self.user_repository.get_by_email(email)
        if u is None:return None
        if not u.is_active: raise ForbiddenError("User account is inactive.")
        if not verify_password(password,u.password_hash): return None
        return u
    def login(self,email,password):
        u=self.authenticate_user(email,password)
        return None if u is None else create_access_token(u.user_id)
