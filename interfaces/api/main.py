from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from interfaces.api.routes import decision_router, health_router, interaction_router, ui_router
from config import get_settings
from observability.logger import configure_logging


settings = get_settings()
configure_logging(settings.log_dir, settings.log_level)

app = FastAPI(
    title="Aervise API",
    version="0.1.0",
    description="Environmental decision engine API for real-time outdoor recommendations.",
)

app.mount("/static", StaticFiles(directory="interfaces/api/static"), name="static")

app.include_router(ui_router)
app.include_router(health_router)
app.include_router(interaction_router)
app.include_router(decision_router)
