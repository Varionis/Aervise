from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def landing_page(request: Request) -> HTMLResponse:
    response = TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "default_message": "Can I go for a run right now for 30 minutes?",
            "default_lat": 43.6532,
            "default_lon": -79.3832,
        },
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
