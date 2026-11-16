"""
frontend/pages/4_Resume_Manager.py
Profile editor, resume versions repository, file upload, and tailoring actions.
"""

import json
import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Resume Manager | Ansh AI JobHunter", page_icon="📄", layout="wide")
st.title("📄 Candidate Profile & Resume Engine")

tab_profile, tab_resumes, tab_tailor = st.tabs(["👤 Profile Information", "📂 Resume Versions", "✨ Tailoring Hub"])

# --- TAB 1: Profile Editor ---
with tab_profile:
    st.subheader("Edit Candidate Information")
    profile = {}
    try:
        p_res = requests.get(f"{API_BASE}/api/candidates", timeout=3)
        if p_res.status_code == 200:
            profile = p_res.json()
    except Exception:
        st.warning("Could not fetch candidate profile.")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", profile.get("name", "Ansh Pathak"))
            email = st.text_input("Email", profile.get("email", "pathakansh696@gmail.com"))
            phone = st.text_input("Phone Number", profile.get("phone", "+91 9999999999"))
            college = st.text_input("College / University", profile.get("college", "MAIT, GGSIPU"))
        with col2:
            degree = st.text_input("Degree", profile.get("degree", "B.Tech"))
            branch = st.text_input("Branch / Specialization", profile.get("branch", "Electrical Engineering (VLSI Design & Technology)"))
            cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, value=float(profile.get("cgpa", 8.4)), step=0.01)
            grad_year = st.number_input("Graduation Year", min_value=2020, max_value=2030, value=int(profile.get("grad_year", 2027)))

        current_skills = profile.get("skills", [])
        skills_str = st.text_area("Skills (comma-separated)", ", ".join(current_skills))

        col3, col4 = st.columns(2)
        with col3:
            linkedin = st.text_input("LinkedIn Profile URL", profile.get("linkedin_url", "https://linkedin.com/in/anshpathak"))
        with col4:
            github = st.text_input("GitHub Profile URL", profile.get("github_url", "https://github.com/anshpathak"))

        summary = st.text_area("Professional Summary", profile.get("summary", ""))

        if st.form_submit_button("💾 Save Profile Changes", type="primary"):
            updated_skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            payload = {
                "name": name,
                "email": email,
                "phone": phone,
                "college": college,
                "degree": degree,
                "branch": branch,
                "cgpa": cgpa,
                "grad_year": grad_year,
                "skills": updated_skills,
                "linkedin_url": linkedin,
                "github_url": github,
                "summary": summary,
            }
            u_res = requests.put(f"{API_BASE}/api/candidates", json=payload)
            if u_res.status_code == 200:
                st.success("Profile updated successfully!")
            else:
                st.error("Failed to update profile.")

# --- TAB 2: Resume Versions ---
with tab_resumes:
    st.subheader("Upload & Version Management")

    with st.expander("⬆️ Upload New Resume File"):
        uploaded_file = st.file_uploader("Upload PDF, DOCX, or TXT Resume", type=["pdf", "txt", "docx"])
        v_label = st.text_input("Version Tag / Label", "Master Software & Analytics Resume 2026")
        is_pri = st.checkbox("Set as Primary Active Resume", value=True)

        if st.button("Submit Upload", type="primary"):
            if uploaded_file is not None:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"version_label": v_label, "is_primary": str(is_pri).lower()}
                up_res = requests.post(f"{API_BASE}/api/resumes/upload", files=files, data=data)
                if up_res.status_code == 200:
                    st.success("Resume uploaded successfully!")
                    st.rerun()
                else:
                    st.error("Upload error")

    st.markdown("### Stored Versions")
    try:
        resumes = requests.get(f"{API_BASE}/api/resumes", timeout=3).json()
        if not resumes:
            st.info("No resumes uploaded yet.")
        else:
            for r in resumes:
                with st.container(border=True):
                    rc1, rc2, rc3 = st.columns([3, 2, 2])
                    with rc1:
                        st.write(f"**{r.get('filename')}**")
                        st.caption(f"Label: {r.get('version_label')} | Size: {r.get('file_size', 0)} bytes")
                    with rc2:
                        if r.get("is_primary"):
                            st.success("★ Primary Active Resume")
                        else:
                            if st.button("Set as Primary", key=f"pri_{r['id']}"):
                                requests.put(f"{API_BASE}/api/resumes/{r['id']}/set-primary")
                                st.rerun()
                    with rc3:
                        st.link_button("📥 Download", f"{API_BASE}/api/resumes/{r['id']}/download")
                        if st.button("🗑️ Delete", key=f"del_{r['id']}"):
                            requests.delete(f"{API_BASE}/api/resumes/{r['id']}")
                            st.rerun()
    except Exception as ex:
        st.error(f"Cannot load resumes: {ex}")

# --- TAB 3: Tailoring Hub ---
with tab_tailor:
    st.subheader("On-Demand ATS Resume Tailor")
    st.write("Generates a customized, keyword-aligned PDF matching the specific requirements of a job posting.")

    job_id_input = st.number_input("Enter Job ID to Tailor For", min_value=1, step=1)
    if st.button("⚡ Generate Tailored Resume", type="primary"):
        with st.spinner("Tailoring resume and compiling PDF..."):
            t_res = requests.post(f"{API_BASE}/api/resumes/tailor/{job_id_input}", timeout=15)
            if t_res.status_code == 200:
                t_data = t_res.json()
                st.success("Tailored Resume PDF Generated Successfully!")
                st.write(f"**Saved To:** `{t_data.get('pdf_path')}`")
                st.text_area("Preview", t_data.get("tailored_text", ""), height=300)
                st.link_button("📥 Download Generated PDF", f"{API_BASE}/api/resumes/{t_data.get('resume_id')}/download")
            else:
                st.error(f"Failed to tailor resume: {t_res.text}")
