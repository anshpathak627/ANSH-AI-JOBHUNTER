"""
discovery/job_filter.py
Title relevance, eligibility checks, salary extraction, and location parsing.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

TARGET_JOB_TITLES = [
    # Analyst roles
    "business analyst",
    "data analyst",
    "product analyst",
    "operations analyst",
    "strategy analyst",
    "technology analyst",
    "consulting analyst",
    "financial analyst",
    "risk analyst",
    "implementation analyst",
    "graduate analyst",
    "junior analyst",
    "associate analyst",
    "bi analyst",
    "analytics",

    # Product & Management roles
    "associate product manager",
    "apm",
    "product manager",
    "management trainee",
    "graduate trainee",
    "business operations",

    # Engineering / Developer roles
    "software engineer",
    "software developer",
    "sde",
    "sde 1",
    "sde-1",
    "sde i",
    "sde-i",
    "full stack",
    "fullstack",
    "backend developer",
    "backend engineer",
    "frontend developer",
    "frontend engineer",
    "graduate engineer trainee",
    "get",
    "junior software",
    "junior engineer",
    "developer trainee",
    "systems engineer",
    "application developer",

    # AI / ML roles
    "ai engineer",
    "genai",
    "generative ai",
    "machine learning",
    "ml engineer",
    "nlp",

    # Entry level & Internships
    "intern",
    "internship",
    "graduate",
    "fresher",
    "entry level",
    "new grad",
    "campus",
]

ELIGIBILITY_RULES = {
    "grad_year_range": (2024, 2027),
    "max_experience_years": 2.0,
    "target_cgpa": 8.4,
    "min_cgpa": None,
    "accepted_degrees": ["b.tech", "btech", "b.e", "be", "bachelor", "engineering"],
}


def is_relevant_title(title: str) -> bool:
    """Return True if the title matches target job keywords."""
    if not title:
        return False
    title_lower = title.lower()

    # Exclude clearly senior/leadership roles
    senior_exclusions = [
        "principal", "director", "staff engineer", "vp ", "vice president",
        "engineering manager", "head of", "architect", "lead architect"
    ]
    # Check if senior exclusions are present and no 'intern' or 'trainee' override
    for excl in senior_exclusions:
        if excl in title_lower and not any(k in title_lower for k in ["intern", "trainee", "associate"]):
            return False

    return any(keyword in title_lower for keyword in TARGET_JOB_TITLES)


def check_eligibility(job_data: dict, candidate: dict) -> Tuple[bool, str]:
    """
    Check if the candidate is eligible for the position.
    Default to inclusive (eligible) if criteria are not explicitly restrictive.
    """
    title = (job_data.get("title") or "").lower()
    desc = (job_data.get("description") or "").lower()

    # 1. Experience check
    # Look for "X+ years", "minimum X years", "X-Y years"
    exp_matches = re.findall(r"(\d+)\s*(?:\+|to|-)\s*(\d*)\s*(?:years|yrs)", desc)
    for m in exp_matches:
        try:
            min_exp = float(m[0])
            if min_exp > 3.0:
                # Unless it also mentions entry level or campus
                if not any(k in desc or k in title for k in ["campus", "intern", "entry level", "fresher", "new grad"]):
                    return False, f"Requires {min_exp}+ years of experience."
        except ValueError:
            pass

    # 2. Graduation year check
    grad_year_pattern = re.findall(r"\b(20[12]\d)\b(?:\s*(?:batch|passout|graduates|pass out))?", desc)
    # If explicit grad year mentioned, check if 2027 or 2026 or 2025
    if any(y in desc for y in ["2022 batch", "2023 batch", "2021 batch"]) and not any(
        y in desc for y in ["2026", "2027", "2025"]
    ):
        return False, "Restricted to earlier graduating batches."

    # 3. Explicit CGPA check
    cgpa_match = re.search(r"(?:cgpa|gpa)\s*(?:of|>=|above|minimum|min)?\s*(\d(?:\.\d+)?)", desc)
    if cgpa_match:
        try:
            req_cgpa = float(cgpa_match.group(1))
            cand_cgpa = candidate.get("cgpa", 8.4)
            if req_cgpa > 8.5 and cand_cgpa < req_cgpa:
                return False, f"Requires minimum {req_cgpa} CGPA (Candidate: {cand_cgpa})."
        except ValueError:
            pass

    return True, "Meets initial eligibility criteria."


def extract_salary_info(description: str, title: str) -> Dict[str, Any]:
    """Extract salary figures (LPA / INR / USD) via regex."""
    text = f"{title}\n{description}"
    result = {
        "min_lpa": None,
        "max_lpa": None,
        "currency": "INR",
        "disclosed": False,
        "raw_text": None,
    }

    # Pattern for Lakhs / LPA e.g. "10-15 LPA", "12 LPA", "8 to 14 lakhs"
    lpa_pattern = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:lpa|lakhs?|lac|lacs)",
        text,
        re.IGNORECASE,
    )
    if lpa_pattern:
        try:
            g1 = float(lpa_pattern.group(1))
            g2 = float(lpa_pattern.group(2)) if lpa_pattern.group(2) else g1
            result["min_lpa"] = min(g1, g2)
            result["max_lpa"] = max(g1, g2)
            result["disclosed"] = True
            result["raw_text"] = lpa_pattern.group(0)
            return result
        except Exception:
            pass

    # Pattern for INR amounts e.g. ₹10,00,000 or Rs. 800000
    inr_pattern = re.search(
        r"(?:₹|rs\.?|inr)\s*([\d,]+)(?:\s*(?:-|to)\s*([\d,]+))?",
        text,
        re.IGNORECASE,
    )
    if inr_pattern:
        try:
            val1 = float(inr_pattern.group(1).replace(",", ""))
            val2 = float(inr_pattern.group(2).replace(",", "")) if inr_pattern.group(2) else val1
            if val1 >= 100000:
                result["min_lpa"] = round(min(val1, val2) / 100000.0, 2)
                result["max_lpa"] = round(max(val1, val2) / 100000.0, 2)
                result["disclosed"] = True
                result["raw_text"] = inr_pattern.group(0)
                return result
        except Exception:
            pass

    return result


def parse_location(location_str: str) -> Dict[str, Any]:
    """Parse city, country, work mode, and India eligibility."""
    loc = (location_str or "").strip()
    loc_lower = loc.lower()

    work_mode = "unknown"
    if "remote" in loc_lower:
        work_mode = "remote"
    elif "hybrid" in loc_lower:
        work_mode = "hybrid"
    elif any(city in loc_lower for city in ["noida", "gurugram", "gurgaon", "delhi", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "chennai"]):
        work_mode = "onsite"

    # Indian locations check
    india_cities = [
        "noida", "gurugram", "gurgaon", "delhi", "new delhi", "ncr",
        "bangalore", "bengaluru", "hyderabad", "pune", "mumbai",
        "chennai", "kolkata", "ahmedabad", "chandigarh", "india"
    ]
    india_eligible = any(city in loc_lower for city in india_cities) or ("remote" in loc_lower)
    international_remote_ok = "remote" in loc_lower

    city = None
    for c in ["Noida", "Gurugram", "Delhi", "Bangalore", "Bengaluru", "Hyderabad", "Pune", "Mumbai", "Chennai"]:
        if c.lower() in loc_lower:
            city = c
            break

    country = "India" if india_eligible else "International"

    return {
        "city": city,
        "country": country,
        "work_mode": work_mode,
        "india_eligible": india_eligible,
        "international_remote_india_ok": international_remote_ok,
    }
