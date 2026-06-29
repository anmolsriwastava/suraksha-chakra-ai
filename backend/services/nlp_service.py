
"""
NLP Intent Extractor

Takes raw Hindi/English text from a worker and extracts:
- Intent (wage_query | report_wage | contractor_check | help)
- Occupation
- Location (district + state)
- Contractor name (if mentioned)
- Reported wage (if reporting)
- Language detected

Uses Groq Llama 3.1 with a tight JSON prompt.
Keyword fallback is truly last-resort (API unavailable only).
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from groq import Groq

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = Groq(api_key=settings.groq_api_key)


class WorkerIntent(str, Enum):
    WAGE_QUERY = "wage_query"           # "Delhi mein mason ka kitna milta hai?"
    REPORT_WAGE = "report_wage"         # "Mujhe 400 mila"
    CONTRACTOR_CHECK = "contractor_check"  # "Ramesh Constructions ke baare mein batao"
    HELP = "help"                       # anything else
    UNKNOWN = "unknown"


@dataclass
class ExtractedIntent:
    intent: WorkerIntent
    occupation: Optional[str] = None
    location_district: Optional[str] = None
    location_state: Optional[str] = None
    contractor_name: Optional[str] = None
    reported_wage: Optional[float] = None
    language: str = "hi"  # "hi" for Hindi/Hinglish, "en" for English
    raw_text: str = ""


# ── Extraction prompt ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a structured data extractor for an Indian labour rights platform.
Your job is to extract intent and entities from messages sent by migrant construction workers.
Workers write in Hindi, Hinglish (Hindi + English), or English.

You MUST respond with valid JSON only. No markdown fences. No explanation. No extra text.
Just the raw JSON object."""


def _build_extraction_prompt(
    message: str,
    last_intent: Optional[str] = None,
    pending_occupation: Optional[str] = None,
    pending_location: Optional[str] = None,
) -> str:
    """Build the user prompt with conversation context and examples."""

    context_section = ""
    if last_intent or pending_occupation or pending_location:
        context_section = (
            f"\nConversation context (previous state):\n"
            f"- Last intent: {last_intent or 'none'}\n"
            f"- Pending occupation: {pending_occupation or 'none'}\n"
            f"- Pending location: {pending_location or 'none'}\n"
            f"\nUse this context to understand follow-up messages. "
            f"For example, if last intent was 'wage_query' and the worker sends a number, "
            f"that means they are reporting their wage (intent = 'report_wage').\n"
        )

    return f"""Extract structured data from this worker message.
{context_section}
Worker message: "{message}"

CRITICAL RULES for contractor_name:
1. contractor_name must be a REAL proper noun — a person name or business name like "Ramesh Constructions", "Sharma Builders", "JP Infrastructure". 
2. Generic words like doosra, koi, woh, contractor, thekedaar, naam, batana, check, haan are NEVER contractor names → set contractor_name to null.
3. If the user says they WANT to check a contractor but has NOT given the name yet, set contractor_name to null. Example: "Contractor ka naam batana hai" → contractor_name is null.
4. "raaj mistri" or "rajmistri" is an OCCUPATION (mason). It is NEVER a contractor_name.
5. When the user IS responding with a real name (e.g. answering the question "Contractor ka naam batayein"), take the full input as the contractor_name. Example: "Deen Dayal, Obra" → contractor_name is "Deen Dayal, Obra".

Respond with this exact JSON structure:
{{
  "intent": "wage_query" | "report_wage" | "contractor_check" | "help" | "unknown",
  "occupation": "<job type in English: mason, electrician, plumber, helper, carpenter, painter, welder, driver, or null>",
  "location_district": "<district/city name in English, e.g. Delhi, Mumbai, Patna, or null>",
  "location_state": "<state name in English, e.g. Delhi, Maharashtra, UP, Bihar, or null>",
  "contractor_name": "<contractor or company PROPER NAME as mentioned, or null>",
  "reported_wage": <number (daily wage in INR) or null>,
  "language": "hi" | "en"
}}

Examples:
- "Delhi mein raaj mistri ka kaam mila hai" → {{"intent":"wage_query","occupation":"mason","location_district":"Delhi","location_state":"Delhi","contractor_name":null,"reported_wage":null,"language":"hi"}}
- "Mumbai mein electrician hoon" → {{"intent":"wage_query","occupation":"electrician","location_district":"Mumbai","location_state":"Maharashtra","contractor_name":null,"reported_wage":null,"language":"hi"}}
- "Mujhe 400 rupaye mil rahe hain" → {{"intent":"report_wage","occupation":null,"location_district":null,"location_state":null,"contractor_name":null,"reported_wage":400,"language":"hi"}}
- "500" → {{"intent":"report_wage","occupation":null,"location_district":null,"location_state":null,"contractor_name":null,"reported_wage":500,"language":"hi"}}
- "Ramesh Constructions ke baare mein batao" → {{"intent":"contractor_check","occupation":null,"location_district":null,"location_state":null,"contractor_name":"Ramesh Constructions","reported_wage":null,"language":"hi"}}
- "JP Infrastructure ka kya scene hai?" → {{"intent":"contractor_check","occupation":null,"location_district":null,"location_state":null,"contractor_name":"JP Infrastructure","reported_wage":null,"language":"hi"}}
- "Contractor ka naam batana hai" → {{"intent":"contractor_check","occupation":null,"location_district":null,"location_state":null,"contractor_name":null,"reported_wage":null,"language":"hi"}}
- "Contractor check karna hai" → {{"intent":"contractor_check","occupation":null,"location_district":null,"location_state":null,"contractor_name":null,"reported_wage":null,"language":"hi"}}
- "Kya karna chahiye?" → {{"intent":"help","occupation":null,"location_district":null,"location_state":null,"contractor_name":null,"reported_wage":null,"language":"hi"}}
- "What is the wage for a plumber in Patna?" → {{"intent":"wage_query","occupation":"plumber","location_district":"Patna","location_state":"Bihar","contractor_name":null,"reported_wage":null,"language":"en"}}
- "Gorakhpur mein helper ka kitna milta hai" → {{"intent":"wage_query","occupation":"helper","location_district":"Gorakhpur","location_state":"UP","contractor_name":null,"reported_wage":null,"language":"hi"}}
- "Mazdoori 350 mili sirf" → {{"intent":"report_wage","occupation":"helper","location_district":null,"location_state":null,"contractor_name":null,"reported_wage":350,"language":"hi"}}

Respond with ONLY the JSON. No other text."""


# ── Safe JSON parsing ──────────────────────────────────────────────────


def _safe_parse_json(raw: str) -> dict:
    """
    Parse JSON from LLM output, handling common issues:
    - Markdown code fences (```json ... ```)
    - Leading/trailing whitespace
    - Multiple JSON objects (take first)
    """
    cleaned = raw.strip()

    # Strip markdown code fences
    if cleaned.startswith("```"):
        # find content between ``` markers
        lines = cleaned.split("\n")
        # drop first line (```json) and last line (```)
        inner_lines = []
        in_fence = False
        for line in lines:
            if line.strip().startswith("```") and not in_fence:
                in_fence = True
                continue
            elif line.strip() == "```" and in_fence:
                break
            elif in_fence:
                inner_lines.append(line)
        cleaned = "\n".join(inner_lines).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try to find JSON with nested braces
    brace_start = cleaned.find('{')
    if brace_start >= 0:
        depth = 0
        for i in range(brace_start, len(cleaned)):
            if cleaned[i] == '{':
                depth += 1
            elif cleaned[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(cleaned[brace_start:i + 1])
                    except json.JSONDecodeError:
                        break

    raise json.JSONDecodeError("Could not find valid JSON", cleaned, 0)


# ── Main extraction ───────────────────────────────────────────────────


def extract_intent(
    text: str,
    last_intent: Optional[str] = None,
    pending_occupation: Optional[str] = None,
    pending_location: Optional[str] = None,
) -> ExtractedIntent:
    """
    Main entry point. Takes raw text + optional conversation context,
    returns structured ExtractedIntent.

    Uses Groq for extraction. Falls back to keyword matching ONLY if
    the Groq API itself is unreachable (network error, rate limit).
    """
    if not text or not text.strip():
        return ExtractedIntent(intent=WorkerIntent.UNKNOWN, raw_text=text)

    try:
        user_prompt = _build_extraction_prompt(
            text, last_intent, pending_occupation, pending_location
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw_json = response.choices[0].message.content.strip()
        parsed = _safe_parse_json(raw_json)

        return _build_extracted_intent(parsed, text)

    except json.JSONDecodeError:
        # LLM returned something unparseable — still try keyword fallback
        logger.warning(f"Intent extraction returned non-JSON for: {text[:80]}")
        return _fallback_keyword_extraction(text)

    except Exception as e:
        # API error (network, rate limit, etc.) — use keyword fallback
        logger.error(f"Intent extraction API failed: {e}")
        return _fallback_keyword_extraction(text)


def _build_extracted_intent(parsed: dict, raw_text: str) -> ExtractedIntent:
    """Map the parsed dict to an ExtractedIntent dataclass."""
    intent_str = parsed.get("intent", "unknown")

    try:
        intent = WorkerIntent(intent_str)
    except ValueError:
        intent = WorkerIntent.UNKNOWN

    return ExtractedIntent(
        intent=intent,
        occupation=parsed.get("occupation"),
        location_district=parsed.get("location_district"),
        location_state=parsed.get("location_state"),
        contractor_name=parsed.get("contractor_name"),
        reported_wage=parsed.get("reported_wage"),
        language=parsed.get("language", "hi"),
        raw_text=raw_text,
    )


def _fallback_keyword_extraction(text: str) -> ExtractedIntent:
    """
    Dumb keyword matching when the Groq API is completely unavailable.
    This is truly last-resort — should rarely be hit in practice.
    """
    text_lower = text.lower()

    occupation_map = {
        "mason": ["mason", "rajmistri", "raaj mistri", "राजमिस्त्री"],
        "electrician": ["electrician", "bijli", "बिजली"],
        "plumber": ["plumber", "plumber"],
        "helper": ["helper", "mazdoor", "मजदूर", "unskilled"],
        "carpenter": ["carpenter", "badhai", "बढ़ई"],
    }

    detected_occupation = None
    for occ, keywords in occupation_map.items():
        if any(kw in text_lower for kw in keywords):
            detected_occupation = occ
            break

    wage_match = re.search(r"\b(\d{3,4})\b", text)
    reported_wage = float(wage_match.group(1)) if wage_match else None

    intent = WorkerIntent.UNKNOWN

    if reported_wage and any(
        w in text_lower for w in ["mila", "mile", "de raha", "milta", "mil raha"]
    ):
        intent = WorkerIntent.REPORT_WAGE

    elif any(
        w in text_lower
        for w in ["contractor", "thekedar", "ठेकेदार", "company", "builder"]
    ):
        intent = WorkerIntent.CONTRACTOR_CHECK

    elif detected_occupation:
        intent = WorkerIntent.WAGE_QUERY

    # If it's just a bare number and we have context, treat as wage report
    elif reported_wage and not detected_occupation:
        intent = WorkerIntent.REPORT_WAGE

    logger.info(
        f"Fallback extraction: intent={intent}, occ={detected_occupation}"
    )

    return ExtractedIntent(
        intent=intent,
        occupation=detected_occupation,
        reported_wage=reported_wage,
        raw_text=text,
    )
