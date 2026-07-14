# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from decimal import Decimal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class WorkCenter(Base, MultiTenantMixin):
    """Physical or logical work centers on the manufacturing shop floor."""
    __tablename__ = "mrp_work_centers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    capacity = Column(Numeric(6, 2), default=1.0, nullable=False)
    oee_target = Column(Numeric(5, 2), default=85.0, nullable=False)


class BillOfMaterials(Base, MultiTenantMixin):
    """Structure defining raw material and component ratios to manufacture a product."""
    __tablename__ = "mrp_boms"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)  # Links to inv_products
    name = Column(String, nullable=False)
    version = Column(String, default="1.0", nullable=False)
    costing_method = Column(String, default="standard")  # standard | average | fifo


class BillOfMaterialsLine(Base, MultiTenantMixin):
    """Raw material component line inside a Bill of Materials."""
    __tablename__ = "mrp_bom_lines"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("mrp_boms.id"), nullable=False)
    component_product_id = Column(Integer, nullable=False)  # Links to inv_products
    qty = Column(Numeric(12, 4), default=1.0, nullable=False)


class WorkOrder(Base, MultiTenantMixin):
    """Shop floor work execution sheet linked to work centers and routing steps."""
    __tablename__ = "mrp_work_orders"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("mrp_boms.id"), nullable=False)
    work_center_id = Column(Integer, ForeignKey("mrp_work_centers.id"), nullable=False)
    qty_to_produce = Column(Numeric(12, 4), nullable=False)
    qty_produced = Column(Numeric(12, 4), default=0.0, nullable=False)
    state = Column(String, default="draft")  # draft | ready | progress | done | cancel


# =========================================================================
#   MANUFACTURING ORDERS & ROUTING STEPS
# =========================================================================

class ManufacturingOrder(Base, MultiTenantMixin):
    """B2B Parent Manufacturing Orders."""
    __tablename__ = "mrp_manufacturing_orders"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    product_id = Column(Integer, nullable=False, index=True)
    bom_id = Column(Integer, ForeignKey("mrp_boms.id"), nullable=False)
    qty_planned = Column(Numeric(12, 4), nullable=False)
    qty_produced = Column(Numeric(12, 4), default=0.0, nullable=False)
    state = Column(String, default="draft")  # draft | confirmed | progress | done | cancel


class Routing(Base, MultiTenantMixin):
    """Manufacturing routing instructions."""
    __tablename__ = "mrp_routings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)


class RoutingStep(Base, MultiTenantMixin):
    """Sequenced routing steps mapped to work centers."""
    __tablename__ = "mrp_routing_steps"

    id = Column(Integer, primary_key=True, index=True)
    routing_id = Column(Integer, ForeignKey("mrp_routings.id"), nullable=False)
    sequence = Column(Integer, default=1, nullable=False)
    work_center_id = Column(Integer, ForeignKey("mrp_work_centers.id"), nullable=False)
    operation_name = Column(String, nullable=False)
    cycle_time_mins = Column(Numeric(8, 2), default=15.0, nullable=False)


class MRPProductionService:
    """Manages shop floor execution and inventory syncs."""

    @staticmethod
    def complete_manufacturing_order(db: Session, mo_id: int, component_loc_id: int, finished_loc_id: int, tenant_id: int, company_id: int) -> ManufacturingOrder:
        from apps.inventory.models import InventoryService, Product

        mo = db.query(ManufacturingOrder).filter(ManufacturingOrder.id == mo_id).first()
        if not mo:
            raise ValueError("Manufacturing Order not found")

        # 1. Retrieve the BOM Lines associated with this MO's BOM
        bom_lines = db.query(BillOfMaterialsLine).filter(BillOfMaterialsLine.bom_id == mo.bom_id).all()

        # 2. Consume components from component location to virtual production
        for line in bom_lines:
            qty_to_consume = Decimal(str(line.qty)) * Decimal(str(mo.qty_planned))
            # Fetch component cost to record value
            comp = db.query(Product).filter(Product.id == line.component_product_id).first()
            cost = Decimal(str(comp.cost)) if comp else Decimal("0.0")

            InventoryService.execute_stock_move(
                db=db,
                product_id=line.component_product_id,
                from_loc_id=component_loc_id,
                to_loc_id=None,  # Virtual production consumption
                qty=qty_to_consume,
                price_unit=cost,
                reference=f"MO CONSUME: {mo.number}",
                tenant_id=tenant_id,
                company_id=company_id
            )

        # 3. Produce finished product into finished goods warehouse location
        finished_product = db.query(Product).filter(Product.id == mo.product_id).first()
        finished_cost = Decimal(str(finished_product.cost)) if finished_product else Decimal("0.0")

        InventoryService.execute_stock_move(
            db=db,
            product_id=mo.product_id,
            from_loc_id=None,  # Produced out of virtual manufacturing
            to_loc_id=finished_loc_id,
            qty=mo.qty_planned,
            price_unit=finished_cost,
            reference=f"MO PRODUCE: {mo.number}",
            tenant_id=tenant_id,
            company_id=company_id
        )

        # 4. Mark MO as done
        mo.qty_produced = mo.qty_planned
        mo.state = "done"
        db.commit()
        db.refresh(mo)

        return mo
