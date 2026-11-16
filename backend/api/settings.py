"""
backend/api/settings.py
User preferences and automation runtime configuration endpoints.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from database.models import UserSetting

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class SettingsUpdateSchema(BaseModel):
    settings: Dict[str, Any]


class ModeUpdateSchema(BaseModel):
    mode: str


@router.get("/")
def get_all_settings(db: Session = Depends(get_db)):
    """Retrieve all runtime settings from DB."""
    rows = db.scalars(select(UserSetting)).all()
    result = {}
    for r in rows:
        try:
            result[r.key] = json.loads(r.value)
        except Exception:
            result[r.key] = r.value
    return result


@router.put("/")
def update_settings(data: SettingsUpdateSchema, db: Session = Depends(get_db)):
    """Update arbitrary settings key/values."""
    for key, val in data.settings.items():
        row = db.get(UserSetting, key)
        val_str = json.dumps(val) if isinstance(val, (dict, list, bool)) else str(val)
        if row:
            row.value = val_str
        else:
            db.add(UserSetting(key=key, value=val_str))
    db.commit()
    return {"status": "success"}


@router.get("/application-mode")
def get_mode(db: Session = Depends(get_db)):
    """Get active operating mode: DISCOVERY, PREPARE, or APPROVED."""
    row = db.get(UserSetting, "application_mode")
    return {"mode": row.value if row else "DISCOVERY"}


@router.put("/application-mode")
def set_mode(data: ModeUpdateSchema, db: Session = Depends(get_db)):
    """Switch operating mode."""
    valid_modes = ["DISCOVERY", "PREPARE", "APPROVED", "APPROVED_AUTO_SUBMIT"]
    mode_clean = data.mode.upper()
    if mode_clean not in valid_modes:
        mode_clean = "DISCOVERY"

    row = db.get(UserSetting, "application_mode")
    if row:
        row.value = mode_clean
    else:
        db.add(UserSetting(key="application_mode", value=mode_clean))
    db.commit()
    return {"mode": mode_clean, "status": "updated"}
