"""
backend/main.py
FastAPI application entry point for ANSH AI JOBHUNTER.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.applications import router as applications_router
from backend.api.candidates import router as candidates_router
from backend.api.companies import router as companies_router
from backend.api.discovery import router as discovery_router
from backend.api.jobs import router as jobs_router
from backend.api.resumes import router as resumes_router
from backend.api.settings import router as settings_router
from database import Base, SessionLocal, engine
from database.init_db import create_data_directory, seed_default_settings
from discovery.discovery_engine import DiscoveryEngine
from discovery.scheduler import JobScheduler
from integrations.company_registry import seed_companies_to_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("anshai")

scheduler = JobScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown management."""
    logger.info("Initializing Ansh AI JobHunter backend services...")

    # 1. Initialize DB & tables
    create_data_directory()
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        seed_default_settings(db)
        seeded_count = seed_companies_to_db(db)
        if seeded_count:
            logger.info("Seeded %d companies into registry.", seeded_count)

    # 2. Start scheduler
    def _engine_factory():
        return DiscoveryEngine(SessionLocal())

    scheduler.start(_engine_factory)

    yield

    logger.info("Shutting down Ansh AI JobHunter services...")
    scheduler.stop()


app = FastAPI(
    title="Ansh AI JobHunter API",
    version="1.0.0",
    description="Personal AI-driven Job Discovery, Matching, and Application Platform for Ansh Pathak.",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(candidates_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(companies_router)
app.include_router(resumes_router)
app.include_router(settings_router)
app.include_router(discovery_router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Ansh AI JobHunter Backend"}


@app.get("/")
def root():
    """Welcome root endpoint."""
    return {
        "status": "running",
        "app": "Ansh AI JobHunter",
        "developer": "Ansh Pathak",
        "docs_url": "/docs",
    }
