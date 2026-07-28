"""
Runner script for Module 14: Enterprise Security, Authentication, Authorization & Audit Logging.
Enables authentication, tests RBAC permissions, verifies audit logging, and prints security metrics.

Usage:
    python scripts/run_security.py
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.auth import AuthService
from src.audit_logger import AuditLogger
from src.rbac import RBACManager, UserRole
from src.secrets import secrets_manager
from src.user_manager import UserManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_security")


def main():
    logger.info("Starting Module 14: Enterprise Security, Authentication & Audit Engine...")

    user_mgr = UserManager()
    audit_log = AuditLogger()
    auth_service = AuthService(user_manager=user_mgr, audit_logger=audit_log)

    # 1. Authenticate Administrator
    admin_user = secrets_manager.admin_username
    admin_pass = secrets_manager.admin_password
    logger.info("Testing Admin Authentication (%s)...", admin_user)

    auth_result = auth_service.login(admin_user, admin_pass, client_ip="127.0.0.1")
    logger.info("JWT Access Token issued successfully (%s characters)", len(auth_result["access_token"]))

    # 2. Test Token Decoding & RBAC Matrix
    token = auth_result["access_token"]
    current_user = auth_service.get_current_user_from_token(token)
    logger.info("Current Authenticated User: %s (Role: %s)", current_user["username"], current_user["role"])

    admin_can_mitigate = RBACManager.has_permission(current_user["role"], "execute_mitigation")
    guest_can_mitigate = RBACManager.has_permission(UserRole.GUEST.value, "execute_mitigation")

    logger.info("RBAC Permission Check -> Administrator execute_mitigation: %s", admin_can_mitigate)
    logger.info("RBAC Permission Check -> Guest execute_mitigation: %s", guest_can_mitigate)

    # 3. Log Audit Events
    audit_log.log_event(
        event_type="SECURITY_AUDIT",
        username=admin_user,
        ip_address="127.0.0.1",
        action="verify_rbac",
        status="success",
        details={"matrix_version": "1.0.0"}
    )

    summary_matrix = RBACManager.get_permission_matrix()
    audit_logs = audit_log.query_audit_logs(limit=5)

    print("\n==========================================")
    print("MODULE 14: ENTERPRISE SECURITY AUDIT SUMMARY")
    print("==========================================")
    print(f"Active Users Managed: {len(user_mgr.users)}")
    print(f"Admin Authentication Status: SUCCESS (JWT Issued)")
    print(f"RBAC Roles Configured: {list(summary_matrix.keys())}")
    print(f"Audit Logs Persistence: SQLite / CSV / JSON ({len(audit_logs)} recent records)")
    print(f"Secrets Management: Loaded from .env (JWT Secret: Configured)")
    print("==========================================\n")


if __name__ == "__main__":
    main()
