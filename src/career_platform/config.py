from __future__ import annotations

import os
from pathlib import Path


def data_directory() -> Path:
    configured_path = os.getenv("CAREER_PLATFORM_DATA_DIR")
    data_path = Path(configured_path) if configured_path else Path.cwd() / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def database_path() -> Path:
    configured_path = os.getenv("CAREER_PLATFORM_DATABASE")
    return Path(configured_path) if configured_path else data_directory() / "career_platform.db"


def fallback_path() -> Path:
    configured_path = os.getenv("CAREER_PLATFORM_FALLBACK")
    return Path(configured_path) if configured_path else data_directory() / "profile_fallback.json"
