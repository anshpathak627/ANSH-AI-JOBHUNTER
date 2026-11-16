"""
integrations/lever.py
Async client for the Lever public job board postings API.

Endpoint:
  GET https://api.lever.co/v0/postings/{company}?mode=json
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

USER_AGENT = "AnshAIJobHunter/1.0 (personal job search automation)"


class LeverIntegration:
    """Async client for Lever public job board API."""

    BASE_URL = "https://api.lever.co/v0/postings/{company}?mode=json"

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    async def fetch_jobs(self, company_slug: str) -> List[Dict[str, Any]]:
        """
        Fetch all active postings for a company slug from Lever.

        Parameters
        ----------
        company_slug : str
            The company identifier on Lever (e.g. 'uber', 'cred', 'swiggy').

        Returns
        -------
        list[dict]
            Normalized job dictionaries.
        """
        if not company_slug:
            return []

        url = self.BASE_URL.format(company=company_slug)
        raw_postings = await self._get_with_retry(url)
        if not raw_postings or not isinstance(raw_postings, list):
            return []

        normalized_jobs = []

        for item in raw_postings:
            try:
                job_id = str(item.get("id", ""))
                if not job_id:
                    continue

                title = (item.get("text") or "").strip()
                categories = item.get("categories") or {}
                department_name = categories.get("department") or categories.get("team")
                location_str = categories.get("location") or ""
                work_type = (categories.get("commitment") or "").lower()

                work_mode = "unknown"
                workplace_type = (item.get("workplaceType") or "").lower()
                if "remote" in workplace_type or "remote" in location_str.lower() or "remote" in title.lower():
                    work_mode = "remote"
                elif "hybrid" in workplace_type or "hybrid" in location_str.lower():
                    work_mode = "hybrid"
                elif "onsite" in workplace_type:
                    work_mode = "onsite"

                app_url = item.get("hostedUrl") or item.get("applyUrl") or f"https://jobs.lever.co/{company_slug}/{job_id}"

                created_at_ms = item.get("createdAt")
                posted_date = None
                if created_at_ms:
                    try:
                        posted_date = datetime.fromtimestamp(created_at_ms / 1000.0, tz=timezone.utc)
                    except Exception:
                        posted_date = None

                description_plain = item.get("descriptionPlain") or item.get("description") or ""
                lists = item.get("lists") or []
                lists_text = ""
                for lst in lists:
                    list_name = lst.get("text", "")
                    items_content = lst.get("content", "")
                    lists_text += f"\n\n{list_name}\n{items_content}"

                full_description = f"{description_plain}\n{lists_text}".strip()

                normalized_jobs.append({
                    "external_job_id": job_id,
                    "title": title,
                    "department": department_name,
                    "location": location_str,
                    "work_mode": work_mode,
                    "application_url": app_url,
                    "posted_date": posted_date,
                    "description": full_description,
                    "ats_provider": "lever",
                })
            except Exception as ex:
                logger.warning("Error normalizing Lever job %s: %s", item.get("id"), ex)

        return normalized_jobs

    async def _get_with_retry(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch URL with exponential backoff on 429 / 5xx."""
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 429:
                            logger.warning("Lever rate limit (429) on %s, backing off %.1fs", url, delay)
                            await asyncio.sleep(delay)
                            delay *= 2
                        elif resp.status == 404:
                            logger.info("Lever postings not found (404): %s", url)
                            return None
                        else:
                            logger.warning("Lever HTTP %d on %s", resp.status, url)
                            if attempt < self.max_retries:
                                await asyncio.sleep(delay)
                                delay *= 2
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                logger.warning("Lever request failed (attempt %d/%d): %s", attempt, self.max_retries, err)
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2
            except Exception as ex:
                logger.error("Unexpected error in Lever request: %s", ex)
                return None
        return None
