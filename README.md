
﻿# 🎯 ANSH AI JOBHUNTER

**Personal Autonomous AI Job Discovery & Application Assistant**  
Built specifically for **Ansh Pathak** (MAIT, GGSIPU — B.Tech EE VLSI, 2027 Batch, 8.4 CGPA).

---

## 🚀 Key Highlights & Capabilities

- **Zero-Cost Discovery Engine**: Scans 70+ top tech companies, investment banks, consulting firms, Indian fintech startups, and IT service providers across public ATS APIs (**Greenhouse, Lever, Ashby**) and custom career pages without paid third-party API dependencies.
- **100-Point Precision Fit Matcher**: Evaluates role alignment against Ansh's actual skills, college, graduation year (2027), CGPA (8.4), and internship experience (DRDO, American Express) with zero false statements or hallucinations.
- **Dynamic ATS Resume Tailoring**: Automatically aligns resume priority skills and exports clean, single-column ATS-friendly PDFs using ReportLab.
- **Playwright Browser Automation (3 Strict Safety Modes)**:
  - `MODE 1: DISCOVERY` — Purely reads and scores opportunities. Zero form interaction.
  - `MODE 2: PREPARE` — Automatically fills known fields, detects form structures, and pauses for your manual inspection.
  - `MODE 3: APPROVED` — Autonomous submission only with explicit per-job approval, daily limits (default: 10), and automatic CAPTCHA/OTP stop guards.
- **Multi-Channel Alerts**: Instant Telegram Bot and SMTP email notifications on high-scoring openings (≥70% fit) and application submissions.
- **Automated Scheduling**: APScheduler background daemon running automated scans every morning (07:00), afternoon (13:00), and evening (20:00).

---

## 🛠️ Architecture & Tech Stack

```
Ansh-AI-JobHunter/
├── backend/                  # FastAPI backend (Port 8000)
│   ├── main.py               # App entrypoint, CORS, scheduler startup
│   └── api/                  # REST endpoints (jobs, candidates, applications, etc.)
├── frontend/                 # Streamlit multi-page dashboard (Port 8501)
│   ├── streamlit_app.py      # Main navigation and high-level metrics
│   └── pages/                # 7 specialized operational pages
├── agents/                   # AI & eligibility matching agents
│   ├── matching_agent.py     # 100-pt weighted scoring + Ollama integration
│   └── eligibility_agent.py  # Hard constraint and graduation batch checks
├── discovery/                # Job scraping and filtering orchestrators
│   ├── discovery_engine.py   # Multi-ATS scanner & deduplicator
│   ├── job_filter.py         # Keyword matching, salary & location parsing
│   └── scheduler.py          # APScheduler morning/afternoon/evening triggers
├── integrations/             # Native ATS API clients
│   ├── greenhouse.py         # Greenhouse Boards API
│   ├── lever.py              # Lever Postings API
│   ├── ashby.py              # Ashby Job Board API
│   ├── career_scraper.py     # BeautifulSoup / JSON-LD fallback
│   └── company_registry.py   # 70+ pre-seeded employers
├── resume_engine/            # Document synthesis & ATS generation
│   ├── resume_tailor.py      # Keyword alignment engine
│   ├── pdf_generator.py      # ReportLab ATS PDF compiler
│   └── version_manager.py    # Multi-version CV repository
├── browser_automation/       # Playwright browser assistant
│   ├── form_agent.py         # Form filling & screenshot verification
│   └── submission_guard.py   # Safety policies & CAPTCHA safeguards
├── database/                 # SQLAlchemy 2.0 ORM & SQLite
│   ├── models.py             # 11 normalized database entities
│   ├── crud.py               # Data access helpers
│   └── init_db.py            # Table initialization and seeding
├── tests/                    # Pytest test suite
├── setup.bat                 # One-click Windows 11 setup
└── run.bat                   # One-click dual-server launcher
```

---

## 💻 Quickstart on Windows 11

### 1. One-Click Automated Setup
Double-click `setup.bat` or run:
```cmd
setup.bat
```
This automatically:
- Creates a virtual environment in `.venv`
- Installs all dependencies from `requirements.txt`
- Configures `.env` from `.env.example`
- Creates database tables in `data/jobhunter.db` and seeds 70+ target companies
- Installs Playwright Chromium browser

### 2. Launch Application
Double-click `run.bat` or run:
```cmd
run.bat
```
Your browser will open:
- **Streamlit Dashboard:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Tests

To verify database integrity and the matching algorithm:
```cmd
.venv\Scripts\activate.bat
pytest tests/ -v
```

---

## 🛡️ Safety & Compliance

- **No Credential Fabrication**: Under no circumstances does the engine fabricate employment dates, companies, or alter numerical metrics.
- **No CAPTCHA / OTP Bypass**: The system immediately pauses and notifies the user whenever an authentication challenge or CAPTCHA is encountered.
- **LinkedIn Safeguard**: Strictly avoids unauthorized scraping of LinkedIn to remain 100% compliant with Terms of Service.
# ANSH-AI-JOBHUNTER
AI-powered job discovery and application assistant
