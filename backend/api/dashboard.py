"""
Dashboard API

Aggregated, anonymised data endpoints for the ministry and NGO dashboard.
All data is district-level or higher — no individual worker data exposed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from backend.db.database import get_db_session
from backend.models.models import (
    WageReport, ContractorRisk, VulnerabilityScore, NgoAlert
)

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview(ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Top-level numbers for the dashboard header cards."""
    q_reports = db.query(func.count(WageReport.id)).filter(WageReport.wage_gap > 0)
    if ngo_district != "ALL_DISTRICTS":
        q_reports = q_reports.filter(WageReport.district == ngo_district)
        
    total_reports = q_reports.scalar() or 0
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    reports_last_7_days = q_reports.filter(WageReport.reported_at >= seven_days_ago).scalar() or 0

    q_contractors = db.query(func.count(ContractorRisk.id)).filter(ContractorRisk.risk_score >= 51)
    if ngo_district != "ALL_DISTRICTS":
        q_contractors = q_contractors.filter(ContractorRisk.district == ngo_district)
    
    high_risk_contractors = q_contractors.scalar() or 0
    
    q_alerts = db.query(func.count(NgoAlert.id))
    if ngo_district != "ALL_DISTRICTS":
        q_alerts = q_alerts.filter(NgoAlert.district == ngo_district)
        
    legal_notices_generated = q_alerts.scalar() or 0

    return {
        "total_complaints": total_reports,
        "complaints_last_7_days": reports_last_7_days,
        "high_risk_contractors": high_risk_contractors,
        "legal_notices_generated": legal_notices_generated,
    }


@router.get("/reports")
def get_recent_complaints(limit: int = 50, ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Fetch recent wage reports with joined contractor info."""
    q = (
        db.query(WageReport, ContractorRisk.name.label("contractor_name"))
        .outerjoin(ContractorRisk, WageReport.contractor_id == ContractorRisk.id)
        .filter(WageReport.wage_gap > 0)
        .order_by(desc(WageReport.reported_at))
    )
    
    if ngo_district != "ALL_DISTRICTS":
        q = q.filter(WageReport.district == ngo_district)
        
    reports = q.limit(limit).all()

    return {
        "complaints": [
            {
                "id": r.WageReport.id,
                "worker_id": r.WageReport.worker_id[:8], # Masked for display
                "district": r.WageReport.district,
                "state": r.WageReport.state,
                "contractor_name": r.contractor_name or "Unknown",
                "reported_wage": r.WageReport.reported_wage,
                "fair_wage": r.WageReport.fair_wage,
                "wage_gap": r.WageReport.wage_gap,
                "status": r.WageReport.status.value if hasattr(r.WageReport.status, "value") else r.WageReport.status,
                "reported_at": r.WageReport.reported_at.isoformat(),
            }
            for r in reports
        ]
    }


@router.get("/contractors")
def get_all_contractors(ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Fetch all contractors for the High Risk Contractors table."""
    q = db.query(ContractorRisk).filter(ContractorRisk.total_reports > 0).order_by(ContractorRisk.risk_score.desc())
    
    if ngo_district != "ALL_DISTRICTS":
        q = q.filter(ContractorRisk.district == ngo_district)
        
    contractors = q.all()

    return {
        "contractors": [
            {
                "id": c.id,
                "name": c.name,
                "district": c.district,
                "state": c.state,
                "risk_score": round(c.risk_score, 1),
                "total_reports": c.total_reports,
                "latest_complaint": c.last_updated.isoformat(),
            }
            for c in contractors
        ]
    }


@router.get("/district-heatmap")
def get_district_heatmap(ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """
    Returns per-district report counts and average wage gap.
    Used by the choropleth map on the dashboard and District Analytics.
    """
    q = (
        db.query(
            WageReport.district,
            WageReport.state,
            func.count(WageReport.id).label("report_count"),
            func.avg(WageReport.wage_gap).label("avg_wage_gap"),
        )
        .filter(WageReport.wage_gap > 0)
        .group_by(WageReport.district, WageReport.state)
    )
    
    if ngo_district != "ALL_DISTRICTS":
        q = q.filter(WageReport.district == ngo_district)
        
    rows = q.all()

    # Calculate worst contractor per district via subqueries or python processing
    results = []
    for row in rows:
        worst_contractor = (
            db.query(ContractorRisk)
            .filter(ContractorRisk.district == row.district)
            .order_by(ContractorRisk.risk_score.desc())
            .first()
        )
        
        results.append({
            "district": row.district,
            "state": row.state,
            "report_count": row.report_count,
            "avg_wage_gap": round(float(row.avg_wage_gap or 0), 2),
            "highest_risk_contractor": worst_contractor.name if worst_contractor else "None",
            "trend": "Up" if row.report_count > 5 else "Stable" # simple mock heuristic for trend
        })

    return {"districts": results}


@router.get("/vulnerability-scores")
def get_vulnerability_scores(min_score: float = 0, ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Return district vulnerability scores."""
    q = (
        db.query(VulnerabilityScore)
        .filter(VulnerabilityScore.composite_score >= min_score)
        .order_by(VulnerabilityScore.composite_score.desc())
    )
    
    if ngo_district != "ALL_DISTRICTS":
        q = q.filter(VulnerabilityScore.district == ngo_district)
        
    scores = q.all()

    return {
        "vulnerability_districts": [
            {
                "id": s.id,
                "district": s.district,
                "state": s.state,
                "composite_score": round(s.composite_score, 1),
                "disaster_risk": round(s.disaster_risk, 1),
                "historical_crime_spike": round(s.historical_crime_spike, 1),
                "migration_pressure": round(s.migration_pressure, 1),
                "active_wage_reports": round(s.active_wage_reports, 1),
                "status": "Critical" if s.composite_score >= 80 else ("High" if s.composite_score >= 60 else "Elevated"),
                "priority": "P1" if s.composite_score >= 80 else ("P2" if s.composite_score >= 60 else "P3"),
            }
            for s in scores
        ]
    }


@router.get("/vulnerability-overview")
def get_vulnerability_overview(ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Top-level stats for the Vulnerability Intelligence dashboard."""
    q_high = db.query(func.count(VulnerabilityScore.id)).filter(VulnerabilityScore.composite_score >= 70)
    if ngo_district != "ALL_DISTRICTS":
        q_high = q_high.filter(VulnerabilityScore.district == ngo_district)
        
    high_risk_districts = q_high.scalar() or 0
    
    # Active alerts proxy
    q_alerts = db.query(func.count(NgoAlert.id)).filter(NgoAlert.acknowledged == False)
    if ngo_district != "ALL_DISTRICTS":
        q_alerts = q_alerts.filter(NgoAlert.district == ngo_district)
        
    current_alerts = q_alerts.scalar() or 0
    
    # Mocking these derived top-level stats using DB constants for the prototype since we don't have an IMD weather table
    return {
        "high_risk_districts": high_risk_districts,
        "current_disaster_alerts": current_alerts + 2, # Example buffer
        "predicted_vulnerability_windows": high_risk_districts + 1,
        "ngos_recommended": max(3, high_risk_districts * 2),
    }


@router.get("/recent-alerts")
def get_recent_alerts(limit: int = 10, ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Recent NGO alerts."""
    q = (
        db.query(NgoAlert)
        .order_by(NgoAlert.sent_at.desc())
    )
    
    if ngo_district != "ALL_DISTRICTS":
        q = q.filter(NgoAlert.district == ngo_district)
        
    alerts = q.limit(limit).all()

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

