# GEOMATRIX — Land Acquisition AI

> **Predictive Intelligence for Smarter Infrastructure**  
> **Smart India Hackathon 2026 · Problem Statement 26017 · Smart Automation**

Geomatrix is an AI-powered decision-support prototype for the **early detection of land-acquisition delays**. Instead of only monitoring delays after they happen, Geomatrix is designed to identify risk early, explain the reasons behind that risk, prioritize projects, and recommend corrective action.

### Core workflow

**PREDICT → EXPLAIN → PRIORITIZE → ACT**

---

## 🎯 Problem

Land acquisition projects can be delayed because of:

- Pending approvals
- Compensation issues
- Legal disputes
- Incomplete documentation
- Rehabilitation and resettlement challenges

Authorities need more than a status dashboard: they need to know **which project is likely to face problems, why, which project needs attention first, and what action can be taken.**

## 💡 Our Solution

Geomatrix brings these capabilities into one platform:

| Capability | What Geomatrix does |
|---|---|
| **Predict** | Generates a project delay-risk score and category |
| **Explain** | Shows the major factors contributing to the risk |
| **Prioritize** | Highlights critical/high-risk projects for intervention |
| **Act** | Provides action-oriented recommendations |
| **GIS** | Shows project risk geographically on an interactive map |
| **Alerts** | Surfaces projects requiring attention |
| **Analytics** | Provides portfolio-level risk insights |
| **Reports** | Supports administrative and policy decisions |

---

## 🧠 AI / ML Architecture

```text
Land / Project Data
        ↓
Feature Engineering
        ↓
Prediction Engine
        ↓
Risk Score + Risk Category
        ↓
Explainable AI (SHAP)
        ↓
Key Risk Factors
        ↓
Recommendation Engine
        ↓
Prioritization + Corrective Action
        ↓
Dashboard + GIS + Alerts + Reports
```

### Production ML direction

The production architecture is designed to support:

- Python
- pandas / NumPy
- scikit-learn
- XGBoost or Random Forest
- SHAP for Explainable AI
- GeoPandas / Shapely for spatial processing where required

### ⚠️ Prototype transparency

The current SIH prototype uses **deterministic synthetic/demo data and a mock risk/explanation engine** to demonstrate the complete product workflow. It is **not claimed to be trained on real government data**.

For production, the system can be trained and validated using authorized historical land-acquisition data and known project outcomes, subject to government data access, security, governance, and domain validation.

---

## 🗺️ GIS Risk Intelligence

The GIS Risk Map displays project locations using risk-based markers:

- 🔴 Critical
- 🟠 High risk
- 🟡 Medium risk
- 🟢 Low risk

### Google Maps

The current application uses the **Google Maps JavaScript API** when this environment variable is configured:

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_browser_key
```


**Security:** Never commit API keys to GitHub. Configure them through Vercel/environment variables and restrict the Google Maps browser key to authorized HTTP referrers and required APIs in Google Cloud.

---

## 🏗️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| UI | Tailwind-style UI, reusable components, Lucide |
| Charts | Recharts |
| Backend | Next.js API routes; FastAPI production option |
| Database | PostgreSQL + PostGIS + Prisma |
| GIS | Google Maps JavaScript API |
| ML | XGBoost / Random Forest, pandas, NumPy, scikit-learn |
| Explainability | SHAP |
| Deployment | Vercel |

---

## 📁 Application Modules

- `/login` — Prototype role-based login
- `/dashboard` — Executive risk overview
- `/projects` — Project portfolio
- `/projects/[id]` — Project-level intelligence
- `/map` — GIS risk intelligence
- `/alerts` — Risk and intervention alerts
- `/analytics` — Risk analytics and trends
- `/reports` — Reports and decision support
- `/data` — Data management view
- `/settings` — Application settings
- `/admin/model` — Model administration/prototype view

---

## 🔐 Demo Accounts

For prototype demonstration only:

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@geomatrix.gov.in` | `Admin@123` |
| Project Officer | `officer@geomatrix.gov.in` | `Officer@123` |
| Policy Maker | `policymaker@geomatrix.gov.in` | `Policy@123` |

> These are demo credentials, not production authentication. A production system should use secure identity, role-based authorization, session management, audit controls, and managed secrets.

---

## ⚙️ Run Locally

### 1. Clone

```bash
git clone https://github.com/rohitbiswas1/geomatrix.git
cd geomatrix
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment

Create `.env.local`:

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_browser_key
DATABASE_URL=your_database_url
NEXTAUTH_SECRET=your_auth_secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
MODEL_API_URL=
```

### 4. Start development server

```bash
npm run dev
```

Open `http://localhost:3000/login`.

---

## ☁️ Deploy on Vercel

1. Import the GitHub repository into Vercel.
2. Add environment variables under **Project → Settings → Environment Variables**.
3. For Google Maps, add `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`.
4. Configure the Google key with HTTP-referrer restrictions and only the APIs required by the application.
5. Select the required deployment environments, especially **Production**.
6. Trigger a new deployment after changing `NEXT_PUBLIC_*` values because they are included in the Next.js client build.
7. Open `/map` and verify the **Google Maps GIS** indicator and project markers.

---

## 🔄 How the Demo Works

1. A user logs into the platform according to their role.
2. The dashboard summarizes project risk.
3. A project can be inspected for its risk score and contributing factors.
4. The explanation layer identifies the main drivers.
5. Recommendations suggest possible corrective actions.
6. Alerts and prioritization highlight projects requiring intervention.
7. GIS shows where the projects are located and their risk level.
8. Analytics and reports provide higher-level decision support.

---

## 🛣️ Production Roadmap

### Phase 1 — Data readiness
- Integrate authorized historical land-acquisition records.
- Standardize project, parcel, approval, compensation, legal, rehabilitation, and document features.
- Establish data-quality and governance rules.

### Phase 2 — ML validation
- Train candidate models such as XGBoost and Random Forest.
- Evaluate precision/recall, calibration, false positives/negatives, and stage-wise performance.
- Validate explanations with domain experts.

### Phase 3 — Government integration
- Connect approved government data sources.
- Add secure authentication, role-based access, and audit trails.
- Add production GIS layers and spatial analytics.

### Phase 4 — Continuous intelligence
- Monitor model performance and drift.
- Capture intervention outcomes as feedback.
- Retrain and validate models under controlled governance.

---

## 🌟 What Makes Geomatrix Different?

Traditional monitoring asks:

> **“What is happening now?”**

Geomatrix is designed to answer four questions:

1. **What is likely to happen?**
2. **Why is it likely to happen?**
3. **Which project needs attention first?**
4. **What action should be taken?**

That is the core value of **PREDICT → EXPLAIN → PRIORITIZE → ACT**.

---

## 📚 Reference Basis

The solution concept is informed by the SIH problem statement and reference areas including:

- Digital India Land Records Modernization Programme (DILRMP)
- DILRMP 3.0 Operational Guidelines 2026–2031
- PRS material on land records and titles
- MoRTH BhoomiRashi
- XGBoost — Chen & Guestrin
- SHAP / Explainable AI — Lundberg & Lee

These references provide conceptual and technical grounding. The prototype does not claim access to restricted government datasets.

---

## ⚠️ Disclaimer

Geomatrix is an **SIH 2026 decision-support prototype**. Demonstration risk scores and recommendations are not official government decisions, legal determinations, compensation decisions, or guaranteed forecasts.

Production use requires authorized data, domain validation, secure infrastructure, model validation, human oversight, and appropriate government governance.

---

## 👨‍💻 Project

**Geomatrix — Land Acquisition AI**  
**Smart India Hackathon 2026**  
**Problem Statement 26017: Predictive Analytics System for Early Detection of Land Acquisition Delays**

## ⭐ Vision

> **Prevent land-acquisition delays before they become critical.**
