"""
Database models for Suraksha Chakra.

Tables:
- Worker          : registered worker identity
- ContractorRisk  : contractor/company risk scores (the core feedback loop)
- WageReport      : anonymous wage report from a worker
- NgoAlert        : alert sent to an NGO (tracks what was sent and when)
- VulnerabilityScore : district-level predictive score, updated periodically
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
import enum

from backend.db.database import Base


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISMISSED = "dismissed"


class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True)  # phone-hash, not raw phone
    phone_hash = Column(String, unique=True, nullable=False)
    state = Column(String, nullable=False)       # home state (UP, Bihar etc.)
    occupation = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)  # OTP verified
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("WageReport", back_populates="worker")


class ContractorRisk(Base):
    __tablename__ = "contractor_risk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)

    # starts at 100 (clean), goes down with each credible bad report
    risk_score = Column(Float, default=100.0)
    total_reports = Column(Integer, default=0)
    verified_bad_reports = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("WageReport", back_populates="contractor")


class WageReport(Base):
    __tablename__ = "wage_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractor_risk.id"), nullable=True)

    occupation = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)

    reported_wage = Column(Float, nullable=False)   # what worker was actually paid
    fair_wage = Column(Float, nullable=False)        # what RAG engine returned
    wage_gap = Column(Float, nullable=False)         # fair - reported (positive = underpaid)
    gap_percent = Column(Float, nullable=False)

    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    assigned_officer = Column(String, nullable=True)
    reported_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="reports")
    contractor = relationship("ContractorRisk", back_populates="reports")


class NgoAlert(Base):
    __tablename__ = "ngo_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(Integer, ForeignKey("contractor_risk.id"), nullable=True)
    district = Column(String, nullable=True)

    alert_type = Column(String, nullable=False)  # "wage_theft" | "vulnerability_window"
    message = Column(Text, nullable=False)
    ngo_email = Column(String, nullable=False)

    sent_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)


class VulnerabilityScore(Base):
    __tablename__ = "vulnerability_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)

    # component scores (0-100 each)
    disaster_risk = Column(Float, default=0.0)
    historical_crime_spike = Column(Float, default=0.0)
    migration_pressure = Column(Float, default=0.0)
    active_wage_reports = Column(Float, default=0.0)

    # weighted composite
    composite_score = Column(Float, default=0.0)

    computed_at = Column(DateTime, default=datetime.utcnow)
    forecast_window_days = Column(Integer, default=30)
