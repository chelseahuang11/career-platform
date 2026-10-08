from __future__ import annotations

import logging
import re
import psycopg
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from markupsafe import Markup, escape
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import fallback_path
from .database import get_profile, get_projects, init_db
from .models import Profile, Project

BASE_DIR = Path(__file__).resolve().parent
RESUME_PDF = BASE_DIR / "static" / "files" / "Chelsea_Huang_Resume.pdf"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

FIGURE = re.compile(r"\$?\d[\d,.]*\d[%MKB]?|\$?\d[%MKB]?")


def figures(text: str) -> Markup:
    """Wrap each number in <strong> so project results stand out from the prose."""
    parts = FIGURE.split(text)
    numbers = FIGURE.findall(text)
    marked = Markup(escape(parts[0]))
    for number, rest in zip(numbers, parts[1:]):
        marked += Markup("<strong>") + escape(number) + Markup("</strong>") + escape(rest)
    return marked


templates.env.filters["figures"] = figures

app = FastAPI(title="Career Platform", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

logger = logging.getLogger(__name__)


def load_fallback() -> tuple[Profile, list[Project]]:
    import json

    fallback = json.loads(fallback_path().read_text(encoding="utf-8"))
    profile = Profile(**fallback["profile"])
    projects = [Project(**project) for project in fallback["projects"]]
    return profile, projects


def load_public_content() -> tuple[Profile, list[Project]]:
    try:
        return get_profile(), get_projects()
    except (OSError, psycopg.Error, ValueError):
        logger.exception("Database unavailable; serving the public profile fallback")
        return load_fallback()


try:
    init_db()
except (OSError, psycopg.Error, ValueError):
    logger.exception("Database initialization failed; the public fallback remains available")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def home(request: Request):
    profile, projects = load_public_content()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "profile": profile,
            "projects": projects,
        },
    )


@app.get("/resume")
async def resume(request: Request):
    if RESUME_PDF.is_file():
        return FileResponse(
            RESUME_PDF,
            media_type="application/pdf",
            filename=RESUME_PDF.name,
            content_disposition_type="inline",
        )

    # Without the PDF, fall back to the resume page built from the database.
    profile, projects = load_public_content()
    response = templates.TemplateResponse(
        request,
        "resume.html",
        {
            "profile": profile,
            "projects": projects,
        },
    )
    response.headers["Content-Disposition"] = 'attachment; filename="resume.html"'
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
