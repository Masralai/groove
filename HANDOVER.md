# Handover: Meta Ads Data Pipeline + NL Chatbot

## Project Overview

Production-ready service integrating with the Meta Marketing API to fetch ads data (campaigns, ad sets, ads, insights) into PostgreSQL + MongoDB, with a natural language chatbot powered by Gemini.

## Current State

### Documents Written

| File | Contents |
|------|----------|
| `PRD.md` | Full product requirements — pipeline, chatbot, architecture, data model, API design, testing, infra, documentation |
| `DECISIONS.md` | 16 architecture decisions with rationale — MongoDB vs JSONB, incremental sync, PG advisory lock, SQL injection, Alembic, GraphQL rejection, LLM framework choice, etc. |
| `DESIGN.md` | Frontend design reference (Note: This appears to be from a different project and will be replaced) |

### Code Written

**Phase 1: Project Scaffold + Config** - COMPLETED
- Project directory structure (backend/, frontend/, config/, tests/)
- Configuration management (.env.example, config/sources.yaml, core/config.py)
- FastAPI application setup (main.py)
- Database connectivity (core/database.py)
- Docker configuration (Dockerfile, docker-compose.yml)
- Dependencies (requirements.txt)
- Basic test suite (tests/test_config.py, tests/test_health.py)
- Meta API service foundation (services/meta_api_service.py)

**Phase 2: Meta API + Data Sync** - IN PROGRESS
- MetaAPI Service implementation with facebook-business SDK
- Rate limiting and error handling
- Basic test coverage for MetaAPI service

## Architecture

```
┌────────────┐    ┌────────────────────────────┐    ┌──────────────┐
│  Next.js   │    │         FastAPI             │    │  PostgreSQL  │
│  :3000     │───▶│         :8000               │───▶│  :5432       │
│            │    │                             │    │              │
│  Dashboard │    │  Fetch Router  Chat Router  │    │  analytics   │
│  Chat Page │    │  DataSyncSvc   LLM Agent    │    │  (4 tables)  │
└────────────┘    │  MetaAPISvc    SQL Validator │    └──────────────┘
                  │  Config (YAML)               │
                  │  APScheduler                 │    ┌──────────────┐
                  │                              │───▶│  MongoDB     │
                  └────────────────────────────┘    │  :27017      │
                                                    │  raw staging │
                                                    └──────────────┘
```

### Services

| Service | Responsibility |
|---------|---------------|
| MetaAPI Service | REST calls to Graph API via `facebook_business` SDK, pagination, rate-limit backoff |
| Data Sync Service | Orchestrates fetch → MongoDB → transform → PostgreSQL upsert |
| Transform Pipeline | Raw JSON → typed records with field mapping |
| LLM Agent Service | Gemini integration, text-to-SQL, result summarization |
| SQL Validator | Multi-layer: regex block on DDL, single-statement enforcement, read-only txn |

### Data Model

**PostgreSQL** (analytics):

```
campaigns (id PK, name, status, objective, daily_budget, ...)
ad_sets   (id PK, campaign_id FK, name, status, daily_budget, targeting JSONB, ...)
ads       (id PK, ad_set_id FK, name, status, creative JSONB, ...)
insights  (id SERIAL PK, ad_id FK, date DATE, impressions, clicks, spend, ..., UNIQUE(ad_id, date))
```

**MongoDB** (raw staging):

```
campaigns_raw, ad_sets_raw, ads_raw, insights_raw
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/fetch` | Trigger manual data sync |
| GET | `/api/fetch/status` | Last sync time, row counts, status |
| GET | `/api/campaigns` | List campaigns (?status filter) |
| GET | `/api/ads` | List ads (?campaign_id, ?status) |
| GET | `/api/insights` | Query insights (?date_from, ?date_to, ?campaign_id) |
| POST | `/api/chat` | `{ query: string } → { answer, sql, data }` |
| GET | `/api/schema` | DDL introspection |
| GET | `/health` | Health check |

### Key Decisions (see DECISIONS.md for full detail)

- **Dual DB**: MongoDB for raw staging, PostgreSQL for analytics
- **Incremental sync**: Time-range filtering, full override via `?full=true`
- **Concurrency**: PG advisory lock (`pg_try_advisory_xact_lock(42)`)
- **Sync failure**: Exponential backoff + cursor resume
- **Transaction integrity**: MongoDB-first writes, PG best-effort upsert
- **Migrations**: Alembic (production standard)
- **Meta API**: REST via `facebook_business` SDK (GraphQL deferred to separate branch)
- **LLM**: Gemini (Google AI, free tier)
- **SQL guardrails**: Regex block + single-statement enforcement + read-only txn
- **Scheduling**: APScheduler in FastAPI process, advisory lock prevents double-fire
- **Connection pool**: `pool_size=20, max_overflow=10, pool_timeout=10s`

## Skills Reference

| Skill | When to Use |
|-------|-------------|
| `frontend-design` | Phase 5 — Generate DESIGN.md and build Next.js UI |
| `create-readme` | Phase 6 — Generate README.md |
| `docker-expert` | Any phase — Dockerfile or docker-compose optimization |
| `supabase-postgres-best-practices` | Phase 2/3/4 — PostgreSQL query design, indexing, connection pooling |
| `framer-motion-animator` | Phase 5 — Chat message animations, page transitions |
| `high-end-visual-design` | Phase 5 — Premium frontend styling |
| `ui-ux-pro-max` | Phase 5 — Component design patterns, accessibility |

## Implmentation Plan (TDD Vertical Slices)

### Phase 1: Project Scaffold + Config

**Skills:** None required (general scaffolding)

| Order | Test | What it proves |
|-------|------|---------------|
| RED | Config YAML loads and validates required fields | ConfigService works |
| GREEN | Implement ConfigService, config/sources.yaml, .env.example, pyproject.toml | |
| RED | FastAPI app starts and /health returns OK | App boots |
| GREEN | main.py, database.py, Dockerfile, docker-compose.yml (postgres, mongodb, backend) | |

### Phase 2: Meta API + Data Sync

**Skills:** `docker-expert` if optimizing containers, `supabase-postgres-best-practices` for upsert/index design

| Order | Test | What it proves |
|-------|------|---------------|
| RED | Meta API fetches campaigns with pagination | MetaAPIService works |
| GREEN | MetaAPIService with facebook_business SDK, cursor handling, rate-limit backoff | |
| RED | Raw campaign saves to MongoDB | MongoDB write path works |
| GREEN | MongoDB write via motor (async driver) | |
| RED | Transform normalizes raw campaign to typed record | Transform logic correct |
| GREEN | TransformPipeline with field mapping, type coercion, timestamp parsing | |
| RED | Upsert to PostgreSQL is idempotent | PostgreSQL write path works |
| GREEN | SQLAlchemy upsert (ON CONFLICT DO UPDATE) | |
| RED | POST /api/fetch orchestrates end-to-end | Full sync pipeline |
| GREEN | DataSyncService + fetch router + sync status table | |
| RED | Scheduler fires daily sync | APScheduler integration |
| GREEN | APScheduler in FastAPI lifespan with advisory lock | |

### Phase 3: Read APIs

**Skills:** `supabase-postgres-best-practices` for query perf

| Order | Test | What it proves |
|-------|------|---------------|
| RED | GET /api/campaigns returns data from DB | Read API works |
| GREEN | data router with filtering (status), pagination | |
| RED | GET /api/insights with date range + campaign filter | Filtered query works |
| GREEN | insights endpoint with query params | |

### Phase 4: LLM Agent + Chat

**Skills:** `supabase-postgres-best-practices` for query injection prevention patterns

| Order | Test | What it proves |
|-------|------|---------------|
| RED | LLM Agent generates valid SQL from user query | Prompt engineering works |
| GREEN | LLMAgentService with Gemini client + 3-part system prompt | |
| RED | SQL validator rejects DDL / multi-statement queries | Security mitigation works |
| GREEN | SQLValidator with regex + sqlparse + read-only enforcement | |
| RED | POST /api/chat returns answer | Full chat flow |
| GREEN | chat router + agent orchestration + error handling (empty, invalid, retry) | |
| RED | Chat handles empty data / out-of-scope gracefully | Guardrails work |
| GREEN | Clarification prompting, "can't find data" responses, retry logic | |

### Phase 5: Frontend

**Skills:** `frontend-design` → generates DESIGN.md, then builds components; `ui-ux-pro-max` for component architecture; `high-end-visual-design` for premium styling; `framer-motion-animator` for chat animations

| Step | What |
|------|------|
| 1 | Load frontend-design skill → generate DESIGN.md |
| 2 | Next.js app with Dashboard (`/`) + Chat (`/chat`) pages |
| 3 | Dockerfile for frontend, add to docker-compose.yml |

### Phase 6: Documentation

**Skills:** `create-readme` for README.md generation

| File | Contents |
|------|----------|
| README.md | Setup, run, assumptions, limitations, prompt engineering, security, scaling |
| DESIGN.md | Component tree, layout, color palette, typography, interaction states |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Databases | PostgreSQL 16 (analytics), MongoDB 7 (staging) |
| Meta API | `facebook_business` SDK (REST) |
| LLM | Gemini via `google-genai-sdk` |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Testing | pytest, pytest-asyncio, testcontainers, httpx_mock / responses |
| Infrastructure | Docker Compose (4 services) |
| Config | YAML (`config/sources.yaml`) |

## Environment Variables (.env.example)

```env
META_ACCESS_TOKEN=<meta-api-access-token>
META_AD_ACCOUNT_ID=act_<account-id>
GEMINI_API_KEY=<google-ai-studio-api-key>
POSTGRES_DSN=postgresql+asyncpg://groove:groove@postgres:5432/groove
MONGODB_URI=mongodb://mongodb:27017/groove
```

## Dependencies (Python)

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
motor  # async MongoDB
facebook-business  # Meta API SDK
google-genai-sdk  # Gemini
pydantic-settings
pyyaml
alembic
apscheduler
httpx
sqlparse  # SQL validation
pytest
pytest-asyncio
testcontainers[postgres,mongodb]
httpx-mock  # or responses
```

## Verification

```bash
# Start everything
docker compose up --build

# Check health
curl http://localhost:8000/health

# Trigger sync
curl -X POST http://localhost:8000/api/fetch

# Check campaigns
curl http://localhost:8000/api/campaigns

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Which campaign spent the most last week?"}'

# Run tests (inside container)
docker compose exec backend pytest
```

## Gotchas & Notes

1. **Meta API creds**: Needed for `POST /api/fetch` to work. Without them, the chat can still answer based on seeded/empty DB data.
2. **Gemini API key**: Free from Google AI Studio. Without it, the chat endpoint returns errors.
3. **APScheduler + multi-worker**: The PG advisory lock prevents double-fires. For production, use a dedicated scheduler container.
4. **MongoDB vs JSONB kept separate** — not merged per PRD decision. If asked why, refer to DECISIONS.md #1.
5. **GraphQL rejected** — REST/SDK chosen. See DECISIONS.md #15 for rationale.
6. **Frontend DESIGN.md**: Use `frontend-design` skill when implementing. File goes in `frontend/DESIGN.md`.
7. **LLM uses 2-call pattern**: SQL gen → execute → summarize. Acceptable latency (3-4s total) for single-user tool.
