/// <reference types="vite/client" />
import axios from 'axios';
import {
  RootResponse,
  HealthResponse,
  ModelInfoResponse,
  SingleFlowInput,
  SinglePredictionResponse,
  BatchSummaryResponse,
  MetricsResponse,
  FeatureImportanceResponse,
} from '../types/api';

/**
 * Dynamically resolves the API base URL.
 * Automatically adapts when accessed from any other laptop/phone on Wi-Fi (e.g. http://192.168.0.194:8000),
 * localhost, or custom domain/tunnel.
 */
export const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dynamic request interceptor ensuring active hostname is always used
apiClient.interceptors.request.use((config) => {
  if (!config.baseURL || config.baseURL === 'http://localhost:8000') {
    config.baseURL = getApiBaseUrl();
  }
  return config;
});

/**
 * Dynamically resolves the WebSocket URL for live alerts.
 * Automatically connects to the host machine's backend (e.g. ws://192.168.0.194:8000/ws/alerts).
 */
export const getWebSocketUrl = (): string => {
  if (typeof window !== 'undefined' && window.location.hostname) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    if (import.meta.env.VITE_API_BASE_URL) {
      const host = import.meta.env.VITE_API_BASE_URL.replace(/^https?:\/\//, '');
      return `${wsProtocol}//${host}/ws/alerts`;
    }
    return `${wsProtocol}//${window.location.hostname}:8000/ws/alerts`;
  }
  return 'ws://localhost:8000/ws/alerts';
};

export const apiService = {
  // GET /
  getRoot: async (): Promise<RootResponse> => {
    const res = await apiClient.get<RootResponse>('/');
    return res.data;
  },

  // GET /health
  getHealth: async (): Promise<HealthResponse> => {
    const res = await apiClient.get<HealthResponse>('/health');
    return res.data;
  },

  // GET /model
  getModelInfo: async (): Promise<ModelInfoResponse> => {
    const res = await apiClient.get<ModelInfoResponse>('/model');
    return res.data;
  },

  // POST /predict
  predictSingle: async (input: SingleFlowInput): Promise<SinglePredictionResponse> => {
    const res = await apiClient.post<SinglePredictionResponse>('/predict', input);
    return res.data;
  },

  // POST /batch_predict
  predictBatchCsv: async (file: File): Promise<BatchSummaryResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const res = await apiClient.post<BatchSummaryResponse>('/batch_predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // GET /metrics
  getMetrics: async (): Promise<MetricsResponse> => {
    const res = await apiClient.get<MetricsResponse>('/metrics');
    return res.data;
  },

  // GET /feature_importance
  getFeatureImportance: async (): Promise<FeatureImportanceResponse> => {
    const res = await apiClient.get<FeatureImportanceResponse>('/feature_importance');
    return res.data;
  },

  // GET /alerts
  getAlerts: async (params?: Record<string, any>): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/alerts', { params });
    return res.data;
  },

  // GET /alerts/daily_report
  getDailyReport: async (): Promise<any> => {
    const res = await apiClient.get<any>('/alerts/daily_report');
    return res.data;
  },

  // GET /analytics/summary
  getHistoricalSummary: async (): Promise<any> => {
    const res = await apiClient.get<any>('/analytics/summary');
    return res.data;
  },

  // GET /analytics/trends
  getHistoricalTrends: async (timeRange: string = 'all'): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/analytics/trends', { params: { time_range: timeRange } });
    return res.data;
  },

  // GET /analytics/top-attacks
  getHistoricalTopAttacks: async (limit: number = 10): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/analytics/top-attacks', { params: { limit } });
    return res.data;
  },

  // GET /analytics/severity
  getHistoricalSeverity: async (): Promise<Record<string, number>> => {
    const res = await apiClient.get<Record<string, number>>('/analytics/severity');
    return res.data;
  },

  // GET /historical-threats
  getHistoricalThreats: async (params?: Record<string, any>): Promise<any> => {
    const res = await apiClient.get<any>('/historical-threats', { params });
    return res.data;
  },

  // GET /alerts/recent
  getRecentAlerts: async (limit = 25): Promise<any[]> => {
    try {
      const res = await apiClient.get<any[]>('/alerts/recent', { params: { limit } });
      return res.data;
    } catch {
      return [];
    }
  },

  // GET /historical-threats/search
  searchHistoricalThreats: async (query: string, page = 1, pageSize = 20): Promise<any> => {
    const res = await apiClient.get<any>('/historical-threats/search', {
      params: { q: query, page, page_size: pageSize },
    });
    return res.data;
  },

  // Export URLs
  getExportHistoricalCsvUrl: (params?: Record<string, any>): string => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] !== undefined && params[key] !== null) {
          searchParams.append(key, String(params[key]));
        }
      });
    }
    return `${API_BASE_URL}/historical-threats/export/csv?${searchParams.toString()}`;
  },

  getExportHistoricalJsonUrl: (params?: Record<string, any>): string => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] !== undefined && params[key] !== null) {
          searchParams.append(key, String(params[key]));
        }
      });
    }
    return `${API_BASE_URL}/historical-threats/export/json?${searchParams.toString()}`;
  },

  // Dynamic Report Engine API
  generateReport: async (): Promise<any> => {
    const res = await apiClient.get<any>('/reports/generate');
    return res.data;
  },

  getReportPdfUrl: (): string => `${API_BASE_URL}/reports/download/pdf`,
  getReportHtmlUrl: (): string => `${API_BASE_URL}/reports/download/html`,
  getReportCsvUrl: (): string => `${API_BASE_URL}/reports/download/csv`,
  getReportMarkdownUrl: (): string => `${API_BASE_URL}/reports/download/markdown`,

  // GET /search
  globalSearch: async (query: string, limit = 10): Promise<any> => {
    const res = await apiClient.get<any>('/search', { params: { q: query, limit } });
    return res.data;
  },
};
