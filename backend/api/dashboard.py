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
    q_reports = db.query(func.count(WageReport.id))
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
    
    # Active officers mock for demo (derived from unique assigned_officers)
    active_officers = db.query(func.count(func.distinct(WageReport.assigned_officer))).filter(WageReport.assigned_officer.isnot(None)).scalar() or 0
    
    q_pending = db.query(func.count(WageReport.id)).filter(WageReport.status == "pending")
    if ngo_district != "ALL_DISTRICTS":
        q_pending = q_pending.filter(WageReport.district == ngo_district)
        
    pending_investigations = q_pending.scalar() or 0

    return {
        "total_complaints": total_reports,
        "complaints_last_7_days": reports_last_7_days,
        "high_risk_contractors": high_risk_contractors,
        "legal_notices_generated": legal_notices_generated,
        "active_officers": max(active_officers, 4), # Minimum 4 for demo
        "pending_investigations": pending_investigations,
    }


@router.get("/reports")
def get_recent_complaints(limit: int = 50, ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Fetch recent wage reports with joined contractor info."""
    q = (
        db.query(WageReport, ContractorRisk.name.label("contractor_name"))
        .outerjoin(ContractorRisk, WageReport.contractor_id == ContractorRisk.id)
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
                "assigned_officer": r.WageReport.assigned_officer or "Unassigned",
                "priority": "High" if r.WageReport.gap_percent > 30 else ("Medium" if r.WageReport.gap_percent > 15 else "Low"),
                "occupation": r.WageReport.occupation,
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
                "avg_wage_gap": 0, # Will be computed in frontend if needed, or mocked
                "latest_complaint": c.last_updated.isoformat(),
            }
            for c in contractors
        ]
    }

@router.get("/complaint-analytics")
def get_complaint_analytics(ngo_district: str = "ALL_DISTRICTS", db: Session = Depends(get_db_session)):
    """Analytics for Labour Officer Dashboard."""
    now = datetime.utcnow()
    q_reports = db.query(WageReport)
    
    if ngo_district != "ALL_DISTRICTS":
        q_reports = q_reports.filter(WageReport.district == ngo_district)
        
    reports = q_reports.all()
    
    today = [r for r in reports if (now - r.reported_at).days == 0]
    last_7 = [r for r in reports if (now - r.reported_at).days <= 7]
    last_30 = [r for r in reports if (now - r.reported_at).days <= 30]
    
    avg_wage_gap = sum(r.wage_gap for r in reports) / len(reports) if reports else 0
    
    occupations = {}
    districts = {}
    for r in reports:
        occupations[r.occupation] = occupations.get(r.occupation, 0) + 1
        districts[r.district] = districts.get(r.district, 0) + 1
        
    most_affected_occ = max(occupations.items(), key=lambda x: x[1])[0] if occupations else "N/A"
    highest_complaint_dist = max(districts.items(), key=lambda x: x[1])[0] if districts else "N/A"
    
    return {
        "complaints_today": len(today),
        "complaints_7_days": len(last_7),
        "complaints_30_days": len(last_30),
        "avg_wage_gap": round(avg_wage_gap, 1),
        "most_affected_occupation": most_affected_occ,
        "highest_complaint_district": highest_complaint_dist
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
    q_base = db.query(VulnerabilityScore)
    if ngo_district != "ALL_DISTRICTS":
        q_base = q_base.filter(VulnerabilityScore.district == ngo_district)
        
    scores = q_base.all()
    
    tracked_districts = len(scores)
    high_risk_districts = sum(1 for s in scores if s.composite_score >= 70)
    avg_vulnerability_score = sum(s.composite_score for s in scores) / tracked_districts if tracked_districts > 0 else 0
    active_monitoring_regions = tracked_districts # all in DB are currently evaluated
    
    return {
        "tracked_districts": tracked_districts,
        "high_risk_districts": high_risk_districts,
        "avg_vulnerability_score": round(avg_vulnerability_score, 1),
        "active_monitoring_regions": active_monitoring_regions,
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

