# -*- coding: utf-8 -*-
from sqlalchemy import Column, String
from app.db.base import Base


class ConfigParameter(Base):
    """Clean-room equivalent of ir.config_parameter for storing setup defaults."""
    __tablename__ = "ir_config_parameter"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=True)
