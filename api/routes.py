"""
Routes module for NIDS FastAPI Backend.
Defines API endpoints for root info, health check, model info, single flow prediction,
batch CSV upload prediction, metrics, feature importances, live alerts, WebSockets, SIEM, Threat Intelligence, SOAR Mitigation, Auth, and Audit Logs.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status

from api.dependencies import get_api_service
from api.schemas import (
    RootResponse,
    HealthResponse,
    ModelInfoResponse,
    SingleFlowRequest,
    SinglePredictionResponse,
    BatchSummaryResponse,
    MetricsResponse,
    FeatureImportanceResponse,
)
from api.services import APIService
from src.alert_engine import AlertEngine
from src.audit_logger import AuditLogger
from src.auth import AuthService
from src.ioc_manager import IOCManager
from src.rbac import RBACManager
from src.siem_connector import SIEMConnectorManager
from src.soar_engine import SOAREngine
from src.user_manager import UserManager
from src.websocket_server import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()
alert_engine = AlertEngine()
siem_manager = SIEMConnectorManager()
ioc_manager = IOCManager()
soar_engine = SOAREngine()
audit_logger = AuditLogger()
user_manager = UserManager()
auth_service = AuthService(user_manager=user_manager, audit_logger=audit_logger)


@router.get("/", response_model=RootResponse, summary="Get API Metadata", tags=["General"])
async def get_root(service: APIService = Depends(get_api_service)) -> Dict[str, Any]:
    """Returns project metadata, current status, and model load status."""
    return {
        "project_name": "Machine Learning-Based Network Intrusion Detection System",
        "version": "1.0.0",
        "status": "online",
        "model_loaded": service.model_loaded
    }


@router.get("/health", response_model=HealthResponse, summary="Check Health Status", tags=["General"])
async def get_health(service: APIService = Depends(get_api_service)) -> Dict[str, Any]:
    """Returns system health, prediction engine status, and model load state."""
    return {
        "healthy": service.model_loaded,
        "version": "1.0.0",
        "model_loaded": service.model_loaded,
        "prediction_engine_status": "active" if service.model_loaded else "inactive"
    }


@router.get("/model", response_model=ModelInfoResponse, summary="Get Model Details", tags=["Model Info"])
async def get_model_info(service: APIService = Depends(get_api_service)) -> Dict[str, Any]:
    """Returns model metadata, version, training date, and accuracy metrics."""
    return service.get_model_info()


@router.post(
    "/predict",
    response_model=SinglePredictionResponse,
    summary="Predict Single Network Flow",
    tags=["Inference"]
)
async def predict_single_flow(
    request: SingleFlowRequest,
    service: APIService = Depends(get_api_service)
) -> Dict[str, Any]:
    """
    Accepts a single network flow record dictionary/schema and returns
    predicted attack type, confidence, risk score (0-100), risk level, and class probabilities.
    """
    flow_dict = request.model_dump(by_alias=True)
    result = service.predict_single_flow(flow_dict)
    return result


@router.post(
    "/batch_predict",
    response_model=BatchSummaryResponse,
    summary="Batch Predict via CSV Upload",
    tags=["Inference"]
)
async def batch_predict_csv(
    file: UploadFile = File(..., description="Network traffic CSV file for batch inference"),
    service: APIService = Depends(get_api_service)
) -> Dict[str, Any]:
    """
    Accepts a CSV file upload containing network traffic flows.
    Executes batch inference, exports prediction_results.csv, and returns execution statistics.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are accepted for batch prediction."
        )

    file_bytes = await file.read()
    summary = service.predict_batch_csv(file_bytes, file.filename)
    return summary


@router.get("/metrics", response_model=MetricsResponse, summary="Get API & Prediction Metrics", tags=["Monitoring"])
async def get_api_metrics(service: APIService = Depends(get_api_service)) -> Dict[str, Any]:
    """Returns total requests served, prediction count, average latency (ms), and average confidence."""
    return service.get_metrics()


@router.get(
    "/feature_importance",
    response_model=FeatureImportanceResponse,
    summary="Get Top Feature Importances",
    tags=["Model Info"]
)
async def get_feature_importance(service: APIService = Depends(get_api_service)) -> Dict[str, Any]:
    """Returns top ranked features and normalized feature importances for the loaded classifier."""
    return service.get_feature_importance()


@router.get("/alerts", summary="Query Live Stored Alerts", tags=["Live Monitoring"])
async def get_alerts(
    protocol: Optional[str] = Query(None, description="Filter by protocol (TCP, UDP, ICMP)"),
    src_ip: Optional[str] = Query(None, description="Filter by Source IP"),
    dst_ip: Optional[str] = Query(None, description="Filter by Destination IP"),
    risk_level: Optional[str] = Query(None, description="Filter by Risk Level (Low, Medium, High, Critical)"),
    attack_type: Optional[str] = Query(None, description="Filter by Attack Category"),
    limit: int = Query(100, ge=1, le=1000)
) -> List[Dict[str, Any]]:
    """Queries stored intrusion alerts from SQLite database with multi-parameter filtering."""
    return alert_engine.query_alerts(
        protocol=protocol,
        src_ip=src_ip,
        dst_ip=dst_ip,
        risk_level=risk_level,
        attack_type=attack_type,
        limit=limit
    )


@router.get("/alerts/daily_report", summary="Get Daily Threat Statistics", tags=["Live Monitoring"])
async def get_daily_alert_report() -> Dict[str, Any]:
    """Returns daily threat summary report and statistics."""
    return alert_engine.generate_daily_report()


# ==========================================
# MODULE 12: SIEM & THREAT INTEL ENDPOINTS
# ==========================================

@router.get("/threats", summary="Get Threat Intelligence Summary & Enriched Alerts", tags=["SIEM & Threat Intel"])
async def get_threats(limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    """Returns threat intelligence enriched alert feed and provider status."""
    alerts = alert_engine.query_alerts(limit=limit)
    enriched_list = []
    for alt in alerts:
        enriched_list.append(siem_manager.process_and_export_alert(alt))

    return {
        "count": len(enriched_list),
        "threats": enriched_list,
        "providers": siem_manager.ti_enricher.enabled_providers
    }


@router.get("/ioc", summary="Get Active Indicators of Compromise (IOCs)", tags=["SIEM & Threat Intel"])
async def get_ioc_summary() -> Dict[str, Any]:
    """Returns whitelist, blacklist, and known malicious IP indicator rules."""
    return {
        "summary": ioc_manager.get_summary(),
        "whitelist": list(ioc_manager.whitelist),
        "blacklist": list(ioc_manager.blacklist),
        "known_malicious_ips": ioc_manager.known_malicious_ips
    }


@router.post("/webhook/test", summary="Test Webhook Dispatch", tags=["SIEM & Threat Intel"])
async def test_webhook(url: str = Query(..., description="Target Webhook URL to test")) -> Dict[str, Any]:
    """Tests dispatching a sample threat alert JSON payload to a target webhook URL."""
    test_alert = {
        "id": "ALT-TEST-9999",
        "timestamp": "2026-07-26 13:30:00",
        "attack_type": "DoS Hulk",
        "confidence": 0.9995,
        "risk_score": 89.5,
        "risk_level": "Critical",
        "src_ip": "185.220.101.5",
        "dst_ip": "10.0.0.1",
        "protocol": "TCP",
        "dst_port": 80
    }
    result = siem_manager.webhook_dispatcher.dispatch_alert(test_alert, target_url=url)
    return result


@router.get("/siem/status", summary="Get SIEM Connector Status", tags=["SIEM & Threat Intel"])
async def get_siem_status() -> Dict[str, Any]:
    """Returns connectivity and export metrics for Elastic, Splunk HEC, Microsoft Sentinel, Syslog, and Webhooks."""
    return siem_manager.get_status()


# ==========================================
# MODULE 13: SOAR ACTIVE MITIGATION ENDPOINTS
# ==========================================

@router.post("/mitigation/block_ip", summary="Enforce Firewall Block Rule", tags=["SOAR Mitigation"])
async def block_ip(ip_address: str = Query(..., description="Source IP address to block"), reason: str = Query("Manual SOC Block")) -> Dict[str, Any]:
    """Enforces an active firewall block rule on a target IP address."""
    return soar_engine.firewall.block_ip(ip_address, reason=reason)


@router.post("/mitigation/unblock_ip", summary="Remove Firewall Block Rule", tags=["SOAR Mitigation"])
async def unblock_ip(ip_address: str = Query(..., description="Source IP address to unblock")) -> Dict[str, Any]:
    """Removes an active firewall block rule for a target IP address."""
    return soar_engine.firewall.unblock_ip(ip_address)


@router.get("/mitigation/rules", summary="Get Active Mitigation Rules", tags=["SOAR Mitigation"])
async def get_mitigation_rules() -> Dict[str, Any]:
    """Returns active firewall block rules and mitigation history."""
    return soar_engine.get_summary()


@router.post("/playbook/execute", summary="Execute Threat Mitigation Playbook", tags=["SOAR Mitigation"])
async def execute_playbook(playbook_name: str = Query(..., description="Playbook name (dos_mitigation, port_scan_containment, botnet_isolation)"), target_ip: str = Query("185.220.101.5")) -> Dict[str, Any]:
    """Executes a target threat response playbook."""
    alert_payload = {
        "src_ip": target_ip,
        "attack_type": "DoS Hulk",
        "risk_score": 85.0,
        "dst_port": 80
    }
    return soar_engine.execute_playbook(playbook_name, alert_payload)


# ==========================================
# MODULE 14: AUTH, USER & AUDIT ENDPOINTS
# ==========================================

@router.post("/auth/login", summary="User Login & Token Generation", tags=["Authentication"])
async def login(username: str = Query(...), password: str = Query(...)) -> Dict[str, Any]:
    """Authenticates username & password and returns JWT Access & Refresh tokens."""
    try:
        return auth_service.login(username, password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/auth/logout", summary="User Logout", tags=["Authentication"])
async def logout(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Revokes the current JWT Access token."""
    token = authorization.replace("Bearer ", "") if authorization else ""
    return auth_service.logout(token)


@router.post("/auth/refresh", summary="Refresh Access Token", tags=["Authentication"])
async def refresh_token(refresh_token: str = Query(...)) -> Dict[str, Any]:
    """Generates a new access token using a valid refresh token."""
    try:
        return auth_service.refresh_access_token(refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/auth/me", summary="Get Current Authenticated User", tags=["Authentication"])
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Validates JWT access token and returns user details."""
    token = authorization.replace("Bearer ", "") if authorization else ""
    try:
        return auth_service.get_current_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/audit", summary="Get Security Audit Logs", tags=["Audit & Security"])
async def get_audit_logs(
    event_type: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
) -> List[Dict[str, Any]]:
    """Queries security audit logs across login, predictions, playbooks, and configuration changes."""
    return audit_logger.query_audit_logs(event_type=event_type, username=username, limit=limit)


@router.get("/users", summary="List All User Accounts", tags=["User Management"])
async def list_users() -> List[Dict[str, Any]]:
    """Returns list of all user accounts and assigned RBAC roles."""
    return user_manager.get_users_list()


@router.post("/users", summary="Create User Account", tags=["User Management"])
async def create_user(
    username: str = Query(...),
    password: str = Query(...),
    role: str = Query("SOC Analyst"),
    email: str = Query("")
) -> Dict[str, Any]:
    """Creates a new user account with role assignment."""
    try:
        return user_manager.create_user(username, password, role, email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{username}", summary="Delete User Account", tags=["User Management"])
async def delete_user(username: str) -> Dict[str, Any]:
    """Deletes a user account."""
    success = user_manager.delete_user(username)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {username} not found.")
    return {"status": "deleted", "username": username}


@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """WebSocket endpoint streaming live real-time threat predictions and alerts."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open for incoming messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
