# Geomatrix – Land Acquisition AI

> **Smart India Hackathon 2026 · Problem Statement 26017 · Smart Automation**

**Geomatrix** is a decision-support prototype for the early detection of land-acquisition delays. It combines predictive risk scoring, Explainable AI, prioritization, recommendations, and GIS intelligence in one workflow:

**PREDICT → EXPLAIN → PRIORITIZE → ACT**

Instead of waiting for a project to become delayed, Geomatrix is designed to identify potential risk early, explain the drivers behind that risk, and help authorities decide where intervention is needed first.

## 🎯 Problem

Land acquisition projects can be delayed by pending approvals, compensation issues, legal disputes, incomplete documentation, and rehabilitation challenges. Traditional monitoring shows current status; Geomatrix adds predictive and action-oriented intelligence.

## 💡 Core Capabilities

- **Predict** – Generate project delay-risk scores and categories.
- **Explain** – Show the major factors contributing to risk.
- **Prioritize** – Identify critical and high-risk projects needing attention first.
- **Act** – Provide action-oriented recommendations.
- **Visualize** – View project risk geographically through GIS.
- **Monitor** – Surface alerts, analytics, project status, and governance information.
- **Report** – Support decisions with project and risk reports.

## 🗺️ GIS Risk Map

The GIS page displays project locations using risk-based markers: Critical, High, Medium, and Low.

The current implementation uses **Google Maps JavaScript API** when `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is configured, with **OpenStreetMap** as a fallback for local/demo use.

> Never commit an API key to GitHub. Configure it through Vercel/environment variables and restrict it in Google Cloud to authorized websites and APIs.

## 🤖 AI / ML Architecture

```text
Project / Land Data
        ↓
Feature Engineering
        ↓
Prediction Service
        ↓
Risk Score + Category
        ↓
Explainability (SHAP)
        ↓
Risk Factors / Drivers
        ↓
Recommendation Service
        ↓
Prioritization + Corrective Actions
        ↓
Dashboard + GIS + Alerts + Reports
```

### Proposed production ML stack

Python, pandas, NumPy, scikit-learn, XGBoost or Random Forest, SHAP, GeoPandas, and Shapely.

### Prototype disclosure

The current SIH prototype uses **deterministic demonstration/mock prediction data** to demonstrate the complete workflow. It must not be represented as a model trained on real government data. Production can use authorized historical acquisition data and real project outcomes after appropriate validation and governance.

## 🏗️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| UI / Charts | Tailwind-style UI, Recharts, Lucide |
| Backend | Next.js API routes; FastAPI production option |
| Database | PostgreSQL + PostGIS + Prisma |
| GIS | Google Maps JavaScript API + OpenStreetMap fallback |
| ML | XGBoost / Random Forest, pandas, NumPy, scikit-learn |
| Explainability | SHAP |
| Deployment | Vercel |

## 📁 Main Routes

`/login` · `/dashboard` · `/projects` · `/projects/[id]` · `/map` · `/alerts` · `/analytics` · `/reports` · `/data` · `/settings` · `/admin/model`

## 🔐 Demo Accounts

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@geomatrix.gov.in` | `Admin@123` |
| Project Officer | `officer@geomatrix.gov.in` | `Officer@123` |
| Policy Maker | `policymaker@geomatrix.gov.in` | `Policy@123` |

> These credentials are for prototype demonstration only. Production should use secure managed authentication and authorization.

## ⚙️ Local Setup

```bash
git clone https://github.com/rohitbiswas1/geomatrix.git
cd geomatrix
npm install
```

Create `.env.local`:

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_browser_key
DATABASE_URL=your_database_url
NEXTAUTH_SECRET=your_auth_secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
MODEL_API_URL=
```

Then:

```bash
npm run dev
```

Open `http://localhost:3000`.

## ☁️ Vercel Deployment

1. Import the repository into Vercel.
2. Add `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` under Environment Variables.
3. Select the required environment(s), especially Production.
4. Configure the Google key with website HTTP-referrer restrictions and only the APIs required by the app.
5. Redeploy after changing `NEXT_PUBLIC_*` values because they are included in the client build.
6. Verify `/map` and confirm the **Google Maps GIS** indicator appears.

## 🧪 Prototype Status

The prototype demonstrates the complete product workflow: dashboard, projects, risk scoring, explanations, recommendations, prioritization, alerts, GIS visualization, analytics, reports, data/settings views, and core API routes.

It is intentionally transparent about prototype data. Real government data integration, trained/validated ML, secure authentication, production monitoring, and enterprise governance are production-roadmap items.

## 🛣️ Production Roadmap

**Phase 1 – Data:** integrate authorized historical acquisition records and standardize project, parcel, approval, compensation, legal, and document features.

**Phase 2 – ML:** train and compare candidate models, evaluate precision/recall and calibration, validate explanations, and monitor bias/drift.

**Phase 3 – Integration:** connect approved government systems, add secure identity/role controls, audit trails, and production GIS layers.

**Phase 4 – Continuous intelligence:** capture intervention outcomes, monitor model performance, and retrain under controlled governance.

## 🧭 What Makes Geomatrix Different?

Most monitoring systems answer **“What is happening now?”** Geomatrix is designed to answer:

1. **What is likely to happen?**
2. **Why is it likely to happen?**
3. **Which project needs attention first?**
4. **What action should be taken?**

That is the core workflow: **PREDICT → EXPLAIN → PRIORITIZE → ACT**.

## 📚 Reference Basis

The concept is informed by the SIH problem statement and reference areas including DILRMP, DILRMP 3.0 Operational Guidelines 2026–2031, PRS material on land records/titles, MoRTH BhoomiRashi, XGBoost, and SHAP/Explainable AI.

## ⚠️ Disclaimer

Geomatrix is a **decision-support prototype**. Demonstration risk scores and recommendations are not official government decisions, legal determinations, compensation decisions, or guaranteed forecasts. Production use requires authorized data, domain validation, security controls, model validation, human oversight, and appropriate governance.

## 👨‍💻 Project

**Geomatrix – Land Acquisition AI**  
**Smart India Hackathon 2026**  
**Problem Statement 26017 – Predictive Analytics System for Early Detection of Land Acquisition Delays**

Repository: https://github.com/rohitbiswas1/geomatrix

## ⭐ Vision

**Prevent land-acquisition delays before they become critical.**
