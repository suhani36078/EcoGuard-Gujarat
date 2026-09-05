# AI-Powered Industrial Pollution Intelligence & Response Platform
### Gujarat Hackathon 2026 — Challenge 9

> Real-time AI-driven pollution monitoring, anomaly detection, forecasting, community risk assessment, and regulatory compliance for Gujarat's industrial zones — powered by IBM Granite 4.

---

## 🚀 Quick Start

### Option 1 — Local Development (Recommended)

#### Backend (Python 3.10+)
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # edit with your watsonx credentials
python start.py --seed        # seeds 7 demo factories + 35,000+ sensor readings
```
API available at **http://localhost:8000** | Swagger docs: **http://localhost:8000/docs**

#### Frontend (Node.js 18+)
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev                   # dev server at http://localhost:3000
```

### Option 2 — Docker Compose
```bash
cp backend/.env.example .env  # add watsonx credentials
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Option 3 — One-Shot Setup Scripts
```bash
# Linux / macOS
chmod +x scripts/setup.sh && ./scripts/setup.sh

# Windows PowerShell
.\scripts\setup.ps1
```

---

## 🔐 Demo Credentials

| Username   | Password      | Role       | Access                        |
|------------|---------------|------------|-------------------------------|
| admin      | admin123      | admin      | Full platform access          |
| regulator  | regulator123  | regulator  | Read + compliance actions     |
| officer    | officer123    | officer    | Operational actions           |
| viewer     | viewer123     | viewer     | Read-only                     |

---

## 🏭 Demo Scenarios (7 Factories)

| Factory | Location    | Type             | Scenario                                      |
|---------|-------------|------------------|-----------------------------------------------|
| F001    | Vapi        | Chemical         | Normal baseline operations                    |
| F002    | Ankleshwar  | Textile Dye      | Moderate pollution (approaching limits)       |
| F003    | Vatva       | Pharmaceutical   | Repeated violation cycles                     |
| F004    | Vapi        | Petrochemical    | SO₂ spike: 50→55→60→75→95→120→150 µg/m³     |
| F005    | Ankleshwar  | Effluent Treatment | Effluent: high pH (9.8) + turbidity 55 NTU  |
| F006    | Vapi        | Mixed Industry   | Community risk: wind toward residential       |
| F007    | Vatva       | Chemical         | Predicted future violation (rising trend)     |

---

## 🤖 Multi-Agent Pipeline Architecture

`POST /api/agents/process` triggers a 9-step pipeline:

```
Sensor Reading
     │
     ▼
┌──────────────────────┐
│  1. MonitoringAgent  │  Threshold check → NORMAL / WARNING / CRITICAL
└──────────┬───────────┘
           │ (WARNING/CRITICAL only)
     ┌─────▼──────────────────────────────────────────────────────────┐
     │  2. AnomalyAgent       Z-score + Isolation Forest (0–100)      │
     │  3. ComplianceAgent    Exceedance % + severity classification   │
     │  4. ForecastingAgent   Linear regression 1h/2h/4h prediction   │
     │  5. EffluentAgent      Water quality analysis (pH/turbidity)   │
     │  6. FactoryRiskAgent   Composite risk score 0–100              │
     │  7. CommunityHealthAgent  Population exposure assessment       │
     │  8. InvestigationAgent Root cause + pattern analysis           │
     │  9. AlertAgent         Dedup + routing + escalation            │
     └──────────────────────────────────────────────────────────────┘
           │
     ▼
SupervisorAgent: Combined alert_level (LOW/MEDIUM/HIGH/CRITICAL)
     +
IBM Granite 4: AI narrative in combined_assessment
```

---

## 🌐 API Reference

| Method | Endpoint                          | Description                           |
|--------|-----------------------------------|---------------------------------------|
| POST   | /api/auth/login                   | Authenticate → JWT token              |
| POST   | /api/auth/register                | Register new user                     |
| GET    | /api/factories                    | List all factories                    |
| GET    | /api/factories/{id}               | Factory details                       |
| GET    | /api/readings/{factory_id}        | Sensor readings (paginated)           |
| GET    | /api/violations                   | All violations                        |
| GET    | /api/violations/{factory_id}      | Factory-specific violations           |
| GET    | /api/anomalies                    | All detected anomalies                |
| GET    | /api/alerts                       | All alerts                            |
| POST   | /api/alerts/{id}/acknowledge      | Acknowledge an alert                  |
| GET    | /api/incidents                    | All incidents                         |
| POST   | /api/incidents/{id}/action        | Take action (resolve/escalate/assign) |
| GET    | /api/forecasts/{factory_id}       | 24h ML-based forecasts                |
| GET    | /api/risk-scores                  | All factory risk scores               |
| GET    | /api/risk-scores/{factory_id}     | Factory risk score + breakdown        |
| GET    | /api/community-risk               | Community exposure risk               |
| GET    | /api/dashboard/summary            | Platform-wide KPI summary             |
| POST   | /api/agents/process               | Run the full multi-agent pipeline     |

---

## 📊 Pollution Limits

| Parameter      | Limit       | Unit    |
|----------------|-------------|---------|
| PM₂.₅          | 60          | µg/m³   |
| PM₁₀           | 100         | µg/m³   |
| SO₂            | 80          | µg/m³   |
| NO₂            | 80          | µg/m³   |
| CO             | 10          | mg/m³   |
| pH             | 6.5 – 8.5   | pH      |
| Turbidity      | 10          | NTU     |
| Chemical Level | 50          | mg/L    |

---

## 🖥️ Frontend Pages

| Route         | Page              | Description                                      |
|---------------|-------------------|--------------------------------------------------|
| `/`           | Dashboard         | Platform KPIs, violation charts, live alerts     |
| `/factories`  | Factories         | Factory list + sensor reading time-series        |
| `/violations` | Violations        | Filterable violation table with severity badges  |
| `/alerts`     | Alerts            | Pending/acknowledged alerts + acknowledge action |
| `/anomalies`  | Anomalies         | Anomaly scores with statistical context          |
| `/incidents`  | Incidents         | Incident management with action modal            |
| `/forecasts`  | Forecasts         | 24h ML forecast chart + confidence bars          |
| `/risk`       | Risk Scores       | Factory risk breakdown + bar chart               |
| `/community`  | Community Risk    | Population exposure cards with advisories        |
| `/agents`     | Agent Pipeline    | Interactive pipeline trigger + result viewer     |

---

## 🧪 Tests

```bash
# Run all 39 backend tests
python -m pytest tests/ -v

# TypeScript check
cd frontend && npx tsc --noEmit
```

**Test coverage:**
- Auth (login, register, JWT validation)
- REST API endpoints (factories, violations, anomalies, alerts, dashboard)
- Multi-agent pipeline (normal + critical scenarios)
- Agent unit tests (MonitoringAgent, AnomalyAgent, ComplianceAgent, ForecastingAgent, SupervisorAgent)
- Auth service (bcrypt hashing, token encoding/decoding)
- Granite service fallback behavior

---

## 🏗️ Project Structure

```
pollution-platform/
├── backend/
│   ├── main.py                   FastAPI entry point
│   ├── start.py                  Startup + seeding script
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── api/                      12 route handlers
│   │   ├── auth.py               JWT auth + registration
│   │   ├── factories.py          Factory CRUD
│   │   ├── readings.py           Sensor reading queries
│   │   ├── violations.py         Violation management
│   │   ├── anomalies.py          Anomaly records
│   │   ├── alerts.py             Alert management + acknowledge
│   │   ├── incidents.py          Incident lifecycle
│   │   ├── forecasts.py          24h forecasts
│   │   ├── risk_scores.py        Risk score queries
│   │   ├── community_risk.py     Community exposure API
│   │   ├── dashboard.py          KPI summary
│   │   └── agents.py             Agent pipeline trigger
│   ├── models/
│   │   ├── database.py           SQLAlchemy ORM (10 models)
│   │   └── schemas.py            Pydantic v2 schemas
│   ├── services/
│   │   ├── agent_service.py      Pipeline orchestration
│   │   ├── auth_service.py       JWT + bcrypt
│   │   ├── data_service.py       Query helpers
│   │   └── granite_service.py    IBM Granite integration
│   └── database/
│       ├── init_db.py            Table creation
│       └── seed_data.py          Synthetic data (7 factories × 504 readings)
├── agents/
│   ├── monitoring/agent.py       Threshold monitoring
│   ├── anomaly/agent.py          Z-score + Isolation Forest
│   ├── compliance/agent.py       Violation detection
│   ├── forecasting/agent.py      Linear regression forecasts
│   ├── effluent/agent.py         Water quality analysis
│   ├── risk/agent.py             Factory risk scoring
│   ├── health/agent.py           Community health risk
│   ├── investigation/agent.py    Root cause analysis
│   ├── alerts/alert_agent.py     Alert generation + dedup
│   └── supervisor/agent.py       Pipeline orchestrator
├── frontend/
│   ├── src/
│   │   ├── App.tsx               Root component + routing
│   │   ├── index.css             Dark theme design system
│   │   ├── components/
│   │   │   ├── Sidebar.tsx       Navigation
│   │   │   ├── Topbar.tsx        Header
│   │   │   ├── KpiCards.tsx      Dashboard KPI grid
│   │   │   └── Charts.tsx        Recharts visualizations
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── FactoriesPage.tsx
│   │   │   ├── ViolationsPage.tsx
│   │   │   ├── AlertsPage.tsx
│   │   │   ├── AnomaliesPage.tsx
│   │   │   ├── IncidentsPage.tsx
│   │   │   ├── ForecastsPage.tsx
│   │   │   ├── RiskPage.tsx
│   │   │   ├── CommunityRiskPage.tsx
│   │   │   ├── AgentsPage.tsx
│   │   │   └── LoginPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts            Axios instance + auth
│   │   │   ├── queries.ts        API query functions
│   │   │   └── types.ts          TypeScript interfaces
│   │   └── utils/helpers.ts      Formatting + badge utilities
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
├── ml/
│   ├── preprocessing/preprocessor.py  Data preprocessing pipeline
│   └── training/train_models.py       Model training scripts
├── tests/
│   └── test_platform.py              39-test backend test suite
├── scripts/
│   ├── setup.sh                      Linux/macOS setup
│   ├── setup.ps1                     Windows setup
│   └── run_tests.sh                  Test runner
├── docker-compose.yml
├── pytest.ini
└── README.md
```

---

## 🌐 IBM Granite Integration

The platform uses **IBM Granite 4-h-small** via the `ibm-watsonx-ai` SDK for:

- **Incident explanations** — plain-language summaries for regulatory officers
- **Factory risk narratives** — grounded risk analysis with contributing factors
- **Community risk advisories** — environmental exposure communication
- **Alert messages** — concise operational alerts with parameter details
- **Violation explanations** — regulatory impact summaries
- **Executive summaries** — platform-wide AI digest

Configure via environment variables:
```
WATSONX_API_KEY=your-key
WATSONX_AI_URL=https://api.au-syd.watson-orchestrate.cloud.ibm.com/instances/...
GRANITE_MODEL_ID=ibm/granite-4-h-small
```

All Granite calls include **fallback responses** — the platform functions fully when AI is unavailable.

---

## 🔒 Security

- JWT authentication on all API endpoints
- bcrypt password hashing
- CORS restricted to configured origins
- Credentials via environment variables only — never hardcoded
- Role-based access (admin / regulator / officer / viewer)

---

## 📄 License

Gujarat Hackathon 2026 — Demonstration Platform
