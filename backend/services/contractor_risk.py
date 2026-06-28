"""
Contractor Risk Scoring Service

Manages the risk score for every contractor in the system.
Score starts at 100 (clean), degrades with each credible bad report.

The scoring logic is intentionally simple and explainable —
judges and NGOs need to understand it, not just trust it.

Score ranges:
  80-100 : Green  — no significant complaints
  50-79  : Yellow — some concerns, worker should be cautious
  0-49   : Red    — high risk, alert pre-loaded for next query
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.models import ContractorRisk, WageReport, NgoAlert
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def find_or_create_contractor(
    db: Session,
    name: str,
    district: str,
    state: str,
    phone: str = None,
) -> ContractorRisk:
    """
    Look up a contractor by name + district. If not found, create a new entry.
    We normalise the name to lowercase for matching.
    """
    normalised_name = name.strip().lower()

    contractor = (
        db.query(ContractorRisk)
        .filter(
            ContractorRisk.name == normalised_name,
            ContractorRisk.district == district,
        )
        .first()
    )

    if not contractor:
        contractor = ContractorRisk(
            name=normalised_name,
            phone=phone,
            district=district,
            state=state,
            risk_score=100.0,
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
    wage_gap = fair_wage - reported_wage
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

    # only hurt the risk score if the gap is meaningful (>10%)
    if gap_percent > 10:
        _degrade_contractor_risk(db, contractor_id, gap_percent)

    db.commit()
    db.refresh(report)

    logger.info(
        f"Wage report saved: worker={worker_id}, "
        f"gap={wage_gap:.0f} ({gap_percent:.1f}%)"
    )
    return report


def _degrade_contractor_risk(
    db: Session,
    contractor_id: int,
    gap_percent: float,
):
    """
    Reduce a contractor's risk score based on wage gap severity.
    Bigger the theft, bigger the penalty.

    Penalty scale:
      10-25% gap  → -8 points
      25-50% gap  → -15 points
      >50% gap    → -25 points
    """
    contractor = db.get(ContractorRisk, contractor_id)
    if not contractor:
        return

    if gap_percent > 50:
        penalty = 25
    elif gap_percent > 25:
        penalty = 15
    else:
        penalty = 8

    contractor.risk_score = max(0.0, contractor.risk_score - penalty)
    contractor.total_reports += 1
    contractor.verified_bad_reports += 1
    contractor.last_updated = datetime.utcnow()

    db.add(contractor)
    logger.info(
        f"Contractor {contractor_id} risk score: "
        f"{contractor.risk_score + penalty:.0f} → {contractor.risk_score:.0f} "
        f"(penalty={penalty}, gap={gap_percent:.1f}%)"
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
    if score >= 80:
        level = "low"
        label = "Safe"
        advice = "No major complaints found. Still, report your wage so others are informed."
    elif score >= 50:
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
            logger.info(f"Alert already sent {days_since_last}d ago for contractor {contractor_id}")
            return False

    return True
