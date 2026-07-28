"""
JWT Manager module for NIDS.
Handles JWT token generation, decoding, verification, and secure PBKDF2 password hashing.
"""
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import jwt

from src.secrets import secrets_manager

logger = logging.getLogger(__name__)


class JWTManager:
    """
    Manages JWT Access Tokens, Refresh Tokens, and PBKDF2 Password Hashing.
    """

    def __init__(self):
        self.secret_key = secrets_manager.jwt_secret
        self.algorithm = secrets_manager.jwt_algorithm
        self.access_expire_minutes = secrets_manager.access_token_expire_minutes
        self.refresh_expire_days = secrets_manager.refresh_token_expire_days

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes password using PBKDF2-HMAC-SHA256 with a random 16-byte salt.
        Returns format: salt_hex$hash_hex
        """
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return f"{salt.hex()}${pwd_hash.hex()}"

    @staticmethod
    def verify_password(password: str, hashed_digest: str) -> bool:
        """
        Verifies input password against PBKDF2 salt$hash digest string using hmac.compare_digest.
        """
        try:
            parts = hashed_digest.split("$")
            if len(parts) != 2:
                return False
            salt = bytes.fromhex(parts[0])
            expected_hash = bytes.fromhex(parts[1])
            actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
            return hmac.compare_digest(actual_hash, expected_hash)
        except Exception as e:
            logger.error("Password verification error: %s", e)
            return False

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Encodes a JWT Access Token.
        """
        to_encode = data.copy()
        now = datetime.utcnow()
        expire = now + (expires_delta or timedelta(minutes=self.access_expire_minutes))
        to_encode.update({"iat": now, "exp": expire, "token_type": "access"})
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Encodes a JWT Refresh Token.
        """
        to_encode = data.copy()
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_expire_days)
        to_encode.update({"iat": now, "exp": expire, "token_type": "refresh"})
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes and verifies a JWT token. Returns payload dict or None if invalid/expired.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT Token has expired.")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT Token: %s", e)
            return None


# Global JWTManager singleton
jwt_manager = JWTManager()
