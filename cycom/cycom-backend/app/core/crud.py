"""Tiny CRUD helper shared by all module routers.

This is intentionally minimal — it eliminates per-router boilerplate while keeping
each router free to express its own domain logic.
"""

from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.base import BaseEntity

T = TypeVar("T", bound=BaseEntity)


def list_for_company(
    db: Session,
    model: Type[T],
    company_id: int,
    *,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[Sequence] = None,
) -> List[T]:
    q = db.query(model).filter(model.company_id == company_id, model.is_active.is_(True))
    if filters:
        for k, v in filters.items():
            if v is None:
                continue
            q = q.filter(getattr(model, k) == v)
    if order_by:
        q = q.order_by(*order_by)
    return q.offset(skip).limit(limit).all()


def get_for_company(db: Session, model: Type[T], company_id: int, obj_id: int) -> T:
    obj = (
        db.query(model)
        .filter(model.id == obj_id, model.company_id == company_id, model.is_active.is_(True))
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def create_for_company(
    db: Session, model: Type[T], company_id: int, data: dict, *, created_by_id: Optional[int] = None
) -> T:
    obj = model(**data, company_id=company_id, created_by_id=created_by_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_for_company(
    db: Session,
    model: Type[T],
    company_id: int,
    obj_id: int,
    data: dict,
    *,
    updated_by_id: Optional[int] = None,
) -> T:
    obj = get_for_company(db, model, company_id, obj_id)
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)
    if updated_by_id is not None:
        obj.updated_by_id = updated_by_id
    db.commit()
    db.refresh(obj)
    return obj


def soft_delete_for_company(
    db: Session, model: Type[T], company_id: int, obj_id: int
) -> None:
    obj = get_for_company(db, model, company_id, obj_id)
    obj.is_active = False
    db.commit()
