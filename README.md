<!-- Portfolio repository -->

> **Manufacturing Execution System Dashboard** — portfolio demonstration.
> Time-series telemetry, quality views, and ML anomaly detection
>
> This is a sanitized public version of a real-world prototype. Client names,
> credentials, internal endpoints, and proprietary assets have been removed; all
> configuration is environment-driven (`.env.example`). Authored by
> [Paul Cleenewerck](https://github.com/pcleene).

---

# Manufacturing Group Manufacturing - OEM Partner Assembly Line MES

**Manufacturing Execution System Dashboard**

A proof-of-concept MES dashboard demonstrating MongoDB Time Series collections and aggregation pipelines for real-time manufacturing analytics, serving Manufacturing Group Malaysia's OEMPartner motorcycle assembly operations.

---

## Executive Summary

This solution provides a modern Manufacturing Execution System (MES) dashboard built on MongoDB Atlas, designed to demonstrate:

| Capability | Description |
|------------|-------------|
| **Time Series Analytics** | Efficient storage and querying of high-frequency machine telemetry data using MongoDB Time Series collections |
| **Cross-Department Insights** | Pre-computed materialized views serving Quality, Operations, and Anomaly Detection teams with sub-100ms response times |
| **ML-Ready Architecture** | Feature engineering pipeline with anomaly detection using Isolation Forest and Random Forest models |
| **Scalable Foundation** | Architecture designed to evolve from batch processing to real-time streaming via Change Streams or Atlas Stream Processing |

The system monitors **14 machines** across **4 assembly lines** (Frame Welding, Engine Assembly, Paint Shop, Final Assembly), processing telemetry at 1-minute intervals and generating actionable insights for production optimization.

---

## System Architecture

```
                              DATA INGESTION
                                    |
                                    v
+------------------+        +------------------+        +------------------+
|   Data Generator |------->|  MongoDB Atlas   |<-------|   ML Pipeline    |
|   (Telemetry)    |        |  (Time Series)   |        |  (Anomaly Det.)  |
+------------------+        +--------+---------+        +------------------+
                                     |
                    +----------------+----------------+
                    |                                 |
            +-------v--------+               +-------v--------+
            | Quality Views  |               | Operations     |
            | mv_quality_*   |               | Views          |
            | (Pre-computed) |               | mv_production_*|
            +-------+--------+               +-------+--------+
                    |                                 |
                    +----------------+----------------+
                                     |
                            +--------v--------+
                            |    FastAPI      |
                            |    REST API     |
                            +--------+--------+
                                     |
                            +--------v--------+
                            |   SvelteKit     |
                            |   Dashboard     |
                            +-----------------+
```

### Component Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | SvelteKit 5 + Tailwind CSS | Interactive dashboard with real-time charts |
| **Backend** | FastAPI + PyMongo Async | RESTful API with async database operations |
| **Database** | MongoDB Atlas (Time Series) | Telemetry storage with automatic compression |
| **ML Engine** | Scikit-learn / PySpark | Anomaly detection and feature engineering |

---

## Key Features

### Real-Time Dashboards

| Dashboard | Purpose | Data Source |
|-----------|---------|-------------|
| **Overview** | KPI summary across all lines | Aggregated from all views |
| **Quality** | Defect rates, alert analysis, quality scores | `mv_quality_core`, `mv_quality_analytics` |
| **Operations** | Production output, utilization, downtime | `mv_production_core`, `mv_production_analytics` |
| **Anomalies** | ML-detected anomalies, severity breakdown | `anomaly_detections` |
| **Telemetry** | Raw sensor data exploration | `machine_telemetry` |

### Materialized Views

Pre-computed aggregations eliminate expensive real-time queries:

| View | Refresh | Window | Purpose |
|------|---------|--------|---------|
| `mv_quality_core` | 15 min | 24 hours | Real-time quality KPIs |
| `mv_quality_analytics` | 30 min | 7 days | Machine health trends |
| `mv_production_core` | 15 min | 24 hours | Production metrics |
| `mv_production_analytics` | 30 min | 7 days | Efficiency analysis |

### ML Anomaly Detection

| Model | Type | Use Case |
|-------|------|----------|
| **Isolation Forest** | Unsupervised | Outlier detection without labels |
| **Random Forest** | Supervised | Anomaly type classification |

Detected anomaly types: `temperature_spike`, `vibration_anomaly`, `power_surge`, `cycle_degradation`, `bearing_failure`

---

## Performance Metrics

| Metric | Raw Query | Materialized View | Improvement |
|--------|-----------|-------------------|-------------|
| Quality Dashboard | ~2.5s | <100ms | **25x faster** |
| Operations Dashboard | ~2.0s | <100ms | **20x faster** |
| Documents Scanned | 600,000+ | 20-100 | **6000x fewer** |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas account (M0 free tier or higher)

### 1. Clone and Configure

```bash
# Navigate to project
cd ManufacturingOEM-MES

# Configure backend environment
cd backend
cp .env.example .env
```

Edit `backend/.env` with your MongoDB Atlas credentials:

```env
# MongoDB Atlas Connection (REQUIRED)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=ManufacturingOEM_db

# Application Settings
APP_ENV=development
APP_DEBUG=true
TIMEZONE=Asia/Kuala_Lumpur
```

> **Important:** Replace `<username>`, `<password>`, and `<cluster>` with your actual MongoDB Atlas credentials. These are placeholder values only.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data (7 days by default, or specify days)
python generate_assembly_line_data.py 7

# Refresh materialized views (REQUIRED after data generation)
python refresh_views.py

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Data Setup

### Sample Data Generation

The data generator creates realistic telemetry data with:
- Shift patterns (Morning, Evening, Night)
- Weekend production reduction
- Scheduled maintenance windows
- 2% anomaly injection rate for ML training

```bash
# Generate 7 days of data (default)
python generate_assembly_line_data.py

# Generate 30 days of data
python generate_assembly_line_data.py 30
```

### Materialized View Refresh

**Important:** After generating data, materialized views must be refreshed to populate the dashboards.

```bash
# Refresh all views
python refresh_views.py

# Refresh specific views
python refresh_views.py --view quality
python refresh_views.py --view production
python refresh_views.py --type analytics
```

> **Note on Real-Time Updates:** This POC uses scheduled batch refresh for materialized views. Automatic real-time refresh via MongoDB Change Streams or Atlas Stream Processing was not implemented for this demo. For production deployment, consider implementing Change Streams for near real-time updates or Atlas Stream Processing for complex streaming transformations.

### Collections Created

| Collection | Type | Description |
|------------|------|-------------|
| `machine_telemetry` | Time Series | Raw sensor readings (1-minute granularity) |
| `machines` | Document | Machine reference data and thresholds |
| `mv_quality_core` | Document | Pre-computed quality metrics (24h) |
| `mv_quality_analytics` | Document | Machine health scores (7 days) |
| `mv_production_core` | Document | Pre-computed production stats (24h) |
| `mv_production_analytics` | Document | Weekly efficiency metrics |
| `anomaly_detections` | Document | ML pipeline output |

---

## API Reference

### Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/summary` | Lightweight KPI summary |
| GET | `/api/v1/dashboard/quality` | Quality department metrics |
| GET | `/api/v1/dashboard/operations` | Operations/production metrics |
| GET | `/api/v1/dashboard/anomalies` | Anomaly detection summary |
| GET | `/api/v1/dashboard/lines` | Assembly line reference data |
| POST | `/api/v1/dashboard/views/refresh` | Trigger view refresh |

### Telemetry Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/telemetry` | Query telemetry with filters |
| GET | `/api/v1/telemetry/latest` | Latest reading per machine |
| GET | `/api/v1/telemetry/machines` | Machine reference data |
| GET | `/api/v1/telemetry/stats` | Aggregated statistics |
| GET | `/api/v1/telemetry/anomalies` | Anomaly readings |

### Query Parameters

| Parameter | Endpoints | Description |
|-----------|-----------|-------------|
| `line_id` | telemetry, stats | Filter by assembly line |
| `machine_id` | telemetry, stats | Filter by machine |
| `status` | telemetry | Filter by status (running/idle/maintenance/error) |
| `start_date` | telemetry, stats | Start of date range (ISO format) |
| `end_date` | telemetry, stats | End of date range (ISO format) |
| `limit` | telemetry | Max records to return |

---

## Assembly Line Configuration

| Line ID | Name | Machines | Description |
|---------|------|----------|-------------|
| LINE-1 | Frame Welding | WLD-001, WLD-002, WLD-003 | Robotic welding stations |
| LINE-2 | Engine Assembly | ENG-001 to ENG-004 | Crankshaft, Piston, Cylinder Head, Transmission |
| LINE-3 | Paint Shop | PNT-001, PNT-002 | Paint booths with curing |
| LINE-4 | Final Assembly | FIN-001 to FIN-005 | Electrical, Fuel, Wheels, Body, QC |

---

## Project Structure

```
ManufacturingOEM-MES/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/          # API endpoints
│   │   ├── aggregations/           # Materialized view pipelines
│   │   ├── ml/                     # ML models and feature engineering
│   │   ├── models/                 # Pydantic schemas
│   │   ├── services/               # Business logic
│   │   ├── config.py               # Environment settings
│   │   ├── database.py             # MongoDB connection
│   │   └── main.py                 # FastAPI application
│   ├── generate_assembly_line_data.py    # Sample data generator
│   ├── refresh_views.py            # View refresh utility
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── lib/                    # Components, API client, stores
│   │   └── routes/                 # Page components
│   ├── package.json
│   └── tailwind.config.js
├── TECHNICAL_OVERVIEW.md           # Detailed architecture documentation
└── README.md
```

---

## Production Deployment Notes

### View Refresh Scheduling

For production, schedule materialized view refreshes:

```bash
# Core pipelines - every 15 minutes
*/15 * * * * cd /path/to/backend && python refresh_views.py --type core

# Analytics pipelines - every 30 minutes
*/30 * * * * cd /path/to/backend && python refresh_views.py --type analytics
```

### MongoDB Atlas Configuration

| Setting | Recommended |
|---------|-------------|
| Cluster Tier | M10+ (for Stream Processing) |
| Storage | Auto-scaling enabled |
| Backup | Continuous backup |
| Retention | 90 days (configured in collection) |

---

## Additional Documentation

- **[TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md)** - Detailed architecture, aggregation pipelines, and future enhancement options including Change Streams and Atlas Stream Processing

---

## Technology Stack

- **Backend:** Python 3.11+, FastAPI, PyMongo Async
- **Frontend:** SvelteKit 5, Svelte 5, Tailwind CSS 4, Chart.js
- **Database:** MongoDB Atlas with Time Series Collections
- **ML:** Scikit-learn, NumPy, (optional) PySpark

---

*Manufacturing Group Malaysia - OEMPartner Assembly Line MES Dashboard*
