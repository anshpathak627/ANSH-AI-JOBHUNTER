"""
tests/test_db.py
Database models and CRUD unit tests using SQLite in-memory.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, CandidateProfile, Company, JobListing, AutomationLog, LogLevel, ATSProvider
from database.crud import upsert_job_listing, create_automation_log, get_by_id


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_candidate_profile(db_session):
    profile = CandidateProfile(
        name="Ansh Pathak",
        college="MAIT",
        degree="B.Tech",
        branch="EE (VLSI)",
        cgpa=8.4,
        grad_year=2027,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    fetched = get_by_id(db_session, CandidateProfile, profile.id)
    assert fetched is not None
    assert fetched.name == "Ansh Pathak"
    assert fetched.cgpa == 8.4


def test_upsert_job_listing_deduplication(db_session):
    company = Company(name="Test Corp", ats_provider=ATSProvider.greenhouse)
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    # First insert
    job1, created1 = upsert_job_listing(
        db_session,
        company_id=company.id,
        external_job_id="job_123",
        title="Software Engineer",
        location="Noida",
    )
    assert created1 is True
    assert job1.id is not None

    # Second insert with same external_job_id
    job2, created2 = upsert_job_listing(
        db_session,
        company_id=company.id,
        external_job_id="job_123",
        title="Software Engineer - Updated",
        location="Noida, India",
    )
    assert created2 is False
    assert job2.id == job1.id
    assert job2.title == "Software Engineer - Updated"


def test_automation_log_creation(db_session):
    log = create_automation_log(
        db_session,
        event_type="DISCOVERY_START",
        message="Starting scan",
        level=LogLevel.info,
    )
    assert log.id is not None
    assert log.event_type == "DISCOVERY_START"
