"""
discovery/discovery_engine.py
Orchestrates multi-ATS scanning, filtering, deduplication, and persistence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.crud import create_automation_log, upsert_job_listing
from database.models import ATSProvider, Company, JobListing, LogLevel
from discovery.job_filter import extract_salary_info, is_relevant_title, parse_location
from integrations.ashby import AshbyIntegration
from integrations.career_scraper import CareerPageScraper
from integrations.greenhouse import GreenhouseIntegration
from integrations.lever import LeverIntegration

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Discovers relevant job openings across supported ATS platforms and custom career pages."""

    def __init__(self, db: Session):
        self.db = db
        self.greenhouse = GreenhouseIntegration()
        self.lever = LeverIntegration()
        self.ashby = AshbyIntegration()
        self.scraper = CareerPageScraper()

    async def run_discovery(self, company_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Run discovery across all active companies or a specific company by ID.
        """
        stats = {
            "companies_scanned": 0,
            "jobs_discovered": 0,
            "jobs_saved": 0,
            "duplicates": 0,
            "errors": 0,
        }

        if company_id:
            companies = self.db.scalars(
                select(Company).where(Company.id == company_id, Company.is_active.is_(True))
            ).all()
        else:
            companies = self.db.scalars(
                select(Company).where(Company.is_active.is_(True))
            ).all()

        create_automation_log(
            self.db,
            event_type="DISCOVERY_START",
            message=f"Starting discovery run for {len(companies)} company/companies.",
            level=LogLevel.info,
        )

        for company in companies:
            try:
                comp_stats = await self.scan_company(company)
                stats["companies_scanned"] += 1
                stats["jobs_discovered"] += comp_stats.get("discovered", 0)
                stats["jobs_saved"] += comp_stats.get("saved", 0)
                stats["duplicates"] += comp_stats.get("duplicates", 0)
            except Exception as ex:
                stats["errors"] += 1
                logger.error("Failed scanning company %s (id=%s): %s", company.name, company.id, ex)
                company.scan_status = f"Error: {str(ex)[:100]}"
                self.db.commit()

            # Respectful rate limiting between companies
            await asyncio.sleep(0.5)

        create_automation_log(
            self.db,
            event_type="DISCOVERY_COMPLETE",
            message=(
                f"Discovery completed. Scanned: {stats['companies_scanned']}, "
                f"New jobs saved: {stats['jobs_saved']}, Duplicates: {stats['duplicates']}, "
                f"Errors: {stats['errors']}"
            ),
            level=LogLevel.info,
        )

        return stats

    async def scan_company(self, company: Company) -> Dict[str, int]:
        """Scan a single company using its configured ATS provider."""
        discovered_jobs: List[Dict[str, Any]] = []
        ats_str = str(company.ats_provider.value if hasattr(company.ats_provider, "value") else company.ats_provider).lower()

        try:
            if ats_str == "greenhouse" and company.board_identifier:
                discovered_jobs = await self.greenhouse.fetch_jobs(company.board_identifier)
            elif ats_str == "lever" and company.board_identifier:
                discovered_jobs = await self.lever.fetch_jobs(company.board_identifier)
            elif ats_str == "ashby" and company.board_identifier:
                discovered_jobs = await self.ashby.fetch_jobs(company.board_identifier)
            elif company.careers_url:
                discovered_jobs = await self.scraper.scrape(company.careers_url, company.name)

            company.last_scan_at = datetime.now(timezone.utc)
            company.scan_status = f"Success ({len(discovered_jobs)} raw jobs found)"
            self.db.commit()

        except Exception as ex:
            company.scan_status = f"Failed: {str(ex)[:80]}"
            self.db.commit()
            raise

        saved_count = 0
        dup_count = 0

        for raw_job in discovered_jobs:
            title = (raw_job.get("title") or "").strip()
            if not title or not is_relevant_title(title):
                continue

            external_id = raw_job.get("external_job_id") or str(abs(hash(raw_job.get("application_url", title))))
            loc_data = parse_location(raw_job.get("location", ""))
            salary_data = extract_salary_info(raw_job.get("description", ""), title)

            work_mode_str = raw_job.get("work_mode") or loc_data.get("work_mode", "unknown")

            job_fields = {
                "title": title,
                "department": raw_job.get("department"),
                "location": raw_job.get("location"),
                "city": loc_data.get("city"),
                "state": None,
                "country": loc_data.get("country"),
                "work_mode": work_mode_str,
                "salary_min": salary_data.get("min_lpa"),
                "salary_max": salary_data.get("max_lpa"),
                "salary_currency": salary_data.get("currency", "INR"),
                "salary_disclosed": salary_data.get("disclosed", False),
                "description": raw_job.get("description", ""),
                "requirements_text": None,
                "posted_date": raw_job.get("posted_date"),
                "source_url": raw_job.get("application_url"),
                "application_url": raw_job.get("application_url"),
                "is_active": True,
            }

            job, created = upsert_job_listing(
                self.db,
                company_id=company.id,
                external_job_id=str(external_id),
                **job_fields,
            )

            if created:
                saved_count += 1
            else:
                dup_count += 1

        return {
            "discovered": len(discovered_jobs),
            "saved": saved_count,
            "duplicates": dup_count,
        }
