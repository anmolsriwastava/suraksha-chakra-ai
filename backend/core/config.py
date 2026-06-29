"""
App-wide config loaded from environment variables.
Using pydantic-settings so we get type safety + clear errors
when something is missing.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # External APIs
    groq_api_key: str
    sarvam_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    sendgrid_api_key: Optional[str] = None
    alert_from_email: str = "anmol.isik@gmail.com"

    # Business logic thresholds
    wage_gap_alert_threshold: int = 5
    risk_score_decay_per_report: int = 10

    # App
    app_env: str = "development"
    app_secret_key: str = "change-in-production"

    # Paths (relative to project root)
    embeddings_dir: str = "data/embeddings"
    raw_data_dir: str = "data/raw"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    # cached so we don't read disk on every request
    return Settings()
