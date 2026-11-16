"""
frontend/streamlit_app.py
Main entry point for ANSH AI JOBHUNTER Streamlit UI.
"""

import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Ansh AI JobHunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullseye.png", width=64)
    st.title("ANSH AI JOBHUNTER")
    st.caption("Personal Autonomous Job Discovery & Application Engine")

    # API Health Check
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=2)
        if resp.status_code == 200:
            st.success("● Backend API Online (Port 8000)")
        else:
            st.warning("Backend API Warning")
    except Exception:
        st.error("● Backend API Offline (Run backend/main.py)")

    st.markdown("---")
    st.subheader("Candidate Quick View")
    st.write("**Name:** Ansh Pathak")
    st.write("**College:** MAIT, GGSIPU")
    st.write("**Degree:** B.Tech (EE — VLSI)")
    st.write("**Batch:** 2027 | **CGPA:** 8.4")

    st.markdown("---")
    st.caption("v1.0.0 • Developed for Ansh Pathak")

# Main Page Greeting
st.markdown("<div class='main-header'>🎯 Welcome to ANSH AI JOBHUNTER</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>Personal autonomous AI agent that tracks corporate career portals, matches opportunities, tailors ATS resumes, and assists application submissions.</div>",
    unsafe_allow_html=True,
)

# Fetch quick stats
col1, col2, col3, col4 = st.columns(4)
stats = {"total_jobs": 0, "eligible_jobs": 0, "high_match_jobs": 0, "above_10_lpa_jobs": 0}

try:
    s_resp = requests.get(f"{API_BASE}/api/jobs/stats/summary", timeout=3)
    if s_resp.status_code == 200:
        stats = s_resp.json()
except Exception:
    pass

with col1:
    st.metric("Total Jobs Discovered", stats.get("total_jobs", 0))
with col2:
    st.metric("Eligible Openings", stats.get("eligible_jobs", 0))
with col3:
    st.metric("High Matches (≥70%)", stats.get("high_match_jobs", 0))
with col4:
    st.metric("10+ LPA Compensation", stats.get("above_10_lpa_jobs", 0))

st.markdown("---")

# Quick Action Banner
c_left, c_right = st.columns([3, 1])
with c_left:
    st.info("💡 **Quick Navigation:** Use the sidebar pages to browse discovered jobs, tailor resumes, manage application states, or configure automated scrapers.")
with c_right:
    if st.button("🚀 Trigger Full Scan Now", use_container_width=True, type="primary"):
        try:
            scan_resp = requests.post(f"{API_BASE}/api/discovery/scan", timeout=3)
            if scan_resp.status_code == 200:
                st.success("Discovery scan started in background!")
            else:
                st.error("Failed to start scan.")
        except Exception as ex:
            st.error(f"Cannot connect to API: {ex}")

# Overview Highlights
st.subheader("Key Platform Capabilities")
p1, p2, p3 = st.columns(3)
with p1:
    st.markdown("""
    #### 🔍 Multi-Portal Discovery
    - 70+ Curated Employers
    - Greenhouse, Lever, Ashby APIs
    - Custom Enterprise Scrapers
    - No third-party API costs
    """)
with p2:
    st.markdown("""
    #### ⚖️ Precision Matching
    - 100-Point Weighted Scoring
    - Zero Hallucination Guarantee
    - Grad Year & CGPA Verification
    - Optional Local Ollama LLM
    """)
with p3:
    st.markdown("""
    #### 📄 Tailoring & Protection
    - ReportLab ATS PDF Engine
    - Never Fabricates Credentials
    - Strict Submission Guard Mode
    - Real-time Telegram/Email Alerts
    """)
