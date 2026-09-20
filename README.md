# GEOMATRIX

GEOMATRIX is a land-acquisition risk intelligence and decision-support application for infrastructure project monitoring.

## Architecture

- Next.js frontend
- FastAPI + SQLAlchemy backend
- PostgreSQL for production persistence
- Scikit-learn Random Forest / XGBoost classification
- Optional delay-days regression only when a complete approved target is available
- SHAP explainability
- Google Identity Services authentication
- Signed session cookies
- Audit logging
- GIS project mapping
- CSV/JSON controlled ingestion
- Vercel Services for one-domain frontend + FastAPI deployment

## Data and ML governance

The application does not create historical labels, project precedents, risk scores or delay forecasts for records that have not been supported by approved source data.

Historical records enter the training pool only when data_classification=REAL, validation_status is validated or approved, both delay classes are present, the minimum sample threshold is met, and the feature set is usable. Missing source values in training are handled by the recorded median-imputation pipeline and never by fixed business defaults.

Model metadata records the source dataset fingerprint, feature schema, validation metrics, cross-validation metrics and whether a regression target was actually available.

Production runtime training is disabled by default. Use scripts/train_approved_model.py on an approved dataset, review the metadata, then package the approved artifact for deployment.

## Local development

Create a Python 3.12 environment, install the Python and Node dependencies, configure .env, then run:

    uvicorn geomatrix_v2.main:app --reload --port 8000
    npm install
    npm run dev

The frontend uses /backend/... for the FastAPI service. In local Vercel development, use vercel dev after configuring Vercel Services.

## Production environment

Required: DATABASE_URL, AUTH_SECRET or NEXTAUTH_SECRET, NEXT_PUBLIC_GOOGLE_CLIENT_ID, APP_ENV=production, CORS_ALLOWED_ORIGINS, and ALLOWED_HOSTS.

Optional: GEMINI_API_KEY, DATAGOVIN_API_KEY plus verified resource IDs, NEXT_PUBLIC_GOOGLE_MAPS_API_KEY, and ADMIN_API_TOKEN.

Do not commit .env, credentials, API keys, government data containing personal information, or sensitive model metadata.

## Vercel

The repository is configured as two Vercel Services in one project: frontend root ./ and backend root geomatrix_v2 with entrypoint vercel_app:app. FastAPI is exposed under /backend/* through the same domain.

The current codebase intentionally contains no active trained model artifact until an approved model is produced. Prediction endpoints therefore return an explicit no-validated-model state rather than fabricating a score.

## Government handover

Before operational use, the receiving department should complete source authorization and retention rules, a source-to-field data dictionary, PII handling and access control, model acceptance criteria, approved model registration, database backup and migration procedures, incident and rollback procedures, security assessment, and legal review of AI-assisted decision support.

GEOMATRIX is a decision-support system. Final administrative, legal and acquisition decisions remain with authorized government personnel.
