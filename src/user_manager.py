"""
User Manager module for NIDS.
Handles user creation, deletion, disabling, password reset, and session management.
"""
import logging, time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.jwt_manager import jwt_manager
from src.rbac import UserRole
from src.secrets import secrets_manager
from src.utils.utils import ensure_directory, get_absolute_path, load_json, save_json

logger = logging.getLogger(__name__)


class UserManager:
    """
    Manages platform user accounts, authentication credentials, role assignments, and sessions.
    """

    def __init__(self, db_path: Union[str, Path] = "predictions/users_database.json"):
        self.db_path = get_absolute_path(db_path)
        ensure_directory(self.db_path.parent)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        self._load_users()

    def _load_users(self) -> None:
        """Loads user accounts from JSON file or creates default admin account."""
        if self.db_path.exists():
            try:
                data = load_json(self.db_path)
                self.users = data.get("users", {})
                logger.info("Loaded %d user accounts from %s", len(self.users), self.db_path)
                return
            except Exception as e:
                logger.error("Failed loading user accounts: %s", e)

        # Create default Admin account from secrets
        admin_pass_hash = jwt_manager.hash_password(secrets_manager.admin_password)
        self.users = {
            secrets_manager.admin_username: {
                "id": "USR-1001",
                "username": secrets_manager.admin_username,
                "password_hash": admin_pass_hash,
                "role": UserRole.ADMINISTRATOR.value,
                "email": "admin@cortex-nids.local",
                "is_active": True,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "analyst": {
                "id": "USR-1002",
                "username": "analyst",
                "password_hash": jwt_manager.hash_password("AnalystPassword123!"),
                "role": UserRole.SOC_ANALYST.value,
                "email": "analyst@cortex-nids.local",
                "is_active": True,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        self.save_users()

    def save_users(self) -> None:
        """Saves current user accounts to JSON file."""
        save_json({"users": self.users}, self.db_path)

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates username and password against stored PBKDF2 hashes.
        Returns user dictionary if valid and active, else None.
        """
        user = self.users.get(username)
        if not user or not user.get("is_active", False):
            return None

        if jwt_manager.verify_password(password, user["password_hash"]):
            logger.info("User %s authenticated successfully.", username)
            return user
        return None

    def create_user(self, username: str, password: str, role: str = "SOC Analyst", email: str = "") -> Dict[str, Any]:
        """Creates a new user account."""
        if username in self.users:
            raise ValueError(f"User {username} already exists.")

        user_id = f"USR-{int(time.time() * 1000) % 10000}"
        user_record = {
            "id": user_id,
            "username": username,
            "password_hash": jwt_manager.hash_password(password),
            "role": role,
            "email": email or f"{username}@cortex-nids.local",
            "is_active": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.users[username] = user_record
        self.save_users()
        logger.info("Created user account %s (%s)", username, role)
        return user_record

    def delete_user(self, username: str) -> bool:
        """Deletes a user account."""
        if username in self.users:
            self.users.pop(username)
            self.save_users()
            logger.info("Deleted user account %s", username)
            return True
        return False

    def disable_user(self, username: str) -> bool:
        """Disables a user account."""
        if username in self.users:
            self.users[username]["is_active"] = False
            self.save_users()
            logger.info("Disabled user account %s", username)
            return True
        return False

    def get_users_list(self) -> List[Dict[str, Any]]:
        """Returns list of user accounts without password hashes."""
        result = []
        for u in self.users.values():
            rec = u.copy()
            rec.pop("password_hash", None)
            result.append(rec)
        return result
