"""
agents/matching_agent.py
Match scoring engine with 100-point weighted model and Ollama LLM support.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import aiohttp

from agents.eligibility_agent import EligibilityAgent

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE = {
    "name": "Ansh Pathak",
    "college": "Maharaja Agrasen Institute of Technology (MAIT), GGSIPU",
    "degree": "B.Tech",
    "branch": "Electrical Engineering (VLSI Design & Technology)",
    "cgpa": 8.4,
    "grad_year": 2027,
    "skills": [
        "Java", "Python", "JavaScript", "TypeScript", "SQL", "React",
        "Node.js", "Express", "MySQL", "PostgreSQL", "Excel", "Power BI",
        "Pandas", "NumPy", "REST APIs", "Generative AI", "RAG", "LangChain",
        "Business Analysis", "Data Analytics", "ASP.NET", "Git", "Docker",
        "Problem Solving", "Data Structures"
    ],
    "experience_summary": (
        "DRDO Full Stack Developer & Team Lead (React, Node.js, Express, MySQL, 100+ users, "
        "40% reduction in reporting time); American Express MIS Intern (Excel, SQL, Power BI, KPI dashboards)"
    ),
    "projects": [
        "GenAI Document Q&A (Python, LangChain, LLM APIs, RAG, vector embeddings)",
        "User Management Application (ASP.NET, MySQL, REST API)"
    ],
}


class MatchingAgent:
    """Evaluates job relevance, skills overlap, and computes an objective 0-100 match score."""

    def __init__(self):
        self.eligibility = EligibilityAgent()

    def calculate_match_score(self, job_data: Dict[str, Any], candidate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Rule-based keyword match scoring algorithm.

        Weights:
        - Skills match: 30%
        - Education + Graduation eligibility: 20%
        - Experience match: 15%
        - Role relevance: 15%
        - Location + work authorization: 10%
        - Salary & preferences: 10%
        """
        cand = candidate or DEFAULT_CANDIDATE
        cand_skills = [s.lower() for s in cand.get("skills", [])]

        title = (job_data.get("title") or "").strip()
        desc = (job_data.get("description") or "").lower()
        title_lower = title.lower()

        match_reasons: List[str] = []
        missing_requirements: List[str] = []

        # 0. Check Hard Eligibility
        is_eligible, disq_reasons = self.eligibility.check_eligibility(job_data, cand)
        if not is_eligible:
            return {
                "match_score": 0.0,
                "skills_score": 0.0,
                "education_score": 0.0,
                "experience_score": 0.0,
                "role_score": 0.0,
                "location_score": 0.0,
                "salary_score": 0.0,
                "match_reasons": [],
                "missing_requirements": disq_reasons,
                "disqualified": True,
                "disqualification_reason": "; ".join(disq_reasons),
            }

        # 1. Skills Score (0 - 30)
        found_skills = []
        for skill in cand_skills:
            # Word boundary matching
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, desc) or re.search(pattern, title_lower):
                found_skills.append(skill.title())

        # If description is short (e.g. from custom scraper), use title matching
        if len(desc) < 150:
            skills_score = 20.0
            match_reasons.append("Job description summarized; default strong profile match assumed.")
        else:
            overlap_count = len(found_skills)
            if overlap_count >= 6:
                skills_score = 30.0
            elif overlap_count >= 4:
                skills_score = 25.0
            elif overlap_count >= 2:
                skills_score = 18.0
            elif overlap_count == 1:
                skills_score = 12.0
            else:
                skills_score = 8.0

            if found_skills:
                match_reasons.append(f"Matching candidate skills found: {', '.join(found_skills[:5])}")

        # 2. Education Score (0 - 20)
        education_score = 15.0
        if any(deg in desc for deg in ["b.tech", "btech", "b.e", "bachelor", "engineering", "undergraduate"]):
            education_score += 5.0
            match_reasons.append("B.Tech / Engineering degree recognized.")
        if any(y in desc for y in ["2026", "2027", "2025", "fresh", "campus", "graduate", "trainee"]):
            education_score = min(20.0, education_score + 3.0)
            match_reasons.append("Target graduation batch matches candidate timeline.")

        # 3. Experience Score (0 - 15)
        experience_score = 15.0
        if any(k in desc or k in title_lower for k in ["intern", "fresher", "entry level", "graduate trainee", "campus"]):
            experience_score = 15.0
            match_reasons.append("Entry-level / Internship role aligns perfectly with candidate status.")
        elif any(k in desc for k in ["1 year", "2 years", "1-2 years", "0-2 years"]):
            experience_score = 13.0
            match_reasons.append("Experience requirement (0-2 years) fully matched by internship credentials.")
        else:
            experience_score = 12.0

        # 4. Role Relevance Score (0 - 15)
        role_score = 10.0
        high_priority_roles = [
            "business analyst", "data analyst", "product analyst", "apm",
            "software engineer", "sde", "full stack", "backend", "ai engineer", "genai"
        ]
        if any(r in title_lower for r in high_priority_roles):
            role_score = 15.0
            match_reasons.append(f"Title '{title}' is an exact primary career target.")
        elif any(k in title_lower for k in ["analyst", "developer", "engineer", "trainee"]):
            role_score = 12.0
            match_reasons.append(f"Role title '{title}' is highly relevant.")

        # 5. Location Score (0 - 10)
        location = str(job_data.get("location") or "").lower()
        location_score = 5.0
        if "remote" in location or job_data.get("work_mode") == "remote":
            location_score = 10.0
            match_reasons.append("Remote position — ideal flexibility.")
        elif any(c in location for c in ["noida", "gurugram", "gurgaon", "delhi"]):
            location_score = 10.0
            match_reasons.append("Prime local NCR location (Noida / Gurugram / Delhi).")
        elif any(c in location for c in ["bangalore", "bengaluru", "hyderabad", "pune", "mumbai"]):
            location_score = 9.0
            match_reasons.append("Major Indian tech hub location.")
        elif "india" in location or str(job_data.get("country", "")).lower() == "india":
            location_score = 8.0
            match_reasons.append("India-based position.")
        else:
            location_score = 5.0

        # 6. Salary Score (0 - 10)
        salary_min = job_data.get("salary_min")
        salary_max = job_data.get("salary_max")
        salary_disclosed = job_data.get("salary_disclosed", False)

        salary_score = 5.0
        if salary_disclosed and (salary_min or salary_max):
            val = salary_max or salary_min or 0
            if val >= 10.0:
                salary_score = 10.0
                match_reasons.append(f"High compensation package disclosed (>10 LPA: ~{val} LPA).")
            elif val >= 7.0:
                salary_score = 8.0
                match_reasons.append(f"Competitive compensation package (~{val} LPA).")
            elif val >= 4.0:
                salary_score = 6.0
            else:
                salary_score = 3.0
        else:
            salary_score = 6.0  # Undisclosed standard industry package

        total_score = round(
            skills_score + education_score + experience_score + role_score + location_score + salary_score,
            1,
        )
        total_score = min(100.0, max(0.0, total_score))

        return {
            "match_score": total_score,
            "skills_score": skills_score,
            "education_score": education_score,
            "experience_score": experience_score,
            "role_score": role_score,
            "location_score": location_score,
            "salary_score": salary_score,
            "match_reasons": match_reasons,
            "missing_requirements": missing_requirements,
            "disqualified": False,
            "disqualification_reason": None,
        }

    async def calculate_match_score_ollama(
        self,
        job_data: Dict[str, Any],
        candidate: Dict[str, Any],
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.2",
    ) -> Dict[str, Any]:
        """
        Evaluate match score via local Ollama LLM, falling back to rule-based method on error.
        """
        fallback_result = self.calculate_match_score(job_data, candidate)
        prompt = (
            f"You are an ATS Matchmaker. Evaluate candidate fit (0-100 score):\n"
            f"Candidate: {json.dumps(candidate)}\n"
            f"Job: Title: {job_data.get('title')}, Location: {job_data.get('location')}, "
            f"Description: {job_data.get('description', '')[:1000]}\n\n"
            f"Respond ONLY in valid JSON with keys: match_score (float), skills_score (float 0-30), "
            f"education_score (float 0-20), experience_score (float 0-15), role_score (float 0-15), "
            f"location_score (float 0-10), salary_score (float 0-10), match_reasons (list of strings)."
        )

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                payload = {
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                }
                async with session.post(f"{ollama_base_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("response", "")
                        parsed = json.loads(response_text)
                        parsed["disqualified"] = fallback_result["disqualified"]
                        parsed["disqualification_reason"] = fallback_result["disqualification_reason"]
                        return parsed
        except Exception as ex:
            logger.debug("Ollama matching unavailable, using rule-based scoring: %s", ex)

        return fallback_result
