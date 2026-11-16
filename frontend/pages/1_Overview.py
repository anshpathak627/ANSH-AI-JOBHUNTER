"""
frontend/pages/1_Overview.py
System overview metrics, pipeline charts, and quick triggers.
"""

import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Overview | Ansh AI JobHunter", page_icon="📊", layout="wide")
st.title("📊 Mission Control & Analytics")

# Quick Scan Action & Auto-refresh
col_top_left, col_top_right = st.columns([3, 1])
with col_top_right:
    if st.button("🔄 Scan All Employers Now", type="primary", use_container_width=True):
        try:
            r = requests.post(f"{API_BASE}/api/discovery/scan", timeout=3)
            if r.status_code == 200:
                st.toast("Discovery cycle launched in background!", icon="🚀")
            else:
                st.error("Scan launch failed.")
        except Exception as ex:
            st.error(f"Backend offline: {ex}")

# Metrics Row 1
m1, m2, m3, m4 = st.columns(4)

total_jobs = 0
eligible_jobs = 0
high_match = 0
above_10lpa = 0

try:
    s = requests.get(f"{API_BASE}/api/jobs/stats/summary", timeout=3).json()
    total_jobs = s.get("total_jobs", 0)
    eligible_jobs = s.get("eligible_jobs", 0)
    high_match = s.get("high_match_jobs", 0)
    above_10lpa = s.get("above_10_lpa_jobs", 0)
except Exception:
    pass

with m1:
    st.metric("Total Jobs Discovered", total_jobs)
with m2:
    st.metric("Eligible Roles Evaluated", eligible_jobs)
with m3:
    st.metric("Top Matches (≥70%)", high_match)
with m4:
    st.metric("≥10 LPA Packages", above_10lpa)

# Metrics Row 2
m5, m6, m7, m8 = st.columns(4)
apps_prepared = 0
apps_submitted = 0
interviews = 0
rejections = 0

status_counts = {
    "DISCOVERED": 0, "MATCHED": 0, "PREPARED": 0,
    "PENDING_APPROVAL": 0, "SUBMITTED": 0, "CONFIRMED": 0, "REJECTED": 0
}

try:
    apps = requests.get(f"{API_BASE}/api/applications", timeout=3).json()
    for app in apps:
        st_val = app.get("status", "DISCOVERED")
        status_counts[st_val] = status_counts.get(st_val, 0) + 1

    apps_prepared = status_counts.get("PREPARED", 0)
    apps_submitted = status_counts.get("SUBMITTED", 0) + status_counts.get("CONFIRMED", 0)
    rejections = status_counts.get("REJECTED", 0)
except Exception:
    pass

with m5:
    st.metric("Applications Prepared", apps_prepared)
with m6:
    st.metric("Applications Submitted", apps_submitted)
with m7:
    st.metric("Interviews Scheduled", interviews)
with m8:
    st.metric("Rejections Logged", rejections)

st.markdown("---")

# Visual Pipeline
col_chart, col_activity = st.columns([1, 1])

with col_chart:
    st.subheader("Application Pipeline Distribution")
    chart_data = {
        "Discovered": status_counts.get("DISCOVERED", 0),
        "Matched": status_counts.get("MATCHED", 0),
        "Prepared": status_counts.get("PREPARED", 0),
        "Pending Approval": status_counts.get("PENDING_APPROVAL", 0),
        "Submitted": status_counts.get("SUBMITTED", 0),
        "Confirmed": status_counts.get("CONFIRMED", 0),
    }
    st.bar_chart(chart_data)

with col_activity:
    st.subheader("Recent System Events")
    try:
        logs = requests.get(f"{API_BASE}/api/discovery/logs?limit=8", timeout=3).json()
        if logs:
            for l in logs:
                level_icon = "🔵" if l["level"] == "info" else ("🟡" if l["level"] == "warning" else "🔴")
                st.caption(f"{level_icon} **{l.get('event_type')}** — {l.get('message')}")
        else:
            st.info("No logs recorded yet. Start a discovery scan to populate logs.")
    except Exception:
        st.caption("Unable to fetch activity logs.")
