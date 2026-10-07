# Industrial AI Lead Intelligence

A full-stack lead scoring application. Upload a CSV of
leads, get each one scored 0–100 by an XGBoost model with a plain-
English explanation of *why* it scored that way, then search, filter,
and export the results from a dashboard.

**Stack:** React + Tailwind (frontend) · FastAPI (backend) · PostgreSQL
(storage) · XGBoost + SHAP (scoring + explainability)

This is intentionally an MVP: no auth, no payments, no Docker/K8s, no
message queues. The architecture is laid out so those can be added
later without a rewrite — see [Extending this project](#extending-this-project).

---

## What it does

1. **Upload** a CSV of leads (drag-and-drop or file picker).
2. **Column detection** automatically maps common column names
   ("Company", "Account Name", "Employees", "Deal Size", etc.) onto a
   canonical schema — see `backend/app/services/data_cleaning.py`.
3. **Cleaning** coerces messy numeric fields (`"$1,200,000"`, `"15%"`),
   drops exact duplicate rows, and drops rows with no usable signal.
   Any column that isn't recognized is preserved per-row as
   `extra_fields` rather than silently discarded.
4. **Scoring**: an XGBoost classifier predicts a conversion
   probability, scaled to a 0–100 "lead score," bucketed into
   Hot (≥70) / Warm (≥40) / Cold (<40).
5. **Explainability**: SHAP's `TreeExplainer` computes each feature's
   exact contribution to a lead's score; the top 3 are turned into
   human-readable sentences ("Engagement score of 85 increased the
   score.").
6. **Dashboard**: searchable/sortable/filterable table, a stats strip,
   a per-lead detail panel with a score gauge and full explanation,
   and CSV export of the current filtered view.

### Important: the model is trained on synthetic data

There's no proprietary CRM history to train on for a portfolio
project, so `backend/app/ml/train.py` generates a synthetic dataset
from an explicit, documented rule (bigger budget, more engagement,
more recent contact, larger company → higher conversion probability +
noise), then trains an XGBoost classifier on it. This is disclosed in
the UI footer and in this README rather than presented as if it were
trained on real outcomes. A real deployment would swap this training
script for one that reads historical CRM data (closed-won vs.
closed-lost leads) — the rest of the pipeline (feature prep, scoring,
SHAP explanations, API, dashboard) would not need to change.

---

## Project structure

```
lead-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app setup, CORS, router registration
│   │   ├── config.py            # env-based settings (DB url, CORS, upload limits)
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── models.py            # ORM models: UploadBatch, Lead
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── upload.py        # POST /api/upload
│   │   │   └── leads.py         # GET /api/leads, /api/batches, CSV export
│   │   ├── services/
│   │   │   └── data_cleaning.py # column detection + cleaning
│   │   └── ml/
│   │       ├── features.py      # shared feature list/defaults/labels
│   │       ├── train.py         # synthetic data + XGBoost training script
│   │       ├── scorer.py        # inference + SHAP explanations
│   │       └── artifacts/       # trained model (lead_scorer.json)
│   ├── tests/test_pipeline.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api/client.js        # fetch wrapper for the backend API
    │   └── components/          # UploadZone, LeadTable, ScoreDial, etc.
    └── vite.config.js           # dev proxy: /api -> localhost:8000
```

---

## Running it locally

### 1. Database

You need a PostgreSQL instance. Quickest options:

```bash
# Local Postgres (adjust to your setup)
createdb lead_intelligence
```

Or, for zero-setup local testing, SQLite works too since the app only
uses SQLAlchemy's ORM (no Postgres-specific SQL) — just point
`DATABASE_URL` at a SQLite file (see `.env.example`).

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL to your Postgres connection string

python -m app.ml.train        # trains the model, writes app/ml/artifacts/lead_scorer.json
uvicorn app.main:app --reload --port 800
```

The API is now at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*`
requests to `localhost:8000`, so no CORS configuration is needed
locally.

### 4. Try it

Upload any CSV with lead-like columns. If you don't have one handy,
here's a minimal example:

```csv
Company Name,Contact Name,Email,Industry,Employees,Annual Revenue,Engagement Score,Emails Opened,Website Visits,Days Since Last Contact,Deal Size
Acme Corp,Jane Doe,jane@acme.com,SaaS,120,5000000,85,12,20,2,45000
Globex Inc,John Smith,john@globex.com,Manufacturing,15,800000,20,1,1,90,3000
```

### Running tests

```bash
cd backend
pytest
```

---

## Extending this project

The codebase is structured so the following are additive, not
rewrites:

- **Authentication**: add a `users` table + JWT/session middleware in
  FastAPI, then scope `UploadBatch`/`Lead` queries by `user_id`. The
  router functions already take `db: Session = Depends(get_db)`, so
  adding `current_user: User = Depends(get_current_user)` is a small
  diff, not a redesign.
- **Background job processing** (for large CSVs): the upload endpoint
  currently scores synchronously. Swapping to a task queue (Celery,
  RQ, or FastAPI `BackgroundTasks` first) only touches
  `routers/upload.py` — `services/data_cleaning.py` and `ml/scorer.py`
  are already pure functions with no request/response coupling.
- **Real training data**: replace `ml/train.py`'s synthetic generator
  with a loader for historical CRM exports; `ml/features.py` and
  `ml/scorer.py` don't need to change as long as the same feature
  columns are used.
- **Database migrations**: swap `Base.metadata.create_all()` in
  `main.py` for Alembic once the schema needs to evolve safely in
  production.
- **Containerization**: each service (`backend/`, `frontend/`) is
  already isolated with its own dependency manifest, so adding
  Dockerfiles later is mechanical.

---

## Design notes

The UI uses a "technical drawing / blueprint" visual language (grid
background, corner-bracketed panels, an analog gauge for the lead
score, monospaced data) to match the "industrial AI" framing rather
than a generic SaaS dashboard look.
