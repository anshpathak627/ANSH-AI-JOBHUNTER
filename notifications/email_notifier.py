"""
notifications/email_notifier.py
SMTP-based email notifier for dispatching job search updates.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Dispatches email digests and instant alerts via SMTP."""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        recipient: Optional[str] = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipient = recipient or username

    def send_email_sync(self, subject: str, html_content: str) -> bool:
        """Send email via smtplib (synchronous worker)."""
        if not self.username or not self.password or not self.recipient:
            logger.debug("Email credentials incomplete. Skipping email alert.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Ansh AI JobHunter <{self.username}>"
            msg["To"] = self.recipient
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, [self.recipient], msg.as_string())
            return True
        except Exception as ex:
            logger.warning("SMTP email delivery failed: %s", ex)
            return False

    async def send_email(self, subject: str, html_content: str) -> bool:
        """Async wrapper for SMTP delivery."""
        return await asyncio.to_thread(self.send_email_sync, subject, html_content)

    async def notify_new_job(self, job: Dict[str, Any], match_score: float) -> bool:
        """Send formatted HTML email for high match jobs."""
        subject = f"🎯 Job Alert: {job.get('title')} at {job.get('company_name')} ({match_score:.0f}% Match)"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #2563eb; color: white; padding: 16px; border-radius: 8px;">
                <h2 style="margin: 0;">ANSH AI JOBHUNTER — High Match Role</h2>
            </div>
            <div style="padding: 16px; border: 1px solid #e5e7eb; border-radius: 8px; margin-top: 12px;">
                <p><strong>Company:</strong> {job.get('company_name')}</p>
                <p><strong>Position:</strong> {job.get('title')}</p>
                <p><strong>Location:</strong> {job.get('location')}</p>
                <p><strong>Match Score:</strong> <span style="color: #16a34a; font-weight: bold;">{match_score:.1f} / 100</span></p>
                <p><a href="{job.get('application_url')}" style="background-color: #2563eb; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">View & Apply</a></p>
            </div>
        </body>
        </html>
        """
        return await self.send_email(subject, html)
