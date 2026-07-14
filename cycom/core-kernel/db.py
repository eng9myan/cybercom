# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine, Column, Integer, String, Index, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///cycom_erp.db")
EU_DATABASE_URL = os.getenv("EU_DATABASE_URL", "sqlite:///cycom_erp_eu.db")

# Dynamic database driver and connection pool configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True
    )

if EU_DATABASE_URL.startswith("sqlite"):
    eu_engine = create_engine(
        EU_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    eu_engine = create_engine(
        EU_DATABASE_URL,
        pool_size=10,
        max_overflow=5,
        pool_pre_ping=True
    )

Base = declarative_base()


class MultiTenantMixin:
    """Enforces B2B multi-tenancy constraints and tracks last modified times for sync."""
    tenant_id = Column(Integer, nullable=False, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    last_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    @classmethod
    def __declare_last__(cls):
        """Enforces a composite index on (tenant_id, company_id) for the model table."""
        if hasattr(cls, "__tablename__") and cls.__tablename__:
            Index(
                f"idx_{cls.__tablename__}_tenant_company",
                cls.tenant_id,
                cls.company_id
            )


class AuditLog(Base, MultiTenantMixin):
    """Immutable tamper-evident ledger of operations with cryptographic hash chaining."""
    __tablename__ = "core_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prev_hash = Column(String, nullable=False, default="0")
    current_hash = Column(String, nullable=False)


class SyncLog(Base, MultiTenantMixin):
    """Tracks synchronization runs of geo-distributed edge POS or clinic nodes."""
    __tablename__ = "core_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    edge_id = Column(String, nullable=False, index=True)
    last_sync_timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="success")  # success | error
    details = Column(String, nullable=True)


def get_engine_for_tenant(tenant_id: int):
    """Dynamic Shard Router enforcing EU GDPR Data Residency boundaries."""
    if tenant_id >= 1000:
        return eu_engine
    return engine


def get_tenant_session(tenant_id: int):
    """Generates an isolated database session bound to the tenant shard."""
    tenant_engine = get_engine_for_tenant(tenant_id)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=tenant_engine)
    return Session()


def get_db(tenant_id: int = 1):
    """Yields scoped session matching tenant region."""
    db = get_tenant_session(tenant_id)
    try:
        yield db
    finally:
        db.close()
