"""
Schemas module for NIDS FastAPI Backend.
Defines Pydantic request and response models with OpenAPI examples and field validations.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RootResponse(BaseModel):
    project_name: str = Field(..., json_schema_extra={"example": "Machine Learning-Based Network Intrusion Detection System"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    status: str = Field(..., json_schema_extra={"example": "online"})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})


class HealthResponse(BaseModel):
    healthy: bool = Field(..., json_schema_extra={"example": True})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})
    prediction_engine_status: str = Field(..., json_schema_extra={"example": "active"})


class ModelInfoResponse(BaseModel):
    model_name: str = Field(..., json_schema_extra={"example": "LGBMClassifier"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    training_date: str = Field(..., json_schema_extra={"example": "2026-07-25 19:23:02"})
    accuracy: float = Field(..., json_schema_extra={"example": 0.9987})
    feature_count: int = Field(..., json_schema_extra={"example": 20})


class SingleFlowRequest(BaseModel):
    destination_port: float = Field(80.0, alias="Destination Port", description="Destination network port number")
    total_length_fwd_pkt: float = Field(120.0, alias="Total Length of Fwd Packets", description="Total size of forward packets")
    fwd_pkt_len_max: float = Field(60.0, alias="Fwd Packet Length Max", description="Maximum forward packet length")
    bwd_pkt_len_max: float = Field(1460.0, alias="Bwd Packet Length Max", description="Maximum backward packet length")
    flow_bytes_s: float = Field(5000.0, alias="Flow Bytes/s", description="Flow throughput in bytes per second")
    flow_iat_std: float = Field(1200.0, alias="Flow IAT Std", description="Standard deviation of inter-arrival time")
    fwd_iat_min: float = Field(10.0, alias="Fwd IAT Min", description="Minimum forward inter-arrival time")
    fwd_header_len: float = Field(40.0, alias="Fwd Header Length", description="Total forward header bytes")
    bwd_header_len: float = Field(40.0, alias="Bwd Header Length", description="Total backward header bytes")
    bwd_pkts_s: float = Field(15.0, alias="Bwd Packets/s", description="Backward packet rate")
    fin_flag_cnt: float = Field(0.0, alias="FIN Flag Count", description="FIN flag count")
    psh_flag_cnt: float = Field(1.0, alias="PSH Flag Count", description="PSH flag count")
    init_win_bytes_fwd: float = Field(8192.0, alias="Init_Win_bytes_forward", description="Initial TCP window size forward")
    init_win_bytes_bwd: float = Field(255.0, alias="Init_Win_bytes_backward", description="Initial TCP window size backward")
    act_data_pkt_fwd: float = Field(2.0, alias="act_data_pkt_fwd", description="Active payload data packet count")
    min_seg_size_fwd: float = Field(20.0, alias="min_seg_size_forward", description="Minimum segment size forward")
    active_mean: float = Field(0.0, alias="Active Mean", description="Mean active time before idle")
    active_std: float = Field(0.0, alias="Active Std", description="Standard deviation of active time")
    active_max: float = Field(0.0, alias="Active Max", description="Maximum active time")
    idle_std: float = Field(0.0, alias="Idle Std", description="Standard deviation of idle time")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
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
            }
        }
    )


class SinglePredictionResponse(BaseModel):
    attack_type: str = Field(..., alias="Attack_Type", json_schema_extra={"example": "BENIGN"})
    prediction_confidence: float = Field(..., alias="Prediction_Confidence", json_schema_extra={"example": 0.9985})
    risk_score: float = Field(..., alias="Risk_Score", json_schema_extra={"example": 0.0})
    risk_level: str = Field(..., alias="Risk_Level", json_schema_extra={"example": "Low"})
    class_probabilities: Dict[str, float] = Field(..., alias="Class_Probabilities", json_schema_extra={"example": {"BENIGN": 0.9985, "PortScan": 0.0015}})
    model_name: str = Field(..., alias="Model_Name", json_schema_extra={"example": "LGBMClassifier"})
    prediction_time_ms: float = Field(..., alias="Prediction_Time_ms", json_schema_extra={"example": 0.035})

    model_config = ConfigDict(populate_by_name=True)


class BatchSummaryResponse(BaseModel):
    total_records_predicted: int = Field(..., json_schema_extra={"example": 1000})
    average_confidence: float = Field(..., json_schema_extra={"example": 0.9958})
    average_risk_score: float = Field(..., json_schema_extra={"example": 13.06})
    average_latency_ms: float = Field(..., json_schema_extra={"example": 0.027})
    attack_breakdown: Dict[str, int] = Field(..., json_schema_extra={"example": {"BENIGN": 850, "DoS Hulk": 100, "PortScan": 50}})
    risk_level_breakdown: Dict[str, int] = Field(..., json_schema_extra={"example": {"Low": 850, "Critical": 100, "Medium": 50}})
    prediction_file_saved: str = Field(..., json_schema_extra={"example": "predictions/prediction_results.csv"})


class MetricsResponse(BaseModel):
    prediction_count: int = Field(..., json_schema_extra={"example": 12500})
    average_latency_ms: float = Field(..., json_schema_extra={"example": 0.032})
    average_confidence: float = Field(..., json_schema_extra={"example": 0.9961})
    requests_served: int = Field(..., json_schema_extra={"example": 42})


class FeatureImportanceResponse(BaseModel):
    model_name: str = Field(..., json_schema_extra={"example": "LGBMClassifier"})
    feature_count: int = Field(..., json_schema_extra={"example": 20})
    top_features: List[Dict[str, Any]] = Field(
        ...,
        json_schema_extra={
            "example": [
                {"rank": 1, "feature": "Bwd Packet Length Max", "importance": 0.1732},
                {"rank": 2, "feature": "Flow IAT Std", "importance": 0.1217}
            ]
        }
    )
