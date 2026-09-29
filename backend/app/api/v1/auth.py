from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.core.exceptions import UnauthorizedError
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest,TokenResponse
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user, get_user_repository
router=APIRouter(prefix="/auth",tags=["Authentication"])
def get_auth_service(db:Session=Depends(get_db)): return AuthService(db,UserRepository(db))
@router.post("/login",response_model=TokenResponse)
def login(request:LoginRequest,service:AuthService=Depends(get_auth_service)):
    token=service.login(request.email,request.password)
    if token is None: raise UnauthorizedError("Invalid email or password.")
    return TokenResponse(access_token=token)

@router.get("/me")
def get_me(
    current_user=Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    permissions = user_repo.get_permissions(current_user.user_id)
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role_id": current_user.role_id,
        "permissions": permissions,
    }

