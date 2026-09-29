from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()
def hash_password(password: str) -> str: return password_hash.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool: return password_hash.verify(plain_password, hashed_password)
def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "user_id": user_id, "iat": now, "exp": now + timedelta(minutes=settings.access_token_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if "user_id" not in payload and "sub" in payload:
        payload["user_id"] = int(payload["sub"])
    return payload

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired access token.") from exc
    subject = payload.get("sub")
    if subject is None: raise UnauthorizedError("Access token is missing subject.")
    try: user_id = int(subject)
    except (TypeError, ValueError) as exc: raise UnauthorizedError("Invalid user identity in access token.") from exc
    user = UserRepository(db).get_by_id(user_id)
    if user is None: raise UnauthorizedError("Authenticated user no longer exists.")
    if not user.is_active: raise ForbiddenError("User account is inactive.")
    return user
