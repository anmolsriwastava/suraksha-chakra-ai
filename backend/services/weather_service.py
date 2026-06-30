"""
Weather Service using OpenWeatherMap

Fetches live weather data for tracked districts to compute a Flood Severity Index.
"""

import time
import logging
import requests
from typing import Dict, Tuple

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Cache to avoid hitting API limits during demo. Map: district_name -> (timestamp, flood_severity_index)
_cache: Dict[str, Tuple[float, float]] = {}
CACHE_TTL = 30 * 60  # 30 minutes in seconds

# District coordinates mapping
DISTRICT_COORDS = {
    "darbhanga": {"lat": 26.1522, "lon": 85.8971},
    "muzaffarpur": {"lat": 26.1209, "lon": 85.3647},
    "sitamarhi": {"lat": 26.5975, "lon": 85.4900},
    "varanasi": {"lat": 25.3176, "lon": 82.9739},
    "azamgarh": {"lat": 26.0715, "lon": 83.1859},
    "gorakhpur": {"lat": 26.7606, "lon": 83.3732},
    "purnia": {"lat": 25.7771, "lon": 87.4753},
    "samastipur": {"lat": 25.8622, "lon": 85.7801},
}

def get_district_flood_severity(district: str, state: str) -> float:
    """
    Returns a normalized Flood Severity Index (0-100) based on live weather.
    Falls back to cached value, or 40.0 historical average if API fails.
    """
    district_lower = district.lower()
    now = time.time()
    
    # 1. Check Cache
    if district_lower in _cache:
        cached_time, cached_score = _cache[district_lower]
        if (now - cached_time) < CACHE_TTL:
            logger.info(f"[CACHE HIT] Weather for {district}: {cached_score:.1f}")
            return cached_score

    # 2. Check API Key
    api_key = settings.openweather_api_key
    if not api_key:
        logger.warning(f"OpenWeather API Key missing. Using fallback for {district}")
        return _get_fallback(district_lower)

    # 3. Check Coordinates / Setup Params
    coords = DISTRICT_COORDS.get(district_lower)
    params = {
        "appid": api_key,
        "units": "metric"
    }
    
    if coords:
        params["lat"] = coords["lat"]
        params["lon"] = coords["lon"]
    else:
        # Fallback to city name search if not in our hardcoded dict
        params["q"] = f"{district},IN"

    # 4. Fetch Live Weather
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        
        logger.info(f"Fetching live weather for {district}...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"OpenWeather API error ({response.status_code}): {response.text}")
            return _get_fallback(district_lower)
            
        data = response.json()
        
        # 5. Extract Metrics
        rainfall = 0.0
        if "rain" in data and "1h" in data["rain"]:
            rainfall = data["rain"]["1h"]
            
        humidity = data.get("main", {}).get("humidity", 50)
        wind_speed = data.get("wind", {}).get("speed", 0.0)
        
        # 6. Check Severe Weather
        is_severe = False
        if "weather" in data and len(data["weather"]) > 0:
            weather_id = data["weather"][0].get("id", 800)
            # Weather IDs < 600 cover thunderstorms and heavy drizzle/rain
            if weather_id < 600:
                is_severe = True
                
        # 7. Compute Flood Severity Index
        # Formula: (Rainfall * 2) + (Humidity * 0.3) + (Wind * 1.5) + (50 if severe else 0)
        raw_score = (rainfall * 2.0) + (humidity * 0.3) + (wind_speed * 1.5) + (50.0 if is_severe else 0.0)
        
        # Clamp to 0-100
        normalized_score = max(0.0, min(100.0, raw_score))
        
        logger.info(f"[LIVE WEATHER] {district}: Rain={rainfall}mm, Humidity={humidity}%, Wind={wind_speed}m/s, Severe={is_severe} -> Index={normalized_score:.1f}")
        
        # 8. Cache & Return
        _cache[district_lower] = (now, normalized_score)
        return normalized_score
        
    except Exception as e:
        logger.error(f"Weather fetch failed for {district}: {e}")
        return _get_fallback(district_lower)

def _get_fallback(district_lower: str) -> float:
    """Returns the last cached value if available, else a historical average."""
    if district_lower in _cache:
        logger.warning(f"Using expired cached weather for {district_lower}.")
        return _cache[district_lower][1]
    
    # Historical dataset average fallback (no hardcoded exact dicts)
    logger.warning(f"Using static historical average for {district_lower}.")
    return 40.0
