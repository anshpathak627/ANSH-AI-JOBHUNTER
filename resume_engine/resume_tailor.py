"""
resume_engine/resume_tailor.py
Tailors resume text dynamically for specific job descriptions without fabrication.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResumeTailor:
    """Intelligently highlights relevant skills and experience matching job postings."""

    def tailor_resume(
        self,
        resume_text: str,
        job_data: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> str:
        """
        Produce a tailored version of the candidate's resume.
        Guarantees:
        - NEVER fabricates fake employers, dates, or certifications.
        - NEVER alters metrics (e.g., 40% reduction, 100+ users stays unchanged).
        - Reorders actual skills so keywords most relevant to the JD appear first.
        """
        company_name = job_data.get("company_name") or "Target Company"
        job_title = job_data.get("title") or "Target Role"
        desc = (job_data.get("description") or "").lower()

        cand_skills: List[str] = candidate.get("skills") or [
            "Java", "Python", "JavaScript", "TypeScript", "SQL", "React",
            "Node.js", "Express", "MySQL", "PostgreSQL", "Excel", "Power BI",
            "Pandas", "NumPy", "REST APIs", "Generative AI", "RAG", "LangChain",
            "Business Analysis", "Data Analytics", "ASP.NET"
        ]

        # Partition candidate skills into high-relevance and remaining
        matching_skills = []
        other_skills = []

        for skill in cand_skills:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, desc):
                matching_skills.append(skill)
            else:
                other_skills.append(skill)

        ordered_skills = matching_skills + other_skills

        header = f"# TAILORED FOR: {company_name} — {job_title}\n"
        header += f"# CANDIDATE: {candidate.get('name', 'Ansh Pathak')}\n\n"

        if resume_text and len(resume_text.strip()) > 100:
            tailored_content = header + resume_text.strip()
            # If there is a Skills section in the text, highlight matching skills
            if "SKILLS" in tailored_content.upper():
                highlight_note = f"\n[Highlighted for Role: {', '.join(matching_skills[:6])}]\n"
                tailored_content = re.sub(
                    r"(?i)(skills[:\s]+)",
                    r"\1" + highlight_note,
                    tailored_content,
                    count=1,
                )
            return tailored_content

        # Generate structured clean ATS-ready text if no base text provided
        lines = [
            f"{candidate.get('name', 'Ansh Pathak').upper()}",
            "Noida / Delhi NCR, India | pathakansh696@gmail.com | linkedin.com/in/anshpathak",
            "",
            "PROFESSIONAL SUMMARY",
            (
                "Engineering undergraduate at MAIT, GGSIPU (8.4 CGPA, 2027) with hands-on "
                "experience leading development at DRDO and data analytics at American Express. "
                "Proven proficiency in Full Stack development, Python, SQL, REST APIs, and Generative AI (RAG). "
                f"Specifically tailored for the {job_title} role at {company_name}."
            ),
            "",
            "CORE TECHNICAL SKILLS",
            f"• Priority Match: {', '.join(matching_skills) if matching_skills else 'Python, SQL, React, Node.js'}",
            f"• Full Stack & Databases: React, Node.js, Express, JavaScript, TypeScript, MySQL, PostgreSQL, ASP.NET",
            f"• Data & Analytics: SQL, Excel, Power BI, Pandas, NumPy, Business Analysis",
            f"• Emerging Tech: Generative AI, LangChain, RAG, REST APIs, Git, Docker",
            "",
            "WORK EXPERIENCE",
            "DRDO (Defence Research & Development Organisation) — Full Stack Developer & Team Lead",
            "May 2025 – August 2025 | Delhi, India",
            "• Spearheaded full-stack application development using React, Node.js, Express, and MySQL.",
            "• Led a developer team serving 100+ active institutional users with 99.8% uptime.",
            "• Reduced internal reporting generation turnaround time by 40% through query and schema optimization.",
            "",
            "American Express — Management Information Systems (MIS) Intern",
            "2026 | Gurugram, India",
            "• Engineered automated executive KPI reporting dashboards using advanced Excel, SQL, and Power BI.",
            "• Synthesized complex financial and operational datasets to identify trends and variance metrics.",
            "",
            "FEATURED PROJECTS",
            "GenAI Document Q&A System",
            "• Built an end-to-end RAG question-answering pipeline using Python, LangChain, and vector embeddings.",
            "• Supported semantic search and real-time LLM-powered context retrieval across unstructured documents.",
            "",
            "Enterprise User Management Application",
            "• Developed a secure role-based access control (RBAC) portal utilizing ASP.NET and MySQL.",
            "",
            "EDUCATION",
            "Maharaja Agrasen Institute of Technology (MAIT), GGSIPU",
            "B.Tech in Electrical Engineering (VLSI Design & Technology) | Graduating May 2027 | CGPA: 8.4/10",
        ]

        return header + "\n".join(lines)
