"""
notifications/telegram_notifier.py
Telegram Bot API integration for real-time job and application alerts.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends formatted alerts to Ansh's private Telegram chat."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    async def send_message(self, text: str) -> bool:
        """Send a plain or markdown text message."""
        if not self.bot_token or not self.chat_id or not self.base_url:
            logger.debug("Telegram credentials not configured. Skipping alert.")
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    },
                )
                if resp.status_code == 200:
                    return True
                logger.warning("Telegram API error %d: %s", resp.status_code, resp.text)
                return False
        except Exception as ex:
            logger.warning("Failed to send Telegram notification: %s", ex)
            return False

    async def notify_new_job(self, job: Dict[str, Any], match_score: float) -> bool:
        """Notify Ansh of a newly discovered relevant job."""
        company = job.get("company_name") or "Target Company"
        title = job.get("title") or "Role"
        location = job.get("location") or "India / Remote"
        url = job.get("application_url") or job.get("source_url") or "#"
        salary = f"{job.get('salary_min') or ''}-{job.get('salary_max') or ''} LPA" if job.get("salary_disclosed") else "Undisclosed"

        msg = (
            f"🎯 <b>ANSH AI JOBHUNTER — High Match Discovered!</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Role:</b> {title}\n"
            f"📍 <b>Location:</b> {location}\n"
            f"💰 <b>Salary:</b> {salary}\n"
            f"⭐ <b>Match Score:</b> {match_score:.1f} / 100\n\n"
            f"🔗 <a href='{url}'>View & Apply Here</a>"
        )
        return await self.send_message(msg)

    async def notify_application_submitted(self, application: Dict[str, Any]) -> bool:
        """Notify when an application is successfully submitted."""
        job_title = application.get("job_title", "Position")
        company = application.get("company_name", "Company")
        msg = (
            f"🚀 <b>ANSH AI JOBHUNTER — Application Submitted!</b>\n\n"
            f"✅ Successfully submitted application for <b>{job_title}</b> at <b>{company}</b>.\n"
            f"Status has been updated to <code>SUBMITTED</code>."
        )
        return await self.send_message(msg)

    async def notify_application_failed(self, application: Dict[str, Any], error: str) -> bool:
        """Notify when an automated submission stops or encounters an issue."""
        job_title = application.get("job_title", "Position")
        company = application.get("company_name", "Company")
        msg = (
            f"⚠️ <b>ANSH AI JOBHUNTER — Attention Required</b>\n\n"
            f"Application for <b>{job_title}</b> at <b>{company}</b> paused.\n"
            f"<b>Reason:</b> {error}\n"
            f"Action needed in dashboard."
        )
        return await self.send_message(msg)
