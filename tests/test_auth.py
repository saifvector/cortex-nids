"""
Unit Test Suite for NIDS Authentication, JWT & User Management.
"""
import pytest
from src.auth import AuthService
from src.jwt_manager import jwt_manager
from src.secrets import secrets_manager
from src.user_manager import UserManager


def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = jwt_manager.hash_password(pwd)
    assert hashed != pwd
    assert jwt_manager.verify_password(pwd, hashed) is True
    assert jwt_manager.verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding():
    payload = {"sub": "admin", "role": "Administrator"}
    token = jwt_manager.create_access_token(payload)
    assert isinstance(token, str)

    decoded = jwt_manager.decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "Administrator"


def test_auth_service_admin_login():
    user_mgr = UserManager()
    auth_service = AuthService(user_manager=user_mgr)

    res = auth_service.login(secrets_manager.admin_username, secrets_manager.admin_password)
    assert "access_token" in res
    assert "refresh_token" in res
    assert res["user"]["role"] == "Administrator"


def test_auth_service_invalid_login():
    user_mgr = UserManager()
    auth_service = AuthService(user_manager=user_mgr)

    with pytest.raises(ValueError):
        auth_service.login("invalid_user", "invalid_password")


def test_auth_service_token_refresh():
    user_mgr = UserManager()
    auth_service = AuthService(user_manager=user_mgr)

    login_res = auth_service.login(secrets_manager.admin_username, secrets_manager.admin_password)
    refresh_res = auth_service.refresh_access_token(login_res["refresh_token"])
    assert "access_token" in refresh_res
    assert refresh_res["token_type"] == "bearer"


def test_user_creation_and_deletion():
    user_mgr = UserManager()
    test_user = f"test_analyst_{pytest.__version__.replace('.', '')}"

    if test_user in user_mgr.users:
        user_mgr.delete_user(test_user)

    created = user_mgr.create_user(test_user, "Password123!", role="SOC Analyst")
    assert created["username"] == test_user
    assert created["role"] == "SOC Analyst"

    deleted = user_mgr.delete_user(test_user)
    assert deleted is True
