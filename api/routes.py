"""
Routes module for NIDS FastAPI Backend.
Defines API endpoints for root info, health check, model info, single flow prediction,
batch CSV upload prediction, metrics, feature importances, live alerts, WebSockets, SIEM, Threat Intelligence, SOAR Mitigation, Auth, and Audit Logs.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Response, UploadFile, WebSocket, WebSocketDisconnect, status

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
from src.report_engine import DynamicReportEngine
from src.rbac import RBACManager
from src.siem_connector import SIEMConnectorManager
from src.soar_engine import SOAREngine
from src.user_manager import UserManager
from src.websocket_server import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()
alert_engine = AlertEngine()
report_engine = DynamicReportEngine()
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


    return summary


@router.get("/metrics", response_model=MetricsResponse, summary="Get Active Session Metrics", tags=["Monitoring"])
async def get_api_metrics(service: APIService = Depends(get_api_service)) -> Dict[str, Any]:
    """Returns active in-memory session metrics (resets to zero when backend starts)."""
    return service.get_metrics()


@router.post("/metrics/record", summary="Record Live Session Metric Event", tags=["Monitoring"])
async def record_session_metric(payload: Dict[str, Any]) -> Dict[str, str]:
    """Records a live prediction event into active SessionMetricsManager."""
    from api.session_metrics import session_metrics_manager
    session_metrics_manager.record_prediction(
        attack_type=payload.get("attack_type", "BENIGN"),
        confidence=float(payload.get("confidence", 0.99)),
        risk_score=float(payload.get("risk_score", 0.0)),
        risk_level=payload.get("risk_level", "Low"),
        latency_ms=float(payload.get("latency_ms", 0.035)),
        count=int(payload.get("count", 1))
    )
    return {"status": "success"}


@router.post("/metrics/reset", summary="Reset Active Session Metrics", tags=["Monitoring"])
async def reset_session_metrics() -> Dict[str, str]:
    """Resets all session metric counters to zero."""
    from api.session_metrics import session_metrics_manager
    session_metrics_manager.reset()
    return {"status": "reset", "message": "Session metrics reset to zero"}


# ==========================================
# DYNAMIC REPORTING ENGINE ENDPOINTS
# ==========================================

@router.get("/reports/generate", summary="Generate Fresh Dynamic Security Report", tags=["Reports Engine"])
async def generate_dynamic_report() -> Dict[str, Any]:
    """Triggers fresh live report compilation pulling directly from predictions/alerts.db and active session metrics."""
    data = report_engine.get_live_report_data()
    return {
        "status": "success",
        "message": "Report compiled dynamically from alerts.db",
        "timestamp": data.get("timestamp"),
        "total_flows": data.get("db_summary", {}).get("total_flows_ever", 0),
        "total_attacks": data.get("db_summary", {}).get("total_attacks_ever", 0),
        "session_predictions": data.get("session_metrics", {}).get("prediction_count", 0)
    }


@router.get("/reports/download/html", summary="Download Fresh HTML Security Report", tags=["Reports Engine"])
async def download_html_report():
    """Generates and downloads a fresh responsive HTML security report compiled from alerts.db."""
    html_content = report_engine.generate_html_report()
    headers = {"Content-Disposition": "inline; filename=cortex_security_report.html"}
    return Response(content=html_content, media_type="text/html", headers=headers)


@router.get("/reports/download/pdf", summary="Download Fresh PDF Security Report", tags=["Reports Engine"])
async def download_pdf_report():
    """Generates and downloads a fresh PDF security report compiled from alerts.db using ReportLab."""
    pdf_bytes = report_engine.generate_pdf_bytes()
    headers = {"Content-Disposition": "attachment; filename=cortex_security_report.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/reports/download/csv", summary="Download Fresh CSV Detection Logs", tags=["Reports Engine"])
async def download_csv_report():
    """Generates and downloads a fresh CSV export of all detection logs in alerts.db."""
    csv_content = report_engine.generate_csv_string()
    headers = {"Content-Disposition": "attachment; filename=cortex_detection_logs.csv"}
    return Response(content=csv_content, media_type="text/csv", headers=headers)


@router.get("/reports/download/markdown", summary="Download Fresh Markdown Audit Report", tags=["Reports Engine"])
async def download_markdown_report():
    """Generates and downloads a fresh Markdown security audit report."""
    md_content = report_engine.generate_markdown_report()
    headers = {"Content-Disposition": "attachment; filename=cortex_security_report.md"}
    return Response(content=md_content, media_type="text/markdown", headers=headers)


# ==========================================
# HISTORICAL THREAT ARCHIVE ENDPOINTS (alerts.db)
# ==========================================

@router.get("/historical-threats", summary="Get Paginated Permanent Historical Threat Archive", tags=["Historical Threats"])
async def get_historical_threats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    time_range: str = Query("all", description="Time filter: 24h, 7d, 30d, all"),
    attack_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Returns paginated, searchable, and filterable threat alerts directly from alerts.db."""
    return alert_engine.query_historical_threats_paginated(
        page=page,
        page_size=page_size,
        time_range=time_range,
        attack_type=attack_type,
        risk_level=risk_level,
        search=search,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/historical-threats/search", summary="Search Historical Threats", tags=["Historical Threats"])
async def search_historical_threats(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """Searches historical threats by IP, alert ID, or attack category."""
    return alert_engine.query_historical_threats_paginated(
        page=page,
        page_size=page_size,
        search=q
    )


@router.get("/historical-threats/export/csv", summary="Export Historical Threat Alerts as CSV", tags=["Historical Threats"])
async def export_historical_threats_csv(
    time_range: str = Query("all"),
    attack_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Exports matching historical alerts from alerts.db as a downloadable CSV file."""
    csv_content = alert_engine.export_alerts_csv_string(
        time_range=time_range,
        attack_type=attack_type,
        risk_level=risk_level,
        search=search
    )
    headers = {"Content-Disposition": "attachment; filename=historical_threat_alerts.csv"}
    return Response(content=csv_content, media_type="text/csv", headers=headers)


@router.get("/historical-threats/export/json", summary="Export Historical Threat Alerts as JSON", tags=["Historical Threats"])
async def export_historical_threats_json(
    time_range: str = Query("all"),
    attack_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Exports matching historical alerts from alerts.db as a downloadable JSON file."""
    json_content = alert_engine.export_alerts_json_string(
        time_range=time_range,
        attack_type=attack_type,
        risk_level=risk_level,
        search=search
    )
    headers = {"Content-Disposition": "attachment; filename=historical_threat_alerts.json"}
    return Response(content=json_content, media_type="application/json", headers=headers)


# ==========================================
# HISTORICAL ANALYTICS ENDPOINTS (alerts.db)
# ==========================================

@router.get("/analytics/summary", summary="Get Historical Permanent Analytics Summary", tags=["Historical Analytics"])
async def get_historical_summary() -> Dict[str, Any]:
    """Returns permanent historical totals (total flows ever, attacks ever, benign ever, avg confidence, avg latency) from alerts.db."""
    return alert_engine.get_analytics_summary()


@router.get("/analytics/trends", summary="Get Historical Threat Trend Time Series", tags=["Historical Analytics"])
async def get_historical_trends(time_range: str = Query("all", description="Time range filter: 24h, 7d, 30d, all")) -> List[Dict[str, Any]]:
    """Returns historical time-series flow and attack trend data points directly from alerts.db."""
    return alert_engine.get_analytics_trends(time_range=time_range)


@router.get("/analytics/top-attacks", summary="Get Top Historical Attack Categories", tags=["Historical Analytics"])
async def get_historical_top_attacks(limit: int = Query(10, ge=1, le=50)) -> List[Dict[str, Any]]:
    """Returns top ranked attack categories and counts directly from alerts.db."""
    return alert_engine.get_analytics_top_attacks(limit=limit)


@router.get("/analytics/severity", summary="Get Historical Risk Severity Distribution", tags=["Historical Analytics"])
async def get_historical_severity() -> Dict[str, int]:
    """Returns severity distribution breakdown directly from alerts.db."""
    return alert_engine.get_analytics_severity()


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
    """
    WebSocket endpoint streaming live real-time threat predictions and alerts.
    Polls SQLite alerts.db every 1.0 second for newly inserted alerts (from live monitor or API)
    and broadcasts them to the connected frontend client.
    """
    await ws_manager.connect(websocket)
    # Start tracking from current max rowid so client receives new live events
    last_rowid = alert_engine.get_max_rowid()
    try:
        while True:
            await asyncio.sleep(1.0)
            new_alerts, max_rowid = alert_engine.get_alerts_after_rowid(last_rowid=last_rowid, limit=50)
            if new_alerts:
                last_rowid = max_rowid
                for alt in new_alerts:
                    await websocket.send_json(alt)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket streaming error: %s", e)
        ws_manager.disconnect(websocket)
