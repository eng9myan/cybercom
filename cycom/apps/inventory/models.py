# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from decimal import Decimal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class Warehouse(Base, MultiTenantMixin):
    """Physical warehouse facility."""
    __tablename__ = "inv_warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)


class StockLocation(Base, MultiTenantMixin):
    """Specific stock bins or zones (e.g. Input, WIP, Scrap) within a warehouse."""
    __tablename__ = "inv_locations"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("inv_warehouses.id"), nullable=False)
    name = Column(String, nullable=False)


class Product(Base, MultiTenantMixin):
    """B2B Inventory Products."""
    __tablename__ = "inv_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    barcode = Column(String, nullable=True)
    uom = Column(String, default="unit", nullable=False)  # Unit of Measure (unit, kg, litre)
    category = Column(String, nullable=True)
    cost = Column(Numeric(14, 4), default=0.0, nullable=False)  # Recalculated on AVCO
    price = Column(Numeric(14, 2), default=0.0, nullable=False)
    is_active = Column(Numeric, default=1.0)


class StockQuant(Base, MultiTenantMixin):
    """Real-time physical stock counts per product and location."""
    __tablename__ = "inv_quants"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("inv_locations.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("inv_products.id"), nullable=False, index=True)
    qty = Column(Numeric(12, 4), default=0.0, nullable=False)


class StockMove(Base, MultiTenantMixin):
    """Double-entry inventory stock transaction ledger."""
    __tablename__ = "inv_stock_moves"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("inv_products.id"), nullable=False, index=True)
    from_location_id = Column(Integer, ForeignKey("inv_locations.id"), nullable=True)
    to_location_id = Column(Integer, ForeignKey("inv_locations.id"), nullable=True)
    qty = Column(Numeric(12, 4), default=0.0, nullable=False)
    price_unit = Column(Numeric(14, 4), default=0.0, nullable=False)
    reference = Column(String, nullable=False)  # PO or SO reference
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    state = Column(String, default="done")  # draft | done | cancel


class PurchaseOrder(Base, MultiTenantMixin):
    """B2B Purchase Orders (Procurement)."""
    __tablename__ = "inv_purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    partner_id = Column(Integer, nullable=False, index=True)  # Vendor Partner ID
    date = Column(Date, nullable=False)
    amount_untaxed = Column(Numeric(14, 2), default=0.0, nullable=False)
    amount_tax = Column(Numeric(14, 2), default=0.0, nullable=False)
    amount_total = Column(Numeric(14, 2), default=0.0, nullable=False)
    state = Column(String, default="draft")  # draft | confirmed | done | cancel


class PurchaseOrderLine(Base, MultiTenantMixin):
    """Lines containing item orders inside a Purchase Order."""
    __tablename__ = "inv_purchase_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("inv_purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("inv_products.id"), nullable=False)
    name = Column(String, nullable=False)
    qty = Column(Numeric(12, 4), default=1.0, nullable=False)
    price_unit = Column(Numeric(14, 2), default=0.0, nullable=False)
    price_subtotal = Column(Numeric(14, 2), default=0.0, nullable=False)


# =========================================================================
#   REVERSE LOGISTICS (Trade-ins, Recycling & Remanufacturing Loops)
# =========================================================================

class ReverseLogisticsRecord(Base, MultiTenantMixin):
    """Tracks circular economy lifecycle loops for returned physical goods."""
    __tablename__ = "inv_reverse_logistics"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("inv_products.id"), nullable=False, index=True)
    partner_id = Column(Integer, nullable=True)
    return_reason = Column(String, nullable=False)  # defective | trade_in | recycling
    disposition = Column(String, default="inspect")  # inspect | remanufacture | recycle | scrap
    status = Column(String, default="received")  # received | sorting | processing | completed
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryService:
    """Manages transactional double-entry inventory moves and costing rules."""

    @staticmethod
    def execute_stock_move(db: Session, product_id: int, from_loc_id: int, to_loc_id: int, qty: Decimal, price_unit: Decimal, reference: str, tenant_id: int, company_id: int) -> StockMove:
        # 1. AVCO recalculation on incoming purchase moves (from external supplier) - Done before updating quants
        if not from_loc_id and to_loc_id:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                old_qty_res = db.query(func.sum(StockQuant.qty)).filter(StockQuant.product_id == product_id).scalar()
                old_qty = Decimal(str(old_qty_res or 0.0))
                old_cost = Decimal(str(product.cost))
                
                # Ensure we handle division by zero
                total_qty = old_qty + qty
                if total_qty > 0:
                    new_cost = ((old_qty * old_cost) + (qty * price_unit)) / total_qty
                    product.cost = round(new_cost, 4)

        # 2. Update source location quant
        if from_loc_id:
            from_quant = db.query(StockQuant).filter(StockQuant.location_id == from_loc_id, StockQuant.product_id == product_id).first()
            if from_quant:
                from_quant.qty -= qty
            else:
                from_quant = StockQuant(location_id=from_loc_id, product_id=product_id, qty=-qty, tenant_id=tenant_id, company_id=company_id)
                db.add(from_quant)

        # 3. Update destination location quant
        if to_loc_id:
            to_quant = db.query(StockQuant).filter(StockQuant.location_id == to_loc_id, StockQuant.product_id == product_id).first()
            if to_quant:
                to_quant.qty += qty
            else:
                to_quant = StockQuant(location_id=to_loc_id, product_id=product_id, qty=qty, tenant_id=tenant_id, company_id=company_id)
                db.add(to_quant)

        # 4. Create Stock Move ledger entry
        move = StockMove(
            product_id=product_id,
            from_location_id=from_loc_id,
            to_location_id=to_loc_id,
            qty=qty,
            price_unit=price_unit,
            reference=reference,
            tenant_id=tenant_id,
            company_id=company_id
        )
        db.add(move)
        db.commit()
        db.refresh(move)
        return move
