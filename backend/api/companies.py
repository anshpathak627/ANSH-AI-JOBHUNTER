"""
backend/api/companies.py
Target company registry and individual company scan endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from database.models import ATSProvider, Company, JobListing
from discovery.discovery_engine import DiscoveryEngine

router = APIRouter(prefix="/api/companies", tags=["Companies"])


class CompanyCreateSchema(BaseModel):
    name: str
    careers_url: Optional[str] = None
    ats_provider: str = "custom"
    board_identifier: Optional[str] = None
    country: Optional[str] = "India"
    industry: Optional[str] = "Technology"


@router.get("/")
def list_companies(
    ats_provider: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all configured target employers."""
    stmt = select(Company)
    if ats_provider:
        stmt = stmt.where(Company.ats_provider == ats_provider)
    if country:
        stmt = stmt.where(Company.country.ilike(f"%{country}%"))
    if industry:
        stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))

    stmt = stmt.order_by(Company.name.asc())
    companies = db.scalars(stmt).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "careers_url": c.careers_url,
            "ats_provider": c.ats_provider.value if hasattr(c.ats_provider, "value") else str(c.ats_provider),
            "board_identifier": c.board_identifier,
            "country": c.country,
            "industry": c.industry,
            "is_active": c.is_active,
            "last_scan_at": c.last_scan_at.isoformat() if c.last_scan_at else None,
            "scan_status": c.scan_status,
        }
        for c in companies
    ]


@router.post("/")
def create_company(data: CompanyCreateSchema, db: Session = Depends(get_db)):
    """Add a new target employer to the registry."""
    existing = db.scalars(select(Company).where(Company.name.ilike(data.name))).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already registered")

    try:
        ats_enum = ATSProvider(data.ats_provider.lower())
    except ValueError:
        ats_enum = ATSProvider.custom

    comp = Company(
        name=data.name,
        careers_url=data.careers_url,
        ats_provider=ats_enum,
        board_identifier=data.board_identifier,
        country=data.country,
        industry=data.industry,
        is_active=True,
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return {"id": comp.id, "name": comp.name, "status": "created"}


@router.post("/{company_id}/scan")
async def trigger_company_scan(company_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger an immediate scan for a specific target employer."""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    async def _scan():
        from database import SessionLocal
        with SessionLocal() as session:
            engine = DiscoveryEngine(session)
            await engine.run_discovery(company_id=company_id)

    background_tasks.add_task(_scan)
    return {"message": f"Scan scheduled for {company.name}"}


@router.get("/{company_id}/jobs")
def get_company_jobs(company_id: int, db: Session = Depends(get_db)):
    """List all open positions discovered for this company."""
    jobs = db.scalars(
        select(JobListing).where(JobListing.company_id == company_id, JobListing.is_active.is_(True))
    ).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "location": j.location,
            "work_mode": j.work_mode.value if hasattr(j.work_mode, "value") else str(j.work_mode),
            "application_url": j.application_url,
            "posted_date": j.posted_date.isoformat() if j.posted_date else None,
        }
        for j in jobs
    ]
