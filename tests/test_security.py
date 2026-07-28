"""
Security Test Suite for NIDS Security Headers, Rate Limiting & RBAC Permissions.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.rbac import RBACManager, UserRole
from src.security import RateLimiter, security_manager

client = TestClient(app)


def test_security_headers_present():
    headers = security_manager.get_security_headers()
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-XSS-Protection") == "1; mode=block"


def test_rbac_permission_matrix():
    assert RBACManager.has_permission(UserRole.ADMINISTRATOR.value, "execute_mitigation") is True
    assert RBACManager.has_permission(UserRole.ADMINISTRATOR.value, "manage_users") is True

    assert RBACManager.has_permission(UserRole.SOC_ANALYST.value, "execute_mitigation") is True
    assert RBACManager.has_permission(UserRole.SOC_ANALYST.value, "manage_users") is False

    assert RBACManager.has_permission(UserRole.READ_ONLY.value, "execute_mitigation") is False
    assert RBACManager.has_permission(UserRole.READ_ONLY.value, "view_alerts") is True

    assert RBACManager.has_permission(UserRole.GUEST.value, "execute_mitigation") is False


def test_rate_limiter_logic():
    limiter = RateLimiter(requests_per_minute=5)
    ip = "192.168.1.99"

    for _ in range(5):
        assert limiter.is_allowed(ip) is True

    # 6th request exceeds 5 reqs/min limit
    assert limiter.is_allowed(ip) is False


def test_unauthorized_token_rejection():
    res = client.get("/auth/me", headers={"Authorization": "Bearer invalid_fake_token_12345"})
    assert res.status_code == 401
