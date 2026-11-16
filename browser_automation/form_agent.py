"""
browser_automation/form_agent.py
Playwright browser automation for job application filling and submission.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FormAgent:
    """Automates form interaction in DISCOVERY, PREPARE, or APPROVED modes."""

    def __init__(self, mode: str = "DISCOVERY"):
        self.mode = mode.upper()

    async def fill_application(
        self,
        job_url: str,
        candidate: Dict[str, Any],
        resume_path: Optional[str] = None,
        screenshots_dir: str = "data/screenshots",
    ) -> Dict[str, Any]:
        """
        Navigate to application portal, identify fields, fill profile data,
        and either pause for user review (PREPARE) or submit (APPROVED).
        """
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshots_dir, f"app_{abs(hash(job_url))}.png")

        result = {
            "success": False,
            "fields_filled": [],
            "stopped_reason": None,
            "screenshot_path": None,
        }

        if self.mode == "DISCOVERY":
            result["stopped_reason"] = "DISCOVERY mode active. Form filling is disabled."
            return result

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            result["stopped_reason"] = "Playwright is not installed in the environment."
            return result

        try:
            async with async_playwright() as p:
                # In PREPARE mode, run with visible browser if desktop allows, or headless
                headless = (self.mode != "PREPARE")
                browser = await p.chromium.launch(headless=headless)
                page = await browser.new_page()

                try:
                    await page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                except Exception as ex:
                    result["stopped_reason"] = f"Failed to load URL: {str(ex)[:80]}"
                    await browser.close()
                    return result

                # Check for CAPTCHA
                content = await page.content()
                if any(k in content.lower() for k in ["recaptcha", "hcaptcha", "cf-turnstile", "g-recaptcha"]):
                    await page.screenshot(path=screenshot_path)
                    result["stopped_reason"] = "CAPTCHA / Security Challenge detected. Manual submission required."
                    result["screenshot_path"] = screenshot_path
                    await browser.close()
                    return result

                # Detect and fill common input fields
                filled: List[str] = []
                name = candidate.get("name", "Ansh Pathak")
                parts = name.split()
                first_name = parts[0] if parts else "Ansh"
                last_name = parts[-1] if len(parts) > 1 else "Pathak"

                # First Name / Full Name
                if await self._try_fill(page, ["first_name", "firstname", "first-name", "fname"], first_name):
                    filled.append("first_name")
                    if await self._try_fill(page, ["last_name", "lastname", "last-name", "lname"], last_name):
                        filled.append("last_name")
                else:
                    if await self._try_fill(page, ["name", "full_name", "fullname", "applicant_name"], name):
                        filled.append("full_name")

                # Email
                if await self._try_fill(page, ["email", "e-mail", "email_address"], candidate.get("email", "")):
                    filled.append("email")

                # Phone
                if await self._try_fill(page, ["phone", "tel", "mobile", "phone_number"], candidate.get("phone", "")):
                    filled.append("phone")

                # LinkedIn
                if candidate.get("linkedin_url"):
                    if await self._try_fill(page, ["linkedin", "linkedin_profile", "urls[LinkedIn]"], candidate["linkedin_url"]):
                        filled.append("linkedin")

                # GitHub
                if candidate.get("github_url"):
                    if await self._try_fill(page, ["github", "github_profile", "urls[GitHub]"], candidate["github_url"]):
                        filled.append("github")

                # Resume file upload
                if resume_path and os.path.exists(resume_path):
                    try:
                        file_input = await page.query_selector("input[type='file']")
                        if file_input:
                            await file_input.set_input_files(resume_path)
                            filled.append("resume_file")
                    except Exception as ex:
                        logger.debug("Resume file upload selector failed: %s", ex)

                # Capture screenshot
                await page.screenshot(path=screenshot_path)
                result["screenshot_path"] = screenshot_path
                result["fields_filled"] = filled

                if self.mode == "PREPARE":
                    result["success"] = True
                    result["stopped_reason"] = "PREPARE mode: Form populated and preserved for manual review."
                elif self.mode in ["APPROVED", "APPROVED_AUTO_SUBMIT"]:
                    # Attempt submit
                    submit_button = await page.query_selector("button[type='submit'], input[type='submit']")
                    if submit_button:
                        await submit_button.click()
                        await page.wait_for_timeout(3000)
                        await page.screenshot(path=screenshot_path)
                        result["success"] = True
                    else:
                        result["stopped_reason"] = "Could not identify primary submit button."

                await browser.close()
                return result

        except Exception as ex:
            logger.error("Browser automation error: %s", ex)
            result["stopped_reason"] = f"Automation runtime exception: {str(ex)[:100]}"
            return result

    async def _try_fill(self, page, field_hints: List[str], value: str) -> bool:
        """Try filling an input matching any of the name/id/placeholder hints."""
        if not value:
            return False
        for hint in field_hints:
            selector = (
                f"input[name*='{hint}' i], input[id*='{hint}' i], input[placeholder*='{hint}' i]"
            )
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    await el.fill(value)
                    return True
            except Exception:
                continue
        return False
