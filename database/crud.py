"""
database/crud.py
Generic and domain-specific CRUD helpers for ANSH AI JOBHUNTER.

All helpers accept a SQLAlchemy ``Session`` as their first argument and
operate synchronously.  They are designed to be called from FastAPI route
handlers (via ``Depends(get_db)``) or from background automation scripts.

Generic helpers
---------------
get_by_id          – Fetch a single row by primary key.
get_all            – Fetch all rows of a model with optional limit/offset.
create_object      – Persist a new mapped object.
update_object      – Apply a dict of field updates to an existing object.
delete_object      – Delete a row by primary key.

Domain-specific helpers
-----------------------
get_or_create_candidate_profile
get_active_jobs
upsert_job_listing
get_job_match
create_automation_log
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from database.models import (
    Application,
    AutomationLog,
    CandidateProfile,
    Company,
    JobListing,
    JobMatch,
    LogLevel,
    UserSetting,
)

logger = logging.getLogger(__name__)

# Generic type variable for ORM model classes
ModelT = TypeVar("ModelT")


# ─────────────────────────────────────────────────────────────────────────────
# Generic helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_by_id(db: Session, model: Type[ModelT], pk: Any) -> Optional[ModelT]:
    """
    Return the row for *model* with the given primary key, or ``None``.

    Example::

        job = get_by_id(db, JobListing, 42)
    """
    return db.get(model, pk)


def get_all(
    db: Session,
    model: Type[ModelT],
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[ModelT]:
    """
    Return up to *limit* rows of *model* starting at *offset*.

    Example::

        companies = get_all(db, Company, limit=50)
    """
    stmt = select(model).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def create_object(db: Session, model: Type[ModelT], **kwargs: Any) -> ModelT:
    """
    Instantiate *model* with **kwargs, add it to the session, flush and
    refresh, then return the persisted object.

    Example::

        company = create_object(db, Company, name="Acme", ats_provider="greenhouse")
    """
    obj = model(**kwargs)  # type: ignore[call-arg]
    db.add(obj)
    db.flush()
    db.refresh(obj)
    db.commit()
    return obj


def update_object(
    db: Session,
    model: Type[ModelT],
    pk: Any,
    updates: Dict[str, Any],
) -> Optional[ModelT]:
    """
    Apply a dictionary of *updates* to the row identified by *pk*.
    Returns the updated object, or ``None`` if the row does not exist.

    Example::

        updated = update_object(db, Company, 5, {"scan_status": "completed"})
    """
    obj = db.get(model, pk)
    if obj is None:
        return None
    for field, value in updates.items():
        if hasattr(obj, field):
            setattr(obj, field, value)
    db.flush()
    db.refresh(obj)
    db.commit()
    return obj


def delete_object(db: Session, model: Type[ModelT], pk: Any) -> bool:
    """
    Delete the row identified by *pk* from *model*.
    Returns ``True`` if a row was deleted, ``False`` if it did not exist.

    Example::

        deleted = delete_object(db, JobListing, 99)
    """
    obj = db.get(model, pk)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Domain-specific helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_candidate_profile(
    db: Session,
    **kwargs: Any,
) -> Tuple[CandidateProfile, bool]:
    """
    Return the existing ``CandidateProfile`` (there is usually only one), or
    create a new one populated with **kwargs.

    Returns a ``(profile, created)`` tuple where *created* is ``True`` when a
    new row was inserted.

    If *email* is supplied in **kwargs the lookup uses it; otherwise the first
    row in the table is returned.

    Example::

        profile, created = get_or_create_candidate_profile(
            db, name="Ansh", email="ansh@example.com"
        )
    """
    email: Optional[str] = kwargs.get("email")

    if email:
        stmt = select(CandidateProfile).where(CandidateProfile.email == email)
        existing = db.scalars(stmt).first()
    else:
        existing = db.scalars(select(CandidateProfile).limit(1)).first()

    if existing is not None:
        return existing, False

    profile = CandidateProfile(**kwargs)
    db.add(profile)
    db.flush()
    db.refresh(profile)
    db.commit()
    return profile, True


def get_active_jobs(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
) -> list[JobListing]:
    """
    Return active ``JobListing`` rows, optionally filtered by a dict of
    column→value constraints.

    Supported filter keys:
    - ``company_id``  (int)
    - ``work_mode``   (WorkMode enum value or string)
    - ``country``     (str)
    - ``city``        (str)
    - ``title_like``  (str)  – case-insensitive substring search on title

    Example::

        remote_jobs = get_active_jobs(db, {"work_mode": "remote"})
    """
    filters = filters or {}
    stmt = select(JobListing).where(JobListing.is_active.is_(True))

    if "company_id" in filters:
        stmt = stmt.where(JobListing.company_id == filters["company_id"])
    if "work_mode" in filters:
        stmt = stmt.where(JobListing.work_mode == filters["work_mode"])
    if "country" in filters:
        stmt = stmt.where(JobListing.country == filters["country"])
    if "city" in filters:
        stmt = stmt.where(JobListing.city == filters["city"])
    if "title_like" in filters:
        stmt = stmt.where(
            JobListing.title.ilike(f"%{filters['title_like']}%")
        )

    return list(db.scalars(stmt).all())


def upsert_job_listing(
    db: Session,
    company_id: int,
    external_job_id: str,
    **data: Any,
) -> Tuple[JobListing, bool]:
    """
    Insert a new ``JobListing`` or update the existing one identified by
    ``(company_id, external_job_id)``.

    Returns a ``(job, created)`` tuple where *created* is ``True`` for new
    rows.

    Example::

        job, created = upsert_job_listing(
            db,
            company_id=1,
            external_job_id="gh-12345",
            title="Backend Engineer",
            work_mode="remote",
        )
    """
    stmt = select(JobListing).where(
        and_(
            JobListing.company_id == company_id,
            JobListing.external_job_id == external_job_id,
        )
    )
    existing = db.scalars(stmt).first()

    if existing is not None:
        for field, value in data.items():
            if hasattr(existing, field):
                setattr(existing, field, value)
        db.flush()
        db.refresh(existing)
        db.commit()
        return existing, False

    job = JobListing(
        company_id=company_id,
        external_job_id=external_job_id,
        **data,
    )
    db.add(job)
    db.flush()
    db.refresh(job)
    db.commit()
    return job, True


def get_job_match(db: Session, job_id: int) -> Optional[JobMatch]:
    """
    Return the ``JobMatch`` record for *job_id*, or ``None`` if it has not
    been evaluated yet.

    Example::

        match = get_job_match(db, job_id=42)
        if match:
            print(f"Score: {match.match_score}")
    """
    stmt = select(JobMatch).where(JobMatch.job_id == job_id)
    return db.scalars(stmt).first()


def create_automation_log(
    db: Session,
    event_type: str,
    message: str,
    level: str = "info",
    *,
    company_id: Optional[int] = None,
    job_id: Optional[int] = None,
) -> AutomationLog:
    """
    Append an immutable automation log entry.

    Parameters
    ----------
    db:          Active database session.
    event_type:  Short event identifier, e.g. ``"scraper.company_scanned"``.
    message:     Human-readable description of what happened.
    level:       Severity – one of ``"info"``, ``"warning"``, ``"error"``.
    company_id:  Optional FK to the related ``Company`` row.
    job_id:      Optional FK to the related ``JobListing`` row.

    Example::

        create_automation_log(
            db,
            event_type="scraper.job_found",
            message="Discovered 'Backend Engineer' at Acme Corp",
            level="info",
            company_id=3,
            job_id=99,
        )
    """
    # Normalise level to enum
    try:
        log_level = LogLevel(level.lower())
    except ValueError:
        log_level = LogLevel.info
        logger.warning("Unknown log level %r – defaulting to 'info'.", level)

    entry = AutomationLog(
        event_type=event_type,
        message=message,
        level=log_level,
        company_id=company_id,
        job_id=job_id,
    )
    db.add(entry)
    db.flush()
    db.refresh(entry)
    db.commit()
    return entry
