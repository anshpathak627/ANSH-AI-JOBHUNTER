"""
tests/test_matching.py
Unit tests for MatchingAgent and EligibilityAgent.
"""

import pytest
from agents.matching_agent import MatchingAgent
from agents.eligibility_agent import EligibilityAgent


def test_skills_match_high():
    agent = MatchingAgent()
    job_data = {
        "title": "Software Engineer - Full Stack",
        "description": "Looking for a candidate with strong knowledge in Python, SQL, React, and Node.js with REST API experience.",
        "location": "Noida, India",
        "work_mode": "hybrid",
        "salary_disclosed": False,
    }
    result = agent.calculate_match_score(job_data)
    assert not result["disqualified"]
    assert result["skills_score"] >= 20.0
    assert result["match_score"] >= 65.0


def test_disqualification_cgpa():
    agent = MatchingAgent()
    job_data = {
        "title": "Graduate Trainee",
        "description": "Minimum CGPA of 9.2 is strictly required across all semesters.",
        "location": "Bangalore",
    }
    result = agent.calculate_match_score(job_data)
    assert result["disqualified"] is True
    assert "CGPA" in result["disqualification_reason"]


def test_fresher_eligible():
    agent = MatchingAgent()
    job_data = {
        "title": "Associate Product Analyst",
        "description": "Campus hiring for fresher graduates (0-1 years of experience). Knowledge of SQL and Excel is required.",
        "location": "Gurugram",
    }
    result = agent.calculate_match_score(job_data)
    assert not result["disqualified"]
    assert result["experience_score"] == 15.0


def test_location_india():
    agent = MatchingAgent()
    job_data = {
        "title": "Data Analyst",
        "description": "SQL and Python for business reporting.",
        "location": "Bengaluru, Karnataka, India",
    }
    result = agent.calculate_match_score(job_data)
    assert result["location_score"] >= 8.0
