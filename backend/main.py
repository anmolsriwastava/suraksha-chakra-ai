"""
Suraksha Chakra — FastAPI Application

Startup order:
1. Load env config
2. Init DB (create tables if needed)
3. Load wage engine (FAISS index)
4. Mount routers
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.db.database import engine, Base
from backend.services.wage_engine import get_wage_engine
from backend.api import whatsapp, wages, reports, dashboard, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


from sqlalchemy.orm import Session
from backend.services.vulnerability_scorer import run_full_vulnerability_update

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("Starting Suraksha Chakra...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
    get_wage_engine()  # pre-loads FAISS index so first request isn't slow
    logger.info("Wage engine loaded. Ready.")
    
    with Session(engine) as db:
        try:
            run_full_vulnerability_update(db)
            logger.info("Predictive layer active. Vulnerability scores populated.")
        except Exception as e:
            logger.error(f"Failed to populate predictive layer: {e}")
            
    yield
    # shutdown (nothing to clean up for now)
    logger.info("Suraksha Chakra shutting down.")


app = FastAPI(
    title="Suraksha Chakra API",
    description="Labour rights intelligence for India's migrant workers",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(whatsapp.router, prefix="/webhook", tags=["WhatsApp"])
app.include_router(wages.router, prefix="/api/wages", tags=["Wages"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "suraksha-chakra"}
