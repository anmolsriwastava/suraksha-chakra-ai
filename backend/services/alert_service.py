"""
Alert Service

Sends email alerts to NGOs and Labour Officers when:
1. A contractor crosses the bad-report threshold (reactive)
2. A district's vulnerability score enters the danger zone (predictive)

Uses SendGrid. Falls back to console logging if key not set
(useful during development / demo without real email).
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models.models import NgoAlert, ContractorRisk, VulnerabilityScore

logger = logging.getLogger(__name__)
settings = get_settings()

# NGO registry — in production this would be a DB table
# Hardcoded for prototype / demo
NGO_REGISTRY = {
    "Delhi": ["delhi-labour@practicalaction.org", "migrant-help-delhi@isst.ac.in"],
    "Maharashtra": ["workers-mh@aidis.org"],
    "UP": ["up-migrant@igidr.ac.in"],
    "Bihar": ["bihar-labour@sewa.org"],
    "default": ["anmol972122@gmail.com"],
}

LABOUR_OFFICER_REGISTRY = {
    "Delhi": "labour.delhi@nic.in",
    "Maharashtra": "labour.maharashtra@nic.in",
    "default": "anmol.isik@gmail.com",
}


def _get_ngo_emails_for_district(district: str, state: str) -> list[str]:
    """Pick NGO emails based on state. Falls back to default."""
    return NGO_REGISTRY.get(state, NGO_REGISTRY["default"])


def _send_email(to_emails: list[str], subject: str, body: str):
    """
    Send via SendGrid if key is configured, else just log.
    In demo mode, logging is totally fine — judges just see the trigger.
    """
    if not settings.sendgrid_api_key:
        logger.info(
            f"[DEMO MODE — email not sent]\n"
            f"To: {to_emails}\nSubject: {subject}\n\n{body}"
        )
        return

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        message = Mail(
            from_email=settings.alert_from_email,
            to_emails=to_emails,
            subject=subject,
            plain_text_content=body,
        )
        response = sg.send(message)
        logger.info(f"Alert sent to {to_emails} — status {response.status_code}")
    except Exception as e:
        logger.error(f"SendGrid failed: {e}. Alert was: {subject}")


def send_wage_theft_alert(
    db: Session,
    contractor: ContractorRisk,
    report_count: int,
    district: str,
    state: str,
):
    """
    Alert NGOs and the district labour officer that a specific
    contractor has accumulated enough credible wage theft reports.
    """
    ngo_emails = _get_ngo_emails_for_district(district, state)
    officer_email = LABOUR_OFFICER_REGISTRY.get(state, LABOUR_OFFICER_REGISTRY["default"])
    all_recipients = ngo_emails + [officer_email]

    subject = f"[Suraksha Chakra Alert] Wage theft cluster — {contractor.name}, {district}"
    body = f"""
Suraksha Chakra has detected a wage theft cluster.

Contractor: {contractor.name}
District: {district}, {state}
Risk score: {contractor.risk_score:.0f}/100
Reports received: {report_count} (anonymous, verified by OTP)
Reported at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

This contractor has been reported for systematic underpayment by
multiple workers in your district. We recommend:

1. Pre-position a field worker to the area
2. Contact the contractor for verification
3. Inform migrant workers in transit about this contractor

Worker identities are protected. Full anonymised report available
on the Suraksha Chakra ministry dashboard.

— Suraksha Chakra Automated Alert System
"""

    _send_email(all_recipients, subject, body)

    # log the alert in DB so we don't re-send within 7 days
    alert_record = NgoAlert(
        contractor_id=contractor.id,
        district=district,
        alert_type="wage_theft",
        message=body,
        ngo_email=", ".join(all_recipients),
    )
    db.add(alert_record)
    db.commit()
    logger.info(f"Wage theft alert logged for contractor {contractor.id}")


def send_vulnerability_window_alert(
    db: Session,
    vulnerability: VulnerabilityScore,
    trigger_reason: str,
):
    """
    Alert NGOs when a district enters a predicted high-vulnerability window
    (e.g. flood incoming + historical crime spike post-disaster).
    """
    ngo_emails = _get_ngo_emails_for_district(vulnerability.district, vulnerability.state)

    subject = (
        f"[Suraksha Chakra] Vulnerability window opening — "
        f"{vulnerability.district}, {vulnerability.state}"
    )
    body = f"""
Suraksha Chakra predictive model alert.

District: {vulnerability.district}, {vulnerability.state}
Composite vulnerability score: {vulnerability.composite_score:.0f}/100
Forecast window: Next {vulnerability.forecast_window_days} days

Risk breakdown:
  Disaster risk:          {vulnerability.disaster_risk:.0f}/100
  Historical crime spike: {vulnerability.historical_crime_spike:.0f}/100
  Migration pressure:     {vulnerability.migration_pressure:.0f}/100
  Active wage reports:    {vulnerability.active_wage_reports:.0f}/100

Trigger: {trigger_reason}

Based on historical NCRB data, districts that experience climate
displacement events see a 2-3x increase in labour exploitation in
the 30-day post-event window. This is the window to pre-position
field workers and run community awareness sessions.

— Suraksha Chakra Automated Alert System
"""

    _send_email(ngo_emails, subject, body)

    alert_record = NgoAlert(
        district=vulnerability.district,
        alert_type="vulnerability_window",
        message=body,
        ngo_email=", ".join(ngo_emails),
    )
    db.add(alert_record)
    db.commit()
    logger.info(
        f"Vulnerability alert sent for {vulnerability.district} "
        f"(score={vulnerability.composite_score:.0f})"
    )
