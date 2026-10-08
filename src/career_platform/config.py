from __future__ import annotations

import os
from pathlib import Path


def data_directory() -> Path:
    configured_path = os.getenv("CAREER_PLATFORM_DATA_DIR")
    data_path = Path(configured_path) if configured_path else Path.cwd() / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is not set")
    return url


def fallback_path() -> Path:
    configured_path = os.getenv("CAREER_PLATFORM_FALLBACK")
    return Path(configured_path) if configured_path else data_directory() / "profile_fallback.json"
