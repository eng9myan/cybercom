from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date

from app.db.base import BaseEntity


class Lead(BaseEntity):
    __tablename__ = "crm_leads"
    name = Column(String, nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    source = Column(String, nullable=True)
    expected_revenue = Column(Numeric(14, 2), default=0, nullable=False)
    stage = Column(String, default="new", nullable=False)  # new|qualified|proposal|won|lost
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class Opportunity(BaseEntity):
    __tablename__ = "crm_opportunities"
    name = Column(String, nullable=False)
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    amount = Column(Numeric(14, 2), default=0, nullable=False)
    probability = Column(Numeric(5, 2), default=0, nullable=False)
    expected_close = Column(Date, nullable=True)
    stage = Column(String, default="qualified", nullable=False)  # qualified|proposal|negotiation|won|lost
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class Activity(BaseEntity):
    __tablename__ = "crm_activities"
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("crm_opportunities.id"), nullable=True)
    activity_type = Column(String, nullable=False)  # call|email|meeting|task
    subject = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String, default="planned", nullable=False)
