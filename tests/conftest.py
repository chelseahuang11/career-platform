import os
import tempfile
from pathlib import Path

# Importing the app runs init_db(), which writes to the configured database.
# Point every test at a throwaway directory before any test module imports it,
# so the real data/career_platform.db is never touched.
_test_data_dir = tempfile.mkdtemp(prefix="career-platform-tests-")
os.environ["CAREER_PLATFORM_DATA_DIR"] = _test_data_dir
os.environ["CAREER_PLATFORM_DATABASE"] = str(Path(_test_data_dir) / "career_platform.db")
os.environ["CAREER_PLATFORM_FALLBACK"] = str(
    Path(__file__).resolve().parents[1] / "data" / "profile_fallback.json"
)
