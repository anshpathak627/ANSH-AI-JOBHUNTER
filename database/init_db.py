"""
database/init_db.py
One-shot initialisation script for ANSH AI JOBHUNTER.

Responsibilities
----------------
1. Create the ``data/`` directory (where the SQLite file lives).
2. Create all ORM tables (idempotent – safe to run multiple times).
3. Seed default ``UserSetting`` rows if they do not already exist.
4. Print a human-readable summary on completion.

Run with::

    python -m database.init_db
    # or
    python database/init_db.py
"""

from __future__ import annotations

import json
import os
import sys

# Allow running the script directly from the project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from database import engine, SessionLocal
from database.models import Base, UserSetting

# ─────────────────────────────────────────────────────────────────────────────
# Default user settings seeded on first run
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS: dict[str, str] = {
    "max_applications_per_day": "10",
    "application_mode": "DISCOVERY",
    "preferred_locations": json.dumps(["Remote", "Bangalore", "Hyderabad", "Pune", "Mumbai"]),
    "min_salary": "400000",
    "notification_enabled": "true",
}


def create_data_directory() -> str:
    """
    Create the ``data/`` directory relative to the project root if it does
    not already exist.  Returns the absolute path of the directory.
    """
    data_dir = os.path.join(_project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def create_tables() -> None:
    """Create all SQLAlchemy-mapped tables (no-op if they already exist)."""
    Base.metadata.create_all(bind=engine)


def seed_default_settings(db) -> int:
    """
    Insert default ``UserSetting`` rows that do not already exist.
    Returns the number of rows actually inserted.
    """
    inserted = 0
    for key, value in DEFAULT_SETTINGS.items():
        existing = db.get(UserSetting, key)
        if existing is None:
            db.add(UserSetting(key=key, value=value))
            inserted += 1
    db.commit()
    return inserted


def init_db() -> None:
    """Run the full initialisation sequence and print a summary."""
    print("=" * 60)
    print("  ANSH AI JOBHUNTER – Database Initialisation")
    print("=" * 60)

    # 1. Data directory
    data_dir = create_data_directory()
    print(f"[1/3] Data directory ready: {data_dir}")

    # 2. Tables
    create_tables()
    table_names = list(Base.metadata.tables.keys())
    print(f"[2/3] Created / verified {len(table_names)} table(s):")
    for name in sorted(table_names):
        print(f"       - {name}")

    # 3. Default settings
    with SessionLocal() as db:
        inserted = seed_default_settings(db)
    if inserted:
        print(f"[3/3] Seeded {inserted} default UserSetting row(s).")
    else:
        print("[3/3] Default UserSettings already present – nothing inserted.")

    print("-" * 60)
    print("[OK]  Database initialisation complete.")
    print("=" * 60)


if __name__ == "__main__":
    init_db()
