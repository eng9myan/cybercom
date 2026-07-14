from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import Role, User
from app.schemas.user import Token, UserResponse

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    permissions = ["*"] if user.is_superuser else []
    if not user.is_superuser and user.role_id:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role:
            permissions = role.permissions or []

    access_token = create_access_token(
        subject=user.email, permissions=permissions, company_id=user.company_id
    )

    log_action(db, user=user, action="login", entity_type="User", entity_id=user.id)

    return Token(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
