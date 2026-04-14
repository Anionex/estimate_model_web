# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TravelDesigner evaluation platform — compares three AI travel planning models (GPT-5, self-developed TravelDesigner, TravelPlanner baseline) side-by-side. Users submit trip queries, the system runs all three models in parallel, displays results, and collects multi-dimensional ratings (detail, route rationality, representativeness, overall). Data is stored in MySQL for analysis.

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
- Plan 1 (GPT-5): Direct OpenAI API call
- Plan 2 (TravelDesigner): PPTAgent-architecture agent in `TravelDesigner/`, uses OpenAI function calling + Google Maps + Amadeus APIs
- Plan 3 (TravelPlanner): Baseline model in `TravelPlanner-master/`, invoked as subprocess with conda environment

**TravelDesigner Agent Architecture (PPTAgent pattern):**
- `Agent` base class with `action()` / `execute()` / `loop()` pattern
- `AgentEnv` manages tool registration (auto JSON Schema from type hints) and dispatch
- `LLMClient` wraps OpenAI function calling API (non-streaming, structured `tool_calls`)
- YAML role configs in `TravelDesigner/roles/` define system prompts and toolset per agent
- `TravelAgent` gathers info via 6 tools (flights, hotels, attractions, restaurants, distance, web search)
- `CheckerAgent` wraps existing `PlanChecker` for iterative validation (budget, ratings, structure)
- `TravelOrchestrator` coordinates planner-checker loop (max 3 iterations)
- Entry point: `TravelDesigner/run.py`, invoked by backend as subprocess

**Legacy ItineraryAgent** (`ItineraryAgent-master/`): Old agent using custom ReACT text parsing. Replaced by TravelDesigner but kept for reference.

**Async task system:** Long-running model calls use a polling pattern — `POST /submit_task` returns a `task_id`, frontend polls `GET /task_status/<task_id>`. Tasks are stored in-memory dict with thread locks, auto-cleaned after 1 hour.

**Config:** `config.yaml` (copied from `config.yaml.example`) sets frontend/backend hosts. Environment variables loaded from `.env` in project root.

## Key Files

- `back_end/backend.py` — all Flask routes and the `ModelEstimate` ORM model (monolithic)
- `front_end/src/Page/HomePage.jsx` — main UI: query input, parallel model display, rating forms
- `front_end/src/ApiUtill.js` — API base URL configuration (reads from config.yaml)
- `utils/chat_model.py` — shared LLM wrapper used by backend and agents
- `utils/web_apis.py` — tool implementations: Google Maps, Amadeus, Serper APIs (with disk caching)
- `utils/plan_checker.py` — multi-step LLM plan validation (budget, reasonability, ratings, POI count)
- `TravelDesigner/` — PPTAgent-architecture travel agent (see below)
- `TravelDesigner/run.py` — TravelDesigner entry point (subprocess interface)
- `TravelDesigner/agent.py` — Agent base class (action/execute/loop)
- `TravelDesigner/agent_env.py` — AgentEnv: tool registration with auto JSON Schema
- `TravelDesigner/llm_client.py` — OpenAI function calling client
- `TravelDesigner/orchestrator.py` — planner-checker loop coordinator
- `TravelDesigner/tool_wrappers.py` — typed wrappers for utils/web_apis.py functions
- `TravelDesigner/roles/*.yaml` — YAML role configs (system prompts, toolsets)
- `TravelPlanner-master/` — invoked as a separate process under its own conda env

## Environment Variables (.env)

Required: `OPENAI_API_KEY`, `OPENAI_API_BASE`, `DB_PASSWORD`, `GOOGLE_MAPS_API_KEY`, `AMADEUS_API_KEY`, `AMADEUS_API_SECRET`, `SERPER_API_KEY`
Optional: `OPENAI_API_MODEL` (default `gpt-4o`), `GPT_BASELINE` (default `gpt-5`), `LANGFUSE_SECRET_KEY`, `DEBUG`

DB defaults: user `modeltest` (Unix) / `root` (Windows), database `modeltest`, host `localhost`.

## Evaluation Framework

Standalone `evaluation/` module for automated itinerary quality assessment using LLM-as-judge.

**Two modes:**
- **Score**: Evaluate itineraries independently on multiple dimensions (1-10 scale with justification)
- **A/B Compare**: Pairwise comparison of itineraries with Copeland ranking aggregation

**Default dimensions:** route_rationality, detail_level, representativeness, budget_reasonability, feasibility, personalization.

**Three interfaces:**
- **CLI**: `python -m evaluation.cli score|compare --config input.json [--json]`, `python -m evaluation.cli dimensions`
- **API**: `POST /eval/score`, `POST /eval/compare` (async, reuses task polling), `GET /eval/dimensions`
- **Frontend**: `/eval` page with Score and A/B Compare tabs

**Key files:**
- `evaluation/scorer.py` — `ItineraryScorer` class (single LLM call per itinerary for all dimensions)
- `evaluation/comparator.py` — `ItineraryComparator` class (round-robin pairwise, position-bias mitigation via randomized A/B)
- `evaluation/schemas.py` — dataclasses (`EvalInput`, `EvalResult`, `PairwiseResult`, `ABTestResult`) + dimension definitions
- `evaluation/prompts.py` — LLM prompt templates with rubric-based dimension descriptions
- `evaluation/cli.py` — CLI entry point
- `front_end/src/Page/EvalPage.jsx` — frontend evaluation page

**API limits:** max 10 itineraries per request (`MAX_EVAL_ITINERARIES`).

## Constraints

- Query validation enforces: travel dates within 0–60 days from now, max 20-day trip duration
- Model inference can take several minutes; production uses 1500s gunicorn timeout
- TravelPlanner model runs in a separate conda environment (`CONDA_DEFAULT_ENV`, default `estimate_web`)
- Python 3.12 (`.python-version`), Node 16+
