# NIDS REST API Specification & Reference

Complete technical specification for the FastAPI backend serving the Enterprise Network Intrusion Detection System.

**Base URL**: `http://localhost:8000`  
**Swagger UI**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`

---

## 🔐 Authentication

Most administrative and configuration endpoints require a **JWT Bearer Token** in the HTTP Authorization header:

```http
Authorization: Bearer <your_jwt_access_token>
```

### Obtain JWT Token:
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=AdminPassword123!
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "username": "admin",
    "role": "Administrator"
  }
}
```

---

## 📡 API Endpoints Reference

### 1. System Info & Health

#### `GET /`
- **Description**: Root status check.
- **Response**: `200 OK`
```json
{
  "status": "online",
  "project_name": "Enterprise Network Intrusion Detection System (NIDS)",
  "version": "1.0.0",
  "docs_url": "/docs"
}
```

#### `GET /health`
- **Description**: Production health check probe.
- **Response**: `200 OK`
```json
{
  "healthy": true,
  "version": "1.0.0",
  "model_loaded": true,
  "prediction_engine_status": "active"
}
```

#### `GET /metrics`
- **Description**: Runtime prediction & API performance metrics.
- **Response**: `200 OK`
```json
{
  "prediction_count": 1420,
  "average_latency_ms": 20.476,
  "average_confidence": 0.9958,
  "requests_served": 1500
}
```

---

### 2. Machine Learning Inference

#### `POST /predict`
- **Description**: Sub-millisecond single network flow inference.
- **Request Body**:
```json
{
  "Destination Port": 80,
  "Flow Duration": 1000,
  "Total Fwd Packets": 10,
  "Total Backward Packets": 8,
  "Total Length of Fwd Packets": 500,
  "Total Length of Bwd Packets": 400,
  "Fwd Packet Length Max": 100,
  "Fwd Packet Length Min": 20,
  "Fwd Packet Length Mean": 50.0,
  "Fwd Packet Length Stddev": 10.0,
  "Bwd Packet Length Max": 80,
  "Bwd Packet Length Min": 10,
  "Bwd Packet Length Mean": 40.0,
  "Bwd Packet Length Stddev": 5.0,
  "Flow Bytes/s": 900.0,
  "Flow Packets/s": 18.0,
  "Flow IAT Mean": 50.0,
  "Flow IAT Stddev": 5.0,
  "Flow IAT Max": 100,
  "Flow IAT Min": 1
}
```

- **Response**: `200 OK`
```json
{
  "Attack_Type": "BENIGN",
  "Prediction_Confidence": 0.9985,
  "Risk_Score": 0.03,
  "Risk_Level": "Low",
  "Class_Probabilities": {
    "BENIGN": 0.9985,
    "DDoS": 0.0010,
    "PortScan": 0.0005
  },
  "Model_Name": "best_model",
  "Prediction_Time_ms": 20.476
}
```

#### `POST /batch_predict`
- **Description**: Upload CSV network telemetry file for chunked batch inference.
- **Form Data**: `file` (multipart/form-data CSV file)
- **Response**: `200 OK`

---

### 3. Threat Intelligence & Security Integration

#### `GET /alerts`
- **Description**: Retrieve stored threat alerts with optional filtering (`src_ip`, `risk_level`, `limit`).
- **Response**: `200 OK`

#### `GET /siem/status`
- **Description**: Status of active SIEM connectors (Elastic, Splunk, Sentinel, Syslog).
- **Response**: `200 OK`

---

## ❌ Standard Error Codes

| Status Code | Reason | Resolution |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid payload or malformed JSON | Check request body against schema |
| `401 Unauthorized` | Missing or expired JWT token | Obtain a fresh token via `/auth/login` |
| `403 Forbidden` | Insufficient RBAC role permissions | Elevate user permissions |
| `429 Too Many Requests` | Rate limit exceeded | Wait 60 seconds before retrying |
| `500 Internal Error` | Server processing error | Inspect backend logs under `logs/` |
