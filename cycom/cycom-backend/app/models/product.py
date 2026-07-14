from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Boolean

from app.db.base import BaseEntity


class ProductCategory(BaseEntity):
    __tablename__ = "product_categories"
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)


class Product(BaseEntity):
    __tablename__ = "products"
    sku = Column(String, unique=True, index=True, nullable=False)
    barcode = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False, index=True)
    name_ar = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    uom = Column(String, default="unit", nullable=False)
    sale_price = Column(Numeric(12, 2), default=0, nullable=False)
    cost_price = Column(Numeric(12, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    track_stock = Column(Boolean, default=True, nullable=False)
