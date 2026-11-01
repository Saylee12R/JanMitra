"""
JanMitra Backend – FastAPI Application Entry Point
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.government.importer import SchemeImporter
from app.routes import (
    users,
    schemes,
    recommendations,
    saved,
    checklist,
    applications,
    compare,
    assistant,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and seed government schemes on startup."""

    logger.info("Starting JanMitra Backend...")

    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

        # Import verified scheme data from data/schemes/
        try:
            inserted, updated, errors = await asyncio.to_thread(
                SchemeImporter().sync_to_database
            )

            logger.info(
                f"Scheme data sync complete: "
                f"{inserted} added, "
                f"{updated} updated, "
                f"{errors} errors"
            )

        except Exception as e:
            logger.error(f"Scheme data import failed: {e}")

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        logger.warning(
            "Starting without database connection – check DATABASE_URL"
        )

    yield

    logger.info("Shutting down JanMitra Backend")


app = FastAPI(
    title="JanMitra API",
    description=(
        "JanMitra – Personal Government Services Assistant. "
        "Helps Indian citizens discover government schemes they may be eligible for. "
        "\n\n**DISCLAIMER**: Eligibility information is indicative only. "
        "Final eligibility must be confirmed with the official scheme authority."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(users.router)
app.include_router(schemes.router)
app.include_router(recommendations.router)
app.include_router(saved.router)
app.include_router(checklist.router)
app.include_router(applications.router)
app.include_router(compare.router)
app.include_router(assistant.router)


# ── Root / Health ─────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def root():
    return {
        "name": "JanMitra API",
        "version": "1.0.0",
        "description": "Personal Government Services Assistant",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "ai_available": settings.ai_available,
        "version": "1.0.0",
    }