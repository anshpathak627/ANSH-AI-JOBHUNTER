"""
database/models.py
SQLAlchemy ORM models for ANSH AI JOBHUNTER.

Tables
------
CandidateProfile    – The user's profile / CV data.
ResumeVersion       – Uploaded resume files (multiple versions allowed).
Company             – Target companies and their career-page metadata.
JobListing          – Individual job postings discovered by scrapers.
JobRequirement      – Parsed mandatory / preferred requirements for a job.
JobMatch            – AI / rule-based compatibility score for a job.
Application         – State-machine tracking of each job application.
ApplicationDocument – Files attached to a specific application (cover letter, etc.).
Notification        – Outbound notification queue (Telegram, email).
AutomationLog       – Audit trail of all background automation events.
UserSetting         – Key/value store for user-configurable preferences.
"""

from __future__ import annotations

import enum
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ─────────────────────────────────────────────────────────────────────────────
# Declarative base
# ─────────────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class ATSProvider(str, enum.Enum):
    greenhouse = "greenhouse"
    lever = "lever"
    ashby = "ashby"
    workday = "workday"
    taleo = "taleo"
    icims = "icims"
    smartrecruiters = "smartrecruiters"
    custom = "custom"
    unknown = "unknown"


class WorkMode(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unknown = "unknown"


class ApplicationStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    MATCHED = "MATCHED"
    PREPARED = "PREPARED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class NotificationChannel(str, enum.Enum):
    telegram = "telegram"
    email = "email"
    both = "both"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class LogLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"


class RequirementType(str, enum.Enum):
    mandatory = "mandatory"
    preferred = "preferred"


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

class CandidateProfile(Base):
    """
    Stores the job-seeker's personal and academic information.
    There is typically a single row; additional rows can represent
    different "personas" in future versions.
    """
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    college: Mapped[Optional[str]] = mapped_column(String(255))
    degree: Mapped[Optional[str]] = mapped_column(String(100))
    branch: Mapped[Optional[str]] = mapped_column(String(150))
    cgpa: Mapped[Optional[float]] = mapped_column(Float)
    grad_year: Mapped[Optional[int]] = mapped_column(Integer)
    # JSON-serialised list of skill strings, e.g. '["Python", "SQL", "FastAPI"]'
    skills_json: Mapped[Optional[str]] = mapped_column(Text)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512))
    github_url: Mapped[Optional[str]] = mapped_column(String(512))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(512))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # ── helpers ──────────────────────────────────────────────────────────────

    @property
    def skills(self) -> List[str]:
        """Deserialise skills_json to a Python list."""
        if not self.skills_json:
            return []
        try:
            return json.loads(self.skills_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @skills.setter
    def skills(self, value: List[str]) -> None:
        self.skills_json = json.dumps(value)

    def __repr__(self) -> str:
        return f"<CandidateProfile id={self.id} name={self.name!r} email={self.email!r}>"


class ResumeVersion(Base):
    """
    Tracks uploaded resume files.  Multiple versions can exist; the primary
    version is the one sent with applications by default.
    """
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    version_label: Mapped[Optional[str]] = mapped_column(String(100))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    def __repr__(self) -> str:
        return (
            f"<ResumeVersion id={self.id} label={self.version_label!r} "
            f"primary={self.is_primary}>"
        )


class Company(Base):
    """
    A target company whose career page is periodically scanned.
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    careers_url: Mapped[Optional[str]] = mapped_column(String(1024))
    ats_provider: Mapped[ATSProvider] = mapped_column(
        Enum(ATSProvider), default=ATSProvider.unknown, nullable=False
    )
    board_identifier: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scan_status: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # ── relationships ─────────────────────────────────────────────────────────
    job_listings: Mapped[List["JobListing"]] = relationship(
        "JobListing", back_populates="company", cascade="all, delete-orphan"
    )
    automation_logs: Mapped[List["AutomationLog"]] = relationship(
        "AutomationLog", back_populates="company"
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r} ats={self.ats_provider.value}>"


class JobListing(Base):
    """
    A single job posting discovered on a company's career page.
    """
    __tablename__ = "job_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_job_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(512))
    city: Mapped[Optional[str]] = mapped_column(String(150))
    state: Mapped[Optional[str]] = mapped_column(String(150))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    work_mode: Mapped[WorkMode] = mapped_column(
        Enum(WorkMode), default=WorkMode.unknown, nullable=False
    )
    salary_min: Mapped[Optional[float]] = mapped_column(Float)
    salary_max: Mapped[Optional[float]] = mapped_column(Float)
    salary_currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    salary_disclosed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements_text: Mapped[Optional[str]] = mapped_column(Text)
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    source_url: Mapped[Optional[str]] = mapped_column(String(1024))
    application_url: Mapped[Optional[str]] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # ── relationships ─────────────────────────────────────────────────────────
    company: Mapped["Company"] = relationship("Company", back_populates="job_listings")
    requirements: Mapped[List["JobRequirement"]] = relationship(
        "JobRequirement", back_populates="job", cascade="all, delete-orphan"
    )
    match: Mapped[Optional["JobMatch"]] = relationship(
        "JobMatch", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="job", cascade="all, delete-orphan"
    )
    automation_logs: Mapped[List["AutomationLog"]] = relationship(
        "AutomationLog", back_populates="job"
    )

    def __repr__(self) -> str:
        return (
            f"<JobListing id={self.id} title={self.title!r} "
            f"company_id={self.company_id} active={self.is_active}>"
        )


class JobRequirement(Base):
    """
    Individual parsed requirement extracted from a job description.
    """
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    req_type: Mapped[RequirementType] = mapped_column(
        Enum(RequirementType), default=RequirementType.mandatory, nullable=False
    )
    requirement: Mapped[str] = mapped_column(Text, nullable=False)

    # ── relationships ─────────────────────────────────────────────────────────
    job: Mapped["JobListing"] = relationship("JobListing", back_populates="requirements")

    def __repr__(self) -> str:
        return (
            f"<JobRequirement id={self.id} job_id={self.job_id} "
            f"type={self.req_type.value} req={self.requirement[:50]!r}>"
        )


class JobMatch(Base):
    """
    Compatibility score produced by the matching engine for a specific job.
    One-to-one with JobListing.
    """
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_listings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    skills_score: Mapped[Optional[float]] = mapped_column(Float)
    education_score: Mapped[Optional[float]] = mapped_column(Float)
    experience_score: Mapped[Optional[float]] = mapped_column(Float)
    role_score: Mapped[Optional[float]] = mapped_column(Float)
    location_score: Mapped[Optional[float]] = mapped_column(Float)
    salary_score: Mapped[Optional[float]] = mapped_column(Float)
    # JSON list of human-readable reasons, e.g. ["Python match", "Remote role preferred"]
    match_reasons: Mapped[Optional[str]] = mapped_column(Text)
    disqualified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disqualification_reason: Mapped[Optional[str]] = mapped_column(Text)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # ── relationships ─────────────────────────────────────────────────────────
    job: Mapped["JobListing"] = relationship("JobListing", back_populates="match")

    @property
    def reasons(self) -> List[str]:
        """Deserialise match_reasons JSON."""
        if not self.match_reasons:
            return []
        try:
            return json.loads(self.match_reasons)
        except (json.JSONDecodeError, TypeError):
            return []

    @reasons.setter
    def reasons(self, value: List[str]) -> None:
        self.match_reasons = json.dumps(value)

    def __repr__(self) -> str:
        return (
            f"<JobMatch id={self.id} job_id={self.job_id} "
            f"score={self.match_score} disqualified={self.disqualified}>"
        )


class Application(Base):
    """
    State-machine record tracking the lifecycle of a single job application.
    """
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_version_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default=ApplicationStatus.DISCOVERED.value, nullable=False, index=True
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    submission_url: Mapped[Optional[str]] = mapped_column(String(1024))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # ── relationships ─────────────────────────────────────────────────────────
    job: Mapped["JobListing"] = relationship("JobListing", back_populates="applications")
    resume_version: Mapped[Optional["ResumeVersion"]] = relationship("ResumeVersion")
    documents: Mapped[List["ApplicationDocument"]] = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.id} job_id={self.job_id} status={self.status!r}>"
        )


class ApplicationDocument(Base):
    """
    A file (cover letter, writing sample, etc.) attached to an application.
    """
    __tablename__ = "application_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doc_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # ── relationships ─────────────────────────────────────────────────────────
    application: Mapped["Application"] = relationship(
        "Application", back_populates="documents"
    )

    def __repr__(self) -> str:
        return (
            f"<ApplicationDocument id={self.id} app_id={self.application_id} "
            f"type={self.doc_type!r}>"
        )


class Notification(Base):
    """
    Outbound notification queue.  A background worker polls this table and
    delivers pending notifications via the configured channels.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Arbitrary JSON payload for the notification handler
    payload_json: Mapped[Optional[str]] = mapped_column(Text)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), default=NotificationChannel.telegram, nullable=False
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.pending, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    @property
    def payload(self) -> Dict[str, Any]:
        """Deserialise payload_json to a Python dict."""
        if not self.payload_json:
            return {}
        try:
            return json.loads(self.payload_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @payload.setter
    def payload(self, value: Dict[str, Any]) -> None:
        self.payload_json = json.dumps(value)

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} event={self.event_type!r} "
            f"status={self.status.value} channel={self.channel.value}>"
        )


class AutomationLog(Base):
    """
    Immutable audit trail written by all background automation processes.
    """
    __tablename__ = "automation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("job_listings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[LogLevel] = mapped_column(
        Enum(LogLevel), default=LogLevel.info, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # ── relationships ─────────────────────────────────────────────────────────
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="automation_logs"
    )
    job: Mapped[Optional["JobListing"]] = relationship(
        "JobListing", back_populates="automation_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<AutomationLog id={self.id} event={self.event_type!r} "
            f"level={self.level.value} company={self.company_id} job={self.job_id}>"
        )


class UserSetting(Base):
    """
    Simple key/value store for user-configurable preferences persisted in the DB.
    Use this for settings that the user can change at runtime via the UI.
    """
    __tablename__ = "user_settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserSetting key={self.key!r} value={self.value!r}>"
