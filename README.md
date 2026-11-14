# YemenVision-MTMC: Vehicle Detection, ReID, Tracking & Traffic Intelligence

[![CI](https://github.com/Al-Nahari/YemenVision-MTMC/actions/workflows/ci.yml/badge.svg)](https://github.com/Al-Nahari/YemenVision-MTMC/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Research-red.svg)]()

A modular ML and platform architecture for traffic surveillance, vehicle detection, vehicle re-identification (ReID), single-camera tracking, and multi-camera association (MTMC).

---

## 1. System Architecture

The project consists of three integrated layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        YemenVision-MTMC Stack                          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Frontend Dashboard (Angular / Web UI)                               │
│    • Live Camera Streams & Spatial-Temporal Map                        │
│    • Real-time Vehicle Counting & Traffic Aggregate Metrics            │
│    • Vehicle Tracklet Inspection & ReID Search                         │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Backend Platform (FastAPI + SQLAlchemy + SQLite / PostgreSQL)       │
│    • RESTful APIs for Camera Management, Event Ingestion, & Tracklets  │
│    • ML Inference Service (Ultralytics Detector + ReID Extractor)      │
│    • Role-Based Access Control (RBAC) & Tamper-Evident Audit Logging   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. ML & Research Core (`research/`)                                    │
│    • Data Engineering: Adapters, Schema Contracts, Split Manifests     │
│    • Vehicle Detection: YOLO11 Training & Evaluation Pipeline          │
│    • Vehicle ReID: ResNet50 + PK-Sampler + Triplet Loss (mAP/CMC)      │
│    • Tracking: Real-time IoU + Kalman Velocity Lifecycle Engine        │
│    • Multi-Camera Association: Topology-aware Spatio-Temporal Matcher  │
│    • Traffic Intelligence: Privacy-Preserving Event Aggregations       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Truthful Operational Status (Phase Status & Evidence)

In accordance with strict project governance rules, we report what is verified, what is trained, and what is currently pending data:

| Subsystem | Operational State | Evidence & Metrics | Limitations / Pending Items |
|---|---|---|---|
| **Vehicle Detection** | **Operational** | Pipeline trained with `yolo11n.pt` and tested on vehicle classes (`car`, `bus`, `truck`, `motorcycle`). | Public domain adaptation; requires local Yemeni data for dust/lighting shifts. |
| **Vehicle ReID** | **Operational** | ResNet50 Feature Extractor trained with `batch_hard_triplet` + Label Smoothing on disjoint identity splits. Evaluated via Query/Gallery protocol. | Rank-1 and mAP represent visual retrieval ranking, not legal identity proof. |
| **In-Camera Tracking** | **Operational** | Deterministic IoU + Velocity tracker (`research/tracking/engine.py`) managing track life cycle (`tentative`, `confirmed`, `lost`). | Single-camera tracks; resets ID per sequence/camera. |
| **Cross-Camera MTMC** | **Data Pending** | Association Engine implemented with Hungarian matching & topology constraints (`research/association/engine.py`). | **Unassessed:** Cross-camera IDF1 is withheld until synchronized multi-camera video streams are acquired. |
| **Backend & Dashboard** | **Operational** | Full FastAPI backend with endpoints for inference, events, tracklets, and audit logs. | Ready for containerized deployment via Docker Compose. |

---

## 3. Directory Layout

```
.
├── backend/                   # FastAPI Platform & Ingestion Service
│   ├── app/
│   │   ├── main.py            # API routes & lifespan handler
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── schemas.py         # Pydantic v2 schemas
│   │   ├── services.py        # Video inference & audit services
│   │   └── security.py        # API key verification & rate limiting
│   └── tests/                 # Backend unit & integration tests
├── dashboard/                 # Frontend Dashboard application
├── research/                  # Machine Learning research modules
│   ├── configs/               # Official YAML training & topology configs
│   ├── data_engineering/      # Dataset adapters & split validators
│   ├── detection/             # YOLO detection wrappers & evaluation
│   ├── reid/                  # Vehicle ReID models & query/gallery evaluator
│   ├── tracking/              # Single-camera tracking engine
│   ├── association/           # Multi-camera topology & Hungarian matcher
│   ├── traffic/               # Traffic intelligence aggregators
│   └── reports/               # Status audits and readiness reports
├── .github/workflows/         # CI/CD automated test pipelines
├── docker-compose.yml         # One-command platform orchestration
└── YemenVision_MTMC_Colab_Data_Training.ipynb # Colab training pipeline
```

---

## 4. Quick Start

### 4.1 Running Backend Locally

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Start the API server
export PYTHONPATH=backend
export API_KEYS_JSON='{"admin":{"subject":"admin-user","roles":["admin"]}}'
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation available at: `http://localhost:8000/api/v1/docs`

### 4.2 Running All Tests

```bash
# Run ML Research test suite
pytest research/ -v

# Run Backend API & Inference test suite
PYTHONPATH=backend pytest backend/tests/ -v
```

### 4.3 Running with Docker Compose

```bash
docker compose up --build
```

---

## 5. Security & Data Governance Policies

1. **No Raw Data or Weights in Git:** All datasets, video files, SQLite databases, and `.pt` model weights are strictly git-ignored.
2. **No Identity Leakage:** The ReID training split protocol enforces 100% disjoint vehicle identities between `train` and `query`/`gallery` splits.
3. **No Fabricated Benchmarks:** Cross-camera association metrics are labeled `UNASSESSABLE` until physical multi-camera ground-truth data is ingested.
4. **Auditability:** Every camera registration, event ingestion, and video inference execution produces an immutable record in `AuditLog`.
