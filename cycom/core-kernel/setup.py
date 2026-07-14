# -*- coding: utf-8 -*-
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cycom-backend")))

from db import Base, get_tenant_session, get_engine_for_tenant
from app.models.company import Company
from app.db.base import Base as BackendBase
from apps.finance.models import Account, CarbonAccount
from localization import FiscalLocalizationEngine

logger = logging.getLogger("cycom-setup")
router = APIRouter(prefix="/api/setup", tags=["Onboarding Setup"])


class SetupPayload(BaseModel):
    name: str
    vertical: str
    region: str


@router.post("/bootstrap")
def bootstrap_vertical(payload: SetupPayload, request: Request):
    """Seed the database tables and chart of accounts matching the selected vertical."""
    # Resolve the tenant ID for dynamic sharding
    tenant_id_str = request.headers.get("X-Tenant-ID", "1")
    try:
        tenant_id = int(tenant_id_str)
    except ValueError:
        tenant_id = 1

    tenant_engine = get_engine_for_tenant(tenant_id)
    db = get_tenant_session(tenant_id)
    try:
        # Create all tables (Finance, ESG, etc.) on the target tenant shard
        Base.metadata.create_all(bind=tenant_engine)
        BackendBase.metadata.create_all(bind=tenant_engine)

        # 1. Create the Company record
        company = Company(
            name=payload.name,
            short_name=payload.name.split()[0] if payload.name else "Company",
            code=payload.name.replace(" ", "_").upper()[:8],
            currency="JOD" if payload.region == "JO" else "SAR" if payload.region == "SA" else "USD",
            country_code=payload.region,
            type="commercial",
            is_active=True
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        # 2. Seed Chart of Accounts matching the industry vertical
        accounts = []
        if payload.vertical == "manufacturing":
            # Add manufacturing cost accounts & material assets
            accounts.extend([
                Account(code="100100_cash", name="Cash & Liquidity", type="asset", tenant_id=1, company_id=company.id),
                Account(code="110100_inventory_raw", name="Raw Material Inventory", type="asset", tenant_id=1, company_id=company.id),
                Account(code="110200_inventory_wip", name="WIP Production Stock", type="asset", tenant_id=1, company_id=company.id),
                Account(code="500100_cogs_materials", name="Cost of Raw Materials", type="expense", tenant_id=1, company_id=company.id),
            ])
            # Seed Parallel Carbon ESG Ledger Accounts
            carbon_accounts = [
                CarbonAccount(code="GHG_S1_BOILER", name="Natural Gas Boilers", scope=1, emission_type="fuel", tenant_id=1, company_id=company.id),
                CarbonAccount(code="GHG_S2_GRID", name="Grid Electricity Consumption", scope=2, emission_type="electricity", tenant_id=1, company_id=company.id),
                CarbonAccount(code="GHG_S3_LOGISTICS", name="Third Party Delivery Fleet", scope=3, emission_type="logistics", tenant_id=1, company_id=company.id),
            ]
            for ca in carbon_accounts:
                db.add(ca)

        elif payload.vertical == "law":
            # Add trust and service accounts
            accounts.extend([
                Account(code="100100_cash", name="Cash & Liquidity", type="asset", tenant_id=1, company_id=company.id),
                Account(code="120100_client_trust", name="Client Trust Escrow", type="asset", tenant_id=1, company_id=company.id),
                Account(code="400100_revenue_retainers", name="Legal Consultation Retainers", type="revenue", tenant_id=1, company_id=company.id),
            ])

        elif payload.vertical == "education":
            # Add tuition and facilities accounts
            accounts.extend([
                Account(code="100100_cash", name="Cash & Liquidity", type="asset", tenant_id=1, company_id=company.id),
                Account(code="400200_revenue_tuition", name="Tuition Fee Revenue", type="revenue", tenant_id=1, company_id=company.id),
                Account(code="160100_facilities", name="School Real Estate Assets", type="asset", tenant_id=1, company_id=company.id),
            ])

        # Commit all financial accounts
        for acc in accounts:
            db.add(acc)

        db.commit()
        logger.info(f"Provisioned vertical '{payload.vertical}' for company {company.name} successfully.")
        return {"status": "success", "company_id": company.id, "vertical": payload.vertical}

    except Exception as e:
        db.rollback()
        logger.error(f"Error during setup bootstrapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
