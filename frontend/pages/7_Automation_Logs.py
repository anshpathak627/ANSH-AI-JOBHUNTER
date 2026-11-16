"""
frontend/pages/7_Automation_Logs.py
Real-time audit trails of scraper activities, form interactions, and system events.
"""

import os
import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Audit Logs | Ansh AI JobHunter", page_icon="📜", layout="wide")
st.title("📜 Automation Audit Logs")

col_filt, col_dl = st.columns([3, 1])

with col_filt:
    level_filter = st.selectbox("Filter Log Level", ["All", "info", "warning", "error"])

logs = []
try:
    l_res = requests.get(f"{API_BASE}/api/discovery/logs?limit=200", timeout=5)
    if l_res.status_code == 200:
        logs = l_res.json()
except Exception as ex:
    st.error(f"Cannot load audit logs: {ex}")

if level_filter != "All":
    logs = [l for l in logs if l.get("level") == level_filter]

with col_dl:
    if logs:
        df = pd.DataFrame(logs)
        st.download_button(
            "📥 Download Logs (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="automation_audit_logs.csv",
            mime="text/csv",
        )

st.write(f"Displaying **{len(logs)}** log event(s)")

if not logs:
    st.info("No logs found for selected criteria.")
else:
    for entry in logs:
        lvl = entry.get("level", "info")
        color = "#2563eb" if lvl == "info" else ("#ca8a04" if lvl == "warning" else "#dc2626")
        icon = "ℹ️" if lvl == "info" else ("⚠️" if lvl == "warning" else "❌")

        with st.container(border=True):
            st.markdown(
                f"<span style='color:{color}; font-weight:bold;'>{icon} [{lvl.upper()}]</span> "
                f"<b>{entry.get('event_type', 'EVENT')}</b> &nbsp;|&nbsp; "
                f"<small style='color:#6b7280;'>{entry.get('created_at', '')}</small>",
                unsafe_allow_html=True,
            )
            st.write(entry.get("message", ""))
