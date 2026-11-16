"""
integrations/greenhouse.py
Async client for the Greenhouse public job board API.

Endpoint:
  GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

USER_AGENT = "AnshAIJobHunter/1.0 (personal job search automation)"


class GreenhouseIntegration:
    """Async integration client for Greenhouse public job board API."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    async def fetch_jobs(self, board_token: str) -> List[Dict[str, Any]]:
        """
        Fetch all public postings for a company from Greenhouse.

        Parameters
        ----------
        board_token : str
            The board token/slug (e.g. 'adobe', 'salesforce').

        Returns
        -------
        list[dict]
            Normalized job dictionaries.
        """
        if not board_token:
            return []

        url = self.BASE_URL.format(board_token=board_token) + "?content=true"
        jobs_data = await self._get_with_retry(url)
        if not jobs_data or not isinstance(jobs_data, dict):
            return []

        raw_jobs = jobs_data.get("jobs", [])
        normalized_jobs = []

        for item in raw_jobs:
            try:
                job_id = str(item.get("id", ""))
                if not job_id:
                    continue

                title = (item.get("title") or "").strip()
                departments = item.get("departments") or []
                department_name = (
                    departments[0].get("name") if departments else None
                )

                location_obj = item.get("location") or {}
                location_str = (
                    location_obj.get("name") if isinstance(location_obj, dict) else str(location_obj)
                ) or ""

                app_url = item.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"
                updated_at_str = item.get("updated_at")
                posted_date = None
                if updated_at_str:
                    try:
                        posted_date = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    except Exception:
                        posted_date = None

                description = item.get("content") or ""

                normalized_jobs.append({
                    "external_job_id": job_id,
                    "title": title,
                    "department": department_name,
                    "location": location_str,
                    "application_url": app_url,
                    "posted_date": posted_date,
                    "description": description,
                    "ats_provider": "greenhouse",
                })
            except Exception as ex:
                logger.warning("Error normalizing Greenhouse job %s: %s", item.get("id"), ex)

        return normalized_jobs

    async def _get_with_retry(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch URL with exponential backoff on 429 / 5xx."""
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 429:
                            logger.warning("Greenhouse rate limit (429) on %s, backing off %.1fs", url, delay)
                            await asyncio.sleep(delay)
                            delay *= 2
                        elif resp.status == 404:
                            logger.info("Greenhouse board not found (404): %s", url)
                            return None
                        else:
                            logger.warning("Greenhouse HTTP %d on %s", resp.status, url)
                            if attempt < self.max_retries:
                                await asyncio.sleep(delay)
                                delay *= 2
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                logger.warning("Greenhouse request failed (attempt %d/%d): %s", attempt, self.max_retries, err)
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2
            except Exception as ex:
                logger.error("Unexpected error in Greenhouse request: %s", ex)
                return None
        return None
