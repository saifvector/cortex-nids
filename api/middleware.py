"""
Middleware module for NIDS FastAPI Backend.
Includes request logging middleware, simple rate limiting middleware, and CORS configuration.
"""
import logging
import time
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.metrics_manager import metrics_manager

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter tracker: IP -> List[timestamps]
_RATE_LIMIT_STORE: Dict[str, list] = {}
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW_SEC = 60  # Window in seconds


def setup_cors(app: FastAPI) -> None:
    """
    Configures Cross-Origin Resource Sharing (CORS) middleware.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("Configured CORS middleware for all origins (*).")


def setup_middleware(app: FastAPI) -> None:
    """
    Registers request logging and rate limiting middleware on FastAPI app.
    """
    setup_cors(app)

    @app.middleware("http")
    async def request_logging_and_rate_limit(request: Request, call_next: Callable) -> Response:
        metrics_manager.increment_requests()
        t0 = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        # 1. Rate Limiting Check
        now = time.time()
        timestamps = _RATE_LIMIT_STORE.get(client_ip, [])
        # Filter timestamps within window
        valid_timestamps = [ts for ts in timestamps if now - ts < RATE_LIMIT_WINDOW_SEC]
        _RATE_LIMIT_STORE[client_ip] = valid_timestamps

        if len(valid_timestamps) >= RATE_LIMIT_REQUESTS:
            logger.warning("Rate limit exceeded for IP %s on path %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error",
                    "error_type": "RateLimitExceeded",
                    "message": "Too many requests. Please slow down.",
                    "path": str(request.url.path)
                }
            )

        _RATE_LIMIT_STORE[client_ip].append(now)

        # 2. Process Request & Measure Duration
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.info(
                "%s %s -> HTTP %d (%.2f ms) [IP: %s]",
                request.method, request.url.path, response.status_code, duration_ms, client_ip
            )
            response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            logger.error(
                "Error processing %s %s (%.2f ms): %s",
                request.method, request.url.path, duration_ms, e
            )
            raise e
