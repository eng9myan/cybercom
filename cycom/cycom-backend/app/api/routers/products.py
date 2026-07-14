from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.product import Product, ProductCategory
from app.models.user import User
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter()


@router.get("/categories", response_model=List[ProductCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("products.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, ProductCategory, cid)


@router.post("/categories", response_model=ProductCategoryResponse)
def create_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("products.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, ProductCategory, cid, payload.model_dump(), created_by_id=user.id
    )


@router.get("/", response_model=List[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("products.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Product, cid, limit=1000)


@router.post("/", response_model=ProductResponse)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("products.write")),
    cid: int = Depends(get_current_company_id),
):
    if db.query(Product).filter(Product.sku == payload.sku, Product.company_id == cid).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    return crud.create_for_company(db, Product, cid, payload.model_dump(), created_by_id=user.id)


@router.get("/{obj_id}", response_model=ProductResponse)
def get_product(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("products.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.get_for_company(db, Product, cid, obj_id)


@router.put("/{obj_id}", response_model=ProductResponse)
def update_product(
    obj_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("products.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Product, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )
