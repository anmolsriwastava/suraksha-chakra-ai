"""
Suraksha Chakra — FastAPI Application

Startup order:
1. Load env config
2. Init DB (create tables if needed)
3. Load wage engine (FAISS index) — in background
4. Mount routers
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.db.database import engine, Base
from backend.api import whatsapp, wages, reports, dashboard, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


def _heavy_init():
    """Run heavy initialization in a background thread so the port opens fast."""
    try:
        from backend.services.wage_engine import get_wage_engine
        get_wage_engine()
        logger.info("Wage engine loaded.")
    except Exception as e:
        logger.error(f"Wage engine init failed: {e}")

    try:
        from sqlalchemy.orm import Session
        from backend.services.vulnerability_scorer import run_full_vulnerability_update
        with Session(engine) as db:
            run_full_vulnerability_update(db)
            logger.info("Vulnerability scores populated.")
    except Exception as e:
        logger.error(f"Vulnerability scorer failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup — keep it fast so Render detects the port
    logger.info("Starting Suraksha Chakra...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # Heavy ML loading in background thread
    init_thread = threading.Thread(target=_heavy_init, daemon=True)
    init_thread.start()
    logger.info("Background initialization started. Server is ready.")
    
    yield
    logger.info("Suraksha Chakra shutting down.")


app = FastAPI(
    title="Suraksha Chakra API",
    description="Labour rights intelligence for India's migrant workers",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# ── Serve React frontend build (for production / Render deploy) ──────
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_frontend_build = Path(__file__).resolve().parent.parent / "frontend" / "build"

if _frontend_build.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/static", StaticFiles(directory=str(_frontend_build / "static")), name="static")
    
    # Catch-all: serve index.html for any non-API route (React Router support)
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        # If a real file exists in build dir, serve it (favicon, manifest, etc.)
        file_path = _frontend_build / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html and let React Router handle it
        return FileResponse(str(_frontend_build / "index.html"))

