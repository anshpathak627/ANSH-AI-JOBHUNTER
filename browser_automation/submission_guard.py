"""
browser_automation/submission_guard.py
Strict safety checks preventing unauthorized, inaccurate, or unsafe form submissions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class SubmissionGuard:
    """Non-negotiable safety rules before any browser automation action."""

    @staticmethod
    def check_safe_to_submit(
        job_data: Dict[str, Any],
        candidate: Dict[str, Any],
        mode: str,
        approved_by_user: bool = False,
        today_submissions_count: int = 0,
        max_daily_limit: int = 10,
    ) -> Tuple[bool, List[str]]:
        """
        Verify that all preconditions for automated submission are strictly satisfied.
        """
        reasons_not_safe: List[str] = []

        # 1. Mode check
        if mode.upper() not in ["APPROVED", "APPROVED_AUTO_SUBMIT"]:
            reasons_not_safe.append(f"Current mode is '{mode}'. Automatic submission is restricted to APPROVED mode.")

        # 2. Explicit approval check
        if not approved_by_user:
            reasons_not_safe.append("Job has not been explicitly approved for submission by user.")

        # 3. Throttling cap
        if today_submissions_count >= max_daily_limit:
            reasons_not_safe.append(f"Daily submission limit reached ({today_submissions_count}/{max_daily_limit}).")

        # 4. Mandatory ATS platform whitelist
        ats = str(job_data.get("ats_provider", "")).lower()
        if ats in ["workday", "taleo", "icims", "successfactors"]:
            reasons_not_safe.append(f"Portal '{ats}' requires manual review/login; automated submit disabled.")

        # 5. Candidate profile completeness
        required_fields = ["name", "email", "phone"]
        for rf in required_fields:
            if not candidate.get(rf):
                reasons_not_safe.append(f"Candidate profile missing mandatory field: {rf}")

        is_safe = len(reasons_not_safe) == 0
        return is_safe, reasons_not_safe
