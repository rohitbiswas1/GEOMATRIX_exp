# GEOMATRIX — Land Acquisition AI & Risk Monitoring Platform

> **Predictive Intelligence & Decision Support for Smarter National Infrastructure**  
> **Smart India Hackathon 2026 · Problem Statement 26017 · Smart Automation**

Geomatrix is an AI-powered enterprise decision-support system designed for the **early detection, quantification, and mitigation of land-acquisition delays** across major infrastructure corridors (highways, rail, energy, industrial corridors). Rather than passively tracking delays after milestones are missed, Geomatrix employs machine learning and Explainable AI (SHAP) to forecast bottleneck probability, pinpoint underlying drivers, prioritize critical interventions, and provide generative AI mitigation strategies via Google Gemini.

---

## 🏛️ Core System Architecture

Geomatrix runs as a decoupled full-stack platform:

```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend: Next.js (Port 3000)               │
│  - React 19 / Next.js App Router                            │
│  - Custom Design System (globals.css) with Light/Dark Theme │
│  - Interactive Visualizations (Recharts) & GIS Map View     │
│  - Central Typed API Client (lib/apiClient.ts)              │
│  - Server-side Gemini Decision Proxy                        │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / JSON (HTTP & Rewrites)
┌──────────────────────────────▼──────────────────────────────┐
│                 Backend: FastAPI (Port 8000)                │
│  - Python 3.10+ / FastAPI / SQLAlchemy / SQLite             │
│  - Scikit-Learn ML Pipeline (RandomForest + Regressors)     │
│  - TreeExplainer SHAP Feature Attribution Engine            │
│  - Multi-Source Data Ingestion (Bhoomi Rashi / CSV Upload)  │
│  - Google Gemini Generative AI Mitigation Provider          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File-by-File Codebase & Responsibilities

### 1. Root Configuration

- [`package.json`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/package.json): Defines frontend dependencies (`next`, `react`, `recharts`, `lucide-react`, `jspdf`, `xlsx`) and runtime scripts (`npm run dev`, `npm run build`).
- [`next.config.ts`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/next.config.ts): Next.js configuration enabling strict mode and routing `/backend/*` rewrites to the FastAPI server (`http://127.0.0.1:8000/*`).
- [`tsconfig.json`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/tsconfig.json): TypeScript configuration and module resolution with `@/*` aliases.
- [`.env.local`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/.env.local) / [`.env`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/.env): Environment variables for Google OAuth 2.0 credentials, Google Maps API key, Gemini Generative AI API key, and `NEXT_PUBLIC_API_URL`.

---

### 2. Frontend Shared Libraries & Components (`lib/` & `components/`)

- [`lib/apiClient.ts`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/lib/apiClient.ts): **Central Typed API Client**. Manages HTTP requests to the FastAPI backend with structured return types and error handling (`ApiError`). Exposes:
  - `fetchProjects()`, `fetchProject()`, `createProject()`, `updateProject()`
  - `runPrediction()` and `fetchExplanation()` (SHAP attributions)
  - `fetchGeojson()` and `fetchDashboardSummary()`
  - `fetchAlerts()`, `uploadFile()`, `fetchModelStatus()`, and `trainModel()`
- [`components/Shell.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/components/Shell.tsx): Master application shell containing the sidebar navigation (Portfolio, Analytics, GIS Map, Ingestion, ML Models, Reports), header, global search, and Light / Dark / System theme switcher.
- [`components/ExportDropdown.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/components/ExportDropdown.tsx): Dropdown UI component providing instant exports to CSV, Excel (`.xls`), and PDF formats.
- [`lib/exportUtils.ts`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/lib/exportUtils.ts): Client-side report export utilities utilizing `jspdf`, `jspdf-autotable`, and Excel-compatible HTML tables.
- [`lib/data.ts`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/lib/data.ts): Core TypeScript types, risk thresholds (`Critical`, `High`, `Medium`, `Low`), acquisition stages, and benchmark fallbacks.
- [`lib/reports.ts`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/lib/reports.ts): Utility functions for compiling audit logs, formatting KPIs, and generating executive summary statements.

---

### 3. Frontend Application Pages (`app/`)

- [`app/layout.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/layout.tsx): Root HTML wrapper providing font configuration, theme initialization scripts, and the `Shell` layout.
- [`app/globals.css`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/globals.css): Complete custom CSS design system using CSS custom properties for responsive grid layouts, glassmorphic cards, tables, badges, and dark/light modes.
- [`app/login/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/login/page.tsx): Authentication screen with Google OAuth 2.0 Sign-In and an instant zero-credential Demo Mode bypass.
- [`app/dashboard/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/dashboard/page.tsx): **Executive Dashboard**. Displays real-time database KPIs (`total_projects`, `critical_count`, `high_count`, `total_land_ha`), risk distribution charts, and backend connectivity indicators.
- [`app/projects/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/projects/page.tsx): **Master Projects Register**. Displays projects from the database with multi-field filtering (State, Stage, Risk, Compensation, Legal Cases) and sorting. Includes an **"Add Project" modal featuring all 18 prediction fields** (Land Required, Land Acquired, Affected Families, Compensation, Objections, Legal Cases, R&R Status, Clearances, Lat/Lng).
- [`app/projects/[id]/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/projects/%5Bid%5D/page.tsx): **Project Intelligence & Risk Deep-Dive**:
  - **AI Risk Analysis**: Real TreeExplainer SHAP feature importance charts and Gemini decision support recommendations.
  - **Forecast & Prediction**: On-demand "Run Risk Prediction" button with model confidence score and delay estimates.
  - **What-If Simulator**: Interactive sliders adjusting compensation, legal disputes, and documentation completeness against live project baselines.
  - **Interventions**: Automated mitigation action plan.
  - **Pipeline & Timeline**: Acquisition stage milestone tracking.
  - **Data Lineage**: Source tracking, record IDs, and missing field validation warnings.
- [`app/map/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/map/page.tsx): **GIS Spatial Intelligence**. Renders project markers at their real GPS coordinates with risk-level color codes, popups, and district filters.
- [`app/alerts/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/alerts/page.tsx): **Early-Warning Alerts Hub**. Surfaces active database alerts for compensation delays, clearance bottlenecks, and legal disputes with acknowledge capabilities.
- [`app/data/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/data/page.tsx): **Data Ingestion Management**. Supports multipart CSV file upload for Karnataka Bhoomi Rashi records and Historical Delay records, with a live `DataIngestionLog` audit history.
- [`app/model/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/model/page.tsx): **ML Model Intelligence**. Shows live model version, training timestamp, sample size, Precision, Recall, F1, and ROC-AUC scores with an on-demand "Train Model" button.
- [`app/reports/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/reports/page.tsx): Comprehensive multi-format reporting module for executive and audit presentations.
- [`app/analytics/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/analytics/page.tsx): Portfolio-wide comparative risk analytics, authority breakdown, and bottleneck tracking.
- [`app/settings/page.tsx`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/settings/page.tsx): System preferences, API configuration, and theme toggling.
- [`app/api/gemini/explain/route.ts`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/app/api/gemini/explain/route.ts): Server-side API route that proxies decision-support requests to FastAPI `/api/gemini/explain`, keeping secret keys off client browsers.

---

### 4. Backend Engine (`geomatrix_v2/`)

- [`geomatrix_v2/main.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/main.py): FastAPI application initialization, CORS configuration (`allow_origins=["*"]`), router registrations, and database startup.
- [`geomatrix_v2/database.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/database.py): SQLAlchemy SQLite connection and non-destructive `ALTER TABLE` migration routines for dynamic column upgrades.
- [`geomatrix_v2/models.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/models.py): **SQLAlchemy Database Models**:
  - `Project`: Comprehensive entity holding identifiers, geometry (lat/lng), scale, and the 10 real ML risk attributes.
  - `HistoricalDelayRecord`: Historical training delay records with actual outcomes.
  - `Prediction`: Persisted risk score, delay probability, predicted days, and timestamp.
  - `ShapValue`: TreeExplainer SHAP attributions stored per feature per prediction.
  - `Alert`: Early-warning notifications triggered by project conditions.
  - `ModelRun`: Trained model registry tracking algorithms, performance metrics, and artifact paths.
  - `DataIngestionLog`: Ingestion audit log tracking data sources, row counts, and errors.
- [`geomatrix_v2/schemas.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/schemas.py): Pydantic V2 schemas validating API payloads (`ProjectCreate`, `ProjectUpdate`, `ProjectOut`, `PredictionOut`, `ModelStatusOut`, etc.).
- [`geomatrix_v2/seed_db.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/seed_db.py): Seed script that populates 20 historical records, trains the RandomForest model, creates 6 infrastructure projects (`GM-WB-001` through `GM-OD-006`), and stores real predictions and SHAP scores.

---

### 5. Machine Learning Pipeline (`geomatrix_v2/ml/`)

- [`geomatrix_v2/ml/features.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/ml/features.py): Feature extraction pipeline constructing a 10-dimensional numerical vector:
  `[land_area_ha, affected_families, pending_claims, legal_cases, doc_completeness_pct, approval_pending, rr_pending, overdue_milestones, compensation_pending, env_clearance_pending]`.
- [`geomatrix_v2/ml/train.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/ml/train.py): Trains a `RandomForestClassifier` for binary delay classification and a `GradientBoostingRegressor` for delay duration (days). Strictly requires $\ge 10$ labeled samples; generates real evaluation metrics and serializes artifacts (`clf.pkl`, `reg.pkl`, `scaler.pkl`).
- [`geomatrix_v2/ml/predict.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/ml/predict.py): Inference engine that loads serialized model artifacts, scales feature vectors, and computes delay probability, risk score, and confidence.
- [`geomatrix_v2/ml/explain.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/ml/explain.py): Computes true per-feature SHAP attributions using `shap.TreeExplainer` on the trained model.
- [`geomatrix_v2/ml/evaluate.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/ml/evaluate.py): Computes classification reports, confusion matrices, and ROC-AUC curves.

---

### 6. Backend API Routers (`geomatrix_v2/routers/`)

- [`geomatrix_v2/routers/projects.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/projects.py): Project CRUD, risk prediction execution, SHAP explanation retrieval, validation check, and dashboard summary aggregation.
- [`geomatrix_v2/routers/ingest.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/ingest.py): Multi-source data ingestion (Bhoomi Rashi CSV uploads, data.gov.in integration, ingestion audit log).
- [`geomatrix_v2/routers/ml.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/ml.py): Model status reports, training data summaries, and real model re-training triggers.
- [`geomatrix_v2/routers/alerts.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/alerts.py): Risk alert listing, acknowledgement actions, and summary statistics.
- [`geomatrix_v2/routers/map.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/map.py): Generates GeoJSON FeatureCollections from real project coordinates for the GIS map.
- [`geomatrix_v2/routers/gemini.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/gemini.py): Constructs specialized prompts with real project data and queries Google Gemini for mitigation plans.
- [`geomatrix_v2/routers/auth.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/routers/auth.py): Authentication verification and session state handling.

---

### 7. Automated Tests (`geomatrix_v2/tests/`)

- [`geomatrix_v2/tests/test_ml_pipeline.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/tests/test_ml_pipeline.py):
  - `test_model_status_reports_insufficient_real_data_message`
  - `test_predict_project_risk_returns_clear_message_when_model_is_missing`
  - `test_train_model_rejects_insufficient_real_labeled_data` (enforces $\ge 10$ records)
  - `test_train_model_writes_real_metrics_for_valid_training_data`
- [`geomatrix_v2/tests/test_real_pipeline_api.py`](file:///c:/Users/rohit/Downloads/geomatrix-sih2026-prototype.worktrees/geomatrix-full-update-production-ready/geomatrix_v2/tests/test_real_pipeline_api.py):
  - `test_real_upload_training_prediction_and_shap_persisted` (end-to-end integration test)
  - `test_missing_historical_label_is_rejected`

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### 2. Backend Setup
```bash
cd geomatrix_v2
pip install -r requirements.txt

# Seed the database and train the initial model
python seed_db.py

# Start the FastAPI server
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
*The FastAPI backend will be available at `http://127.0.0.1:8000` with interactive docs at `/docs`.*

### 3. Frontend Setup
In a separate terminal at the project root:
```bash
npm install
npm run dev
```
*The Next.js frontend will be available at `http://localhost:3000`.*

---

## 🧪 Verification & Testing

To verify backend tests:
```bash
cd geomatrix_v2
python -m pytest tests/ -v
# Output: 6 passed in ~17 seconds
```

To verify frontend TypeScript types:
```bash
npx tsc --noEmit
# Output: 0 errors
```

---

## 🔒 Security & Data Privacy

- **Server-Side API Key Isolation**: All calls to the Google Gemini API are proxied through server-side routes; client browsers never receive or expose the secret key.
- **Environment Separation**: Sensitive credentials are kept in `.env.local` which is excluded from version control via `.gitignore`.
- **Safe Database Migrations**: The database engine performs non-destructive schema adjustments on startup without risk of table deletion or data loss.
