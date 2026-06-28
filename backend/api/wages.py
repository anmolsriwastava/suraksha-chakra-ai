"""
Wages API

REST endpoints for the web PWA to query fair wages directly.
Same wage engine as the WhatsApp bot, just JSON instead of text.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services.wage_engine import get_wage_engine, WageEngine

router = APIRouter()


class WageQueryRequest(BaseModel):
    occupation: str
    district: str
    state: str


class WageQueryResponse(BaseModel):
    occupation: str
    location: str
    fair_wage_min: float
    fair_wage_max: float
    fair_wage_display: str  # "₹600 – ₹700/day"
    currency: str
    per: str
    source: str
    confidence: str


@router.post("/query", response_model=WageQueryResponse)
def query_fair_wage(
    request: WageQueryRequest,
    wage_engine: WageEngine = Depends(get_wage_engine),
):
    """
    Given an occupation and location, return the BOCW fair wage range.
    Used by the PWA's wage query screen.
    """
    location = f"{request.district}, {request.state}"

    try:
        result = wage_engine.query_fair_wage(request.occupation, location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wage query failed: {e}")

    if result.fair_wage_min == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No wage data found for {request.occupation} in {location}"
        )

    display = f"₹{result.fair_wage_min:.0f} – ₹{result.fair_wage_max:.0f}/{result.per}"

    return WageQueryResponse(
        occupation=result.occupation,
        location=location,
        fair_wage_min=result.fair_wage_min,
        fair_wage_max=result.fair_wage_max,
        fair_wage_display=display,
        currency=result.currency,
        per=result.per,
        source=result.source,
        confidence=result.confidence,
    )


@router.get("/occupations")
def list_common_occupations():
    """
    Return a list of common construction occupations for the PWA dropdown.
    Prevents typos in wage queries.
    """
    occupations = [
        {"en": "Mason", "hi": "राजमिस्त्री (Rajmistri)"},
        {"en": "Electrician", "hi": "बिजली मिस्त्री (Bijli Mistri)"},
        {"en": "Plumber", "hi": "प्लम्बर (Plumber)"},
        {"en": "Carpenter", "hi": "बढ़ई (Badhai)"},
        {"en": "Painter", "hi": "रंग करने वाला (Painter)"},
        {"en": "Helper / Unskilled Worker", "hi": "मजदूर (Mazdoor)"},
        {"en": "Welder", "hi": "वेल्डर (Welder)"},
        {"en": "Steel Fixer", "hi": "सरिया वाला (Sariya Wala)"},
        {"en": "Driver", "hi": "ड्राइवर (Driver)"},
    ]
    return {"occupations": occupations}
