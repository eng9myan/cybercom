from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import sign, users, auth, rpc
from app.db.session import engine, Base
from app.models import (
    attendance as attendance_models,
    audit_log as audit_log_models,
    company as company_models,
    crm as crm_models,
    finance as finance_models,
    fleet as fleet_models,
    helpdesk as helpdesk_models,
    hr as hr_models,
    inventory as inventory_models,
    partner as partner_models,
    payroll as payroll_models,
    pos as pos_models,
    product as product_models,
    projects as projects_models,
    purchase as purchase_models,
    recruitment as recruitment_models,
    sales as sales_models,
    sign as sign_models,
    user as user_models,
    config_param as config_param_models,
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cycom ERP Backend",
    description="Python/FastAPI backend for Cycom ERP",
    version="1.0.0",
)

# Mount static uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(sign.router, prefix="/api/sign", tags=["eSign"])
app.include_router(rpc.router, prefix="/api/rpc", tags=["RPC Proxy"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Cycom ERP API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

