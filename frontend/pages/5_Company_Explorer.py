"""
frontend/pages/5_Company_Explorer.py
Registry of monitored employers, ATS distribution, and single-employer scans.
"""

import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Companies | Ansh AI JobHunter", page_icon="🏢", layout="wide")
st.title("🏢 Monitored Companies & Portals")

# Filters
col_f1, col_f2, col_add = st.columns([2, 2, 2])
with col_f1:
    ats_filter = st.selectbox("Filter ATS Provider", ["All", "greenhouse", "lever", "ashby", "custom"])
with col_f2:
    industry_filter = st.selectbox("Filter Industry", ["All", "Technology", "Banking / Finance", "Consulting", "Startups", "IT Services"])

with col_add:
    st.write("")
    show_add_modal = st.checkbox("➕ Add New Employer")

if show_add_modal:
    with st.form("add_comp_form"):
        st.subheader("Add Target Company")
        c_name = st.text_input("Company Name")
        c_url = st.text_input("Careers Portal URL")
        c_ats = st.selectbox("ATS Platform", ["greenhouse", "lever", "ashby", "custom", "workday", "unknown"])
        c_board = st.text_input("Board Identifier / Slug (e.g. 'adobe', 'uber')")
        c_country = st.text_input("Country", "India")
        c_ind = st.selectbox("Industry", ["Technology", "Banking / Finance", "Consulting", "Fintech / Startups", "IT Services"])

        if st.form_submit_button("Register Company"):
            payload = {
                "name": c_name,
                "careers_url": c_url,
                "ats_provider": c_ats,
                "board_identifier": c_board or None,
                "country": c_country,
                "industry": c_ind,
            }
            res = requests.post(f"{API_BASE}/api/companies", json=payload)
            if res.status_code == 200:
                st.success(f"Registered {c_name}!")
                st.rerun()
            else:
                st.error("Failed to register company.")

params = {}
if ats_filter != "All":
    params["ats_provider"] = ats_filter
if industry_filter != "All":
    params["industry"] = industry_filter

companies = []
try:
    c_res = requests.get(f"{API_BASE}/api/companies", params=params, timeout=5)
    if c_res.status_code == 200:
        companies = c_res.json()
except Exception as ex:
    st.error(f"Cannot load companies: {ex}")

st.write(f"Tracking **{len(companies)}** target employer(s)")

# ATS Distribution
ats_counts = {}
for c in companies:
    prov = c.get("ats_provider", "unknown")
    ats_counts[prov] = ats_counts.get(prov, 0) + 1

if ats_counts:
    st.caption("ATS Coverage: " + " | ".join(f"**{k.capitalize()}**: {v}" for k, v in ats_counts.items()))

st.markdown("---")

for comp in companies:
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.subheader(comp["name"])
            st.caption(f"Industry: {comp.get('industry')} | Country: {comp.get('country')}")
            if comp.get("careers_url"):
                st.link_button("🌐 Careers Link", comp["careers_url"])
        with col2:
            st.write(f"**ATS Engine:** `{comp.get('ats_provider')}`")
            if comp.get("board_identifier"):
                st.caption(f"Slug: `{comp['board_identifier']}`")
            st.caption(f"Last Scan: {comp.get('last_scan_at') or 'Never'}")
            st.caption(f"Status: {comp.get('scan_status') or 'Idle'}")
        with col3:
            if st.button("🔍 Scan Now", key=f"scan_{comp['id']}", type="secondary"):
                s_res = requests.post(f"{API_BASE}/api/companies/{comp['id']}/scan")
                if s_res.status_code == 200:
                    st.success("Scan initiated!")
                else:
                    st.error("Failed to initiate scan.")
