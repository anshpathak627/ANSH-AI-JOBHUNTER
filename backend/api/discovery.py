"""
backend/api/discovery.py
Discovery trigger, automation audit logs, and status endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from database.models import AutomationLog, Company
from discovery.discovery_engine import DiscoveryEngine

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])


async def _run_scan_job(company_id: Optional[int] = None):
    with SessionLocal() as db:
        engine = DiscoveryEngine(db)
        await engine.run_discovery(company_id=company_id)


@router.post("/scan")
def trigger_full_scan(background_tasks: BackgroundTasks):
    """Trigger background job discovery across all active target companies."""
    background_tasks.add_task(_run_scan_job)
    return {"status": "scheduled", "message": "Discovery run started in background"}


@router.post("/scan/{company_id}")
def trigger_company_scan(company_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger background scan for a specific employer."""
    comp = db.get(Company, company_id)
    company_name = comp.name if comp else f"ID {company_id}"
    background_tasks.add_task(_run_scan_job, company_id=company_id)
    return {"status": "scheduled", "message": f"Scan scheduled for {company_name}"}


@router.get("/status")
def get_discovery_status(db: Session = Depends(get_db)):
    """Retrieve the latest discovery automation event log."""
    latest_log = db.scalars(
        select(AutomationLog)
        .where(AutomationLog.event_type.in_(["DISCOVERY_START", "DISCOVERY_COMPLETE"]))
        .order_by(AutomationLog.created_at.desc())
    ).first()

    return {
        "last_event": latest_log.event_type if latest_log else "None",
        "message": latest_log.message if latest_log else "No recent scan recorded.",
        "timestamp": latest_log.created_at.isoformat() if latest_log else None,
    }


@router.get("/logs")
def get_recent_logs(limit: int = 100, db: Session = Depends(get_db)):
    """Fetch recent automation audit trails."""
    logs = db.scalars(
        select(AutomationLog).order_by(AutomationLog.created_at.desc()).limit(limit)
    ).all()

    return [
        {
            "id": l.id,
            "event_type": l.event_type,
            "level": l.level.value if hasattr(l.level, "value") else str(l.level),
            "message": l.message,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
