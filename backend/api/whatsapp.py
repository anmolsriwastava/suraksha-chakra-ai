"""
WhatsApp Webhook Router

Handles incoming Twilio WhatsApp messages.
Every message from a worker flows through here.

Conversation state is kept simple — we store the last intent
in a lightweight session dict (keyed by phone hash).
In production, this would live in Redis.
"""

import hashlib
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Form, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.db.database import get_db_session
from backend.services.speech_service import transcribe_audio
from backend.services.nlp_service import extract_intent, WorkerIntent
from backend.services.wage_engine import get_wage_engine, WageEngine
from backend.services import contractor_risk as risk_service
from backend.services import alert_service

logger = logging.getLogger(__name__)
router = APIRouter()

# in-memory session store (phone_hash → last context)
# good enough for a hackathon demo
_sessions: dict[str, dict] = {}


def _hash_phone(phone: str) -> str:
    """We never store raw phone numbers."""
    return hashlib.sha256(phone.encode()).hexdigest()[:16]


def _get_or_create_session(phone_hash: str) -> dict:
    if phone_hash not in _sessions:
        _sessions[phone_hash] = {
            "last_intent": None,
            "pending_occupation": None,
            "pending_location": None,
            "pending_contractor_id": None,
            "fair_wage": None,
        }
    return _sessions[phone_hash]


async def _get_text_from_message(
    body: str,
    media_url: str | None,
    media_type: str | None,
) -> str:
    """
    If the message is a voice note (audio/ogg), download and transcribe it.
    Otherwise return the text body directly.
    """
    if media_url and media_type and "audio" in media_type:
        logger.info(f"Voice note received, transcribing from {media_url}")
        async with httpx.AsyncClient(timeout=30) as http:
            audio_response = await http.get(media_url)
            audio_response.raise_for_status()
        return await transcribe_audio(audio_response.content)

    return body.strip()


def _build_wage_reply(occupation: str, location: str, wage_result) -> str:
    """
    Craft the Hindi+English wage reply workers see.
    Keeping it simple and readable on a small phone screen.
    """
    if wage_result.confidence == "low" or wage_result.fair_wage_min == 0:
        return (
            f"Sorry, mujhe {occupation} ka {location} mein exact wage nahi mila. "
            f"Approximately ₹450-700/day ho sakta hai. "
            f"Please apna actual wage zaroor batayein."
        )

    return (
        f"✅ *{location} mein {occupation} ka fair wage:*\n"
        f"₹{wage_result.fair_wage_min:.0f} – ₹{wage_result.fair_wage_max:.0f} per day\n\n"
        f"Aapko kitna mil raha hai? (sirf number bhejein, jaise: 400)"
    )


def _build_risk_reply(risk_summary: dict) -> str:
    """Format contractor risk info for WhatsApp."""
    if not risk_summary.get("found"):
        return (
            "Is contractor ke baare mein abhi koi report nahi hai. "
            "Aap pehle reporter ban sakte hain! Apna wage zaroor batayein."
        )

    emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}.get(
        risk_summary["risk_level"], "ℹ️"
    )
    return (
        f"{emoji} *{risk_summary['contractor_name']}*\n"
        f"Risk score: {risk_summary['risk_score']}/100 ({risk_summary['risk_label']})\n"
        f"Reports: {risk_summary['total_reports']}\n\n"
        f"{risk_summary['advice']}"
    )


async def _handle_report_wage(
    phone_hash: str,
    session: dict,
    reported_wage: float,
    db: Session,
    background_tasks: BackgroundTasks,
) -> str:
    """
    Worker just told us what they're being paid.
    Compare with fair wage, record the report, maybe trigger alert.
    """
    fair_wage = session.get("fair_wage")
    occupation = session.get("pending_occupation")
    location = session.get("pending_location", "")
    contractor_id = session.get("pending_contractor_id")

    if not fair_wage or not occupation:
        return (
            "Pehle apna occupation aur location batayein. "
            "Jaise: 'Delhi mein mason ka kaam mila hai'"
        )

    wage_gap = fair_wage - reported_wage
    gap_percent = (wage_gap / fair_wage * 100) if fair_wage > 0 else 0

    # find or create a dummy worker row (using phone hash as ID)
    from backend.models.models import Worker
    worker = db.query(Worker).filter(Worker.phone_hash == phone_hash).first()
    if not worker:
        worker = Worker(
            id=phone_hash,
            phone_hash=phone_hash,
            state=location.split(",")[-1].strip() if "," in location else "",
            occupation=occupation,
            is_verified=True,  # assume OTP-verified for demo
        )
        db.add(worker)
        db.commit()

    # save the report
    state = location.split(",")[-1].strip() if "," in location else location
    report = risk_service.record_wage_report(
        db=db,
        worker_id=phone_hash,
        contractor_id=contractor_id,
        occupation=occupation,
        district=location,
        state=state,
        reported_wage=reported_wage,
        fair_wage=fair_wage,
    )

    # check if we need to fire an NGO alert (run in background, don't block reply)
    if contractor_id and risk_service.should_trigger_ngo_alert(db, contractor_id):
        contractor = db.get(__import__(
            "backend.models.models", fromlist=["ContractorRisk"]
        ).ContractorRisk, contractor_id)
        if contractor:
            background_tasks.add_task(
                alert_service.send_wage_theft_alert,
                db, contractor, contractor.verified_bad_reports, location, state
            )

    # clear session context
    session["fair_wage"] = None
    session["pending_occupation"] = None
    session["pending_contractor_id"] = None
    session["last_intent"] = "report_wage"
    
    is_wage_theft = wage_gap > 0 and gap_percent > 50

    if is_wage_theft:
        base_reply = (
            f"🚨 *Aapka report save ho gaya (anonymously).*\n\n"
            f"Fair wage: ₹{fair_wage:.0f}/day\n"
            f"Aapko mila: ₹{reported_wage:.0f}/day\n"
            f"Farq: ₹{wage_gap:.0f} ({gap_percent:.0f}% kam)\n\n"
            f"Yeh information related NGO aur labour officer ko bhej di gayi hai. "
            f"Aapki identity poori tarah safe hai."
        )
        if contractor_id:
            legal_notice_url = f"https://zippy-preacher-stingy.ngrok-free.dev/api/reports/legal-notice/{report.id}"
            return f"{base_reply}\n\n📄 Download Legal Notice (PDF):\n{legal_notice_url}"
        else:
            return f"{base_reply}\n\nContractor ka naam pata hai? Batayein toh legal notice generate kar sakte hain."
    else:
        return (
            f"✅ *Report save ho gayi.*\n"
            f"Aapka wage fair lag raha hai (₹{reported_wage:.0f} vs fair ₹{fair_wage:.0f}). "
            f"Dhanyavad report karne ke liye! Doosre workers ko bhi yeh system batayein."
        )


@router.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db_session)],
    wage_engine: Annotated[WageEngine, Depends(get_wage_engine)],
    From: str = Form(...),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default=None),
    MediaContentType0: str = Form(default=None),
):
    """
    Main Twilio webhook. Every WhatsApp message arrives here.
    Returns TwiML-compatible plain text (Twilio wraps it).
    """
    phone_hash = _hash_phone(From)
    session = _get_or_create_session(phone_hash)

    # get text (transcribe if voice note)
    try:
        text = await _get_text_from_message(Body, MediaUrl0, MediaContentType0)
    except Exception as e:
        logger.error(f"Failed to get text from message: {e}")
        return "Sorry, message process nahi ho saka. Please text mein likhen."

    if not text:
        return "Koi message nahi mila. Please dobara try karein."

    logger.info(f"Worker [{phone_hash}]: {text[:100]}")

    # extract what they want
    intent_result = extract_intent(text)
    logger.info(f"Intent: {intent_result.intent}")

    if session.get("last_intent") == "report_wage" and intent_result.contractor_name and intent_result.intent != WorkerIntent.WAGE_QUERY:
        from backend.models.models import WageReport, ContractorRisk
        last_report = db.query(WageReport).filter(WageReport.worker_id == phone_hash).order_by(WageReport.reported_at.desc()).first()
        if last_report:
            district = last_report.district or ""
            state = last_report.state or ""
            contractor = risk_service.find_or_create_contractor(db, intent_result.contractor_name, district, state)
            last_report.contractor_id = contractor.id
            db.commit()
            
            if risk_service.should_trigger_ngo_alert(db, contractor.id):
                contractor_db = db.get(ContractorRisk, contractor.id)
                background_tasks.add_task(
                    alert_service.send_wage_theft_alert,
                    db, contractor_db, contractor_db.verified_bad_reports, district, state
                )
                
            session["last_intent"] = "contractor_check"
            legal_notice_url = f"https://zippy-preacher-stingy.ngrok-free.dev/api/reports/legal-notice/{last_report.id}"
            return f"✅ Contractor {intent_result.contractor_name} ka naam record ho gaya hai.\n\n📄 Download Legal Notice (PDF):\n{legal_notice_url}"

    # handle wage reporting (multi-turn: could be just a number)
    if intent_result.intent == WorkerIntent.REPORT_WAGE or (
        session.get("fair_wage") and intent_result.reported_wage
    ):
        wage = intent_result.reported_wage
        if not wage:
            return "Kitna mil raha hai? Sirf number bhejein. Jaise: 500"
        return await _handle_report_wage(
            phone_hash, session, wage, db, background_tasks
        )

    # wage query
    if intent_result.intent == WorkerIntent.WAGE_QUERY:
        occ = intent_result.occupation or "worker"
        loc = intent_result.location_district or intent_result.location_state or "India"

        wage_result = wage_engine.query_fair_wage(occ, loc)

        # save context so next message (reported wage) can be matched
        session["pending_occupation"] = occ
        session["pending_location"] = loc
        session["fair_wage"] = (wage_result.fair_wage_min + wage_result.fair_wage_max) / 2

        return _build_wage_reply(occ, loc, wage_result)

    # contractor check
    if intent_result.intent == WorkerIntent.CONTRACTOR_CHECK:
        contractor_name = intent_result.contractor_name
        if not contractor_name:
            return "Contractor ka naam batayein. Jaise: 'Ramesh Constructions ke baare mein batao'"

        district = intent_result.location_district or session.get("pending_location", "")
        state = intent_result.location_state or ""
        contractor = risk_service.find_or_create_contractor(
            db, contractor_name, district, state
        )
        session["pending_contractor_id"] = contractor.id
        risk_summary = risk_service.get_contractor_risk_summary(db, contractor.id)
        return _build_risk_reply(risk_summary)

    # fallback
    return (
        "Namaste! Main aapki madad kar sakta hoon:\n\n"
        "1️⃣ Fair wage jaanne ke liye: *'Delhi mein mason ka kaam mila'*\n"
        "2️⃣ Contractor check ke liye: *'Ramesh Constructions ke baare mein batao'*\n"
        "3️⃣ Wage report ke liye: apna actual wage number bhejein\n\n"
        "Aap Hindi ya Hinglish mein baat kar sakte hain. "
        "Voice message bhi bhej sakte hain! 🎤"
    )
