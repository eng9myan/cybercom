from sqlalchemy import Column, String, ForeignKey, Integer, Date

from app.db.base import BaseEntity


class JobPosting(BaseEntity):
    __tablename__ = "rec_job_postings"
    title = Column(String, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("hr_departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("hr_positions.id"), nullable=True)
    location = Column(String, nullable=True)
    employment_type = Column(String, default="full_time", nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="open", nullable=False)  # draft|open|filled|closed
    opened_at = Column(Date, nullable=True)


class Candidate(BaseEntity):
    __tablename__ = "rec_candidates"
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    resume_path = Column(String, nullable=True)


class Application(BaseEntity):
    __tablename__ = "rec_applications"
    job_posting_id = Column(Integer, ForeignKey("rec_job_postings.id"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("rec_candidates.id"), nullable=False, index=True)
    stage = Column(String, default="applied", nullable=False)  # applied|screening|interview|offer|hired|rejected
    applied_at = Column(Date, nullable=False)
    notes = Column(String, nullable=True)
