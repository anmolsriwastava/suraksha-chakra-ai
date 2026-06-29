"""
Chat API

JSON-based chat endpoint for the web frontend.
This is the proper chat interface — separate from the Twilio webhook.

Pipeline:
  User text/voice → [Sarvam STT if voice] → Groq extraction →
  Backend routing → RAG/DB lookup → Groq response generation → reply

Session state is kept in-memory (keyed by session_id).
"""

import base64
import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db_session
from backend.services.nlp_service import extract_intent, WorkerIntent
from backend.services.wage_engine import get_wage_engine, WageEngine
from backend.services import contractor_risk as risk_service
from backend.services import alert_service
from backend.services import response_generator as responder
from backend.services.response_generator import generate_welcome_response
from backend.services.speech_service import transcribe_audio, generate_tts_audio_base64

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response models ──────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = ""
    session_id: str = "demo-user"
    audio_base64: Optional[str] = None  # base64-encoded audio for voice messages


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    extracted: Optional[dict] = None  # structured extraction for frontend
    quick_replies: list[str] = []
    audio_base64: Optional[str] = None


async def _create_response(reply: str, session_id: str, extracted: dict = None, quick_replies: list = None) -> ChatResponse:
    audio = await generate_tts_audio_base64(reply)
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        extracted=extracted,
        quick_replies=quick_replies or [],
        audio_base64=audio
    )


# ── Session management ─────────────────────────────────────────────────


_sessions: dict[str, dict] = {}


def _get_or_create_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "last_intent": None,
            "pending_occupation": None,
            "pending_location": None,
            "pending_contractor_id": None,
            "fair_wage": None,
        }
    return _sessions[session_id]


def _hash_phone(session_id: str) -> str:
    """Create a stable phone hash from session ID for worker identification."""
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


# ── Quick reply suggestions ───────────────────────────────────────────


QUICK_REPLIES = {
    "welcome": [
        "Delhi mein raaj mistri ka kaam mila",
        "Mumbai mein electrician hoon",
        "Contractor ka naam check karna hai",
    ],
    "after_wage": [
        "Mujhe ₹400 mil raha hai",
        "Mujhe ₹500 mil raha hai",
        "Mujhe ₹600 mil raha hai",
        "Contractor ka naam batana hai",
    ],
    "after_report": [
        "Doosra contractor check karna hai",
        "Naya wage query karna hai",
    ],
    "after_contractor": [
        "Wage check karna hai",
        "Doosra contractor check karna hai",
    ],
}


def _pick_quick_replies(intent: WorkerIntent) -> list[str]:
    """Select contextual quick replies based on what just happened."""
    mapping = {
        WorkerIntent.WAGE_QUERY: QUICK_REPLIES["after_wage"],
        WorkerIntent.REPORT_WAGE: QUICK_REPLIES["after_report"],
        WorkerIntent.CONTRACTOR_CHECK: QUICK_REPLIES["after_contractor"],
        WorkerIntent.HELP: QUICK_REPLIES["welcome"],
        WorkerIntent.UNKNOWN: QUICK_REPLIES["welcome"],
    }
    return mapping.get(intent, QUICK_REPLIES["welcome"])


# ── Intent handlers ────────────────────────────────────────────────────


def _handle_wage_query(
    session: dict,
    intent_result,
    wage_engine: WageEngine,
) -> str:
    """Look up fair wage via RAG and generate a natural response."""
    occ = intent_result.occupation or "worker"
    loc = intent_result.location_district or intent_result.location_state or "India"

    wage_result = wage_engine.query_fair_wage(occ, loc)

    # Save context for follow-up wage report
    session["pending_occupation"] = occ
    session["pending_location"] = loc
    session["fair_wage"] = (wage_result.fair_wage_min + wage_result.fair_wage_max) / 2
    session["last_intent"] = "wage_query"

    return responder.generate_wage_response(
        occupation=occ,
        location=loc,
        fair_wage_min=wage_result.fair_wage_min,
        fair_wage_max=wage_result.fair_wage_max,
        source=wage_result.source,
        confidence=wage_result.confidence,
        language=intent_result.language,
    )


def _handle_contractor_check(
    session: dict,
    intent_result,
    db: Session,
) -> str:
    """Check contractor risk and generate response."""
    contractor_name = intent_result.contractor_name
    # Expanded blocklist: common Hindi/Hinglish filler words that are NOT real names
    invalid_names = {
        'doosra', 'koi', 'woh', 'contractor', 'thekedaar', 'thekedar',
        'ek', 'us', 'naam', 'batana', 'batao', 'check', 'haan', 'ha',
        'nahi', 'karna', 'hai', 'ka', 'ki', 'ke', 'mein', 'se',
        'raaj mistri', 'rajmistri', 'mason', 'electrician', 'plumber',
        'helper', 'carpenter', 'painter', 'welder', 'driver',
    }
    
    if (not contractor_name or not contractor_name.strip() or 
        len(contractor_name.strip()) < 4 or 
        contractor_name.strip().lower() in invalid_names or
        # Block if name is just common Hindi words (no proper noun detected)
        all(word.lower() in invalid_names for word in contractor_name.strip().split())):
        return responder.generate_ask_missing_info("contractor_name")

    district = intent_result.location_district or session.get("pending_location", "")
    state = intent_result.location_state or ""
    contractor = risk_service.find_or_create_contractor(
        db, contractor_name, district, state
    )
    session["pending_contractor_id"] = contractor.id
    session["last_intent"] = "contractor_check"

    risk_summary = risk_service.get_contractor_risk_summary(db, contractor.id)

    if not risk_summary.get("found"):
        return responder.generate_contractor_not_found_response(
            contractor_name, intent_result.language
        )

    return responder.generate_contractor_risk_response(
        contractor_name=risk_summary["contractor_name"],
        risk_score=risk_summary["risk_score"],
        risk_level=risk_summary["risk_level"],
        risk_label=risk_summary["risk_label"],
        total_reports=risk_summary["total_reports"],
        advice=risk_summary["advice"],
        language=intent_result.language,
    )


def _handle_report_wage(
    session: dict,
    intent_result,
    session_id: str,
    db: Session,
    background_tasks: BackgroundTasks,
) -> str:
    """Record wage report and generate confirmation."""
    reported_wage = intent_result.reported_wage
    if not reported_wage:
        return responder.generate_ask_missing_info("reported_wage")

    fair_wage = session.get("fair_wage")
    occupation = intent_result.occupation or session.get("pending_occupation")
    location = intent_result.location_district or session.get("pending_location", "")
    contractor_id = session.get("pending_contractor_id")

    if not fair_wage or not occupation:
        return (
            "Pehle apna occupation aur location batayein. "
            "Jaise: 'Delhi mein raaj mistri ka kaam mila hai'"
        )

    phone_hash = _hash_phone(session_id)

    # Find or create worker
    from backend.models.models import Worker
    worker = db.query(Worker).filter(Worker.phone_hash == phone_hash).first()
    if not worker:
        state = location.split(",")[-1].strip() if "," in location else location
        worker = Worker(
            id=phone_hash,
            phone_hash=phone_hash,
            state=state,
            occupation=occupation,
            is_verified=True,
        )
        db.add(worker)
        db.commit()

    # Save the report
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

    # Check if we need to fire an NGO alert
    if contractor_id and risk_service.should_trigger_ngo_alert(db, contractor_id):
        from backend.models.models import ContractorRisk
        contractor = db.get(ContractorRisk, contractor_id)
        if contractor:
            background_tasks.add_task(
                alert_service.send_wage_theft_alert,
                db, contractor, contractor.verified_bad_reports, location, state
            )

    wage_gap = fair_wage - reported_wage
    gap_percent = (wage_gap / fair_wage * 100) if fair_wage > 0 else 0

    # Clear session context for next interaction
    session["fair_wage"] = None
    session["pending_occupation"] = None
    session["pending_contractor_id"] = None
    session["last_intent"] = "report_wage"
    
    base_reply = responder.generate_report_confirmation(
        reported_wage=reported_wage,
        fair_wage=fair_wage,
        wage_gap=wage_gap,
        gap_percent=gap_percent,
        language=intent_result.language,
    )
    
    is_wage_theft = (reported_wage < fair_wage) and (gap_percent > 10)
    
    if is_wage_theft:
        if contractor_id:
            # Store report ID to generate legal notice
            session["last_report_id"] = report.id
            return base_reply
        else:
            # Ask for contractor name if not provided
            return f"{base_reply}\n\nContractor ka naam pata hai? Batayein toh legal notice generate kar sakte hain."
    else:
        # Paid fairly, no legal notice needed
        return base_reply


# ── Main chat endpoint ────────────────────────────────────────────────


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    wage_engine: WageEngine = Depends(get_wage_engine),
):
    """
    Main chat endpoint for the web frontend.
    Accepts text or base64-encoded audio, returns a natural response.
    """
    logger.info(f'Audio received: {bool(request.audio_base64)}, length: {len(request.audio_base64) if request.audio_base64 else 0}')

    session = _get_or_create_session(request.session_id)

    # Step 1: Get text (transcribe audio if present)
    text = request.message.strip()

    if request.audio_base64 and not text:
        try:
            audio_bytes = base64.b64decode(request.audio_base64)
            text = await transcribe_audio(audio_bytes)
            logger.info(f"Transcribed audio: {text[:80]}...")
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return await _create_response(
                reply="Voice message process nahi ho saka. Please text mein likhen. 🙏",
                session_id=request.session_id,
                quick_replies=QUICK_REPLIES["welcome"],
            )

    if not text:
        return await _create_response(
            reply=responder.generate_welcome_response(),
            session_id=request.session_id,
            quick_replies=QUICK_REPLIES["welcome"],
        )

    logger.info(f"Chat [{request.session_id}]: {text[:100]}")

    # Step 2: Extract intent with conversation context
    intent_result = extract_intent(
        text,
        last_intent=session.get("last_intent"),
        pending_occupation=session.get("pending_occupation"),
        pending_location=session.get("pending_location"),
    )
    logger.info(f"Intent: {intent_result.intent}, occ={intent_result.occupation}")

    # Build the extraction dict for the frontend
    extracted = {
        "intent": intent_result.intent.value,
        "occupation": intent_result.occupation,
        "district": intent_result.location_district,
        "state": intent_result.location_state,
        "contractor": intent_result.contractor_name,
        "wage": intent_result.reported_wage,
        "language": intent_result.language,
    }

    # Step 3: Route by intent and generate response

    # Handle contractor attachment to previous wage report
    if session.get('last_intent') == 'report_wage' and intent_result.contractor_name is not None and intent_result.intent != WorkerIntent.WAGE_QUERY:
        phone_hash = _hash_phone(request.session_id)
        from backend.models.models import WageReport, ContractorRisk
        last_report = db.query(WageReport).filter(WageReport.worker_id == phone_hash).order_by(WageReport.reported_at.desc()).first()
        
        if last_report:
            district = last_report.district or ""
            state = last_report.state or ""
            contractor = risk_service.find_or_create_contractor(db, intent_result.contractor_name, district, state)
            last_report.contractor_id = contractor.id
            db.commit()
            
            # Check NGO alert
            if risk_service.should_trigger_ngo_alert(db, contractor.id):
                contractor_db = db.get(ContractorRisk, contractor.id)
                background_tasks.add_task(
                    alert_service.send_wage_theft_alert,
                    db, contractor_db, contractor_db.verified_bad_reports, district, state
                )
            
            extracted["report_id"] = last_report.id
            reply = f"✅ Contractor {intent_result.contractor_name} ka naam record ho gaya hai. Aap apna legal notice neeche download kar sakte hain."
            
            session["last_intent"] = "contractor_check"
            
            return await _create_response(
                reply=reply,
                session_id=request.session_id,
                extracted=extracted,
                quick_replies=QUICK_REPLIES["after_report"],
            )

    # Handle wage reporting (multi-turn: could be just a number after wage query)
    if intent_result.intent == WorkerIntent.REPORT_WAGE or (
        session.get("fair_wage") and intent_result.reported_wage
    ):
        reply = _handle_report_wage(
            session, intent_result, request.session_id, db, background_tasks
        )
        if "last_report_id" in session:
            extracted["report_id"] = session.pop("last_report_id")
            
        return await _create_response(
            reply=reply,
            session_id=request.session_id,
            extracted=extracted,
            quick_replies=_pick_quick_replies(WorkerIntent.REPORT_WAGE),
        )

    if intent_result.intent == WorkerIntent.WAGE_QUERY:
        reply = _handle_wage_query(session, intent_result, wage_engine)
        return await _create_response(
            reply=reply,
            session_id=request.session_id,
            extracted=extracted,
            quick_replies=_pick_quick_replies(WorkerIntent.WAGE_QUERY),
        )

    if intent_result.intent == WorkerIntent.CONTRACTOR_CHECK:
        reply = _handle_contractor_check(session, intent_result, db)
        return await _create_response(
            reply=reply,
            session_id=request.session_id,
            extracted=extracted,
            quick_replies=_pick_quick_replies(WorkerIntent.CONTRACTOR_CHECK),
        )

    # Fallback: help / unknown
    return await _create_response(
        reply=responder.generate_welcome_response(intent_result.language),
        session_id=request.session_id,
        extracted=extracted,
        quick_replies=QUICK_REPLIES["welcome"],
    )
