"""
backend/api/jobs.py
Job listing discovery, filtering, and scoring endpoints.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agents.matching_agent import MatchingAgent
from database import get_db
from database.models import CandidateProfile, Company, JobListing, JobMatch

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])
matching_agent = MatchingAgent()


@router.get("/")
def list_jobs(
    title: Optional[str] = None,
    location: Optional[str] = None,
    work_mode: Optional[str] = None,
    min_score: Optional[float] = None,
    salary_min: Optional[float] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List discovered job postings with filtering and match scores."""
    stmt = (
        select(JobListing, JobMatch, Company.name.label("company_name"))
        .join(Company, JobListing.company_id == Company.id)
        .outerjoin(JobMatch, JobListing.id == JobMatch.job_id)
        .where(JobListing.is_active.is_(True))
    )

    if title:
        stmt = stmt.where(JobListing.title.ilike(f"%{title}%"))
    if location:
        stmt = stmt.where(JobListing.location.ilike(f"%{location}%"))
    if work_mode:
        stmt = stmt.where(JobListing.work_mode == work_mode)
    if salary_min:
        stmt = stmt.where(JobListing.salary_max >= salary_min)
    if min_score is not None:
        stmt = stmt.where(JobMatch.match_score >= min_score)

    stmt = stmt.order_by(JobMatch.match_score.desc().nullslast(), JobListing.id.desc())
    stmt = stmt.limit(limit).offset(offset)

    results = []
    for job, match, comp_name in db.execute(stmt).all():
        results.append({
            "id": job.id,
            "company_id": job.company_id,
            "company_name": comp_name,
            "external_job_id": job.external_job_id,
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "city": job.city,
            "country": job.country,
            "work_mode": job.work_mode.value if hasattr(job.work_mode, "value") else str(job.work_mode),
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "salary_disclosed": job.salary_disclosed,
            "application_url": job.application_url,
            "posted_date": job.posted_date.isoformat() if job.posted_date else None,
            "match_score": match.match_score if match else None,
            "disqualified": match.disqualified if match else False,
        })

    return results


@router.get("/stats/summary")
def get_job_stats(db: Session = Depends(get_db)):
    """Aggregate discovery and match statistics."""
    total_jobs = db.scalar(select(func.count(JobListing.id)).where(JobListing.is_active.is_(True))) or 0
    matched_jobs = db.scalar(select(func.count(JobMatch.id)).where(JobMatch.disqualified.is_(False))) or 0
    high_match = db.scalar(select(func.count(JobMatch.id)).where(JobMatch.match_score >= 70.0)) or 0
    above_10lpa = db.scalar(select(func.count(JobListing.id)).where(JobListing.salary_max >= 10.0)) or 0

    return {
        "total_jobs": total_jobs,
        "eligible_jobs": matched_jobs,
        "high_match_jobs": high_match,
        "above_10_lpa_jobs": above_10lpa,
    }


@router.get("/{job_id}")
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    """Get full details of a specific job posting."""
    job = db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    company = db.get(Company, job.company_id)
    match = db.scalars(select(JobMatch).where(JobMatch.job_id == job_id)).first()

    return {
        "id": job.id,
        "company_id": job.company_id,
        "company_name": company.name if company else "Unknown",
        "ats_provider": company.ats_provider.value if company and hasattr(company.ats_provider, "value") else "unknown",
        "external_job_id": job.external_job_id,
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "work_mode": job.work_mode.value if hasattr(job.work_mode, "value") else str(job.work_mode),
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "salary_disclosed": job.salary_disclosed,
        "description": job.description,
        "application_url": job.application_url,
        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
        "match": {
            "match_score": match.match_score,
            "skills_score": match.skills_score,
            "education_score": match.education_score,
            "experience_score": match.experience_score,
            "role_score": match.role_score,
            "location_score": match.location_score,
            "salary_score": match.salary_score,
            "match_reasons": json.loads(match.match_reasons) if match and match.match_reasons else [],
            "disqualified": match.disqualified if match else False,
            "disqualification_reason": match.disqualification_reason if match else None,
        } if match else None,
    }


@router.post("/{job_id}/match")
def score_job(job_id: int, db: Session = Depends(get_db)):
    """Evaluate and store match score for a job posting."""
    job = db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.scalars(select(CandidateProfile)).first()
    candidate_dict = {
        "skills": json.loads(profile.skills_json) if profile and profile.skills_json else [],
        "cgpa": profile.cgpa if profile else 8.4,
        "grad_year": profile.grad_year if profile else 2027,
    }

    job_dict = {
        "title": job.title,
        "description": job.description,
        "location": job.location,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_disclosed": job.salary_disclosed,
        "work_mode": job.work_mode.value if hasattr(job.work_mode, "value") else str(job.work_mode),
    }

    score_data = matching_agent.calculate_match_score(job_dict, candidate_dict)

    match = db.scalars(select(JobMatch).where(JobMatch.job_id == job_id)).first()
    if not match:
        match = JobMatch(job_id=job_id)
        db.add(match)

    match.match_score = score_data["match_score"]
    match.skills_score = score_data["skills_score"]
    match.education_score = score_data["education_score"]
    match.experience_score = score_data["experience_score"]
    match.role_score = score_data["role_score"]
    match.location_score = score_data["location_score"]
    match.salary_score = score_data["salary_score"]
    match.match_reasons = json.dumps(score_data["match_reasons"])
    match.disqualified = score_data["disqualified"]
    match.disqualification_reason = score_data["disqualification_reason"]

    db.commit()
    db.refresh(match)

    return score_data
