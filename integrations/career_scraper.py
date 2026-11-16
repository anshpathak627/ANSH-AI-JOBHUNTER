"""
integrations/career_scraper.py
Fallback HTML / JSON-LD scraper for custom enterprise career pages.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (AnshAIJobHunter/1.0)"


class CareerPageScraper:
    """HTML and JSON-LD scraper for companies with custom career pages."""

    def __init__(self, timeout_seconds: int = 25):
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def scrape(self, url: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape a career page URL for open positions.

        Parameters
        ----------
        url : str
            The career portal URL.
        company_name : str
            Company name for context.

        Returns
        -------
        list[dict]
            Normalized job dictionaries.
        """
        if not url:
            return []

        html = await self._fetch_html(url)
        if not html:
            return []

        jobs: List[Dict[str, Any]] = []

        # 1. First attempt: check for JSON-LD JobPosting schema
        try:
            json_ld_jobs = self._extract_json_ld(html, url)
            if json_ld_jobs:
                return json_ld_jobs
        except Exception as ex:
            logger.debug("JSON-LD extraction failed for %s: %s", company_name, ex)

        # 2. Second attempt: heuristic HTML parsing
        try:
            html_jobs = self._extract_html_links(html, url, company_name)
            jobs.extend(html_jobs)
        except Exception as ex:
            logger.debug("HTML extraction failed for %s: %s", company_name, ex)

        return jobs

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch raw HTML content."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url, allow_redirects=True) as resp:
                    if resp.status == 200:
                        return await resp.text(errors="ignore")
                    logger.info("Career page fetch returned status %d for %s", resp.status, url)
                    return None
        except Exception as ex:
            logger.warning("Failed to fetch career page %s: %s", url, ex)
            return None

    def _extract_json_ld(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract schema.org/JobPosting JSON-LD structures."""
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")
        jobs: List[Dict[str, Any]] = []

        for script in scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]

                for item in items:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        title = item.get("title") or ""
                        job_id = str(item.get("identifier") or item.get("jobLocation") or abs(hash(title)))
                        app_url = item.get("url") or base_url
                        if not app_url.startswith("http"):
                            app_url = urljoin(base_url, app_url)

                        desc = item.get("description") or ""
                        loc_obj = item.get("jobLocation") or {}
                        location_str = ""
                        if isinstance(loc_obj, dict):
                            address = loc_obj.get("address") or {}
                            if isinstance(address, dict):
                                location_str = address.get("addressLocality") or address.get("addressCountry") or ""
                            else:
                                location_str = str(address)

                        jobs.append({
                            "external_job_id": str(job_id),
                            "title": title.strip(),
                            "department": None,
                            "location": location_str,
                            "application_url": app_url,
                            "posted_date": None,
                            "description": desc,
                            "ats_provider": "custom",
                        })
            except Exception:
                continue

        return jobs

    def _extract_html_links(self, html: str, base_url: str, company_name: str) -> List[Dict[str, Any]]:
        """Extract job links using semantic keywords in anchor tags."""
        soup = BeautifulSoup(html, "html.parser")
        job_link_pattern = re.compile(
            r"/(?:job|career|position|opening|role|vacancy|requisition|opp)/",
            re.IGNORECASE,
        )
        found_links = set()
        jobs: List[Dict[str, Any]] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = (a_tag.get_text() or "").strip()

            if len(text) < 5 or len(text) > 100:
                continue

            full_url = urljoin(base_url, href)
            if full_url in found_links:
                continue

            # Match on URL pattern or text
            if job_link_pattern.search(href) or any(
                kw in text.lower()
                for kw in ["engineer", "developer", "analyst", "intern", "manager", "trainee", "associate"]
            ):
                found_links.add(full_url)
                job_id = f"custom_{abs(hash(full_url))}"
                jobs.append({
                    "external_job_id": job_id,
                    "title": text,
                    "department": None,
                    "location": "India",
                    "application_url": full_url,
                    "posted_date": None,
                    "description": f"Position at {company_name}: {text}. Visit URL for complete job details.",
                    "ats_provider": "custom",
                })

            if len(jobs) >= 50:
                break

        return jobs
