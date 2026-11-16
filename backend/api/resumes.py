"""
backend/api/resumes.py
Resume upload, tailoring, version control, and download endpoints.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from database.models import CandidateProfile, JobListing, ResumeVersion
from resume_engine.pdf_generator import PDFGenerator
from resume_engine.resume_tailor import ResumeTailor
from resume_engine.version_manager import ResumeVersionManager

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

version_manager = ResumeVersionManager()
tailor_engine = ResumeTailor()
pdf_generator = PDFGenerator()


@router.get("/")
def list_resumes(db: Session = Depends(get_db)):
    """List all stored resume versions."""
    versions = version_manager.get_all_versions(db)
    return [
        {
            "id": v.id,
            "filename": v.filename,
            "version_label": v.version_label,
            "is_primary": v.is_primary,
            "file_size": v.file_size,
            "mime_type": v.mime_type,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    version_label: str = Form("Uploaded Resume"),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Upload a new PDF or text resume file."""
    content = await file.read()
    version = version_manager.save_uploaded_resume(
        db=db,
        file_content=content,
        filename=file.filename or "resume.pdf",
        version_label=version_label,
        is_primary=is_primary,
    )
    return {"id": version.id, "filename": version.filename, "message": "Uploaded successfully"}


@router.get("/{resume_id}/download")
def download_resume(resume_id: int, db: Session = Depends(get_db)):
    """Serve the resume file for download."""
    version = db.get(ResumeVersion, resume_id)
    if not version or not os.path.exists(version.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found")

    return FileResponse(
        path=version.file_path,
        filename=version.filename,
        media_type=version.mime_type or "application/octet-stream",
    )


@router.put("/{resume_id}/set-primary")
def set_primary_resume(resume_id: int, db: Session = Depends(get_db)):
    """Set the specified version as the default primary resume."""
    version = db.get(ResumeVersion, resume_id)
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found")

    all_versions = db.scalars(select(ResumeVersion)).all()
    for v in all_versions:
        v.is_primary = (v.id == resume_id)

    db.commit()
    return {"message": f"Resume '{version.filename}' set as primary"}


@router.delete("/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Remove a resume version and delete its file."""
    version = db.get(ResumeVersion, resume_id)
    if not version:
        raise HTTPException(status_code=404, detail="Resume not found")

    if os.path.exists(version.file_path):
        try:
            os.remove(version.file_path)
        except Exception:
            pass

    db.delete(version)
    db.commit()
    return {"message": "Resume deleted"}


@router.post("/tailor/{job_id}")
def generate_tailored_resume(job_id: int, db: Session = Depends(get_db)):
    """Dynamically generate a tailored PDF resume for a specific job."""
    job = db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.scalars(select(CandidateProfile)).first()
    candidate_dict = {
        "name": profile.name if profile else "Ansh Pathak",
        "skills": json.loads(profile.skills_json) if profile and profile.skills_json else [],
        "cgpa": profile.cgpa if profile else 8.4,
        "grad_year": profile.grad_year if profile else 2027,
    }

    primary_resume = version_manager.get_primary_resume(db)
    base_text = version_manager.read_resume_text(primary_resume) if primary_resume else ""

    job_data = {
        "title": job.title,
        "company_name": job.company.name if job.company else "Company",
        "description": job.description,
    }

    tailored_text = tailor_engine.tailor_resume(base_text, job_data, candidate_dict)

    tailored_pdf_path = os.path.join(
        "data", "tailored", f"Ansh_Pathak_{abs(hash(job.title))}_Resume.pdf"
    )
    pdf_generator.generate_pdf(tailored_text, tailored_pdf_path, candidate_dict["name"])

    tailored_version = version_manager.save_tailored_resume(
        db, job.id, tailored_text, tailored_pdf_path
    )

    return {
        "resume_id": tailored_version.id,
        "pdf_path": tailored_pdf_path,
        "tailored_text": tailored_text[:500] + "...",
        "message": "Tailored resume generated successfully",
    }
