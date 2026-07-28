"""
Authentication service module for NIDS.
Orchestrates login, logout, refresh tokens, and current user validation.
"""
import logging
from typing import Any, Dict, Optional, Tuple

from src.jwt_manager import jwt_manager
from src.user_manager import UserManager
from src.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles user login, token refresh, session revocation, and current user retrieval.
    """

    def __init__(self, user_manager: Optional[UserManager] = None, audit_logger: Optional[AuditLogger] = None):
        self.user_manager = user_manager or UserManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.revoked_tokens = set()

    def login(self, username: str, password: str, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Authenticates credentials and returns JWT Access & Refresh tokens.
        """
        user = self.user_manager.authenticate_user(username, password)
        if not user:
            self.audit_logger.log_event(
                event_type="LOGIN",
                username=username,
                ip_address=client_ip,
                action="authenticate",
                status="failure",
                details={"reason": "Invalid credentials or inactive account"}
            )
            raise ValueError("Invalid username or password.")

        token_payload = {
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"]
        }

        access_token = jwt_manager.create_access_token(token_payload)
        refresh_token = jwt_manager.create_refresh_token(token_payload)

        self.audit_logger.log_event(
            event_type="LOGIN",
            username=username,
            ip_address=client_ip,
            action="authenticate",
            status="success",
            details={"role": user["role"]}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": jwt_manager.access_expire_minutes * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "email": user.get("email")
            }
        }

    def logout(self, token: str, username: str = "unknown", client_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Revokes an active access token.
        """
        self.revoked_tokens.add(token)
        self.audit_logger.log_event(
            event_type="LOGOUT",
            username=username,
            ip_address=client_ip,
            action="logout",
            status="success"
        )
        return {"status": "logged_out", "message": "Successfully logged out."}

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Issues a new access token using a valid refresh token.
        """
        payload = jwt_manager.decode_token(refresh_token)
        if not payload or payload.get("token_type") != "refresh":
            raise ValueError("Invalid or expired refresh token.")

        username = payload.get("sub")
        user = self.user_manager.users.get(username)
        if not user or not user.get("is_active"):
            raise ValueError("User account is inactive or not found.")

        new_access_token = jwt_manager.create_access_token({
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"]
        })

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": jwt_manager.access_expire_minutes * 60
        }

    def get_current_user_from_token(self, token: str) -> Dict[str, Any]:
        """
        Validates token and returns current user details.
        """
        if token in self.revoked_tokens:
            raise ValueError("Token has been revoked.")

        payload = jwt_manager.decode_token(token)
        if not payload or payload.get("token_type") != "access":
            raise ValueError("Invalid or expired access token.")

        username = payload.get("sub")
        user = self.user_manager.users.get(username)
        if not user or not user.get("is_active"):
            raise ValueError("User account inactive or not found.")

        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user.get("email")
        }
