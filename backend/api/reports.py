"""
Reports API

Endpoints for:
- Submitting a wage report (from PWA)
- Checking a contractor's risk score
- Getting worker's own report history
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from backend.db.database import get_db_session
from backend.services import contractor_risk as risk_service

router = APIRouter()


def _hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:16]


class WageReportRequest(BaseModel):
    phone: str = Field(..., description="Worker phone (will be hashed, never stored raw)")
    occupation: str
    district: str
    state: str
    reported_wage: float = Field(..., gt=0)
    fair_wage: float = Field(..., gt=0)
    contractor_name: Optional[str] = None
    contractor_phone: Optional[str] = None


class ContractorCheckRequest(BaseModel):
    contractor_name: str
    district: str
    state: str


@router.post("/submit")
def submit_wage_report(
    payload: WageReportRequest,
    db: Session = Depends(get_db_session),
):
    """
    Submit a wage underpayment report.
    The worker's phone is hashed immediately — we never log the raw number.
    """
    phone_hash = _hash_phone(payload.phone)

    # find/create worker row
    from backend.models.models import Worker
    worker = db.query(Worker).filter(Worker.phone_hash == phone_hash).first()
    if not worker:
        worker = Worker(
            id=phone_hash,
            phone_hash=phone_hash,
            state=payload.state,
            occupation=payload.occupation,
            is_verified=True,
        )
        db.add(worker)
        db.commit()

    # find/create contractor
    contractor_id = None
    if payload.contractor_name:
        contractor = risk_service.find_or_create_contractor(
            db,
            name=payload.contractor_name,
            district=payload.district,
            state=payload.state,
            phone=payload.contractor_phone,
        )
        contractor_id = contractor.id

    report = risk_service.record_wage_report(
        db=db,
        worker_id=phone_hash,
        contractor_id=contractor_id,
        occupation=payload.occupation,
        district=payload.district,
        state=payload.state,
        reported_wage=payload.reported_wage,
        fair_wage=payload.fair_wage,
    )

    gap = payload.fair_wage - payload.reported_wage
    gap_pct = (gap / payload.fair_wage * 100) if payload.fair_wage > 0 else 0

    return {
        "message": "Report saved anonymously. Shukriya!",
        "report_id": report.id,
        "wage_gap": round(gap, 2),
        "gap_percent": round(gap_pct, 1),
        "underpaid": gap > 0 and gap_pct > 10,
    }


@router.post("/contractor-check")
def check_contractor(
    payload: ContractorCheckRequest,
    db: Session = Depends(get_db_session),
):
    """
    Look up a contractor's risk score before a worker signs up with them.
    If unknown, creates an entry (score 100) for future tracking.
    """
    contractor = risk_service.find_or_create_contractor(
        db,
        name=payload.contractor_name,
        district=payload.district,
        state=payload.state,
    )
    summary = risk_service.get_contractor_risk_summary(db, contractor.id)
    return summary


@router.get("/contractors/high-risk")
def get_high_risk_contractors(
    state: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db_session),
):
    """
    Return contractors with risk score below 50.
    Used by the ministry dashboard to show the blacklist.
    """
    from backend.models.models import ContractorRisk
    query = db.query(ContractorRisk).filter(ContractorRisk.risk_score < 50)
    if state:
        query = query.filter(ContractorRisk.state == state)

    contractors = query.order_by(ContractorRisk.risk_score.asc()).limit(limit).all()

    return {
        "contractors": [
            {
                "name": c.name,
                "district": c.district,
                "state": c.state,
                "risk_score": round(c.risk_score, 1),
                "total_reports": c.total_reports,
                "verified_bad_reports": c.verified_bad_reports,
            }
            for c in contractors
        ]
    }
