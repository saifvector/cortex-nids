# 🛡️ Architectural Refactor Report: Live Session vs Historical Analytics Separation

**Date**: 2026-08-11  
**Author**: Senior SOC Architect & Observability Engineer  
**Status**: 🟢 **100% OPERATIONAL & VERIFIED**  

---

## 🎯 Executive Summary

A complete architectural refactoring of Cortex NIDS was performed to achieve strict separation between **LIVE SESSION MONITORING** and **HISTORICAL ANALYTICS**. 

Previously, the main Dashboard displayed cumulative totals loaded from `alerts.db` (causing counters to continuously grow across backend restarts). Under the new architecture:
1. **Tab 1: Dashboard (Live Session)**: Displays **ONLY in-memory metrics** generated during the active backend process session. Resets to ZERO whenever FastAPI restarts.
2. **Tab 2: Threat Monitor**: Real-time alert feed streaming genuine packet flows and predictions from SQLite `alerts.db` and WebSockets.
3. **Tab 3: Historical Analytics**: Dedicated permanent analytics console (`HistoricalAnalytics.tsx`) querying all historical records ever stored in `predictions/alerts.db`.

---

## 🔍 1. Root Cause Analysis

| Component | Previous Architecture | New Refactored Architecture |
|:---|:---|:---|
| **Metrics Engine** | `MetricsManager` queried `alerts.db` directly for `/metrics`, blending historical rows with active session data. | Created `SessionMetricsManager` (`api/session_metrics.py`). Stores session predictions purely in memory without SQLite dependency. Resets to 0 on backend boot. |
| **Dashboard UI** | `Dashboard.tsx` loaded cumulative SQLite totals, displaying all-time database numbers. | `Dashboard.tsx` displays ONLY active session metrics from `/metrics`. All counters start at 0 on startup and reset on server restart. |
| **Historical Data** | No dedicated historical analytics page; historical DB data was mixed into the live dashboard. | Created `HistoricalAnalytics.tsx` querying dedicated backend endpoints `/analytics/summary`, `/analytics/trends`, `/analytics/top-attacks`, and `/analytics/severity`. |
| **Live Traffic Feed** | `live_monitor.py` inserted into `alerts.db` but did not notify active backend session counters. | `live_monitor.py` inserts into `alerts.db` AND notifies FastAPI's `/metrics/record` endpoint so active session counters update dynamically during live sniffing. |

---

## 🛠️ 2. Files Modified & Code Changes

### 1. `api/session_metrics.py` (NEW FILE)
- Implemented `SessionMetricsManager`: thread-safe singleton managing `prediction_count`, `attack_count`, `benign_count`, `critical_alerts`, `high_alerts`, `medium_alerts`, `low_alerts`, `requests_served`, `average_latency_ms`, `average_confidence`.
- Automatically resets all counters to ZERO upon initialization when FastAPI starts.
- Includes `reset()` method exposed via `POST /metrics/reset`.

### 2. `api/routes.py` (New Analytics & Session Endpoints)
- **`GET /metrics`**: Serves active `session_metrics_manager` counters.
- **`POST /metrics/record`**: Internal endpoint for live monitor to record session prediction events.
- **`POST /metrics/reset`**: Resets active session counters.
- **`GET /analytics/summary`**: Returns total flows ever, attacks ever, benign ever, avg confidence ever, avg latency ever from `alerts.db`.
- **`GET /analytics/trends`**: Returns time-series trend data points (`24h`, `7d`, `30d`, `all`).
- **`GET /analytics/top-attacks`**: Returns top attack categories ranked by count.
- **`GET /analytics/severity`**: Returns severity distribution (`Critical`, `High`, `Medium`, `Low`).

### 3. `api/services.py` & `api/middleware.py`
- Updated `APIService` and `request_logging_and_rate_limit` middleware to invoke `session_metrics_manager`.

### 4. `src/alert_engine.py`
- Added SQL aggregation methods: `get_analytics_summary()`, `get_analytics_trends()`, `get_analytics_top_attacks()`, and `get_analytics_severity()`.

### 5. `src/live_monitor.py`
- Added notification step to POST `/metrics/record` when a flow is evaluated, ensuring live packet capture updates session counters in real time.

### 6. `frontend/src/pages/Dashboard.tsx`
- Refactored to bind strictly to session metrics.
- Subtitles explicitly marked: *"Flows in current session"*, *"Active Session"*.
- Fallbacks set to zero (no mock data, no database aggregation).

### 7. `frontend/src/pages/HistoricalAnalytics.tsx` (NEW FILE) & `Analytics.tsx`
- Created `HistoricalAnalytics.tsx` with time range filters (`24h`, `7d`, `30d`, `all`), 5 KPI cards for all-time totals, Attack Trend Area Chart, Historical Severity Donut Chart, and Top Attack Classes Table.

### 8. `frontend/src/services/api.ts`, `Sidebar.tsx`, `App.tsx`
- Added `getHistoricalSummary()`, `getHistoricalTrends()`, `getHistoricalTopAttacks()`, `getHistoricalSeverity()`.
- Updated navigation bar: **Dashboard (Live)**, **Threat Monitor**, **Historical Analytics**, **Reports**, **Settings**.

---

## 📊 3. API Endpoints Added & Verified

```
POST /metrics/record             -> Updates active session counters
POST /metrics/reset              -> Resets session counters to zero
GET  /analytics/summary          -> SQLite alerts.db historical summary
GET  /analytics/trends           -> SQLite alerts.db time-series trends (?time_range=24h|7d|30d|all)
GET  /analytics/top-attacks      -> SQLite alerts.db top attack categories (?limit=10)
GET  /analytics/severity         -> SQLite alerts.db risk severity distribution
```

---

## 🔄 4. Before vs After Behavior

| Behavior / Feature | Before Refactor | After Refactor |
|:---|:---|:---|
| **FastAPI Startup** | Dashboard showed ~5,700 predictions loaded from `alerts.db` | Dashboard starts at **0 Predictions, 0 Attacks, 0 Requests** |
| **FastAPI Restart** | Counters kept accumulating continuously | Dashboard counters **return to ZERO** |
| **Live Packet Sniffing** | Incremented database total | Increments **Session Predictions** AND updates SQLite `alerts.db` |
| **Historical Records** | Mixed into Live Dashboard | Isolated on dedicated **Historical Analytics** tab |
| **Time Filters** | None | `Last 24 Hours`, `Last 7 Days`, `Last 30 Days`, `All Time` |

---

## 🧪 5. Validation Results

Executed 5-step automated validation suite (`scripts/validate_architectural_refactor.py`):

```
===========================================================================
  CORTEX NIDS ARCHITECTURE REFACTOR VALIDATION
===========================================================================

[STEP 1] Checking GET /metrics on Fresh FastAPI Backend Startup...
  Session prediction_count = 0
  Session attack_count     = 0
  Session benign_count     = 0
  Session requests_served  = 1
  RESULT: PASS (Session counters start at ZERO)

[STEP 2] Checking GET /analytics/summary for Permanent SQLite History...
  Total Flows Ever  : 5766
  Total Attacks Ever: 13
  Total Benign Ever : 5753
  Avg Confidence    : 0.9943
  RESULT: PASS (Database history remains 100% intact)

[STEP 3] Testing Historical Analytics Sub-Endpoints...
  /analytics/trends     : 3 trend time points returned
  /analytics/top-attacks: 4 top attack categories returned
  /analytics/severity   : {'Critical': 13, 'High': 0, 'Medium': 0, 'Low': 5753}
  RESULT: PASS (All analytics endpoints respond correctly)

[STEP 4] Simulating Live Traffic Prediction (Session Increment)...
  Prediction Attack: DoS GoldenEye
  Updated Session prediction_count = 1
  RESULT: PASS (Session predictions incremented to 1)

[STEP 5] Testing Session Metrics Reset (POST /metrics/reset)...
  After Reset Session prediction_count = 0
  RESULT: PASS (Session metrics reset back to zero)

===========================================================================
  ARCHITECTURAL REFACTOR VALIDATION: 100% SUCCESS (ALL TESTS PASSED)
===========================================================================
```

- **Pytest Suite**: 70/70 tests **PASSING** (100%)
- **Git Commit & Push**: Pushed to `main` (`749dbdb`)

---

## 📸 6. Verification Checklist

- [x] Dashboard = Session Data Only (starts at 0 on boot)
- [x] Threat Monitor = Real Live Alerts Only
- [x] Historical Analytics = Database History Only (`alerts.db`)
- [x] `/metrics/reset` returns session counters to zero
- [x] Zero mock data, zero placeholders, zero hardcoded arrays
- [x] 100% Pytest pass rate (70/70)
