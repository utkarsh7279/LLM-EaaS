# Operations Runbook

## Purpose
This runbook is for day-of-deployment execution and post-deploy validation of the LLM Evaluation-as-a-Service project.

## 1. Pre-Deployment Checklist

### Application
- Backend tests pass:
  - `cd backend && /Users/utkarshraj/LLM EaaS/.venv/bin/python -m pytest -q`
- API health endpoint available in app startup (`GET /health`).
- Logging setup is safe for repeated initialization (no duplicate handlers).

### Configuration
- Backend env file exists: `backend/.env`
- Required env vars:
  - `LLM_EAAS_DATABASE_URL`
  - `LLM_EAAS_LLM_PROVIDER` (`ollama` or `openai`)
  - `LLM_EAAS_LLM_API_KEY` (required for OpenAI)
- Frontend env file exists: `frontend/.env.local`
- Frontend base URL is correct:
  - `NEXT_PUBLIC_API_BASE_URL`

### Infrastructure
- Compose config validates:
  - `docker compose config`
- Postgres service has a healthcheck (`pg_isready`).

## 2. Deployment Commands

### Option A: Docker Compose
1. Start services:
   - `docker compose up -d`
2. Confirm service status:
   - `docker compose ps`
3. Follow logs:
   - `docker compose logs -f`

### Option B: Backend and Frontend separately
1. Backend:
   - `cd backend`
   - `source venv/bin/activate`
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## 3. Post-Deployment Smoke Tests

### Core Health
- `curl -sSf http://localhost:8000/health`
- Expected response: `{"status":"ok"}`

### API Route Smoke
- Upload sample dataset:
  - `curl -X POST -F "file=@sample_data.csv" http://localhost:8000/experiments/upload`
- Run an evaluation on returned experiment ID using your rubric.

### Logging Smoke
- Confirm startup and request logs are emitted once per event.
- If duplicate logs appear, inspect logger initialization path usage.

## 4. Monitoring and Alert Focus
- API uptime and non-200 rate on `/health` and experiment endpoints.
- Evaluation latency trends (watch for spikes in LLM call durations).
- DB connectivity errors and connection pool saturation.
- Safety fail-rate anomalies in experiment metrics.

## 5. Rollback Plan
1. Roll back to previous image/tag or previous deployment version.
2. Verify database schema compatibility before rollback.
3. Re-run smoke tests on rolled-back version.
4. Keep incident notes:
   - failure timestamp
   - impacted endpoint
   - rollback duration
   - root-cause hypothesis

## 6. Known Good Validation Snapshot
- Backend tests: passing (4 tests).
- API startup smoke: passed.
- `/health` endpoint: returns 200.
- Compose config: valid and warning-free for current file layout.

## 7. Quick Incident Triage Commands
- Running containers: `docker compose ps`
- Recent container logs: `docker compose logs --tail=200`
- Backend direct health probe: `curl -i http://localhost:8000/health`
- Validate backend imports and diagnostics in editor: Problems panel / workspace diagnostics.

## 8. Ownership Notes
- Business logic lives primarily under `backend/app/services`.
- API routes live under `backend/app/routers`.
- Runtime settings are defined in `backend/app/core/config.py`.
