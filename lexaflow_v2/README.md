# LexaFlow AI v2

Fresh rebuild of the LexaFlow demo as a two-tier app:
- `FastAPI` backend for regulatory monitoring, versioning, analysis, actions, and source updates
- `Streamlit` frontend for the command-center workflow

## Project Structure

```text
lexaflow_v2/
  backend/app/
    api/routes/
    core/config.py
    db/
    services/
    crud.py
    schemas.py
    main.py
  frontend/app.py
  data/sample_docs/
  requirements.txt
  .env.example
```

## Features

- Document version monitoring (`rbi_v1.pdf` vs `rbi_v2.pdf`)
- Hash-based change detection
- Version timeline persisted in SQLite
- AI change analysis:
  - Azure OpenAI path (when credentials are present)
  - deterministic fallback analysis (when credentials are missing)
- Action creation, deduplication, status updates, due date updates
- Regulatory source fetch + fallback feed entries
- Dashboard KPIs and reset endpoint for demo reruns

## Run Locally (Windows PowerShell)

1. Open terminal in `lexaflow_v2`:

```powershell
cd "c:\Users\Rohini.Nagaraj\OneDrive - Wolters Kluwer\Desktop\lexaflow-ai - Copy\lexaflow_v2"
```

2. Create virtual environment and install packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Create environment file:

```powershell
Copy-Item .env.example .env
```

4. Start backend (terminal 1):

```powershell
uvicorn backend.app.main:app --reload
```

5. Start frontend (terminal 2):

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend\app.py
```

6. Open Streamlit URL shown in terminal (usually `http://localhost:8501`).

## API Endpoints

- `GET /health`
- `POST /api/v1/monitor/run`
- `GET /api/v1/actions?status=all|open|completed`
- `PATCH /api/v1/actions/{action_id}`
- `GET /api/v1/versions/{regulation_id}`
- `POST /api/v1/sources/fetch`
- `GET /api/v1/sources/recent`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/regulations/current`
- `POST /api/v1/admin/reset`

## Notes

- SQLite DB file is created at `data/lexaflow_v2.db`.
- If Azure credentials are absent, the app remains fully runnable with fallback logic.
- Sample docs are under `data/sample_docs`.

