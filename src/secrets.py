"""
Secrets Manager module for NIDS.
Loads sensitive credentials, API keys, and JWT secrets from environment variables and .env.
"""
import os
import logging
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from src.utils.utils import get_absolute_path

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages loading and retrieval of secret keys, API tokens, and JWT configuration.
    """

    def __init__(self, env_file: str = ".env"):
        self.env_path = get_absolute_path(env_file)
        if DOTENV_AVAILABLE and self.env_path.exists():
            load_dotenv(self.env_path)
            logger.info("Loaded environment variables from %s", self.env_path)

        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "cortex_default_jwt_secret_key_change_in_production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")

        self.abuseipdb_key = os.getenv("ABUSEIPDB_API_KEY", "")
        self.virustotal_key = os.getenv("VIRUSTOTAL_API_KEY", "")
        self.otx_key = os.getenv("OTX_API_KEY", "")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves an environment variable."""
        return os.getenv(key, default)


# Global SecretsManager singleton
secrets_manager = SecretsManager()
