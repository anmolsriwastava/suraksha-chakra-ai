"""
Response Generator

Uses Groq to convert structured data into natural Hindi/Hinglish responses.

Key principle: Groq NEVER invents data. It only formats the structured
data we feed it into natural language. All numbers, wages, scores come
from the RAG pipeline or database — Groq just makes them sound human.

Falls back to simple template strings if Groq is unavailable.
"""

import logging
from typing import Optional

from groq import Groq

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = Groq(api_key=settings.groq_api_key)

# ── Common generation helper ────────────────────────────────────────────


def _generate(system_prompt: str, user_prompt: str) -> str:
    """
    Call Groq with a system + user prompt.
    Returns the generated text or raises on failure.
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.4,  # slight creativity for natural phrasing
        max_tokens=300,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


SYSTEM_PROMPT = (
    "You are Suraksha Chakra, a helpful assistant for Indian migrant construction workers. "
    "Respond in simple Hindi or Hinglish (mix of Hindi + English) that a worker with "
    "basic education can understand. Keep responses SHORT (2-4 sentences max). "
    "Use ₹ symbol for currency. Use emojis sparingly (1-2 max). "
    "You MUST use ONLY the data provided. Do NOT make up numbers, wages, or facts. "
    "Do NOT add disclaimers or extra information not in the data."
)


# ── Wage query response ────────────────────────────────────────────────


def generate_wage_response(
    occupation: str,
    location: str,
    fair_wage_min: float,
    fair_wage_max: float,
    source: str = "BOCW schedule",
    confidence: str = "high",
    language: str = "hi",
) -> str:
    """Generate a natural response for a wage query."""
    try:
        user_prompt = (
            f"A worker asked about fair wages. Here is the data:\n"
            f"- Occupation: {occupation}\n"
            f"- Location: {location}\n"
            f"- Fair wage range: ₹{fair_wage_min:.0f} to ₹{fair_wage_max:.0f} per day\n"
            f"- Source: {source}\n"
            f"- Confidence: {confidence}\n\n"
            f"Tell the worker their fair wage and ask how much they are actually getting paid. "
            f"If confidence is 'low', mention the data may not be exact for their specific area."
        )
        return _generate(SYSTEM_PROMPT, user_prompt)

    except Exception as e:
        logger.warning(f"Response generation failed, using template: {e}")
        return _template_wage_response(
            occupation, location, fair_wage_min, fair_wage_max, confidence
        )


def _template_wage_response(
    occupation: str,
    location: str,
    fair_wage_min: float,
    fair_wage_max: float,
    confidence: str,
) -> str:
    """Fallback template if Groq is unavailable."""
    if confidence == "low" or fair_wage_min == 0:
        return (
            f"Sorry, {occupation} ka {location} mein exact wage nahi mila. "
            f"Approximately ₹450-700/day ho sakta hai. "
            f"Aapko kitna mil raha hai? Sirf number bhejein."
        )
    return (
        f"✅ {location} mein {occupation} ka fair wage: "
        f"₹{fair_wage_min:.0f} – ₹{fair_wage_max:.0f} per day\n\n"
        f"Aapko kitna mil raha hai? (sirf number bhejein, jaise: 400)"
    )


# ── Contractor risk response ───────────────────────────────────────────


def generate_contractor_risk_response(
    contractor_name: str,
    risk_score: float,
    risk_level: str,
    risk_label: str,
    total_reports: int,
    advice: str,
    language: str = "hi",
) -> str:
    """Generate a natural response for a contractor risk check."""
    try:
        user_prompt = (
            f"A worker asked about a contractor. Here is the data:\n"
            f"- Contractor name: {contractor_name}\n"
            f"- Risk score: {risk_score}/100 (lower = more dangerous)\n"
            f"- Risk level: {risk_level} ({risk_label})\n"
            f"- Total worker reports: {total_reports}\n"
            f"- Advice: {advice}\n\n"
            f"Tell the worker about this contractor's reputation based ONLY on this data. "
            f"If risk is high, warn them clearly. If risk is low or unknown, tell them "
            f"it looks okay but encourage them to report their wage after working."
        )
        return _generate(SYSTEM_PROMPT, user_prompt)

    except Exception as e:
        logger.warning(f"Response generation failed, using template: {e}")
        return _template_risk_response(
            contractor_name, risk_score, risk_level, risk_label,
            total_reports, advice
        )


def _template_risk_response(
    contractor_name: str,
    risk_score: float,
    risk_level: str,
    risk_label: str,
    total_reports: int,
    advice: str,
) -> str:
    """Fallback template for contractor risk."""
    emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}.get(risk_level, "ℹ️")
    return (
        f"{emoji} *{contractor_name}*\n"
        f"Risk score: {risk_score}/100 ({risk_label})\n"
        f"Reports: {total_reports}\n\n"
        f"{advice}"
    )


def generate_contractor_not_found_response(
    contractor_name: str, language: str = "hi"
) -> str:
    """Response when a contractor has no reports yet."""
    try:
        user_prompt = (
            f"A worker asked about contractor '{contractor_name}' but there are no "
            f"reports about them yet. Tell the worker this contractor is unknown to us, "
            f"and encourage them to be the first to report their wage after working."
        )
        return _generate(SYSTEM_PROMPT, user_prompt)
    except Exception:
        return (
            f"'{contractor_name}' ke baare mein abhi koi report nahi hai. "
            f"Aap pehle reporter ban sakte hain! Kaam karne ke baad apna wage zaroor batayein."
        )


# ── Wage report confirmation ───────────────────────────────────────────


def generate_report_confirmation(
    reported_wage: float,
    fair_wage: float,
    wage_gap: float,
    gap_percent: float,
    language: str = "hi",
) -> str:
    """Generate confirmation after a worker submits a wage report."""
    underpaid = wage_gap > 0 and gap_percent > 10

    try:
        status = "significantly underpaid" if underpaid else "fairly paid"
        user_prompt = (
            f"A worker just submitted their wage report. Here is the data:\n"
            f"- Fair wage: ₹{fair_wage:.0f}/day\n"
            f"- Reported wage (what they actually got): ₹{reported_wage:.0f}/day\n"
            f"- Wage gap: ₹{wage_gap:.0f} ({gap_percent:.0f}% less)\n"
            f"- Status: {status}\n\n"
            f"Confirm their report was saved anonymously. "
            f"{'Tell them the information has been shared with relevant NGOs and labour officers. ' if underpaid else ''}"
            f"{'Reassure them their identity is protected. ' if underpaid else ''}"
            f"{'Thank them for reporting — their data helps other workers.' if not underpaid else ''}"
        )
        return _generate(SYSTEM_PROMPT, user_prompt)

    except Exception as e:
        logger.warning(f"Response generation failed, using template: {e}")
        return _template_report_confirmation(
            reported_wage, fair_wage, wage_gap, gap_percent, underpaid
        )


def _template_report_confirmation(
    reported_wage: float,
    fair_wage: float,
    wage_gap: float,
    gap_percent: float,
    underpaid: bool,
) -> str:
    """Fallback template for report confirmation."""
    if underpaid:
        return (
            f"🚨 *Aapka report save ho gaya (anonymously).*\n\n"
            f"Fair wage: ₹{fair_wage:.0f}/day\n"
            f"Aapko mila: ₹{reported_wage:.0f}/day\n"
            f"Farq: ₹{wage_gap:.0f} ({gap_percent:.0f}% kam)\n\n"
            f"Yeh information related NGO aur labour officer ko bhej di gayi hai. "
            f"Aapki identity poori tarah safe hai."
        )
    return (
        f"✅ *Report save ho gayi.*\n"
        f"Aapka wage fair lag raha hai (₹{reported_wage:.0f} vs fair ₹{fair_wage:.0f}). "
        f"Dhanyavad report karne ke liye!"
    )


# ── Welcome message ────────────────────────────────────────────────────


def generate_welcome_response(language: str = "hi") -> str:
    """Generate the initial greeting. Uses a template — no need for LLM here."""
    return (
        "Namaste! 🙏 Main *Suraksha Chakra* hoon.\n\n"
        "Main aapki in chezon mein madad kar sakta hoon:\n\n"
        "1️⃣  Fair wage jaanne ke liye — apna kaam aur shehar batayein\n"
        "2️⃣  Contractor check karne ke liye — unka naam batayein\n"
        "3️⃣  Wage report karne ke liye — aapko kitna mila, batayein\n\n"
        "Aap *Hindi ya Hinglish* mein likh sakte hain.\n"
        "Voice message bhi bhej sakte hain! 🎤"
    )


# ── Ask for missing info ───────────────────────────────────────────────


def generate_ask_missing_info(
    missing_field: str, language: str = "hi"
) -> str:
    """
    When extraction is incomplete, ask the worker for the missing piece.
    Uses templates — fast and reliable.
    """
    prompts = {
        "occupation": "Aap kya kaam karte hain? Jaise: mason, electrician, plumber, helper",
        "location": "Aap kahan kaam kar rahe hain? Shehar ya district ka naam batayein.",
        "contractor_name": "Contractor ka naam batayein jiske baare mein jaanna hai.",
        "reported_wage": "Aapko kitna mil raha hai? Sirf number bhejein (jaise: 400)",
    }
    return prompts.get(
        missing_field,
        "Kripya thoda aur detail mein batayein."
    )
