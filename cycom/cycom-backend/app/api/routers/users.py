from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.dependencies import get_current_superuser, get_current_user, require_permission
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import Role, User
from app.schemas.user import RoleCreate, RoleResponse, UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.write")),
):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role_id=user_in.role_id,
        company_id=user_in.company_id or current_user.company_id,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser and current_user.is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log_action(db, user=current_user, action="create", entity_type="User", entity_id=db_user.id)
    return db_user


@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.read")),
):
    q = db.query(User)
    if not current_user.is_superuser:
        q = q.filter(User.company_id == current_user.company_id)
    return q.all()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.write")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_superuser and user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.hashed_password = get_password_hash(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    log_action(db, user=current_user, action="update", entity_type="User", entity_id=user.id)
    return user


@router.post("/roles", response_model=RoleResponse)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.write")),
):
    role = Role(
        name=role_in.name,
        permissions=role_in.permissions,
        company_id=current_user.company_id,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    log_action(db, user=current_user, action="create", entity_type="Role", entity_id=role.id)
    return role


@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.read")),
):
    q = db.query(Role)
    if not current_user.is_superuser:
        q = q.filter((Role.company_id == current_user.company_id) | (Role.company_id.is_(None)))
    return q.all()
