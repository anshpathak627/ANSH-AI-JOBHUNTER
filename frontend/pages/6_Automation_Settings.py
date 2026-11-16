"""
frontend/pages/6_Automation_Settings.py
Operational mode switches, safety limits, notifications, and LLM configuration.
"""

import json
import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Settings | Ansh AI JobHunter", page_icon="⚙️", layout="wide")
st.title("⚙️ Automation & Safety Controls")

# Fetch current settings
settings = {}
try:
    s_res = requests.get(f"{API_BASE}/api/settings", timeout=3)
    if s_res.status_code == 200:
        settings = s_res.json()
except Exception:
    pass

# --- Section 1: Operation Mode ---
st.subheader("🛡️ Autonomous Submission Mode")

current_mode = str(settings.get("application_mode", "DISCOVERY")).upper()
mode_idx = 0
if "PREPARE" in current_mode:
    mode_idx = 1
elif "APPROVED" in current_mode:
    mode_idx = 2

mode_selection = st.radio(
    "Select Operating Mode:",
    [
        "MODE 1: DISCOVERY (Find & Match Only — Zero Automated Form Input)",
        "MODE 2: PREPARE (Prefill Forms & Drafts — Never Submits Without You)",
        "MODE 3: APPROVED (Autonomous Submission with Explicit Per-Job Approval)"
    ],
    index=mode_idx,
)

if "APPROVED" in mode_selection:
    st.warning(
        "⚠️ **SAFETY NOTICE:** In APPROVED mode, the system will only submit forms for jobs "
        "you explicitly approve in the tracker. Daily caps and CAPTCHA safeguards remain strictly active."
    )
elif "PREPARE" in mode_selection:
    st.info("ℹ️ **PREPARE Mode:** Forms are filled and drafts captured for your final manual review.")
else:
    st.success("🔒 **DISCOVERY Mode:** Fully read-only discovery and matching.")

st.markdown("---")

# --- Section 2: Throttling & Criteria ---
st.subheader("⚡ Search & Throttling Limits")
col1, col2 = st.columns(2)
with col1:
    daily_limit = st.slider("Maximum Submissions Per Day", 1, 50, int(settings.get("max_applications_per_day", 10)))
    min_salary = st.number_input("Minimum Desired Annual CTC (INR)", value=int(settings.get("min_salary", 400000)), step=50000)
with col2:
    st.write("**Scheduled Autonomous Scan Cycles:**")
    st.caption("• Morning Scan: `07:00 IST`")
    st.caption("• Afternoon Scan: `13:00 IST`")
    st.caption("• Evening Scan: `20:00 IST`")

st.markdown("---")

# --- Section 3: Notification Alerts ---
st.subheader("📲 Real-Time Notifications")
col_tg, col_em = st.columns(2)

with col_tg:
    st.markdown("#### Telegram Alerts")
    tg_token = st.text_input("Telegram Bot Token", value=str(settings.get("telegram_bot_token") or ""), type="password")
    tg_chat = st.text_input("Telegram Chat ID", value=str(settings.get("telegram_chat_id") or ""))

with col_em:
    st.markdown("#### SMTP Email Alerts")
    em_host = st.text_input("SMTP Host", value=str(settings.get("email_smtp_host") or "smtp.gmail.com"))
    em_user = st.text_input("Email Username", value=str(settings.get("email_username") or ""))
    em_pwd = st.text_input("Email App Password", value=str(settings.get("email_password") or ""), type="password")

st.markdown("---")

# --- Section 4: AI & Ollama Configuration ---
st.subheader("🧠 Intelligence Engine (Ollama Local LLM)")
col_ai1, col_ai2 = st.columns(2)
with col_ai1:
    use_ai = st.toggle("Enable Ollama Local LLM Matching", value=bool(settings.get("use_ai_matching", False)))
    ollama_url = st.text_input("Ollama Endpoint URL", value=str(settings.get("ollama_base_url") or "http://localhost:11434"))
with col_ai2:
    ollama_model = st.text_input("Ollama Model Tag", value=str(settings.get("ollama_model") or "llama3.2"))
    st.caption("When disabled or unavailable, the system automatically runs the 100-point rule-based matcher.")

st.markdown("---")

# Save Button
if st.button("💾 Save Automation Settings", type="primary", use_container_width=True):
    # Determine mode code
    if "APPROVED" in mode_selection:
        save_mode = "APPROVED"
    elif "PREPARE" in mode_selection:
        save_mode = "PREPARE"
    else:
        save_mode = "DISCOVERY"

    payload = {
        "settings": {
            "application_mode": save_mode,
            "max_applications_per_day": daily_limit,
            "min_salary": min_salary,
            "telegram_bot_token": tg_token,
            "telegram_chat_id": tg_chat,
            "email_smtp_host": em_host,
            "email_username": em_user,
            "email_password": em_pwd,
            "use_ai_matching": use_ai,
            "ollama_base_url": ollama_url,
            "ollama_model": ollama_model,
        }
    }

    try:
        res = requests.put(f"{API_BASE}/api/settings", json=payload)
        if res.status_code == 200:
            st.success("All settings successfully updated!")
        else:
            st.error("Failed to save settings.")
    except Exception as ex:
        st.error(f"Error saving settings: {ex}")
