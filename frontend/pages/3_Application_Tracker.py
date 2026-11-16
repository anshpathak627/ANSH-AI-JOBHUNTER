"""
frontend/pages/3_Application_Tracker.py
State machine tracking for all candidate job applications.
"""

import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Applications | Ansh AI JobHunter", page_icon="📝", layout="wide")
st.title("📝 Application Workflow Tracker")

tabs = st.tabs(["ALL", "DISCOVERED", "PREPARED", "PENDING_APPROVAL", "SUBMITTED", "CONFIRMED", "FAILED", "WITHDRAWN"])

applications = []
try:
    resp = requests.get(f"{API_BASE}/api/applications", timeout=5)
    if resp.status_code == 200:
        applications = resp.json()
except Exception as ex:
    st.error(f"Cannot load applications: {ex}")


def render_application_table(items):
    if not items:
        st.info("No applications in this category.")
        return

    for app in items:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.subheader(app.get("job_title", "Unknown Role"))
                st.caption(f"🏢 **{app.get('company_name')}** | 📍 {app.get('location')}")
                if app.get("notes"):
                    st.write(f"📝 *Notes:* {app['notes']}")
            with col2:
                status_color = {
                    "SUBMITTED": "green", "CONFIRMED": "green",
                    "PREPARED": "blue", "PENDING_APPROVAL": "orange",
                    "FAILED": "red", "WITHDRAWN": "gray"
                }.get(app.get("status", "DISCOVERED"), "blue")

                st.markdown(f"**Status:** :{status_color}[{app.get('status')}]")
                st.caption(f"Applied: {app.get('applied_at') or 'Not yet submitted'}")
                st.caption(f"Tracked Since: {app.get('created_at') or 'N/A'}")

            with col3:
                new_status = st.selectbox(
                    "Transition Status",
                    ["DISCOVERED", "MATCHED", "PREPARED", "PENDING_APPROVAL", "SUBMITTED", "CONFIRMED", "FAILED", "WITHDRAWN"],
                    index=["DISCOVERED", "MATCHED", "PREPARED", "PENDING_APPROVAL", "SUBMITTED", "CONFIRMED", "FAILED", "WITHDRAWN"].index(app.get("status", "DISCOVERED")),
                    key=f"status_sel_{app['id']}"
                )
                if new_status != app.get("status"):
                    if st.button("Update Status", key=f"upd_{app['id']}"):
                        requests.put(f"{API_BASE}/api/applications/{app['id']}/status", json={"status": new_status})
                        st.rerun()

                if app.get("status") == "PREPARED":
                    if st.button("✅ Approve for Submission", key=f"appr_{app['id']}", type="primary"):
                        requests.post(f"{API_BASE}/api/applications/{app['id']}/approve")
                        st.rerun()

                if app.get("status") != "WITHDRAWN":
                    if st.button("Withdraw", key=f"wth_{app['id']}"):
                        requests.delete(f"{API_BASE}/api/applications/{app['id']}")
                        st.rerun()


# Render Tabs
with tabs[0]:
    render_application_table(applications)
with tabs[1]:
    render_application_table([a for a in applications if a.get("status") == "DISCOVERED"])
with tabs[2]:
    render_application_table([a for a in applications if a.get("status") == "PREPARED"])
with tabs[3]:
    render_application_table([a for a in applications if a.get("status") == "PENDING_APPROVAL"])
with tabs[4]:
    render_application_table([a for a in applications if a.get("status") == "SUBMITTED"])
with tabs[5]:
    render_application_table([a for a in applications if a.get("status") == "CONFIRMED"])
with tabs[6]:
    render_application_table([a for a in applications if a.get("status") == "FAILED"])
with tabs[7]:
    render_application_table([a for a in applications if a.get("status") == "WITHDRAWN"])
