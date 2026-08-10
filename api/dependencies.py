"""
Dependencies module for NIDS FastAPI Backend.
Provides dependency injection functions for routes.
"""
from typing import Generator
from api.services import APIService, get_api_service_instance


def get_api_service() -> APIService:
    """
    Dependency injection provider returning the singleton APIService instance.
    """
    return get_api_service_instance()

