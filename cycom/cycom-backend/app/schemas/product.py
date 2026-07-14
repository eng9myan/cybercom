from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProductCategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryResponse(ProductCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int


class ProductBase(BaseModel):
    sku: str
    barcode: Optional[str] = None
    name: str
    name_ar: Optional[str] = None
    category_id: Optional[int] = None
    uom: str = "unit"
    sale_price: Decimal = Decimal("0")
    cost_price: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    track_stock: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    uom: Optional[str] = None
    sale_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    track_stock: Optional[bool] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
