"""
agents/eligibility_agent.py
Rule-based eligibility evaluation agent.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


class EligibilityAgent:
    """Evaluates whether Ansh Pathak meets the hard eligibility constraints for a role."""

    def __init__(self, default_cgpa: float = 8.4, grad_year: int = 2027):
        self.default_cgpa = default_cgpa
        self.grad_year = grad_year

    def check_eligibility(self, job_data: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check hard constraints. Returns (eligible, disqualification_reasons).
        Be inclusive by default.
        """
        reasons: List[str] = []
        desc = (job_data.get("description") or "").lower()
        title = (job_data.get("title") or "").lower()
        cand_cgpa = float(candidate.get("cgpa") or self.default_cgpa)

        # 1. Experience check
        exp_matches = re.findall(r"(\d+)\s*(?:\+|to|-)\s*(\d*)\s*(?:years|yrs)", desc)
        for m in exp_matches:
            try:
                min_exp = float(m[0])
                if min_exp > 3.0:
                    # Allow exceptions for internship/fresher mentions
                    if not any(k in desc or k in title for k in ["intern", "campus", "fresher", "trainee", "entry level"]):
                        reasons.append(f"Requires {min_exp}+ years of experience.")
                        break
            except ValueError:
                pass

        # 2. CGPA check
        cgpa_match = re.search(r"(?:cgpa|gpa)\s*(?:of|>=|above|minimum|min)?\s*(\d(?:\.\d+)?)", desc)
        if cgpa_match:
            try:
                req_cgpa = float(cgpa_match.group(1))
                if req_cgpa > 8.5 and cand_cgpa < req_cgpa:
                    reasons.append(f"Requires minimum CGPA {req_cgpa} (Candidate has {cand_cgpa}).")
            except ValueError:
                pass

        # 3. Restrictive degree check
        # Only disqualify if strictly mentions "only CS/IT branches" or excludes electrical
        if "only computer science" in desc or "only cse" in desc:
            if "electrical" not in desc and "circuital" not in desc and "any branch" not in desc:
                reasons.append("Restricted strictly to Computer Science majors only.")

        # 4. Incompatible graduation batch
        past_batches = ["2020 batch", "2021 batch", "2022 batch", "2023 batch"]
        if any(b in desc for b in past_batches) and not any(b in desc for b in ["2025", "2026", "2027"]):
            reasons.append("Job is targeted exclusively to earlier graduation batches.")

        is_eligible = len(reasons) == 0
        return is_eligible, reasons
