"""
frontend/pages/2_All_Jobs.py
Job discovery feed, multi-factor filtering, deep match inspection, and tailoring triggers.
"""

import os
import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="All Jobs | Ansh AI JobHunter", page_icon="💼", layout="wide")
st.title("💼 Discovered Opportunities")

# Sidebar Filters
with st.sidebar:
    st.subheader("Filter Opportunities")
    search_query = st.text_input("🔍 Search Title or Company", "")
    location_filter = st.text_input("📍 Location Keyword", "")
    work_mode_filter = st.selectbox("🏢 Work Mode", ["All", "remote", "hybrid", "onsite"])
    min_score = st.slider("⭐ Minimum Match Score", 0, 100, 0, step=5)
    salary_filter = st.slider("💰 Min Disclosed CTC (LPA)", 0, 30, 0)

# Build Query Params
params = {"limit": 100}
if search_query:
    params["title"] = search_query
if location_filter:
    params["location"] = location_filter
if work_mode_filter != "All":
    params["work_mode"] = work_mode_filter
if min_score > 0:
    params["min_score"] = float(min_score)
if salary_filter > 0:
    params["salary_min"] = float(salary_filter)

jobs = []
try:
    resp = requests.get(f"{API_BASE}/api/jobs", params=params, timeout=5)
    if resp.status_code == 200:
        jobs = resp.json()
except Exception as ex:
    st.error(f"Failed to fetch jobs: {ex}")

# Toolbar
col_count, col_export = st.columns([3, 1])
with col_count:
    st.write(f"Showing **{len(jobs)}** open position(s)")
with col_export:
    if jobs:
        df_export = pd.DataFrame(jobs)
        csv_data = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export CSV", data=csv_data, file_name="discovered_jobs.csv", mime="text/csv")

if not jobs:
    st.info("No job openings match current filters. Click 'Trigger Full Scan Now' on Overview to fetch fresh openings.")
else:
    for job in jobs:
        score = job.get("match_score")
        score_text = f"{score:.0f}%" if score is not None else "Unscored"
        score_color = "#16a34a" if (score and score >= 70) else ("#ca8a04" if (score and score >= 40) else "#dc2626")

        salary_str = (
            f"₹{job.get('salary_min') or ''}-{job.get('salary_max') or ''} LPA"
            if job.get("salary_disclosed")
            else "Undisclosed"
        )

        with st.expander(f"{job['title']} — {job['company_name']} | {score_text} Match"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.write(f"**Company:** {job['company_name']}")
                st.write(f"**Location:** {job.get('location') or 'Not specified'}")
            with c2:
                st.write(f"**Work Mode:** {job.get('work_mode', 'unknown').capitalize()}")
                st.write(f"**Compensation:** {salary_str}")
            with c3:
                st.write(f"**Match Fit:** <span style='color:{score_color};font-weight:bold;font-size:1.1rem;'>{score_text}</span>", unsafe_allow_html=True)
                st.write(f"**Posted Date:** {job.get('posted_date', 'Recent')}")
            with c4:
                if job.get("application_url"):
                    st.link_button("🌐 Apply Portal", job["application_url"])

            b_score, b_tailor, b_track = st.columns(3)
            with b_score:
                if st.button("⚖️ Run AI Matcher", key=f"score_{job['id']}"):
                    s_res = requests.post(f"{API_BASE}/api/jobs/{job['id']}/match", timeout=10)
                    if s_res.status_code == 200:
                        st.success(f"Score: {s_res.json().get('match_score')}/100")
                        st.rerun()
                    else:
                        st.error("Scoring failed")
            with b_tailor:
                if st.button("📄 Tailor Resume", key=f"tailor_{job['id']}"):
                    t_res = requests.post(f"{API_BASE}/api/resumes/tailor/{job['id']}", timeout=10)
                    if t_res.status_code == 200:
                        st.success("ATS Resume Tailored! Check Resume Manager.")
                    else:
                        st.error("Tailoring failed")
            with b_track:
                if st.button("📌 Track Application", key=f"track_{job['id']}"):
                    tr_res = requests.post(f"{API_BASE}/api/applications/create-for-job/{job['id']}", timeout=5)
                    if tr_res.status_code == 200:
                        st.success("Added to Application Tracker!")
                    else:
                        st.error("Tracking failed")
