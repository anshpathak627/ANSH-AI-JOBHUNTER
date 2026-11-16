"""
config/settings.py
Application-wide configuration loaded from environment variables / .env file.
Uses pydantic-settings for type-safe, validated settings with a singleton accessor.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configurable values for ANSH AI JOBHUNTER.
    Values are read from environment variables or a .env file at the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///./data/jobhunter.db",
        description="SQLAlchemy database connection URL.",
    )

    # ── Telegram ──────────────────────────────────────────────────────────────
    telegram_bot_token: Optional[str] = Field(
        default=None,
        description="Token issued by @BotFather for the Telegram bot.",
    )
    telegram_chat_id: Optional[str] = Field(
        default=None,
        description="Telegram chat/channel ID to send notifications to.",
    )

    # ── Email (SMTP) ──────────────────────────────────────────────────────────
    email_smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname.",
    )
    email_smtp_port: int = Field(
        default=587,
        description="SMTP server port (typically 587 for STARTTLS).",
    )
    email_username: Optional[str] = Field(
        default=None,
        description="SMTP authentication username (usually the full email address).",
    )
    email_password: Optional[str] = Field(
        default=None,
        description="SMTP authentication password or app-specific password.",
    )
    email_to: Optional[str] = Field(
        default=None,
        description="Destination email address for notifications.",
    )

    # ── Ollama / Local LLM ────────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL of the local Ollama server.",
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Ollama model tag to use for AI-powered matching and generation.",
    )

    # ── AI Matching ───────────────────────────────────────────────────────────
    use_ai_matching: bool = Field(
        default=False,
        description="Enable Ollama-based AI job matching. Falls back to rule-based when False.",
    )

    # ── Throttling ────────────────────────────────────────────────────────────
    max_applications_per_day: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Hard cap on the number of job applications submitted per calendar day.",
    )

    # ── Scheduler ─────────────────────────────────────────────────────────────
    scan_interval_hours: int = Field(
        default=8,
        ge=1,
        le=168,
        description="How often (in hours) the scraper scans company career pages.",
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str = Field(
        default="change_this_to_a_random_secret",
        description="Secret key used for signing tokens and sessions.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application Settings singleton.

    Usage::

        from config.settings import get_settings
        cfg = get_settings()
        print(cfg.database_url)

    The first call constructs and validates the Settings object (reading .env
    if present).  Subsequent calls return the same object from the LRU cache.
    """
    return Settings()
