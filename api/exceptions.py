"""
Exceptions module for NIDS FastAPI Backend.
Defines custom API exception classes and global exception handlers.
"""
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class NIDSAPIException(Exception):
    """Base exception class for API errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ModelNotLoadedException(NIDSAPIException):
    """Raised when prediction engine or model checkpoint fails to load."""

    def __init__(self, detail: str = "Machine Learning model is not loaded."):
        super().__init__(detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class InvalidInputFormatException(NIDSAPIException):
    """Raised when input feature data is missing columns, unparseable, or invalid."""

    def __init__(self, detail: str = "Invalid input feature format or schema."):
        super().__init__(detail, status_code=status.HTTP_400_BAD_REQUEST)


class BatchProcessingException(NIDSAPIException):
    """Raised when CSV batch upload or chunk processing fails."""

    def __init__(self, detail: str = "Batch prediction processing failed."):
        super().__init__(detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers on the FastAPI application instance.
    """

    @app.exception_handler(NIDSAPIException)
    async def nids_api_exception_handler(request: Request, exc: NIDSAPIException):
        logger.error("NIDS API Exception on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_type": exc.__class__.__name__,
                "message": exc.message,
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation Error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "error_type": "ValidationError",
                "message": "Input validation failed. Please check feature names and types.",
                "details": exc.errors(),
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP Exception %d on %s: %s", exc.status_code, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_type": "HTTPException",
                "message": str(exc.detail),
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled Server Exception on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error_type": "InternalServerError",
                "message": f"An internal server error occurred: {str(exc)}",
                "path": str(request.url.path)
            }
        )
