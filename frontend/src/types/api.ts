export interface RootResponse {
  project_name: string;
  version: string;
  status: string;
  model_loaded: boolean;
}

export interface HealthResponse {
  healthy: boolean;
  version: string;
  model_loaded: boolean;
  prediction_engine_status: string;
}

export interface ModelInfoResponse {
  model_name: string;
  version: string;
  training_date: string;
  accuracy: number;
  feature_count: number;
}

export interface SingleFlowInput {
  "Destination Port": number;
  "Total Length of Fwd Packets": number;
  "Fwd Packet Length Max": number;
  "Bwd Packet Length Max": number;
  "Flow Bytes/s": number;
  "Flow IAT Std": number;
  "Fwd IAT Min": number;
  "Fwd Header Length": number;
  "Bwd Header Length": number;
  "Bwd Packets/s": number;
  "FIN Flag Count": number;
  "PSH Flag Count": number;
  "Init_Win_bytes_forward": number;
  "Init_Win_bytes_backward": number;
  "act_data_pkt_fwd": number;
  "min_seg_size_forward": number;
  "Active Mean": number;
  "Active Std": number;
  "Active Max": number;
  "Idle Std": number;
}

export interface SinglePredictionResponse {
  Attack_Type: string;
  Prediction_Confidence: number;
  Risk_Score: number;
  Risk_Level: 'Low' | 'Medium' | 'High' | 'Critical';
  Class_Probabilities: Record<string, number>;
  Model_Name: string;
  Prediction_Time_ms: number;
}

export interface BatchSummaryResponse {
  total_records_predicted: number;
  average_confidence: number;
  average_risk_score: number;
  average_latency_ms: number;
  attack_breakdown: Record<string, number>;
  risk_level_breakdown: Record<string, number>;
  prediction_file_saved: string;
}

export interface MetricsResponse {
  prediction_count: number;
  average_latency_ms: number;
  average_confidence: number;
  requests_served: number;
}

export interface FeatureImportanceItem {
  rank: number;
  feature: string;
  importance: number;
}

export interface FeatureImportanceResponse {
  model_name: string;
  feature_count: number;
  top_features: FeatureImportanceItem[];
}
