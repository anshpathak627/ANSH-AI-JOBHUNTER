"""
integrations/company_registry.py
Central registry of all target companies with metadata for the ANSH AI JOBHUNTER.

Each entry in COMPANY_REGISTRY is a dict with:
  - name           : Human-readable company name
  - careers_url    : Direct careers/jobs page URL
  - ats_provider   : ATS platform ('greenhouse'|'lever'|'ashby'|'custom'|'unknown')
  - board_identifier: Slug/token used by the ATS API (None for custom/unknown)
  - country        : Primary country of the company
  - industry       : Industry sector
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

COMPANY_REGISTRY: list[dict] = [
    # ── TECH ─────────────────────────────────────────────────────────────────
    {
        "name": "Google",
        "careers_url": "https://careers.google.com/jobs/results/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Microsoft",
        "careers_url": "https://careers.microsoft.com/us/en/search-results",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Amazon",
        "careers_url": "https://www.amazon.jobs/en/search",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Adobe",
        "careers_url": "https://boards.greenhouse.io/adobe",
        "ats_provider": "greenhouse",
        "board_identifier": "adobe",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Oracle",
        "careers_url": "https://careers.oracle.com/jobs/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "IBM",
        "careers_url": "https://www.ibm.com/employment/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Salesforce",
        "careers_url": "https://boards.greenhouse.io/salesforce",
        "ats_provider": "greenhouse",
        "board_identifier": "salesforce",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Atlassian",
        "careers_url": "https://boards.greenhouse.io/atlassian",
        "ats_provider": "greenhouse",
        "board_identifier": "atlassian",
        "country": "Australia",
        "industry": "Technology",
    },
    {
        "name": "Uber",
        "careers_url": "https://www.lever.co/uber",
        "ats_provider": "lever",
        "board_identifier": "uber",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Airbnb",
        "careers_url": "https://boards.greenhouse.io/airbnb",
        "ats_provider": "greenhouse",
        "board_identifier": "airbnb",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Expedia",
        "careers_url": "https://boards.greenhouse.io/expedia",
        "ats_provider": "greenhouse",
        "board_identifier": "expedia",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Intuit",
        "careers_url": "https://boards.greenhouse.io/intuit",
        "ats_provider": "greenhouse",
        "board_identifier": "intuit",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Cisco",
        "careers_url": "https://jobs.cisco.com/jobs/SearchJobs",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "SAP",
        "careers_url": "https://jobs.sap.com/search/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "Germany",
        "industry": "Technology",
    },
    {
        "name": "ServiceNow",
        "careers_url": "https://boards.greenhouse.io/servicenow",
        "ats_provider": "greenhouse",
        "board_identifier": "servicenow",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Nvidia",
        "careers_url": "https://boards.greenhouse.io/nvidia",
        "ats_provider": "greenhouse",
        "board_identifier": "nvidia",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Qualcomm",
        "careers_url": "https://boards.greenhouse.io/qualcomm",
        "ats_provider": "greenhouse",
        "board_identifier": "qualcomm",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Intel",
        "careers_url": "https://boards.greenhouse.io/intel",
        "ats_provider": "greenhouse",
        "board_identifier": "intel",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Samsung",
        "careers_url": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "South Korea",
        "industry": "Technology",
    },
    {
        "name": "Flipkart",
        "careers_url": "https://boards.greenhouse.io/flipkart",
        "ats_provider": "greenhouse",
        "board_identifier": "flipkart",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "Swiggy",
        "careers_url": "https://careers.swiggy.com/#/",
        "ats_provider": "lever",
        "board_identifier": "swiggy",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "Zomato",
        "careers_url": "https://boards.greenhouse.io/zomato",
        "ats_provider": "greenhouse",
        "board_identifier": "zomato",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "Meesho",
        "careers_url": "https://boards.greenhouse.io/meesho",
        "ats_provider": "greenhouse",
        "board_identifier": "meesho",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "CRED",
        "careers_url": "https://jobs.lever.co/cred",
        "ats_provider": "lever",
        "board_identifier": "cred",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "PhonePe",
        "careers_url": "https://jobs.lever.co/phonepe",
        "ats_provider": "lever",
        "board_identifier": "phonepe",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "Razorpay",
        "careers_url": "https://jobs.lever.co/razorpay",
        "ats_provider": "lever",
        "board_identifier": "razorpay",
        "country": "India",
        "industry": "Technology",
    },
    {
        "name": "PayPal",
        "careers_url": "https://boards.greenhouse.io/paypal",
        "ats_provider": "greenhouse",
        "board_identifier": "paypal",
        "country": "USA",
        "industry": "Technology",
    },
    {
        "name": "Dell",
        "careers_url": "https://boards.greenhouse.io/dell",
        "ats_provider": "greenhouse",
        "board_identifier": "dell",
        "country": "USA",
        "industry": "Technology",
    },
    # ── BANKING ──────────────────────────────────────────────────────────────
    {
        "name": "JPMorgan Chase",
        "careers_url": "https://boards.greenhouse.io/jpmorgan",
        "ats_provider": "greenhouse",
        "board_identifier": "jpmorgan",
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "Goldman Sachs",
        "careers_url": "https://boards.greenhouse.io/goldmansachs",
        "ats_provider": "greenhouse",
        "board_identifier": "goldmansachs",
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "Morgan Stanley",
        "careers_url": "https://boards.greenhouse.io/morganstanley",
        "ats_provider": "greenhouse",
        "board_identifier": "morganstanley",
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "Citi",
        "careers_url": "https://jobs.citi.com/search-jobs",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "Barclays",
        "careers_url": "https://boards.greenhouse.io/barclays",
        "ats_provider": "greenhouse",
        "board_identifier": "barclays",
        "country": "UK",
        "industry": "Banking",
    },
    {
        "name": "HSBC",
        "careers_url": "https://www.hsbc.com/careers/jobs",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "UK",
        "industry": "Banking",
    },
    {
        "name": "Standard Chartered",
        "careers_url": "https://boards.greenhouse.io/standardchartered",
        "ats_provider": "greenhouse",
        "board_identifier": "standardchartered",
        "country": "UK",
        "industry": "Banking",
    },
    {
        "name": "Bank of America",
        "careers_url": "https://boards.greenhouse.io/bankofamerica",
        "ats_provider": "greenhouse",
        "board_identifier": "bankofamerica",
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "American Express",
        "careers_url": "https://boards.greenhouse.io/americanexpress",
        "ats_provider": "greenhouse",
        "board_identifier": "americanexpress",
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "Wells Fargo",
        "careers_url": "https://boards.greenhouse.io/wellsfargo",
        "ats_provider": "greenhouse",
        "board_identifier": "wellsfargo",
        "country": "USA",
        "industry": "Banking",
    },
    {
        "name": "Deutsche Bank",
        "careers_url": "https://boards.greenhouse.io/deutschebank",
        "ats_provider": "greenhouse",
        "board_identifier": "deutschebank",
        "country": "Germany",
        "industry": "Banking",
    },
    {
        "name": "Axis Bank",
        "careers_url": "https://www.axisbank.com/about-us/careers",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "Banking",
    },
    {
        "name": "HDFC Bank",
        "careers_url": "https://www.hdfcbank.com/personal/about-us/career-with-us",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "Banking",
    },
    {
        "name": "ICICI Bank",
        "careers_url": "https://www.icicicareers.com/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "Banking",
    },
    {
        "name": "Kotak Mahindra Bank",
        "careers_url": "https://careers.kotak.com/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "Banking",
    },
    # ── CONSULTING ───────────────────────────────────────────────────────────
    {
        "name": "McKinsey",
        "careers_url": "https://boards.greenhouse.io/mckinsey",
        "ats_provider": "greenhouse",
        "board_identifier": "mckinsey",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "BCG",
        "careers_url": "https://boards.greenhouse.io/bcg",
        "ats_provider": "greenhouse",
        "board_identifier": "bcg",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "Bain",
        "careers_url": "https://boards.greenhouse.io/bain",
        "ats_provider": "greenhouse",
        "board_identifier": "bain",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "Deloitte",
        "careers_url": "https://boards.greenhouse.io/deloitte",
        "ats_provider": "greenhouse",
        "board_identifier": "deloitte",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "EY",
        "careers_url": "https://careers.ey.com/ey/jobs",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "UK",
        "industry": "Consulting",
    },
    {
        "name": "PwC",
        "careers_url": "https://www.pwc.com/gx/en/careers/job-search.html",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "UK",
        "industry": "Consulting",
    },
    {
        "name": "KPMG",
        "careers_url": "https://home.kpmg/careers",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "Netherlands",
        "industry": "Consulting",
    },
    {
        "name": "Accenture",
        "careers_url": "https://boards.greenhouse.io/accenture",
        "ats_provider": "greenhouse",
        "board_identifier": "accenture",
        "country": "Ireland",
        "industry": "Consulting",
    },
    {
        "name": "ZS Associates",
        "careers_url": "https://boards.greenhouse.io/zs",
        "ats_provider": "greenhouse",
        "board_identifier": "zs",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "Kearney",
        "careers_url": "https://boards.greenhouse.io/kearney",
        "ats_provider": "greenhouse",
        "board_identifier": "kearney",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "Oliver Wyman",
        "careers_url": "https://boards.greenhouse.io/oliverwyman",
        "ats_provider": "greenhouse",
        "board_identifier": "oliverwyman",
        "country": "USA",
        "industry": "Consulting",
    },
    {
        "name": "Capgemini",
        "careers_url": "https://boards.greenhouse.io/capgemini",
        "ats_provider": "greenhouse",
        "board_identifier": "capgemini",
        "country": "France",
        "industry": "Consulting",
    },
    # ── INDIAN STARTUPS ───────────────────────────────────────────────────────
    {
        "name": "Groww",
        "careers_url": "https://jobs.lever.co/groww",
        "ats_provider": "lever",
        "board_identifier": "groww",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "Zerodha",
        "careers_url": "https://zerodha.com/careers/",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "Pine Labs",
        "careers_url": "https://boards.greenhouse.io/pinelabs",
        "ats_provider": "greenhouse",
        "board_identifier": "pinelabs",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "Wise",
        "careers_url": "https://boards.greenhouse.io/wise",
        "ats_provider": "greenhouse",
        "board_identifier": "wise",
        "country": "UK",
        "industry": "Fintech",
    },
    {
        "name": "Cashfree",
        "careers_url": "https://jobs.lever.co/cashfree",
        "ats_provider": "lever",
        "board_identifier": "cashfree",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "Navi",
        "careers_url": "https://jobs.lever.co/navi",
        "ats_provider": "lever",
        "board_identifier": "navi",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "Policybazaar",
        "careers_url": "https://boards.greenhouse.io/policybazaar",
        "ats_provider": "greenhouse",
        "board_identifier": "policybazaar",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "ACKO",
        "careers_url": "https://jobs.lever.co/acko",
        "ats_provider": "lever",
        "board_identifier": "acko",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "OfBusiness",
        "careers_url": "https://boards.greenhouse.io/ofbusiness",
        "ats_provider": "greenhouse",
        "board_identifier": "ofbusiness",
        "country": "India",
        "industry": "B2B Commerce",
    },
    {
        "name": "Juspay",
        "careers_url": "https://boards.greenhouse.io/juspay",
        "ats_provider": "greenhouse",
        "board_identifier": "juspay",
        "country": "India",
        "industry": "Fintech",
    },
    {
        "name": "BharatPe",
        "careers_url": "https://jobs.lever.co/bharatpe",
        "ats_provider": "lever",
        "board_identifier": "bharatpe",
        "country": "India",
        "industry": "Fintech",
    },
    # ── IT SERVICES ───────────────────────────────────────────────────────────
    {
        "name": "TCS",
        "careers_url": "https://www.tcs.com/careers",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "IT Services",
    },
    {
        "name": "Infosys",
        "careers_url": "https://career.infosys.com/joblist",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "IT Services",
    },
    {
        "name": "Wipro",
        "careers_url": "https://careers.wipro.com/careers-home/jobs",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "IT Services",
    },
    {
        "name": "HCLTech",
        "careers_url": "https://www.hcltech.com/careers",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "IT Services",
    },
    {
        "name": "Tech Mahindra",
        "careers_url": "https://careers.techmahindra.com/jobs",
        "ats_provider": "custom",
        "board_identifier": None,
        "country": "India",
        "industry": "IT Services",
    },
    {
        "name": "LTIMindtree",
        "careers_url": "https://boards.greenhouse.io/ltimindtree",
        "ats_provider": "greenhouse",
        "board_identifier": "ltimindtree",
        "country": "India",
        "industry": "IT Services",
    },
    {
        "name": "Cognizant",
        "careers_url": "https://boards.greenhouse.io/cognizant",
        "ats_provider": "greenhouse",
        "board_identifier": "cognizant",
        "country": "USA",
        "industry": "IT Services",
    },
    {
        "name": "Genpact",
        "careers_url": "https://boards.greenhouse.io/genpact",
        "ats_provider": "greenhouse",
        "board_identifier": "genpact",
        "country": "USA",
        "industry": "IT Services",
    },
    {
        "name": "CGI",
        "careers_url": "https://boards.greenhouse.io/cgi",
        "ats_provider": "greenhouse",
        "board_identifier": "cgi",
        "country": "Canada",
        "industry": "IT Services",
    },
    {
        "name": "DXC",
        "careers_url": "https://boards.greenhouse.io/dxctechnology",
        "ats_provider": "greenhouse",
        "board_identifier": "dxctechnology",
        "country": "USA",
        "industry": "IT Services",
    },
]


# ---------------------------------------------------------------------------
# DB seeder
# ---------------------------------------------------------------------------

def seed_companies_to_db(db_session) -> int:
    """
    Insert all companies from COMPANY_REGISTRY into the Company table if they
    are not already present (matched by name, case-insensitively).

    Parameters
    ----------
    db_session : sqlalchemy.orm.Session
        An active SQLAlchemy session.

    Returns
    -------
    int
        Number of new Company rows inserted.
    """
    from database.models import Company, ATSProvider

    inserted = 0
    for entry in COMPANY_REGISTRY:
        existing = (
            db_session.query(Company)
            .filter(Company.name.ilike(entry["name"]))
            .first()
        )
        if existing:
            continue

        # Map string ATS provider to enum value safely
        try:
            ats_enum = ATSProvider(entry["ats_provider"])
        except ValueError:
            ats_enum = ATSProvider.unknown

        company = Company(
            name=entry["name"],
            careers_url=entry.get("careers_url"),
            ats_provider=ats_enum,
            board_identifier=entry.get("board_identifier"),
            country=entry.get("country"),
            industry=entry.get("industry"),
            is_active=True,
        )
        db_session.add(company)
        inserted += 1

    if inserted:
        db_session.commit()

    return inserted


__all__ = ["COMPANY_REGISTRY", "seed_companies_to_db"]
