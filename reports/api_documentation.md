# NIDS Production FastAPI Backend API Documentation

The **Network Intrusion Detection System (NIDS) REST API** exposes trained machine learning models, preprocessing pipelines, real-time risk scoring, and batch CSV inference endpoints.

---

## 🚀 Server Execution
Launch the production Uvicorn server:
```bash
python scripts/run_api.py --host 0.0.0.0 --port 8000
```

- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 📌 API Endpoints Overview

| Method | Endpoint | Description | Tags |
| :---: | :--- | :--- | :--- |
| `GET` | `/` | Returns project metadata and model load status | General |
| `GET` | `/health` | Health check and prediction engine status | General |
| `GET` | `/model` | Model versioning, training date, and accuracy | Model Info |
| `POST` | `/predict` | Single network flow prediction & risk scoring | Inference |
| `POST` | `/batch_predict` | CSV file upload batch prediction | Inference |
| `GET` | `/metrics` | Live API request counts & average latency | Monitoring |
| `GET` | `/feature_importance` | Top 20 feature importances for classifier | Model Info |

---

## 🔍 Detailed Endpoint Specifications

### 1. `GET /`
Returns system metadata and online status.

#### Example Request
```bash
curl -X GET "http://localhost:8000/"
```

#### Example Response (`200 OK`)
```json
{
  "project_name": "Machine Learning-Based Network Intrusion Detection System",
  "version": "1.0.0",
  "status": "online",
  "model_loaded": true
}
```

---

### 2. `GET /health`
Verifies backend health and prediction engine readiness.

#### Example Request
```bash
curl -X GET "http://localhost:8000/health"
```

#### Example Response (`200 OK`)
```json
{
  "healthy": true,
  "version": "1.0.0",
  "model_loaded": true,
  "prediction_engine_status": "active"
}
```

---

### 3. `GET /model`
Returns trained classifier metadata and feature count.

#### Example Request
```bash
curl -X GET "http://localhost:8000/model"
```

#### Example Response (`200 OK`)
```json
{
  "model_name": "LGBMClassifier",
  "version": "1.0.0",
  "training_date": "2026-07-25 19:23:02",
  "accuracy": 0.9987,
  "feature_count": 20
}
```

---

### 4. `POST /predict`
Executes single network flow inference and returns Attack Type, Confidence, Risk Score, and Risk Level.

#### Example Request
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
           "Destination Port": 80.0,
           "Total Length of Fwd Packets": 120.0,
           "Fwd Packet Length Max": 60.0,
           "Bwd Packet Length Max": 1460.0,
           "Flow Bytes/s": 5000.0,
           "Flow IAT Std": 1200.0,
           "Fwd IAT Min": 10.0,
           "Fwd Header Length": 40.0,
           "Bwd Header Length": 40.0,
           "Bwd Packets/s": 15.0,
           "FIN Flag Count": 0.0,
           "PSH Flag Count": 1.0,
           "Init_Win_bytes_forward": 8192.0,
           "Init_Win_bytes_backward": 255.0,
           "act_data_pkt_fwd": 2.0,
           "min_seg_size_forward": 20.0,
           "Active Mean": 0.0,
           "Active Std": 0.0,
           "Active Max": 0.0,
           "Idle Std": 0.0
         }'
```

#### Example Response (`200 OK`)
```json
{
  "Attack_Type": "BENIGN",
  "Prediction_Confidence": 0.9985,
  "Risk_Score": 0.0,
  "Risk_Level": "Low",
  "Class_Probabilities": {
    "BENIGN": 0.9985,
    "PortScan": 0.0015
  },
  "Model_Name": "LGBMClassifier",
  "Prediction_Time_ms": 0.035
}
```

---

### 5. `POST /batch_predict`
Accepts a CSV file upload containing network flow records for batch prediction.

#### Example Request
```bash
curl -X POST "http://localhost:8000/batch_predict" \
     -F "file=@data/processed/X_test.csv"
```

#### Example Response (`200 OK`)
```json
{
  "total_records_predicted": 10000,
  "average_confidence": 0.9958,
  "average_risk_score": 13.06,
  "average_latency_ms": 0.027,
  "attack_breakdown": {
    "BENIGN": 8283,
    "DoS Hulk": 674,
    "DDoS": 499,
    "PortScan": 390
  },
  "risk_level_breakdown": {
    "Low": 8283,
    "Critical": 1235,
    "Medium": 379,
    "High": 103
  },
  "prediction_file_saved": "predictions/prediction_results.csv"
}
```

---

### 6. `GET /metrics`
Returns live API request counters and average inference performance metrics.

#### Example Request
```bash
curl -X GET "http://localhost:8000/metrics"
```

#### Example Response (`200 OK`)
```json
{
  "prediction_count": 10001,
  "average_latency_ms": 0.027,
  "average_confidence": 0.9958,
  "requests_served": 5
}
```

---

### 7. `GET /feature_importance`
Returns top feature importances for the loaded classifier.

#### Example Request
```bash
curl -X GET "http://localhost:8000/feature_importance"
```

#### Example Response (`200 OK`)
```json
{
  "model_name": "LGBMClassifier",
  "feature_count": 20,
  "top_features": [
    { "rank": 1, "feature": "Bwd Packet Length Max", "importance": 0.1732 },
    { "rank": 2, "feature": "Flow IAT Std", "importance": 0.1217 },
    { "rank": 3, "feature": "Destination Port", "importance": 0.0896 }
  ]
}
```

---

## 🛡️ Error Handling & HTTP Status Codes

| HTTP Status | Error Type | Cause |
| :---: | :--- | :--- |
| `400 Bad Request` | `InvalidInputFormatException` | Unparseable input schema or non-CSV file uploaded |
| `422 Unprocessable` | `ValidationError` | Missing required fields or incorrect data types |
| `429 Too Many Requests` | `RateLimitExceeded` | IP request rate limit (>100 req/min) exceeded |
| `503 Service Unavailable` | `ModelNotLoadedException` | Model checkpoint or preprocessing pipeline failed to load |

---
*Documentation generated automatically for NIDS FastAPI Backend.*
