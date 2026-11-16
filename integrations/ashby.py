"""
integrations/ashby.py
Async client for the Ashby public job board API and GraphQL service.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

USER_AGENT = "AnshAIJobHunter/1.0 (personal job search automation)"


class AshbyIntegration:
    """Async client for Ashby public job board postings."""

    POSTING_API_URL = "https://jobs.ashbyhq.com/api/posting-api/job-board/{organization_slug}"
    GRAPHQL_URL = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def fetch_jobs(self, organization_slug: str) -> List[Dict[str, Any]]:
        """
        Fetch all public postings for an organization from Ashby.
        Tries posting API first, then falls back to GraphQL.
        """
        if not organization_slug:
            return []

        # 1. Try GraphQL API
        graphql_jobs = await self._fetch_via_graphql(organization_slug)
        if graphql_jobs:
            return graphql_jobs

        # 2. Fallback to posting API
        return await self._fetch_via_posting_api(organization_slug)

    async def _fetch_via_graphql(self, organization_slug: str) -> List[Dict[str, Any]]:
        query = (
            "query ApiJobBoardWithTeams($slug: String!) { "
            "  jobBoard: jobBoardWithTeams(organizationHostedJobsPageName: $slug) { "
            "    jobPostings { "
            "      id title locationName isRemote publishedAt "
            "    } "
            "  } "
            "}"
        )
        payload = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {"slug": organization_slug},
            "query": query,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(self.GRAPHQL_URL, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_jobs = (
                            data.get("data", {})
                            .get("jobBoard", {})
                            .get("jobPostings", [])
                        )
                        normalized = []
                        for item in raw_jobs:
                            jid = str(item.get("id", ""))
                            title = (item.get("title") or "").strip()
                            loc = item.get("locationName") or ""
                            is_remote = bool(item.get("isRemote", False))
                            work_mode = "remote" if is_remote or "remote" in loc.lower() else "unknown"

                            app_url = f"https://jobs.ashbyhq.com/{organization_slug}/{jid}"
                            pub = item.get("publishedAt")
                            posted_date = None
                            if pub:
                                try:
                                    posted_date = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                                except Exception:
                                    posted_date = None

                            normalized.append({
                                "external_job_id": jid,
                                "title": title,
                                "department": None,
                                "location": loc,
                                "work_mode": work_mode,
                                "application_url": app_url,
                                "posted_date": posted_date,
                                "description": f"{title} at {organization_slug}. Location: {loc}",
                                "ats_provider": "ashby",
                            })
                        return normalized
        except Exception as ex:
            logger.debug("Ashby GraphQL query failed for %s: %s", organization_slug, ex)

        return []

    async def _fetch_via_posting_api(self, organization_slug: str) -> List[Dict[str, Any]]:
        url = self.POSTING_API_URL.format(organization_slug=organization_slug)
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_jobs = data.get("jobs", []) if isinstance(data, dict) else []
                        normalized = []
                        for item in raw_jobs:
                            jid = str(item.get("id", ""))
                            title = (item.get("title") or "").strip()
                            loc = item.get("location") or ""
                            normalized.append({
                                "external_job_id": jid,
                                "title": title,
                                "department": item.get("department"),
                                "location": loc,
                                "work_mode": "remote" if "remote" in loc.lower() else "unknown",
                                "application_url": item.get("jobUrl") or f"https://jobs.ashbyhq.com/{organization_slug}/{jid}",
                                "posted_date": None,
                                "description": item.get("descriptionPlain") or "",
                                "ats_provider": "ashby",
                            })
                        return normalized
        except Exception as ex:
            logger.debug("Ashby posting API failed for %s: %s", organization_slug, ex)

        return []
