"""
Main FastAPI Application module for NIDS Production Backend.
Initializes FastAPI instance, attaches middleware, registers exception handlers, and mounts routes.
"""
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

venv_site_packages = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
if venv_site_packages.exists() and str(venv_site_packages) not in sys.path:
    sys.path.insert(0, str(venv_site_packages))

from fastapi import FastAPI

from api.exceptions import setup_exception_handlers
from api.middleware import setup_middleware
from api.routes import router
from src.config.config import ConfigManager
from src.utils.logging import configure_logging

# Configure system logging
try:
    config_manager = ConfigManager()
    config_manager.initialize()
    configure_logging(config_manager.settings)
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("NIDS.api")

app = FastAPI(
    title="Network Intrusion Detection System (NIDS) REST API",
    description="Production-grade FastAPI backend exposing trained ensemble intrusion detection models, risk scoring, and CSV batch prediction.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

from fastapi.staticfiles import StaticFiles

# Setup middleware (CORS, Rate Limiting, Request Logging)
setup_middleware(app)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(router)

# Mount Static File Directories for Reports and Predictions
reports_path = PROJECT_ROOT / "reports"
predictions_path = PROJECT_ROOT / "predictions"

if reports_path.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_path)), name="reports")
if predictions_path.exists():
    app.mount("/predictions", StaticFiles(directory=str(predictions_path)), name="predictions")

logger.info("NIDS FastAPI Backend Application initialized successfully.")
