
"""
NLP Intent Extractor

Takes raw Hindi/English text from a worker and extracts:
- Intent (wage_query | report_wage | contractor_check | help)
- Occupation
- Location (district + state)
- Contractor name (if mentioned)
- Reported wage (if reporting)

Uses Groq Llama 3.1 with a tight JSON prompt.
"""

import json
import logging
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
    raw_text: str = ""


EXTRACTION_PROMPT = """
You are a helpful assistant for Indian migrant workers.
Extract structured information from the worker's message.

Worker message: "{message}"

Respond ONLY with valid JSON. No extra text. No markdown.

{{
  "intent": "wage_query" | "report_wage" | "contractor_check" | "help" | "unknown",
  "occupation": "<job type in English, e.g. mason, electrician, plumber, helper>",
  "location_district": "<district name in English or null>",
  "location_state": "<state name in English or null>",
  "contractor_name": "<contractor or company name or null>",
  "reported_wage": <number (daily wage in INR) or null>
}}

Examples:
- "Delhi mein mason ka kaam karna chahta hoon" → wage_query, mason, Delhi
- "Mujhe 400 rupaye mil rahe hain" → report_wage, reported_wage: 400
- "Ramesh Constructions ke baare mein batao" → contractor_check
- "Kya karna chahiye?" → help
"""


def extract_intent(text: str) -> ExtractedIntent:
    """
    Main entry point. Takes raw text, returns structured ExtractedIntent.
    Falls back gracefully if the LLM fails.
    """
    if not text or not text.strip():
        return ExtractedIntent(intent=WorkerIntent.UNKNOWN, raw_text=text)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(message=text)
                }
            ],
        )

        raw_json = response.choices[0].message.content.strip()
        parsed = json.loads(raw_json)

        return _build_extracted_intent(parsed, text)

    except json.JSONDecodeError:
        logger.error(f"Intent extraction returned non-JSON: {text}")
        return _fallback_keyword_extraction(text)

    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
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
        raw_text=raw_text,
    )


def _fallback_keyword_extraction(text: str) -> ExtractedIntent:
    """
    Dumb keyword matching when the LLM fails.
    Better than returning nothing — covers the most common cases.
    """
    text_lower = text.lower()

    occupation_map = {
        "mason": ["mason", "rajmistri", "राजमिस्त्री"],
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

    import re

    wage_match = re.search(r"\b(\d{3,4})\b", text)
    reported_wage = float(wage_match.group(1)) if wage_match else None

    intent = WorkerIntent.UNKNOWN

    if reported_wage and any(
        w in text_lower for w in ["mila", "mile", "de raha", "milta"]
    ):
        intent = WorkerIntent.REPORT_WAGE

    elif detected_occupation:
        intent = WorkerIntent.WAGE_QUERY

    logger.info(
        f"Fallback extraction: intent={intent}, occ={detected_occupation}"
    )

    return ExtractedIntent(
        intent=intent,
        occupation=detected_occupation,
        reported_wage=reported_wage,
        raw_text=text,
    )

