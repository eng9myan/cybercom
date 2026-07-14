from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_access_token(token)
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise _credentials_exc
    except JWTError:
        raise _credentials_exc

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise _credentials_exc
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser privileges required")
    return current_user


def get_current_company_id(current_user: User = Depends(get_current_user)) -> int:
    if current_user.company_id is None and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="User is not assigned to any company")
    return current_user.company_id or 0


def _user_has_permission(user: User, db: Session, perm: str) -> bool:
    if user.is_superuser:
        return True
    if user.role_id is None:
        return False
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return False
    perms = role.permissions or []
    return "*" in perms or perm in perms or perm.split(".")[0] + ".*" in perms


def require_permission(perm: str) -> Callable:
    def _checker(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        if not _user_has_permission(current_user, db, perm):
            raise HTTPException(status_code=403, detail=f"Missing permission: {perm}")
        return current_user

    return _checker


def require_any_permission(perms: List[str]) -> Callable:
    def _checker(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        for p in perms:
            if _user_has_permission(current_user, db, p):
                return current_user
        raise HTTPException(status_code=403, detail=f"Missing any of: {perms}")

    return _checker
