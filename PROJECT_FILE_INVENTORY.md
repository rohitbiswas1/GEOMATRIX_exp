# Geomatrix Complete Project File Inventory

## 1. Project overview
Geomatrix is a full-stack land acquisition and infrastructure delay intelligence system combining a Next.js frontend, FastAPI backend, SQLite data layer, and a Python ML pipeline. It is designed to show real project risk, model status, and AI-driven explanation while staying honest about when the model is unavailable.

This inventory covers the visible project files in the workspace, grouped by layer and purpose.

---

## 2. Root-level project files

### Core configuration
- .env
- .env.example
- .env.local
- .gitignore
- package.json
- package-lock.json
- next.config.ts
- next-env.d.ts
- tsconfig.json
- tsconfig.tsbuildinfo
- eslint.config.mjs
- vercel.json
- pytest.ini

### Documentation and status files
- README.md
- README_NEW.md
- README.pdf
- REAL_DATA_PROFILING_REPORT.md
- TODO.md
- tb_information_summary.txt
- tb_information_summary.pdf
- all_prompts.txt
- scripts_seed.txt
- GEOMATRIX_TODO_CHECKLIST.pdf
- generate_readme_pdf.py
- generate_todo_pdf.py

### Project inventory and export files
- PROJECT_FILE_INVENTORY.md
- PROJECT_FILE_INVENTORY.pdf
- PROJECT_FILE_INVENTORY_DETAILED.md
- PROJECT_FILE_INVENTORY_DETAILED.pdf
- PROJECT_FILE_INVENTORY_ULTRA_DETAILED.md

### Static public assets
- public/geomatrix-landscape.png

### Generated project folders
- .next/
- .next-dev.log
- .next-dev.pid
- .pytest_cache/
- node_modules/

---

## 3. Frontend app structure

### Root app files
- app/layout.tsx
- app/globals.css
- app/page.tsx
- app/not-found.tsx

### Auth and entry flows
- app/login/page.tsx

### Main product pages
- app/dashboard/page.tsx
- app/projects/page.tsx
- app/projects/[id]/page.tsx
- app/map/page.tsx
- app/alerts/page.tsx
- app/data/page.tsx
- app/model/page.tsx
- app/reports/page.tsx
- app/analytics/page.tsx
- app/settings/page.tsx
- app/admin/model/page.tsx

### App API routes
- app/api/alerts/route.ts
- app/api/alerts/summary/route.ts
- app/api/alerts/[id]/acknowledge/route.ts
- app/api/analytics/overview/route.ts
- app/api/analytics/drivers/route.ts
- app/api/analytics/stages/route.ts
- app/api/auth/google/route.ts
- app/api/documents/upload/route.ts
- app/api/gemini/explain/route.ts
- app/api/ingest/upload/route.ts
- app/api/ingest/log/route.ts
- app/api/map/geojson/route.ts
- app/api/map/projects/route.ts
- app/api/model/status/route.ts
- app/api/model/train/route.ts
- app/api/model/training-data/route.ts
- app/api/predict/route.ts
- app/api/projects/route.ts
- app/api/projects/dashboard-summary/route.ts
- app/api/projects/[id]/route.ts
- app/api/projects/[id]/predict-risk/route.ts
- app/api/projects/[id]/explain/route.ts
- app/api/projects/[id]/explanation/route.ts
- app/api/projects/[id]/risk/route.ts
- app/api/projects/[id]/recommendations/route.ts
- app/api/projects/[id]/validate/route.ts
- app/api/reports/route.ts

### Shared frontend components
- components/Shell.tsx
- components/ExportDropdown.tsx

### Shared frontend libraries
- lib/api.ts
- lib/apiClient.ts
- lib/data.ts
- lib/exportUtils.ts
- lib/reports.ts

### Prisma schema
- prisma/schema.prisma

---

## 4. Backend and service layer

### Core backend files
- geomatrix_v2/main.py
- geomatrix_v2/database.py
- geomatrix_v2/models.py
- geomatrix_v2/schemas.py
- geomatrix_v2/requirements.txt
- geomatrix_v2/seed_db.py
- geomatrix_v2/geomatrix.db

### Backend routers
- geomatrix_v2/routers/__init__.py
- geomatrix_v2/routers/auth.py
- geomatrix_v2/routers/alerts.py
- geomatrix_v2/routers/gemini.py
- geomatrix_v2/routers/ingest.py
- geomatrix_v2/routers/map.py
- geomatrix_v2/routers/ml.py
- geomatrix_v2/routers/projects.py

### Backend static assets
- geomatrix_v2/static/css/style.css
- geomatrix_v2/static/js/app.js

### Backend sample and upload storage
- geomatrix_v2/sample_data/
- geomatrix_v2/uploads/

### Python package caches
- geomatrix_v2/__pycache__/
- geomatrix_v2/routers/__pycache__/
- geomatrix_v2/ml/__pycache__/
- geomatrix_v2/tests/__pycache__/

---

## 5. ML pipeline files

### ML package entry points
- geomatrix_v2/ml/__init__.py
- geomatrix_v2/ml/features.py
- geomatrix_v2/ml/train.py
- geomatrix_v2/ml/predict.py
- geomatrix_v2/ml/explain.py
- geomatrix_v2/ml/evaluate.py

### Model artifact storage
- geomatrix_v2/model_artifacts/active_model.json
- geomatrix_v2/model_artifacts/meta_0ad11dd9-27eb-4edf-89d6-71f283708b85.json
- geomatrix_v2/model_artifacts/meta_01a030a5-f5c5-45e3-9fd7-cda56ba242c8.json
- geomatrix_v2/model_artifacts/clf_0ad11dd9-27eb-4edf-89d6-71f283708b85.pkl
- geomatrix_v2/model_artifacts/clf_01a030a5-f5c5-45e3-9fd7-cda56ba242c8.pkl
- geomatrix_v2/model_artifacts/reg_0ad11dd9-27eb-4edf-89d6-71f283708b85.pkl
- geomatrix_v2/model_artifacts/reg_01a030a5-f5c5-45e3-9fd7-cda56ba242c8.pkl
- geomatrix_v2/model_artifacts/scaler_0ad11dd9-27eb-4edf-89d6-71f283708b85.pkl
- geomatrix_v2/model_artifacts/scaler_01a030a5-f5c5-45e3-9fd7-cda56ba242c8.pkl

### ML-related test files
- geomatrix_v2/tests/test_ml_pipeline.py
- geomatrix_v2/tests/test_real_pipeline_api.py
- geomatrix_v2/tests/test_api.py
- geomatrix_v2/tests/test_database.py
- geomatrix_v2/tests/test_ml.py
- geomatrix_v2/tests/conftest.py

---

## 6. Important functional purpose by folder

### Root-level config and docs
This layer handles project setup, build tooling, deployment, documentation, and operational checkpointing.

### app/
This is the main Next.js frontend surface. It includes routes, page views, and API proxies for the project.

### components/
This directory contains UI shell and reusable export components used across the application.

### lib/
This directory holds shared frontend logic, metadata, API wrappers, and export/report helpers.

### prisma/
Contains the Prisma schema for database modeling and data access definitions.

### geomatrix_v2/
This is the Python backend and ML engine. It contains the database model layer, routers, static assets, validation logic, and ML code.

### geomatrix_v2/ml/
This contains the real feature engineering, training, prediction, evaluation, and explainability pipeline.

### geomatrix_v2/model_artifacts/
This stores active model metadata and the serialized artifacts created during model training.

### geomatrix_v2/tests/
This contains regression and end-to-end validation tests ensuring the app behaves honestly when the model is unavailable or invalid.

---

## 7. Notable file-to-purpose mapping

- app/projects/[id]/page.tsx — main project detail and risk view
- app/api/predict/route.ts — frontend prediction endpoint
- app/api/gemini/explain/route.ts — AI explanation route
- geomatrix_v2/routers/projects.py — project CRUD plus prediction logic integration
- geomatrix_v2/routers/ingest.py — CSV/JSON ingestion and validation
- geomatrix_v2/database.py — SQLite engine and DB-level setup
- geomatrix_v2/models.py — schemas and ORM entities
- geomatrix_v2/ml/train.py — real-data training and validation logic
- geomatrix_v2/ml/predict.py — safe runtime inference and confidence checks
- geomatrix_v2/ml/explain.py — explanation and SHAP support
- geomatrix_v2/tests/test_ml_pipeline.py — model safety regression tests
- geomatrix_v2/tests/test_real_pipeline_api.py — end-to-end backend validation

---

## 8. Generated and machine-created files
The following are visible generated artifacts and caches, not necessarily hand-written application files:
- .next/
- .next-dev.log
- .next-dev.pid
- .pytest_cache/
- node_modules/
- tsconfig.tsbuildinfo
- __pycache__ directories
- compiled Python bytecode files
- PDF exports and generated summary documents

These files support build, test, and artifact generation but are not usually the business logic source files.

---

## 9. Final assessment
This project is organized into a standard full-stack setup:
- frontend in the root app/ and components/ directories
- data access and API wrappers in lib/
- Python backend and ML engine under geomatrix_v2/
- operational, config, and doc files in the root workspace
- test and build artifacts in generated folders and cache directories

The inventory now includes the full visible project structure, not just the primary app files, and covers the important source files as well as the generated artifacts and support files associated with the workspace.

### geomatrix_v2/static/css/style.css
Static CSS for the older/integration web layer.

### geomatrix_v2/static/js/app.js
Static JS used by legacy views.

### geomatrix_v2/templates/partials/
Template partials for earlier backend rendering.

### geomatrix_v2/model_artifacts/
Serialized model metadata, binaries, and active model pointer files.

## Tests

### geomatrix_v2/tests/test_ml_pipeline.py
Regression checks for honest model training and risk behavior.

### geomatrix_v2/tests/test_real_pipeline_api.py
End-to-end tests covering upload, training, prediction, and SHAP persistence.

## Summary of Responsibilities
- Frontend handles user experience and reporting.
- Backend manages persistence, API logic, ingestion, and ML orchestration.
- ML layer ensures only valid real-labeled data is used for risk modeling.
- Gemini acts as a recommendation and explanation layer, not the main prediction engine.
- SQLite stores the project records, training data, and model metadata.

## Final Notes
This repository keeps the UI stable while enforcing integrity: real data only, no fake predictions, no synthetic labels, and no fabricated confidence or delay estimates unless a verified regression target exists.
