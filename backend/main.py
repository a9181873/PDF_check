from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes_compare import router as compare_router
from api.routes_checklist import router as checklist_router
from api.routes_export import router as export_router
from api.routes_project import router as project_router
from api.routes_review import router as review_router
from api.websocket import router as websocket_router
from config import settings
from models.database import ensure_default_project, init_db

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compare_router)
app.include_router(project_router)
app.include_router(review_router)
app.include_router(checklist_router)
app.include_router(export_router)
app.include_router(websocket_router)


@app.on_event("startup")
def on_startup() -> None:
    settings.old_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.new_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    settings.markdown_export_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    ensure_default_project()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


static_dir = Path(__file__).resolve().parent / "static"

# Keep the SPA fallback mount last so API and health routes remain reachable.
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir, check_dir=False), name="uploads")
app.mount("/", StaticFiles(directory=static_dir, html=True, check_dir=False), name="static")
