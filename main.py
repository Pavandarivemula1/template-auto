"""
main.py – FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from database import Base, engine
import models  # noqa: F401
from routes.client   import router as client_router
from routes.template import router as template_router
from routes.admin    import router as admin_router
from routes.deploy   import router as deploy_router
from config import GENERATED_SITES_DIR

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Template Modification Engine",
    description = "Multi-page personalized website generator with preprocessing.",
    version     = "3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    GENERATED_SITES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Database tables verified ✓")
    logger.info("Generated sites dir: %s", GENERATED_SITES_DIR)

# ── Static Files ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Shared UI assets (CSS for the intake/preview forms)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Template CSS/JS/images served at /tmpl/{template_name}/...
app.mount("/tmpl", StaticFiles(directory=str(BASE_DIR / "templates")), name="tmpl")

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(client_router)
app.include_router(template_router)
app.include_router(admin_router)   # /admin/* - preprocessing and template management
app.include_router(deploy_router)  # /deploy/{id} - Vercel deployment

