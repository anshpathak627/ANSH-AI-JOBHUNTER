"""
resume_engine/version_manager.py
Manages resume uploads, version history, text extraction, and storage.
"""

from __future__ import annotations

import os
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ResumeVersion


class ResumeVersionManager:
    """Handles persistent storage and versioning for raw and tailored CVs."""

    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = base_data_dir
        self.resumes_dir = os.path.join(base_data_dir, "resumes")
        self.tailored_dir = os.path.join(base_data_dir, "tailored")
        os.makedirs(self.resumes_dir, exist_ok=True)
        os.makedirs(self.tailored_dir, exist_ok=True)

    def save_uploaded_resume(
        self,
        db: Session,
        file_content: bytes,
        filename: str,
        version_label: str,
        is_primary: bool = False,
    ) -> ResumeVersion:
        """Save an uploaded resume file and record it in the database."""
        safe_filename = f"{int(os.path.getmtime(self.resumes_dir)) if os.path.exists(self.resumes_dir) else 1}_{os.path.basename(filename)}"
        file_path = os.path.join(self.resumes_dir, safe_filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        if is_primary:
            # Unset any existing primary
            existing_primaries = db.scalars(
                select(ResumeVersion).where(ResumeVersion.is_primary.is_(True))
            ).all()
            for r in existing_primaries:
                r.is_primary = False

        mime = "application/pdf" if filename.lower().endswith(".pdf") else "text/plain"

        version = ResumeVersion(
            filename=filename,
            version_label=version_label,
            is_primary=is_primary,
            file_path=file_path,
            file_size=len(file_content),
            mime_type=mime,
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    def get_all_versions(self, db: Session) -> List[ResumeVersion]:
        """Fetch all stored resume versions."""
        return list(db.scalars(select(ResumeVersion).order_by(ResumeVersion.created_at.desc())).all())

    def get_primary_resume(self, db: Session) -> Optional[ResumeVersion]:
        """Return the designated primary resume, or latest if none flagged."""
        res = db.scalars(select(ResumeVersion).where(ResumeVersion.is_primary.is_(True))).first()
        if not res:
            res = db.scalars(select(ResumeVersion).order_by(ResumeVersion.created_at.desc())).first()
        return res

    def read_resume_text(self, resume_version: ResumeVersion) -> str:
        """Read and extract text from the stored file."""
        if not resume_version or not os.path.exists(resume_version.file_path):
            return ""

        path = resume_version.file_path
        if path.lower().endswith(".txt"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        # PDF basic text extraction
        if path.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                # Fallback to plain binary/raw string read
                with open(path, "rb") as f:
                    content = f.read()
                    # Extract printable ascii substrings
                    import re
                    words = re.findall(rb"[\x20-\x7E]{4,}", content)
                    return "\n".join(w.decode("latin1", errors="ignore") for w in words[:150])

        return ""

    def save_tailored_resume(
        self,
        db: Session,
        job_id: int,
        tailored_text: str,
        pdf_path: str,
    ) -> ResumeVersion:
        """Register a tailored resume in the database."""
        version = ResumeVersion(
            filename=os.path.basename(pdf_path),
            version_label=f"Tailored for Job #{job_id}",
            is_primary=False,
            file_path=pdf_path,
            file_size=os.path.getsize(pdf_path) if os.path.exists(pdf_path) else len(tailored_text),
            mime_type="application/pdf",
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version
