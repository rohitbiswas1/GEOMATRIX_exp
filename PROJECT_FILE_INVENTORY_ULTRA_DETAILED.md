# Geomatrix Ultra Detailed File Inventory

## 1. Executive Summary

Geomatrix is a land-acquisition and infrastructure delay intelligence system built with a Next.js frontend and FastAPI backend. The system is designed to support project tracking, risk assessment, and AI-assisted explanation. The key technical point is that the ML pipeline is intentionally strict: it only trains and serves predictions when it has enough real labeled data, and it never fabricates delay-day predictions or fake risk metrics when the model is unavailable.

The project therefore follows a disciplined architecture:
- Frontend remains stable and visually consistent with the existing product
- Backend keeps real project data and risk logic
- ML pipeline validates real data before training
- Gemini is used only for explanatory recommendations, not as a source of truth
- Testing ensures honest behavior when model data is insufficient

---

## 2. High-Level System Architecture

### Layer 1: User Experience
The frontend is the visible product layer. It contains the main application views for dashboard, projects, map, alerts, model monitoring, analytics, and reports.

### Layer 2: API and Integration Layer
The Next.js app includes API routes that proxy or wrap backend calls and AI explanation requests. These routes handle project retrieval, prediction requests, analytics, and Gemini-based explanations.

### Layer 3: Core Backend Service
The FastAPI app in geomatrix_v2 contains the business logic for project handling, ingestion, model training, data validation, and prediction generation. It is the real processing layer for the system.

### Layer 4: Data and ML Runtime
The ML layer reads real historical records, extracts features, validates dataset quality, trains the classifier/regressor, and writes model artifacts and metadata.

### Layer 5: Persistence and Model Artifacts
Historical project records and model outputs are stored in SQLite using SQLAlchemy models. The active model metadata and serialized model artifacts live in model_artifacts/.

---

## 3. Root Project Structure and File Roles

### Root configuration files
- package.json: installs frontend dependencies and defines scripts for dev/build/test
- package-lock.json: lockfile for consistent Node dependency resolution
- next.config.ts: configuration for Next.js behavior and API routing
- tsconfig.json: establishes TypeScript constraints and project compilation rules
- eslint.config.mjs: linting standards for code quality
- vercel.json: deployment configuration for hosting
- next-env.d.ts: TS definitions for Next.js environment

### Documentation and operational files
- README.md: main project usage and architecture notes
- README_NEW.md: additional project guidance
- REAL_DATA_PROFILING_REPORT.md: summary of the real-data profiling work and validation process
- TODO.md: current development and completion checklist
- all_prompts.txt: historical task prompt log
- scripts_seed.txt: seed script or workflow notes
- tb_information_summary.txt: summary of technical/business status and audit notes

### Generated deliverables
- PROJECT_FILE_INVENTORY.md: quick file inventory summary
- PROJECT_FILE_INVENTORY.pdf: PDF export of the inventory
- PROJECT_FILE_INVENTORY_DETAILED.md: more structured technical breakdown
- PROJECT_FILE_INVENTORY_DETAILED.pdf: PDF of the detailed breakdown

### Hidden/system directories
- .next/: generated Next.js build artifacts
- .pytest_cache/: pytest cache data
- node_modules/: installed JavaScript dependencies

---

## 4. Frontend Layer: App Pages and Core Structure

### app/layout.tsx
This file wraps the application and provides the shell structure for the entire interface. It is the first-level layout file for HTML and theme binding.

### app/globals.css
This is the global styling sheet. It defines the visual language of the application: spacing, card designs, table styles, button styles, and responsive layout classes.

### components/Shell.tsx
This component provides the main navigation and frame used throughout the app. It gives the project the consistent shell that preserves its existing UI/UX design.

### components/ExportDropdown.tsx
Provides export controls for generated reports and data exports. It supports multiple export types such as CSV, Excel, or PDF.

### lib/data.ts
Contains the typed business metadata used across the UI, such as project states, status categories, and domain-specific enums.

### lib/apiClient.ts
This is the main client abstraction for calling backend APIs in a structured and typed way. It is the frontend contract for retrieving projects, predictions, alerts, and analytics.

### lib/exportUtils.ts
This helper centralizes export logic and can transform data into downloadable file formats.

### lib/reports.ts
This module structures report summaries and output to keep reporting consistent across the app.

---

## 5. Frontend Pages by Purpose

### app/page.tsx
The landing page for the app. It provides the first screen a user sees when entering the application.

### app/login/page.tsx
Login/entry page. This is used for authentication flow and initial session entry.

### app/dashboard/page.tsx
The executive dashboard page. It aggregates project metrics and system state for leadership and operations users.

### app/projects/page.tsx
Project index page listing the available projects, their risk state, and project status metadata.

### app/projects/[id]/page.tsx
This is the most crucial user-facing detail page for a project. It combines risk display, delay explanation, project metadata, and any AI-based guidance.

### app/map/page.tsx
A map interface to visualize the geographic spread of projects and project boundaries.

### app/alerts/page.tsx
Alerts center used to show operational issues, at-risk projects, or triggered concern states.

### app/data/page.tsx
Data upload and management interface for importing project and historical records.

### app/model/page.tsx
Model status page showing whether the model is trained, active, or unavailable.

### app/reports/page.tsx
Generates summary reporting for project and operational use cases.

### app/analytics/page.tsx
Core analysis dashboard for stage-level or attribute-level trends and comparison metrics.

### app/settings/page.tsx
User/system settings page for preferences and service configuration.

### app/admin/model/page.tsx
Admin page focused on model operations and oversight.

---

## 6. API Route Layer

The app/api directory contains Next.js route handlers that connect the frontend to backend functionality and AI services.

### app/api/projects/route.ts
Handles list creation and retrieval for project records.

### app/api/projects/[id]/route.ts
Handles a single project's data and update operations.

### app/api/predict/route.ts
Issues predictions for a project using the ML backend or model endpoint.

### app/api/gemini/explain/route.ts
Calls the Gemini explanation layer to convert risk context into human-readable recommendations and mitigation guidance.

### app/api/analytics/overview/route.ts
Provides summarized analytics for the main overview page.

### app/api/analytics/drivers/route.ts
Returns the key factors influencing project risk.

### app/api/analytics/stages/route.ts
Provides breakdowns by project stage or phase.

### app/api/map/geojson/...
Generates GIS data for map overlays and project location representation.

### app/api/alerts/route.ts
Returns current alerts as structured data for the alerts page.

### app/api/reports/route.ts
Generates report payloads for export or presentation.

### app/api/documents/upload/route.ts
Supports document upload-related actions.

### app/api/auth/google/route.ts
Handles Google authentication flow or starter entry logic.

---

## 7. Backend Core Configuration

### geomatrix_v2/main.py
This is the main FastAPI application entry point. It initializes the app, configures middleware if needed, and registers the routers responsible for projects, ML, alerts, map, auth, and ingestion.

### geomatrix_v2/database.py
This module defines the SQLAlchemy engine, session factory, and operational helpers. It centralizes DB setup and enforces a consistent SQLite connection strategy. In the hardened version, it ensures temporary SQLite databases are stable and do not fail during testing due to engine lifecycle issues.

### geomatrix_v2/models.py
Defines database schemas such as Project, HistoricalDelayRecord, ModelRun, RiskPrediction, Alert, DataIngestionLog, and GeminiInsight. These models serve as the persistence layer for both business records and training provenance.

### geomatrix_v2/schemas.py
Defines Pydantic schemas for validation of inbound and outbound API payloads. This layer guarantees consistent request types and response formatting across routes.

---

## 8. Database Schema and Functional Roles

### Project
Stores the main project metadata and state such as title, area, legal status, compensation information, location references, and more. It is the business record behind the dashboard and project detail page.

### HistoricalDelayRecord
This table contains historical delay events and training-quality records. It is the main source used to construct the ML dataset.

### ModelRun
Tracks training executions, model metadata, timestamps, and artifact references. It allows the app to know whether a model is valid and whether it should be considered active.

### RiskPrediction
Stores the generated prediction results for a project including risk score, confidence, and model version.

### Alert
Stores system-generated alert objects that represent risk or operational anomalies.

### DataIngestionLog
Logs uploaded and imported records, including source names, validation results, and classification tags.

### GeminiInsight
Stores generated AI explanations and recommendations for a project after risk evaluation.

---

## 9. Ingestion and Data Validation Pipeline

### geomatrix_v2/routers/ingest.py
This is the main ingestion router. It parses uploaded CSV or JSON files, maps alias fields, and stores records into the database.

### Responsible behaviors
- reads uploaded files from the user interface
- normalizes field names and values
- maps legacy or inconsistent field names to canonical names
- checks for required columns
- stores a validated record into the historical delay table
- attaches source classification metadata such as REAL or TEST

### Safety rules enforced in this layer
- incomplete records are rejected
- invalid or missing delay flags are not accepted
- synthetic/test rows are classified and filtered from trusted training data
- duplicate or malformed data is not allowed to contaminate the model dataset

### Why this matters
This creates a trust boundary between real historical data and opportunistic or synthetic examples that should never be used for valid production prediction.

---

## 10. ML Feature Engineering

### geomatrix_v2/ml/features.py
This module defines the canonical features used during training and prediction.

### Real feature contract
The features are standardized so the model uses the same fields regardless of where data is coming from. These represent the core delay-driving characteristics of a project.

### Typical features include
- land_area_ha
- affected_families
- pending_claims
- legal_cases
- doc_completeness_pct
- approval_pending
- rr_pending
- overdue_milestones
- compensation_pending
- env_clearance_pending

### Why this is important
Uniform feature extraction prevents mismatch between train-time and inference-time behavior. It also ensures the safety checks are consistent.

---

## 11. ML Training Logic

### geomatrix_v2/ml/train.py
This is the most important file in the ML pipeline. It is responsible for turning historical records into a trainable dataset and for serializing a valid model artifact set.

### Core responsibilities
- normalize raw dataset records
- validate label integrity
- reject insufficient or one-class datasets
- filter out synthetic or test-like records
- train a classifier and optionally a regressor
- save the active model metadata and the model files
- update the active model pointer file

### Guardrails present in the hardened version
- requires a real labeled dataset
- rejects one-class classification datasets
- rejects inactive or stale model artifacts
- removes unsafe or invalid active model pointer files
- requires legitimate metadata before serving the model

### Key internal concepts
- InsufficientDataError: raised when there are not enough valid records
- _normalize_record_list: converts raw data to canonical format
- train_model: orchestrates the training execution
- load_active_model: loads the currently active model if it passes validation
- _clear_active_model_files: removes stale model artifact files

---

## 12. Prediction Safety and Honest Failure States

### geomatrix_v2/ml/predict.py
This file contains prediction logic that decides whether it is safe to predict risk for a project.

### What it enforces
- no prediction when no valid active model exists
- no confidence above 1.0
- no fabricated delay-day output when no regression model is valid
- no fake explanation values when the model is not trusted

### Important behavior
The app is designed to return honest status messages instead of synthetic numbers. When the model is not valid, the system must tell the user:

Model not trained — insufficient real labeled data.

This is a critical product requirement and a core integrity principle for the project.

---

## 13. Explainability and Gemini Layer

### geomatrix_v2/ml/explain.py
This module generates explanation inputs for a trained model. It helps interpret what features are driving the prediction.

### Safety requirement
It should only generate explainability output if the active model is valid. If the model is absent or stale, no SHAP or explanation output is shown.

### Gemini usage role
Gemini is not the source of truth for risk prediction. It is used only as a secondary layer to produce high-level explanations and recommendations from the validated prediction result.

### Why this matters
This keeps the system truthful: the model makes the risk judgment, and the AI layer explains it in a human-friendly way without inventing unsupported numbers.

---

## 14. Router and Backend Services by Feature Area

### geomatrix_v2/routers/projects.py
This is the main project API service. It handles project creation, listing, retrieval, deletion, and prediction routes.

### geomatrix_v2/routers/alerts.py
Handles alert generation, retrieval, acknowledgements, and alert lifecycle management.

### geomatrix_v2/routers/map.py
Responsible for geospatial endpoints and map-serving logic. It supports GIS queries and map data flows.

### geomatrix_v2/routers/ml.py
The ML service endpoint group. It exposes training and prediction routes for model management and risk scoring.

### geomatrix_v2/routers/auth.py
Authentication-related endpoints and identity handling.

### geomatrix_v2/routers/gemini.py
Routes for AI-generated insight and explanation tasks.

---

## 15. Model Artifacts and Training Output

### geomatrix_v2/model_artifacts/
This directory stores model files and metadata generated during training.

### Typical artifact types
- active_model.json: pointer to the active model metadata
- meta_<uuid>.json: metadata records for individual model runs
- clf_<...>.pkl: serialized classification model file
- reg_<...>.pkl: serialized regression model file when available
- scaler_<...>.pkl: transformer or scaler used during preprocessing

### Why artifact management matters
A stale active model pointer or metadata mismatch can cause the app to serve an invalid model. The hardened system avoids that by validating the active model before use and clearing stale artifacts when necessary.

---

## 16. Testing and Regression Safety

### geomatrix_v2/tests/test_ml_pipeline.py
This file tests the model safety rules: no training on insufficient data, no one-class acceptance, no invalid confidence values, and no fake predictions.

### geomatrix_v2/tests/test_real_pipeline_api.py
This verifies the end-to-end pipeline: real ingestion, data validation, model training, prediction, and explanation flow.

### What the test suite enforces
- data must be real and valid before training
- prediction should fail safely without a valid model
- probability/confidence should stay in a valid range
- delay-day outputs must not be fabricated unless there is a real regression target

---

## 17. Frontend Risk Presentation and Honest UI Messaging

### app/projects/[id]/page.tsx
This file is especially important because it is the product-level user interface where the model status is shown.

### Product behavior
When the backend indicates there is no valid model, the frontend must show an honest failure state rather than a fake risk result. The UI keeps the existing design and simply surfaces the correct message.

### Required messaging
The expected message is:

Model not trained — insufficient real labeled data.

This is a key product requirement and a reliability standard for the project.

---

## 18. Critical Integrity Decisions

The project was intentionally hardened to avoid several common failure modes:

### A. Fake model outputs
The app does not pretend a trained model exists when no valid training data exists.

### B. Synthetic data contamination
Test and synthetic records are filtered out so that only trusted real data can affect the model.

### C. One-class training acceptance
A one-class dataset is rejected because it cannot produce a meaningful binary classifier.

### D. Improper confidence values
Scores are bounded so they never exceed 1.0 or become negative.

### E. Fabricated delay-day predictions
The system does not invent delay days unless a real regression target is available and valid.

### F. Stale artifact reuse
The system invalidates stale artifacts and requires the active model metadata to be verified before serving predictions.

---

## 19. Why the Project Was Hardened This Way

This was not simply a UI improvement exercise. The real goal was to make the application honest and production-safe.

A project like Geomatrix must not show confident predictions unless there is a real basis for them. If the dataset is too small, one-class, synthetic, or stale, the correct action is to show a model-not-trained state instead of making up a risk value.

This is what makes the system credible for real operational use.

---

## 20. Final Assessment

The current architecture is carefully split across:
- UI rendering
- API access layer
- database persistence
- ingestion validation
- ML training
- model artifact management
- AI explanation layer
- test and safety validation

The strongest technical takeaway is the emphasis on real-data integrity. In this project, the model is a trusted decision tool only when based on valid real-labeled historical data; otherwise the application refuses to pretend it is available.

This is the correct engineering posture for a production-grade risk intelligence system.
