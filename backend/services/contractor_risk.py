"""
Contractor Risk Scoring Service

Manages the risk score for every contractor in the system.
Score ranges from 0 (clean) to 100 (maximum risk).

The scoring logic is based on:
- 40 * normalized complaint count
- 30 * average wage gap %
- 20 * repeat offender score
- 10 * recency factor

Score ranges:
  0-25   : Green  — low risk, safe
  26-50  : Yellow — some concerns, caution
  51-75  : Orange — high risk
  76-100 : Red    — maximum risk, avoid
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.models import ContractorRisk, WageReport, NgoAlert
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def find_contractor(
    db: Session,
    name: str,
    district: str,
) -> ContractorRisk:
    """
    Look up a contractor by name + district.
    We normalise the name to lowercase for matching.
    """
    if not name or not district:
        return None
        
    normalised_name = name.strip().lower()

    return (
        db.query(ContractorRisk)
        .filter(
            ContractorRisk.name == normalised_name,
            ContractorRisk.district == district,
        )
        .first()
    )


def create_contractor(
    db: Session,
    name: str,
    district: str,
    state: str,
    phone: str = None,
) -> ContractorRisk:
    """
    Create a new contractor entry.
    Only called when there's an active complaint.
    """
    normalised_name = name.strip().lower()
    
    contractor = ContractorRisk(
        name=normalised_name,
        phone=phone,
        district=district,
        state=state,
        risk_score=0.0,
        total_reports=0,
        verified_bad_reports=0,
    )
    db.add(contractor)
    db.commit()
    db.refresh(contractor)
    logger.info(f"New contractor created: {name} in {district}")
    
    return contractor


def record_wage_report(
    db: Session,
    worker_id: str,
    contractor_id: int,
    occupation: str,
    district: str,
    state: str,
    reported_wage: float,
    fair_wage: float,
) -> WageReport:
    """
    Save a worker's wage report and update the contractor's risk score.
    Returns the saved report.
    """
    wage_gap = max(0.0, fair_wage - reported_wage)  # Only count underpayment as gap
    gap_percent = (wage_gap / fair_wage) * 100 if fair_wage > 0 else 0

    report = WageReport(
        worker_id=worker_id,
        contractor_id=contractor_id,
        occupation=occupation,
        district=district,
        state=state,
        reported_wage=reported_wage,
        fair_wage=fair_wage,
        wage_gap=wage_gap,
        gap_percent=gap_percent,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    if contractor_id:
        _recalculate_risk(db, contractor_id)

    logger.info(
        f"Wage report saved: worker={worker_id}, "
        f"gap={wage_gap:.0f} ({gap_percent:.1f}%)"
    )
    return report


def _recalculate_risk(db: Session, contractor_id: int):
    """
    Recalculate contractor risk based on:
    score = 40(norm_complaint_count) + 30(avg_wage_gap_pct) + 20(repeat_offender) + 10(recency)
    """
    contractor = db.get(ContractorRisk, contractor_id)
    if not contractor:
        return

    # Fetch all bad reports (where gap > 0)
    bad_reports = (
        db.query(WageReport)
        .filter(WageReport.contractor_id == contractor_id, WageReport.wage_gap > 0)
        .all()
    )
    
    num_complaints = len(bad_reports)
    
    if num_complaints == 0:
        contractor.risk_score = 0.0
        contractor.total_reports = 0
        contractor.verified_bad_reports = 0
        db.commit()
        return

    # 1. Normalize complaint count (cap at 10 for max score of 40)
    norm_complaint = min(1.0, num_complaints / 10.0)

    # 2. Average wage gap % (cap at 50% gap for max score of 30)
    avg_gap_pct = sum(r.gap_percent for r in bad_reports) / num_complaints
    norm_gap = min(1.0, avg_gap_pct / 50.0)

    # 3. Repeat offender (multiple reports from DIFFERENT workers)
    unique_workers = len(set(r.worker_id for r in bad_reports))
    norm_repeat = min(1.0, unique_workers / 5.0)

    # 4. Recency (did a complaint happen in the last 30 days?)
    most_recent = max(r.reported_at for r in bad_reports)
    days_ago = (datetime.utcnow() - most_recent).days
    # If 0 days ago -> 1.0. If 90 days ago -> 0.0
    norm_recency = max(0.0, 1.0 - (days_ago / 90.0))

    # Calculate final score
    score = (40 * norm_complaint) + (30 * norm_gap) + (20 * norm_repeat) + (10 * norm_recency)
    
    # Clamp 0 - 100
    final_score = max(0.0, min(100.0, score))

    contractor.risk_score = final_score
    contractor.total_reports = num_complaints
    contractor.verified_bad_reports = num_complaints
    contractor.last_updated = datetime.utcnow()

    db.commit()
    
    logger.info(
        f"Contractor {contractor_id} risk recalculated: "
        f"score={final_score:.1f} (complaints={num_complaints}, avg_gap={avg_gap_pct:.1f}%)"
    )


def get_contractor_risk_summary(
    db: Session, contractor_id: int
) -> dict:
    """
    Return a clean summary dict for the bot to read out to a worker.
    """
    contractor = db.get(ContractorRisk, contractor_id)
    if not contractor:
        return {"found": False}

    score = contractor.risk_score
    
    # 0-25 Green, 26-50 Yellow, 51-75 Orange, 76-100 Red
    if score <= 25:
        level = "low"
        label = "Safe"
        advice = "No major complaints found. Still, report your wage so others are informed."
    elif score <= 50:
        level = "medium"
        label = "Caution"
        advice = (
            f"{contractor.verified_bad_reports} workers have reported wage issues. "
            "Proceed carefully. Ask for written agreement before starting."
        )
    else:
        level = "high"
        label = "High Risk"
        advice = (
            f"WARNING: {contractor.verified_bad_reports} workers reported serious "
            "underpayment. Consider finding alternative work or contact your local "
            "labour office before proceeding."
        )

    return {
        "found": True,
        "contractor_name": contractor.name,
        "risk_score": round(score, 1),
        "risk_level": level,
        "risk_label": label,
        "total_reports": contractor.total_reports,
        "advice": advice,
    }


def should_trigger_ngo_alert(db: Session, contractor_id: int) -> bool:
    """
    Check if this contractor has crossed the threshold for an NGO alert.
    We also check we haven't already alerted recently (within 7 days).
    """
    contractor = db.get(ContractorRisk, contractor_id)
    if not contractor:
        return False

    if contractor.verified_bad_reports < settings.wage_gap_alert_threshold:
        return False

    # check if we've already sent an alert for this contractor recently
    recent_alert = (
        db.query(NgoAlert)
        .filter(
            NgoAlert.contractor_id == contractor_id,
            NgoAlert.alert_type == "wage_theft",
        )
        .order_by(NgoAlert.sent_at.desc())
        .first()
    )

    if recent_alert:
        days_since_last = (datetime.utcnow() - recent_alert.sent_at).days
        if days_since_last < 7:
            return False

    return True
