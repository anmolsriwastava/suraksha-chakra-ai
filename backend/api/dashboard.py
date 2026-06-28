"""
Dashboard API

Aggregated, anonymised data endpoints for the ministry and NGO dashboard.
All data is district-level or higher — no individual worker data exposed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.database import get_db_session
from backend.models.models import (
    WageReport, ContractorRisk, VulnerabilityScore, NgoAlert
)

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db_session)):
    """Top-level numbers for the dashboard header cards."""
    total_reports = db.query(func.count(WageReport.id)).scalar()
    high_risk_contractors = (
        db.query(func.count(ContractorRisk.id))
        .filter(ContractorRisk.risk_score < 50)
        .scalar()
    )
    alerts_sent = db.query(func.count(NgoAlert.id)).scalar()
    avg_gap = (
        db.query(func.avg(WageReport.wage_gap))
        .filter(WageReport.wage_gap > 0)
        .scalar()
    ) or 0

    return {
        "total_anonymous_reports": total_reports,
        "high_risk_contractors": high_risk_contractors,
        "ngo_alerts_sent": alerts_sent,
        "average_wage_gap_inr": round(float(avg_gap), 2),
    }


@router.get("/district-heatmap")
def get_district_heatmap(db: Session = Depends(get_db_session)):
    """
    Returns per-district report counts and average wage gap.
    Used by the choropleth map on the dashboard.
    """
    rows = (
        db.query(
            WageReport.district,
            WageReport.state,
            func.count(WageReport.id).label("report_count"),
            func.avg(WageReport.wage_gap).label("avg_wage_gap"),
            func.avg(WageReport.gap_percent).label("avg_gap_percent"),
        )
        .group_by(WageReport.district, WageReport.state)
        .all()
    )

    return {
        "districts": [
            {
                "district": row.district,
                "state": row.state,
                "report_count": row.report_count,
                "avg_wage_gap": round(float(row.avg_wage_gap or 0), 2),
                "avg_gap_percent": round(float(row.avg_gap_percent or 0), 1),
            }
            for row in rows
        ]
    }


@router.get("/vulnerability-scores")
def get_vulnerability_scores(
    min_score: float = 0,
    db: Session = Depends(get_db_session),
):
    """
    Return district vulnerability scores for the predictive map layer.
    Filter by min_score to show only at-risk districts.
    """
    scores = (
        db.query(VulnerabilityScore)
        .filter(VulnerabilityScore.composite_score >= min_score)
        .order_by(VulnerabilityScore.composite_score.desc())
        .all()
    )

    return {
        "vulnerability_districts": [
            {
                "district": s.district,
                "state": s.state,
                "composite_score": round(s.composite_score, 1),
                "disaster_risk": round(s.disaster_risk, 1),
                "historical_crime_spike": round(s.historical_crime_spike, 1),
                "migration_pressure": round(s.migration_pressure, 1),
                "active_wage_reports": round(s.active_wage_reports, 1),
                "forecast_window_days": s.forecast_window_days,
                "computed_at": s.computed_at.isoformat(),
            }
            for s in scores
        ]
    }


@router.get("/recent-alerts")
def get_recent_alerts(limit: int = 10, db: Session = Depends(get_db_session)):
    """Recent NGO alerts for the dashboard activity feed."""
    alerts = (
        db.query(NgoAlert)
        .order_by(NgoAlert.sent_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "district": a.district,
                "sent_at": a.sent_at.isoformat(),
                "acknowledged": a.acknowledged,
            }
            for a in alerts
        ]
    }
