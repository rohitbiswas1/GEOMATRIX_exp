# GOVERNMENT HANDOVER

## Model acceptance

A production model requires an approved historical dataset with documented provenance, both delay classes, documented label definition, documented feature dictionary, reproducible training, hold-out evaluation, stratified cross-validation, dataset fingerprint, review of feature importance and SHAP behavior, and an explicit decision on regression-target completeness.

The UI must display stored validation metrics only. Placeholder precision, recall, F1, ROC-AUC, calibration, feature importance and portfolio totals are not acceptable for production use.

Risk score is derived from delayed-class probability. Confidence is the classifier's probability certainty for the current record and is distinct from validation metrics. Predicted delay days are available only when an approved regression model has a complete actual_delay_days target.

## Security

Production requires signed HTTP-only sessions, an external identity provider, server-side secrets, HTTPS, restrictive host/origin configuration, audit logs, least-privilege database credentials, and backups. The FastAPI service also verifies the signed session token when APP_ENV=production.

## Data provenance

Production records should preserve source name, source URL, stable source record identifier, import timestamp, validation status, and data classification. Unverified uploads stay outside the REAL training pool.

## Audit

The audit_logs table records project create, update, delete and risk-prediction events with request IDs. The audit API is read-only. Audit records should not contain personal information unless required by an approved retention policy.

## Deployment

Vercel Services provides the Next.js frontend and FastAPI backend in one project, with FastAPI behind the /backend path. Use /backend/health and /backend/health/ready as operational checks.

Production runtime ML training remains disabled unless explicitly enabled for a controlled maintenance window. Model artifacts must carry their dataset fingerprint, validation record, and rollback plan.

## Current limitation

The repository contains the production-grade code path but does not claim that a production model is currently validated. An approved model must be trained from the receiving department's accepted dataset before operational use.
