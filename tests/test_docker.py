"""
Validation Test Suite for Dockerfiles and Docker Compose Specifications.
"""
from pathlib import Path
import pytest
import yaml

from src.utils.utils import get_absolute_path


def test_dockerfile_backend_exists():
    p = get_absolute_path("Dockerfile.backend")
    assert p.exists()
    content = p.read_text()
    assert "FROM python:3.11-slim" in content
    assert "EXPOSE 8000" in content
    assert "HEALTHCHECK" in content


def test_dockerfile_frontend_exists():
    p = get_absolute_path("Dockerfile.frontend")
    assert p.exists()
    content = p.read_text()
    assert "FROM nginx:alpine" in content
    assert "EXPOSE 80" in content
    assert "HEALTHCHECK" in content


def test_docker_compose_valid_yaml():
    p = get_absolute_path("docker-compose.local.yml")
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "services" in data
    assert "backend" in data["services"]
    assert "frontend" in data["services"]
    assert data["services"]["backend"]["ports"] == ["8000:8000"]
    assert data["services"]["frontend"]["ports"] == ["3000:80"]
