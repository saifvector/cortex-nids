"""
Role-Based Access Control (RBAC) module for NIDS.
Defines system roles and permission enforcement matrices.
"""
from enum import Enum
import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    ADMINISTRATOR = "Administrator"
    SOC_ANALYST = "SOC Analyst"
    SECURITY_ENGINEER = "Security Engineer"
    READ_ONLY = "Read Only"
    GUEST = "Guest"


# System Permission Matrix
ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.ADMINISTRATOR: {
        "read", "predict", "batch_predict", "view_alerts", "stream_ws",
        "configure_siem", "manage_ioc", "execute_mitigation", "manage_users",
        "view_audit", "export_reports"
    },
    UserRole.SECURITY_ENGINEER: {
        "read", "predict", "batch_predict", "view_alerts", "stream_ws",
        "configure_siem", "manage_ioc", "execute_mitigation", "export_reports"
    },
    UserRole.SOC_ANALYST: {
        "read", "predict", "batch_predict", "view_alerts", "stream_ws",
        "execute_mitigation", "export_reports"
    },
    UserRole.READ_ONLY: {
        "read", "view_alerts", "stream_ws", "export_reports"
    },
    UserRole.GUEST: {
        "read"
    }
}


class RBACManager:
    """
    Enforces Role-Based Access Control permissions across platform operations.
    """

    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """
        Checks if a user role possesses the target permission string.
        """
        try:
            enum_role = UserRole(role)
            allowed_permissions = ROLE_PERMISSIONS.get(enum_role, set())
            return permission in allowed_permissions
        except Exception:
            return False

    @staticmethod
    def get_permission_matrix() -> Dict[str, List[str]]:
        """
        Returns full permission matrix for security audit reporting.
        """
        return {r.value: sorted(list(perms)) for r, perms in ROLE_PERMISSIONS.items()}
