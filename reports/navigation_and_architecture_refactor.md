# 🛡️ Cortex NIDS: Live vs Historical Data & Navigation Separation Report

**Date**: 2026-08-11  
**Status**: 🟢 **100% OPERATIONAL & VERIFIED**  
**Role**: Senior SOC Architect, React Engineer, FastAPI Engineer, UX Specialist  

---

## 🎯 Executive Summary

The **Cortex NIDS** navigation and backend architecture have been refactored to achieve complete, uncompromising separation between **LIVE SESSION DATA** and **HISTORICAL DATABASE RECORDS**.

### Target Navigation Architecture
```
 1. 📊 Dashboard (Live)        -> Active Session Telemetry Only (resets on server restart)
 2. ⚡ Live Threats            -> Real-Time WebSocket Session Stream (starts clean on startup)
 3. 🏛️ Historical Threats       -> Permanent SQLite alerts.db Archive (paginated, searchable, exportable)
 4. 📈 Historical Analytics     -> Permanent Database Insights, Trends & Severity Distribution
 5. 📄 Reports                 -> PDF Report Generation Engine & Summaries
 6. 🛠️ Settings                -> System Configuration & Parameters
```

---

## 🔍 1. Root Cause Analysis

| Component | Previous Issue | Refactored Resolution |
|:---|:---|:---|
| **Dashboard** | Showed cumulative `alerts.db` totals (counters grew indefinitely). | Shows ONLY in-memory active session metrics (`session_metrics.py`). Resets to ZERO on server boot/restart. |
| **Threat Monitor** | Blended real-time WebSocket events with historical SQLite alerts on mount. | Renamed to **Live Threats** (`LiveThreats.tsx`). In-memory & WebSocket driven ONLY. Starts empty on startup. Includes *Pause Stream*, *Resume Stream*, *Clear View*, *IP Search*, and *Attack/Risk Filters*. |
| **Historical Archive** | No dedicated page for querying permanent alerts with pagination or CSV/JSON exports. | Created **Historical Threats** (`HistoricalThreats.tsx`) powered by `alerts.db` with pagination, live search, time filters (`24h`, `7d`, `30d`, `custom`), and CSV/JSON export buttons. |
| **Analytics** | Hardcoded static charts. | **Historical Analytics** (`HistoricalAnalytics.tsx`) querying permanent SQLite time series, top attack categories, and severity distribution. |

---

## 🛠️ 2. Files Created & Modified

### New Files Created
1. **`frontend/src/pages/LiveThreats.tsx`**: In-memory session threat monitor with WebSocket live feed, Clear View button, Pause/Resume, IP search, and attack/risk filters. Starts empty on startup.
2. **`frontend/src/pages/HistoricalThreats.tsx`**: Permanent threat archive querying `alerts.db`. Supports search, pagination, date range filtering, and CSV/JSON exports.

### Files Modified
1. **`api/routes.py`**: Added `/historical-threats`, `/historical-threats/search`, `/historical-threats/export/csv`, `/historical-threats/export/json`.
2. **`src/alert_engine.py`**: Added `query_historical_threats_paginated()`, `export_alerts_csv_string()`, `export_alerts_json_string()`.
3. **`frontend/src/services/api.ts`**: Added `getHistoricalThreats()`, `searchHistoricalThreats()`, `getExportHistoricalCsvUrl()`, `getExportHistoricalJsonUrl()`.
4. **`frontend/src/components/Sidebar.tsx` & `App.tsx`**: Updated routes to include **Dashboard (Live)**, **Live Threats**, **Historical Threats**, **Historical Analytics**, **Reports**, and **Settings**.
5. **`frontend/src/pages/ThreatMonitor.tsx`**: Updated to re-export `LiveThreats`.

---

## 📊 3. API Endpoints Added & Verified

```
GET /historical-threats               -> Returns paginated threat alerts from alerts.db (?page=1&page_size=20&time_range=24h|7d|30d|all)
GET /historical-threats/search        -> Searches threats by IP, Alert ID, or Attack Type (?q=search_term)
GET /historical-threats/export/csv    -> Downloads matching alerts as CSV file
GET /historical-threats/export/json   -> Downloads matching alerts as JSON file
GET /analytics/summary                -> Permanent historical totals from alerts.db
GET /analytics/trends                 -> Historical attack time-series trend points
GET /analytics/top-attacks            -> Top attack category statistics
GET /analytics/severity               -> Historical severity distribution
```

---

## 🔄 4. Before vs After Architecture Matrix

| Page / Capability | Before Refactor | After Refactor |
|:---|:---|:---|
| **Dashboard (`/`)** | Displayed all-time SQLite totals (~5,800) | Session metrics ONLY. Starts at **0 Predictions, 0 Attacks**. |
| **Live Threats (`/live-threats`)** | Loaded historical database alerts on mount | Starts **EMPTY** on boot. Displays live WebSocket session events with Clear View & Search IP controls. |
| **Historical Threats (`/historical-threats`)** | Not available | Paginated permanent archive with search, date filters, and **CSV/JSON exports**. |
| **Historical Analytics (`/analytics`)** | Static demo charts | 100% dynamic time-series charts, severity distribution, and top attacks from `alerts.db`. |

---

## 🧪 5. Validation Results

Executed 5-step automated separation test suite (`scripts/test_live_vs_historical_separation.py`):

```
================================================================================
  LIVE VS HISTORICAL SEPARATION VALIDATION SUITE
================================================================================

[TEST 1] Verifying Backend Startup (Session = 0)...
  Dashboard Session Predictions: 0
  Dashboard Session Attacks    : 0
  RESULT: PASS (Starts at 0)

[TEST 2] Executing Live Flow Prediction (Session Incursion)...
  Flow Prediction Result: DoS GoldenEye
  Dashboard Session Predictions After Incursion: 1
  RESULT: PASS (Counters increased)

[TEST 3] Simulating Backend Restart (POST /metrics/reset)...
  Dashboard Session Predictions After Reset: 0
  RESULT: PASS (Session reset to 0)

[TEST 4] Verifying Permanent Historical Threats Archive (/historical-threats)...
  Total Historical Threats Archived in alerts.db: 5806
  Alerts Returned on Page 1                    : 10
  RESULT: PASS (Historical threat archive intact)

[TEST 5] Verifying Historical Analytics Engine (/analytics/summary & /analytics/trends)...
  Total Flows Ever  : 5806
  Total Attacks Ever: 19
  Trend Points Count: 4
  RESULT: PASS (Historical analytics intact)

================================================================================
  ALL 5 SEPARATION TESTS PASSED 100%! ARCHITECTURE REFACTOR SUCCESSFUL.
================================================================================
```

- **Pytest Test Suite**: **70/70 PASSED (100%)** ✅
- **Git Commit & Push**: Pushed to `main` (`c422210`) ✅

---

## 📸 6. Verification Checklist

- [x] **Dashboard (Live)**: Shows current session metrics ONLY (starts at 0 on startup).
- [x] **Live Threats**: Real-time session alerts ONLY (starts empty on startup, WebSocket driven, Clear View button).
- [x] **Historical Threats**: Permanent threat archive from `alerts.db` with search, pagination, and CSV/JSON export.
- [x] **Historical Analytics**: Long-term threat intelligence & time-series trends from `alerts.db`.
- [x] **Zero Mock Data**: No hardcoded array fallbacks, no static placeholders.
