# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TravelDesigner evaluation platform — compares three AI travel planning models (GPT-4, self-developed ItineraryAgent, TravelPlanner baseline) side-by-side. Users submit trip queries, the system runs all three models in parallel, displays results, and collects multi-dimensional ratings (detail, route rationality, representativeness, overall). Data is stored in MySQL for analysis.

## Commands

### Frontend (from `front_end/`)
```bash
npm install          # install dependencies
npm run dev          # dev server at http://localhost:5173
npm run build        # production build
npm run lint         # ESLint
```

### Backend (from `back_end/`)
```bash
python backend.py                    # dev server at http://localhost:5000
./restart.sh                         # production: runs migrations + gunicorn (4 workers, port 5000)
export FLASK_APP=backend.py && flask db upgrade   # apply database migrations
```

### Full Stack
```bash
./start.sh           # starts both frontend and backend
uv sync              # install Python dependencies (uses uv, not pip)
```

## Architecture

**Frontend:** React 18 + Vite 5, NextUI component library, TailwindCSS, react-router-dom.

**Backend:** Flask, single-file app (`back_end/backend.py`), Flask-SQLAlchemy with MySQL (`modeltest` database), Flask-Migrate for schema management.

**AI Models (run in parallel via ThreadPoolExecutor):**
- Plan 1 (GPT-4): Direct OpenAI API call
- Plan 2 (ItineraryAgent): Self-developed agent in `ItineraryAgent-master/`, uses LangChain + Google Maps + Amadeus APIs
- Plan 3 (TravelPlanner): Baseline model in `TravelPlanner-master/`, invoked as subprocess with conda environment

**Async task system:** Long-running model calls use a polling pattern — `POST /submit_task` returns a `task_id`, frontend polls `GET /task_status/<task_id>`. Tasks are stored in-memory dict with thread locks, auto-cleaned after 1 hour.

**Config:** `config.yaml` (copied from `config.yaml.example`) sets frontend/backend hosts. Environment variables loaded from `.env` in project root.

## Key Files

- `back_end/backend.py` — all Flask routes and the `ModelEstimate` ORM model (monolithic)
- `front_end/src/Page/HomePage.jsx` — main UI: query input, parallel model display, rating forms
- `front_end/src/ApiUtill.js` — API base URL configuration (reads from config.yaml)
- `utils/chat_model.py` — shared LLM wrapper used by backend and agents
- `ItineraryAgent-master/planner_checker_system.py` — ItineraryAgent entry point
- `TravelPlanner-master/` — invoked as a separate process under its own conda env

## Environment Variables (.env)

Required: `OPENAI_API_KEY`, `DB_PASSWORD`
Optional: `OPENAI_API_BASE`, `GOOGLE_API_KEY`, `SERPER_API_KEY`, `LANGFUSE_SECRET_KEY`, `DEBUG`

DB defaults: user `modeltest` (Unix) / `root` (Windows), database `modeltest`, host `localhost`.

## Constraints

- Query validation enforces: travel dates within 0–60 days from now, max 20-day trip duration
- Model inference can take several minutes; production uses 1500s gunicorn timeout
- TravelPlanner model runs in a separate conda environment (`CONDA_DEFAULT_ENV`, default `estimate_web`)
- Python 3.12 (`.python-version`), Node 16+
