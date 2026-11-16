"""
backend/api/candidates.py
Candidate profile management endpoints.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from database.models import CandidateProfile

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

DEFAULT_PROFILE = {
    "name": "Ansh Pathak",
    "email": "pathakansh696@gmail.com",
    "phone": "+91 9999999999",
    "college": "Maharaja Agrasen Institute of Technology (MAIT), GGSIPU",
    "degree": "B.Tech",
    "branch": "Electrical Engineering (VLSI Design & Technology)",
    "cgpa": 8.4,
    "grad_year": 2027,
    "skills": [
        "Java", "Python", "JavaScript", "TypeScript", "SQL", "React",
        "Node.js", "Express", "MySQL", "PostgreSQL", "Excel", "Power BI",
        "Pandas", "NumPy", "REST APIs", "Generative AI", "RAG", "LangChain",
        "Business Analysis", "Data Analytics", "ASP.NET"
    ],
    "linkedin_url": "https://linkedin.com/in/anshpathak",
    "github_url": "https://github.com/anshpathak",
    "portfolio_url": None,
    "summary": (
        "B.Tech Electrical Engineering (VLSI Design & Tech) student with deep practical experience "
        "in Full Stack Web Development (DRDO team lead) and MIS Data Analytics (American Express). "
        "Specializes in Python, SQL, React, Node.js, and GenAI (RAG/LangChain)."
    ),
}


class CandidateUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    cgpa: Optional[float] = None
    grad_year: Optional[int] = None
    skills: Optional[list[str]] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None


@router.get("/")
def get_candidate_profile(db: Session = Depends(get_db)):
    """Fetch candidate profile from DB or return the seeded default."""
    profile = db.scalars(select(CandidateProfile)).first()
    if not profile:
        # Create and return default profile in DB
        profile = CandidateProfile(
            name=DEFAULT_PROFILE["name"],
            email=DEFAULT_PROFILE["email"],
            phone=DEFAULT_PROFILE["phone"],
            college=DEFAULT_PROFILE["college"],
            degree=DEFAULT_PROFILE["degree"],
            branch=DEFAULT_PROFILE["branch"],
            cgpa=DEFAULT_PROFILE["cgpa"],
            grad_year=DEFAULT_PROFILE["grad_year"],
            skills_json=json.dumps(DEFAULT_PROFILE["skills"]),
            linkedin_url=DEFAULT_PROFILE["linkedin_url"],
            github_url=DEFAULT_PROFILE["github_url"],
            summary=DEFAULT_PROFILE["summary"],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return {
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone,
        "college": profile.college,
        "degree": profile.degree,
        "branch": profile.branch,
        "cgpa": profile.cgpa,
        "grad_year": profile.grad_year,
        "skills": json.loads(profile.skills_json) if profile.skills_json else [],
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
        "summary": profile.summary,
    }


@router.put("/")
def update_candidate_profile(data: CandidateUpdateSchema, db: Session = Depends(get_db)):
    """Update existing candidate profile fields."""
    profile = db.scalars(select(CandidateProfile)).first()
    if not profile:
        profile = CandidateProfile(name="Ansh Pathak")
        db.add(profile)

    for field, val in data.model_dump(exclude_unset=True).items():
        if field == "skills" and val is not None:
            profile.skills_json = json.dumps(val)
        elif hasattr(profile, field):
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return {"status": "success", "profile_id": profile.id}


@router.get("/default")
def get_default_profile():
    """Retrieve template profile for initial setup."""
    return DEFAULT_PROFILE
