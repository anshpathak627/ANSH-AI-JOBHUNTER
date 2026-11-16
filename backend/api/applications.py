"""
backend/api/applications.py
Application tracking and workflow transition endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from database.models import Application, ApplicationStatus, Company, JobListing, UserSetting

router = APIRouter(prefix="/api/applications", tags=["Applications"])


class StatusUpdateSchema(BaseModel):
    status: str
    notes: Optional[str] = None


@router.get("/")
def list_applications(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all tracked job applications."""
    stmt = (
        select(Application, JobListing, Company.name.label("company_name"))
        .join(JobListing, Application.job_id == JobListing.id)
        .join(Company, JobListing.company_id == Company.id)
    )
    if status:
        stmt = stmt.where(Application.status == status)

    stmt = stmt.order_by(Application.created_at.desc())

    results = []
    for app, job, comp_name in db.execute(stmt).all():
        results.append({
            "id": app.id,
            "job_id": job.id,
            "job_title": job.title,
            "company_name": comp_name,
            "location": job.location,
            "status": app.status,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "submission_url": app.submission_url,
            "notes": app.notes,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        })
    return results


@router.post("/create-for-job/{job_id}")
def create_application_for_job(job_id: int, db: Session = Depends(get_db)):
    """Initialize an application record for a discovered job."""
    job = db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.scalars(select(Application).where(Application.job_id == job_id)).first()
    if existing:
        return {"id": existing.id, "status": existing.status, "message": "Application already tracked"}

    app = Application(
        job_id=job_id,
        status="DISCOVERED",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return {"id": app.id, "status": app.status, "message": "Application tracked"}


@router.put("/{app_id}/status")
def update_application_status(app_id: int, data: StatusUpdateSchema, db: Session = Depends(get_db)):
    """Update status (e.g. MATCHED, PREPARED, SUBMITTED, REJECTED)."""
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = data.status.upper()
    if data.notes:
        app.notes = data.notes
    if data.status.upper() == "SUBMITTED" and not app.applied_at:
        app.applied_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(app)
    return {"id": app.id, "status": app.status}


@router.post("/{app_id}/approve")
def approve_application(app_id: int, db: Session = Depends(get_db)):
    """Approve application for submission."""
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "PENDING_APPROVAL"
    db.commit()
    return {"id": app.id, "status": app.status, "message": "Approved for submission"}


@router.delete("/{app_id}")
def withdraw_application(app_id: int, db: Session = Depends(get_db)):
    """Mark application as WITHDRAWN."""
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "WITHDRAWN"
    db.commit()
    return {"id": app.id, "status": app.status, "message": "Application withdrawn"}
