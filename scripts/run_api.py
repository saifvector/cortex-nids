#!/usr/bin/env python
"""
API Server runner script for NIDS.
Launches Uvicorn ASGI server serving the FastAPI backend.
"""
import sys
import argparse
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add project .venv site-packages if running outside virtualenv
venv_site_packages = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
if venv_site_packages.exists() and str(venv_site_packages) not in sys.path:
    sys.path.insert(0, str(venv_site_packages))

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="NIDS FastAPI Production Server Runner")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    logging.info("=" * 60)
    logging.info("Starting NIDS Production FastAPI Backend Server")
    logging.info("Binding to %s:%d", args.host, args.port)
    logging.info("Swagger Documentation: http://localhost:%d/docs", args.port)
    logging.info("ReDoc Documentation:   http://localhost:%d/redoc", args.port)
    logging.info("=" * 60)

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
