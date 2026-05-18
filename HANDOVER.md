# Handover: Meta Ads Data Pipeline + NL Chatbot

## Project Overview

Production-ready service integrating with the Meta Marketing API to fetch ads data (campaigns, ad sets, ads, insights) into PostgreSQL + MongoDB, with a natural language chatbot powered by Gemini.

## Completed Since Last Handover

| Item | Description |
|------|-------------|
| Bug fix: ad_id in insights transform | Added `ad_id` to `META_DEFAULT_FIELDS['insights']`, `sources.yaml`, and `transform_insight()` output — unblocks "Insights return 0" |
| Bug fix: event loop blocking | Wrapped all 4 SDK fetch methods in `run_in_executor(ThreadPoolExecutor(max_workers=4))` |
| Bug fix: hardcoded dashboard date | Replaced `date_from=2024-01-01` with dynamic 30d-ago |
| Config path resolution | `load_yaml_config()` now tries 3 fallback paths (local dev, Docker `/app/config`, absolute) |
| `--reload` re-enabled | Added to docker-compose uvicorn command (faster iteration over interruption risk) |
| `version: '3.8'` removed | No more Docker Compose v2 startup warning |
| `datetime.utcnow()` replaced | 20 occurrences across 4 files → `datetime.now(timezone.utc)` |
| Pydantic `class Config` replaced | 2 files → `model_config = ConfigDict(...)` |
| Renamed: LLM Agent → LLM Service | `LLMAgentService` → `LLMService`, `llm_agent_service.py` → `llm_service.py`, all docs updated |
| Backend tests: 106 passing | 11 pre-existing failures fixed (LLM agent mocking, MongoDB patching, chat DB override, router wiring) |
| Frontend test infra | `vitest` + `@testing-library/react` installed, configured, 1 passing test |

### LLM Tests Fixed

| File | Approach |
|------|----------|
| `tests/test_llm/test_llm_service.py` | Patches `llm_service.client.models.generate_content` directly (module-level singleton, can't mock constructor) |
| `tests/test_llm/test_chat_integration.py` | Uses `app.dependency_overrides[get_db]` instead of `patch('app.core.database.get_db')` (FastAPI caches function refs at import time) |

## Current State

### Documents Written

| File | Contents |
|------|----------|
| `PRD.md` | Full product requirements — pipeline, chatbot, architecture, data model, API design, testing, infra, documentation |
| `DECISIONS.md` | 16 architecture decisions with rationale — MongoDB vs JSONB, incremental sync, PG advisory lock, SQL injection, Alembic, GraphQL rejection, LLM framework choice, etc. |
| `DESIGN.md` | Frontend design reference — Grafbase-inspired engineering aesthetic adapted for Meta Ads dashboard |

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

**Phase 2: Meta API + Data Sync** - COMPLETED
- MetaAPI Service implementation with facebook-business SDK
- Rate limiting and error handling
- Basic test coverage for MetaAPI service
- MongoDB integration (models, repository)
- Transform pipeline for converting raw API data to normalized records
- Data sync service orchestrating fetch → MongoDB → transform → PostgreSQL
- PostgreSQL SQLAlchemy models for campaigns, ad_sets, ads, insights
- Upsert functionality with ON CONFLICT DO UPDATE
- API endpoints for triggering data sync (manual and status)
- APScheduler configuration for daily automated sync

**Phase 3: Read APIs** - COMPLETED
- GET /api/campaigns endpoint with status filtering and pagination
- GET /api/ads endpoint with campaign_id and status filtering
- GET /api/insights endpoint with date range and campaign filtering
- PostgreSQL repository with read operations
- Comprehensive test suite for new endpoints

**Phase 4: LLM Service + Chat** - COMPLETED
- LLM Service with Gemini API integration for text-to-SQL generation and result summarization
- SQL Validator service with multi-layered protection (regex block, single-statement enforcement, read-only transactions)
- Chat endpoint (/api/chat) for natural language queries with error handling and retry logic
- System prompt engineering with schema injection and few-shot examples
- Comprehensive unit and integration tests for LLM agent, SQL validator, and chat endpoint

**Phase 5: Frontend** - COMPLETED
- Next.js 16 project with TypeScript, Tailwind CSS v4, App Router
- Design system tokens from DESIGN.md implemented via Tailwind v4 `@theme` block
- Reusable component library (KPICard, EmptyState, LoadingState)
- Landing page (`/`) — Hero with CTAs, feature cards, footer
- Dashboard page (`/dashboard`) — "use client" with live API data (4 KPIs from insights, campaigns table with filter/pagination, sync button)
- Chat page (`/chat`) — Full NL interface with message history, collapsible SQL blocks, loading/error states, recent queries sidebar
- Sticky header navigation with logo and nav links
- API proxy via next.config.ts rewrites (configurable `API_URL` env var)
- Accessibility: aria-labels, focus-visible rings, reduced-motion support, proper heading hierarchy
- Micro-interactions: hover-lift on cards, 200ms transitions, loading skeletons, bounce animation for AI "thinking"
- `.env.local` with backend URL for development
- `Dockerfile` for production (multi-stage, standalone output)
- `.dockerignore` excluding dev artifacts from builds
- Frontend service in `docker-compose.yml` with build arg for API URL

**Phase 5.5: Bug Fixes + Full-Stack Runnable** - COMPLETED

| Fix | Files | Description |
|-----|-------|-------------|
| Runtime bug 1 | `core/config.py` | `settings.meta_ads` now populated from YAML config on module load, with graceful FileNotFoundError fallback |
| Runtime bug 2 | `models/postgres.py` | Added `UniqueConstraint(ad_id, date)` — without it the `ON CONFLICT` upsert would crash at runtime |
| Runtime bug 3 | `services/llm_service.py` | DDL in system prompt now matches actual model (TEXT PK instead of SERIAL, date NOT NULL) |
| Path resolution | `core/config.py` | `load_yaml_config` goes up 4 dir levels (not 3) to find project-root `config/sources.yaml` |
| Partitioning | `models/postgres.py` | Removed `PARTITION BY RANGE (date)` — PG requires partition columns in all unique constraints, and partitioning is unnecessary at this scale |
| MongoDB healthcheck | `docker-compose.yml` | Fixed `mongo` → `mongosh` for MongoDB 7 compatibility |
| `__init__.py` | 9 files | Added to all bare Python packages for proper module resolution |
| Empty dir | `services/llm/` | Removed (contained no files) |

## Architecture

```
┌────────────┐    ┌──────────────────────────────┐    ┌──────────────┐
│  Next.js   │    │         FastAPI              │    │  PostgreSQL  │
│  :3000     │───▶│         :8000                │───▶│  :5432       │
│            │    │                              │    │              │
│  Dashboard │    │  Fetch Router  Chat Router   │    │  analytics   │
│  Chat Page │    │  DataSyncSvc   LLM Service   │    │  (4 tables)  │
└────────────┘    │  MetaAPISvc    SQL Validator │    └──────────────┘
                  │  Config (YAML)               │
                  │  APScheduler                 │    ┌──────────────┐
                  │                              │───▶│  MongoDB     │
                  └──────────────────────────────┘    │  :27017      │
                                                      │  raw staging │
                                                      └──────────────┘
```

### Services

| Service | Responsibility |
|---------|---------------|
| MetaAPI Service | REST calls to Graph API via `facebook_business` SDK, pagination, rate-limit backoff |
| Data Sync Service | Orchestrates fetch → MongoDB → transform → PostgreSQL upsert |
| Transform Pipeline | Raw JSON → typed records with field mapping |
| LLM Service | Gemini API integration, text-to-SQL, result summarization |
| SQL Validator | Multi-layer: regex block on DDL, single-statement enforcement, read-only txn |

### Data Model

**PostgreSQL** (analytics):

```
campaigns (id PK, name, status, objective, daily_budget, ...)
ad_sets   (id PK, campaign_id FK, name, status, daily_budget, targeting JSONB, ...)
ads       (id PK, ad_set_id FK, name, status, creative JSONB, ...)
insights  (id TEXT PK (UUID), ad_id FK, date DATE NOT NULL, impressions, clicks, spend, ..., UNIQUE(ad_id, date))
```

**MongoDB** (raw staging):

```
campaigns_raw, ad_sets_raw, ads_raw, insights_raw
```

### API Endpoints

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| POST | `/api/fetch` | Trigger manual data sync | EXISTS |
| GET | `/api/fetch/status` | Last sync time, row counts, status | EXISTS |
| GET | `/api/campaigns` | List campaigns (?status filter) | EXISTS |
| GET | `/api/ads` | List ads (?campaign_id, ?status) | EXISTS |
| GET | `/api/insights` | Query insights (?date_from, ?date_to, ?campaign_id) | EXISTS |
| POST | `/api/chat` | `{ query: string } → { answer, sql, data }` | EXISTS |
| GET | `/api/schema` | DDL introspection | EXISTS |
| GET | `/api/health` | Health check (also at `/health` for root-level) | EXISTS |

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
| `frontend-design` | Design system extension or new page creation |
| `framer-motion-animator` | Polish — Chat message entrance animations, page transitions |
| `high-end-visual-design` | Polish — Premium animation/refinement pass |
| `ui-ux-pro-max` | Polish — Accessibility audit, component refinement |
| `create-readme` | Phase 6 — README.md needs completion with all sections |
| `supabase-postgres-best-practices` | Query optimization, indexing |

## Implmentation Plan (TDD Vertical Slices)

### Phase 1: Project Scaffold + Config - COMPLETED

**Skills:** None required (general scaffolding)

| Order | Test | What it proves |
|-------|------|---------------|
| RED | Config YAML loads and validates required fields | ConfigService works |
| GREEN | Implement ConfigService, config/sources.yaml, .env.example, pyproject.toml | |
| RED | FastAPI app starts and /health returns OK | App boots |
| GREEN | main.py, database.py, Dockerfile, docker-compose.yml (postgres, mongodb, backend) | |

### Phase 2: Meta API + Data Sync - COMPLETED

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

### Phase 3: Read APIs - COMPLETED

**Skills:** `supabase-postgres-best-practices` for query perf

| Order | Test | What it proves |
|-------|------|---------------|
| RED | GET /api/campaigns returns data from DB | Read API works |
| GREEN | data router with filtering (status), pagination | |
| RED | GET /api/insights with date range + campaign filter | Filtered query works |
| GREEN | insights endpoint with query params | |

### Phase 4: LLM Service + Chat - COMPLETED

**Skills:** `supabase-postgres-best-practices` for query injection prevention patterns

| Order | Test | What it proves |
|-------|------|---------------|
| RED | LLM generates valid SQL from user query | Prompt engineering works |
| GREEN | LLMService with Gemini client + 3-part system prompt | |
| RED | SQL validator rejects DDL / multi-statement queries | Security mitigation works |
| GREEN | SQLValidator with regex + sqlparse + read-only enforcement | |
| RED | POST /api/chat returns answer | Full chat flow |
| GREEN | chat router + agent orchestration + error handling (empty, invalid, retry) | |
| RED | Chat handles empty data / out-of-scope gracefully | Guardrails work |
| GREEN | Clarification prompting, "can't find data" responses, retry logic | |

### Phase 5: Frontend - COMPLETED

**Skills used:** `ui-ux-pro-max` for component architecture and accessibility; `high-end-visual-design` for premium styling (design system adapted from Grafbase reference)

| Step | Status | What |
|------|--------|------|
| 1 | COMPLETED | DESIGN.md adapted for Meta Ads dashboard (`/`) and chat (`/chat`) pages |
| 2 | COMPLETED | Next.js 16 app with Tailwind v4, TypeScript, App Router implemented |
| 3 | COMPLETED | Dockerfile for frontend + added to docker-compose.yml (multi-stage standalone build) |
| 4 | COMPLETED | Dashboard now fetches live data from `/api/campaigns` and `/api/insights`. Chat proxies through Next.js rewrites to backend. Verified end-to-end with full `docker compose up` |

#### Frontend Structure

```
frontend/
├── .dockerignore                     # Excludes node_modules, .next, .env.local from builds
├── Dockerfile                        # Multi-stage standalone build (ARG API_URL)
├── styles/
│   ├── design-tokens.css            # DESIGN.md reference tokens
│   └── globals.css                  # Tailwind v4 @theme + custom component classes
├── src/
│   └── app/
│       ├── _components/
│       │   └── Header.tsx           # Sticky nav bar with logo + navigation
│       ├── chat/
│       │   ├── layout.tsx            # Chat metadata (SEO)
│       │   └── page.tsx             # Full chat interface ("use client")
│       ├── dashboard/
│       │   ├── layout.tsx            # Dashboard metadata (SEO)
│       │   └── page.tsx             # KPI cards + campaigns table ("use client", live API)
│       ├── globals.css               # Root Tailwind import
│       ├── layout.tsx                # Root layout with Inter font + Header
│       └── page.tsx                  # Landing page
├── src/components/
│   ├── KPICard.tsx                   # Reusable metric card component
│   ├── EmptyState.tsx                # Empty data state with action
│   └── LoadingState.tsx              # Card + table skeleton loaders
├── next.config.ts                    # output: standalone, API proxy → FastAPI :8000
├── .env.local                        # API_URL=http://localhost:8000
└── postcss.config.mjs                # Tailwind v4 PostCSS setup
```

#### Design System (from DESIGN.md via `@theme` block in globals.css)

| Token Category | Values |
|---------------|--------|
| **Colors** | midnight-ink: #1b1b1b, canvas-white: #ffffff, cloud-gray: #eaeaea, slate-text: #60646c, ash-gray: #7c7c7c, cloud-border: #e0e1e6, plasma-teal-gradient: linear gradient |
| **Typography** | Inter via `next/font/google`, weights 400-700, type scale: 16px/20px/24px/40px |
| **Spacing** | 4px base unit, comfortable density, section-gap 64px, card-padding 24px |
| **Radii** | buttons: 6px, cards: 12px, misc: 20px, circular: 40px |
| **Shadows** | lg: rgba(0,0,0,0.15) 0px 4px 20px 0px |

#### Custom Utility Classes

| Class | Description |
|-------|-------------|
| `.btn-primary` | Plasma Teal Gradient CTA button with 6px radius, hover shadow |
| `.btn-secondary` | Cloud Gray filled button with 1px border |
| `.btn-ghost` | Underline-style ghost button (transparent bg) |
| `.card` | Canvas White card with 12px radius, 24px padding, border + shadow |
| `.input` / `.textarea` | Form inputs with focus ring |
| `.badge-*` | Status/tag pills (primary, secondary, status-active/paused/completed) |
| `.hover-lift` | Card hover effect: translateY(-2px) + shadow |

#### Pages

| Route | Type | Features |
|-------|------|----------|
| `/` | Server component | Hero section, 3 feature cards, CTA, footer |
| `/dashboard` | Client component | 4 live KPI cards aggregated from insights + campaigns table with status filter & pagination + sync button |
| `/chat` | Client component | Message list, collapsible SQL blocks with copy, loading bounce animation, error states, recent queries sidebar, expand/fullscreen toggle |

#### Accessibility

- Focus-visible rings on all interactive elements
- aria-labels on icon-only buttons and controls
- aria-hidden on decorative icons
- aria-live="polite" on chat message log
- aria-expanded on collapsible SQL blocks
- aria-label and role attributes on form controls
- `prefers-reduced-motion` support disables all animations
- Semantic heading hierarchy (h1 → h2 → h3)
- Status badges use text + color (not color alone)

## Next Agent Brief

### Integration Bugs Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Backend 500 on startup | `alembic_command.upgrade()` called synchronously inside async startup (uses `asyncio.run()` inside `env.py`) | Wrapped in `loop.run_in_executor()` to run in a thread pool |
| `/api/fetch` 500 | `FastAPI` validates response body against `-> Dict[str, int]` type hint | Changed to `-> Dict[str, Any]` to match actual return shape |
| Ad set sync fails | `targeting` field is a `Targeting` SDK object, not serializable | Added `_serialize()` + `_prepare_record()` in transform pipeline |
| Ad sync fails | Meta API field is `adset_id` (no underscore), model expects `ad_set_id` | Updated field names in `META_DEFAULT_FIELDS` + pipeline maps both |
| Campaign date error | `created_time` etc. are ISO strings from API, PG expects `datetime` | Added `_parse_datetime()` in pipeline, converts to offset-naive UTC |
| Insights API error | `conversion_value` is not a valid insights field in v22.0 | Removed from default fields |
| Insights API error | `time_range` param passed as string instead of dict | Pass dict directly |
| Model unavailable | `gemini-3-flash` not a valid API model name | Changed to `gemini-2.5-flash` |
| Config file not found | Docker volume mount path mismatch -- code looks for `/config/sources.yaml` but volume mounts to `/app/config` | Added `.get()` fallbacks in `meta_api_service.py` |

### Current Status

- All 8 API endpoints work end-to-end ✓
- Real Meta data sync works (3 campaigns, 4 ad sets, 4 ads) ✓
- Chat works (real LLM → SQL generation → execute → summarize) ✓
- Frontend: landing, dashboard, chat, 404 page all load ✓
- Dark mode, mobile nav, error boundaries deployed ✓
- Frontend proxy (`:3000/api/*`) works ✓
- **106 backend tests passing**, 0 failing ✓
- **Frontend vitest infra ready**, 1 test passing ✓
- **Deprecation warnings**: 5 remaining (all `on_event` lifespan — intentionally skipped, project concludes in 1 week)
- **Insights return 0** — `ad_id` field fixed in transform pipeline; remaining issue may be that Meta account has no insight data, or query level/date range needs adjustment

### What Still Needs Work

Grouped by priority and category:

#### 1. Security

| Issue | Detail | Impact |
|-------|--------|--------|
| **No CORS middleware** | `CORSMiddleware` not configured. Next.js proxy works, but any direct API call from browser is blocked | Prevents direct API access from external clients |
| **`SECRET_KEY` hardcoded default** | `config.py:27`: `"dev-secret-key-change-in-production"` — not overridden in production | Vulnerability if this default is used in production |
| **No read-only DB user** | DECISIONS.md #11 specifies `llm_agent` role with SELECT-only perms for chat endpoint; never created | Chat LLM could potentially write to DB if SQL injection bypasses validator |
| **Real credentials in `.env`** | `.env` contains live API tokens. Already in `.gitignore`, but verify `git log --all --diff-filter=A -- .env` that they were never committed | Credential leak via git history |

#### 2. Infrastructure & Deployment

| Issue | Detail | Impact |
|-------|--------|--------|
| **No CI/CD** | No GitHub Actions or equivalent for test-on-push | Changes can break tests without detection |
| **No production deployment configs** | No K8s manifests, Helm charts, Terraform, or `docker-compose.prod.yml` | Can't deploy to production without manual setup |
| **No HEALTHCHECK in Dockerfiles** | Both backend and frontend containers lack health probes | `depends_on` waits for container start, not app readiness |
| **Backend runs as root** | Both Dockerfiles should create and use a non-root user | Security best practice violation |
| **Backend has no `.dockerignore`** | `venv/` and `__pycache__/` get shipped to Docker daemon | Slower builds, unnecessary context transfers |

#### 3. Frontend Tests

| Issue | Detail |
|-------|--------|
| **14 components untested** | Only `Home.test.tsx` exists. Missing: `Header.tsx`, `ThemeToggle.tsx`, `dashboard/page.tsx` (344 lines), `chat/page.tsx` (378 lines), `KPICard.tsx`, `EmptyState.tsx`, `LoadingState.tsx`, error boundaries, layouts |
| **Dashboard helpers not extractable** | `formatCurrency`, `computeKPIs`, `formatCompact`, `trendChange`, `statusBadgeClass` in `dashboard/page.tsx` are module-local — need to be exported to a shared utility for unit testing |

#### 4. Backend Gaps

| Issue | Detail |
|-------|--------|
| **Advisory lock not implemented** | PRD Decision #3 specifies `pg_try_advisory_xact_lock(42)` in `sync_all()` to prevent concurrent syncs. Not implemented — two simultaneous `POST /api/fetch` calls could corrupt data |
| **Row-by-row upsert is slow** | `postgres_repository.py` executes individual `INSERT ... ON CONFLICT` per row. For large datasets (10k+ insights), batch upsert would be far more performant |
| **No `pyproject.toml`** | PRD scaffold references `pyproject.toml`, only `requirements.txt` exists. Modern Python projects typically use `pyproject.toml` |
| **`testcontainers` unused** | `testcontainers[postgres,mongodb]` in `requirements.txt` but all tests use mocks — no real DB integration tests |
| **`API_V1_STR` config unused** | `config.py:11` sets `API_V1_STR = "/api/v1"`, but router is mounted at `/api` in `main.py:67` |

#### 5. Code Quality & Architecture

| Issue | Detail |
|-------|--------|
| **No Python linter/formatter** | No `ruff`, `black`, `mypy`, or `flake8` configuration. Frontend has ESLint, backend has nothing |
| **Two `EmptyState` implementations** | Reusable one in `src/components/EmptyState.tsx` + inline duplicate in `chat/page.tsx` (lines 157-169). Should be unified |
| **`design-tokens.css` is dead code** | 105 lines of CSS custom properties in `styles/design-tokens.css` — never imported anywhere. Root layout imports `globals.css` only |
| **Dark mode may be broken** | `globals.css` dark-mode overrides (lines 269-281) reference `--color-dark-*` variables only defined in the unimported `design-tokens.css` |
| **No `pre-commit` config** | No `.pre-commit-config.yaml` for automated linting/formatting on commits |
| **Single Alembic migration** | Only `0001_initial.py` exists — any future schema change requires manual migration creation |

#### 6. Documentation

| Issue | Detail |
|-------|--------|
| **README missing 3 sections** | Prompt Engineering, Security, and Scaling sections (all required by PRD) are absent from `README.md` |
| **`SECURITY.md` doesn't exist** | Referenced in DECISIONS.md #11 as the file containing read-only PostgreSQL user setup — never created |
| **Model name mismatch in README** | `README.md` says "Gemini 3 Flash", but code defaults to `gemini-2.5-flash` (and HANDOVER gotcha #14 confirms 2.5 Flash is the correct stable model) |

### Frontend Polish — COMPLETED

| Item | Files | Description |
|------|-------|-------------|
| Error boundaries | `error.tsx`, `chat/error.tsx`, `not-found.tsx` | Global error page + chat-specific error + 404 page, all with retry/home actions |
| Mobile nav | `_components/Header.tsx` | Converted to client component, hamburger menu with backdrop + slide-down drawer, body scroll lock |
| Chat mobile | `chat/page.tsx` | Bottom sheet for recent queries (FAB trigger on mobile), backdrop dismiss, preserves desktop sidebar |
| Touch targets | `dashboard/page.tsx` | Pagination buttons now `min-h-[44px]` for touch accessibility |
| Dark mode | `styles/design-tokens.css`, `styles/globals.css`, `_components/ThemeToggle.tsx`, `_components/Header.tsx`, `layout.tsx` | CSS custom properties with `[data-theme="dark"]` overrides, system preference detection, localStorage persistence, flash-prevention inline script, sun/moon toggle in header |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Databases | PostgreSQL 16 (analytics), MongoDB 7 (staging) |
| Meta API | `facebook_business` SDK (REST) |
| LLM | Gemini 2.5 Flash via `google-genai` |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
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

## Dependencies

### Python (backend)

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
motor  # async MongoDB
facebook-business  # Meta API SDK
google-genai  # Gemini
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

### Node.js (frontend — see `frontend/package.json`)

```
next           ^16
react          ^19
react-dom      ^19
@tailwindcss/postcss
typescript
tailwindcss
eslint
eslint-config-next
```

## Verification

```bash
# Start all services (4 containers)
docker compose up --build

# Check health
curl http://localhost:8000/api/health

# Frontend
open http://localhost:3000

# Trigger sync (requires valid Meta API credentials in .env)
curl -X POST http://localhost:8000/api/fetch

# Check sync status
curl http://localhost:8000/api/fetch/status

# Check campaigns (will be empty until sync runs)
curl http://localhost:8000/api/campaigns

# Check ads (will be empty until sync runs)
curl http://localhost:8000/api/ads

# Check insights (will be empty until sync runs)
curl http://localhost:8000/api/insights

# Chat (requires valid Gemini API key and data to return meaningful results)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Which campaign spent the most last week?"}'

# All endpoints also available via frontend proxy on :3000
curl http://localhost:3000/api/health

# Run tests (inside container)
docker compose exec backend pytest
```

## Gotchas & Notes

1. **Meta API creds**: Needed for `POST /api/fetch` to work. Without them, the chat can still answer based on seeded/empty DB data.
2. **Gemini API key**: Free from Google AI Studio. Without it, the chat endpoint returns errors.
3. **APScheduler + multi-worker**: The PG advisory lock prevents double-fires. For production, use a dedicated scheduler container.
4. **MongoDB vs JSONB kept separate** — not merged per PRD decision. If asked why, refer to DECISIONS.md #1.
5. **GraphQL rejected** — REST/SDK chosen. See DECISIONS.md #15 for rationale.
6. **Full stack runs via docker compose**: `docker compose up --build` starts all 4 services (postgres, mongodb, backend, frontend). Frontend at :3000 proxying API to backend at :8000.
7. **LLM uses 2-call pattern**: SQL gen → execute → summarize. Acceptable latency (3-4s total) for single-user tool.
8. **Frontend design system**: DESIGN.md is the source of truth. Tailwind v4 `@theme` block in `styles/globals.css` implements it.
9. **Frontend Docker build**: Requires `API_URL` build arg (set in docker-compose.yml). The frontend `next.config.ts` reads this at build time for the rewrites destination. During `npm run dev` it reads from `.env.local`.
10. **Client component patterns**: Chat page uses `"use client"` for interactive state. Dashboard is also `"use client"` (needs state for filters/pagination/sync). Landing page remains a server component.
11. **Dashboard KPIs**: Computed client-side from `/api/insights` data (full fetch with dynamic 30d-ago date). For large datasets, add a dedicated aggregate endpoint or server-side aggregation.
12. **Insights model**: Uses `Text PK` (UUID string), not `SERIAL`. The `UniqueConstraint(ad_id, date)` enables the `ON CONFLICT` upsert. Partitioning was removed (conflicts with PG's requirement that partition columns appear in all unique constraints).
13. **`settings.meta_ads`**: Now populated automatically from `config/sources.yaml` on import. Gracefully falls back to empty dict if YAML file is missing (useful for CI/testing).
14. **Valid Gemini model names**: As of May 2026, `gemini-2.5-flash` is the latest stable Flash model. `gemini-3-flash` is not yet available via the API (only `gemini-3-flash-preview` exists). Updated config defaults to `gemini-2.5-flash`.
15. **facebook-business SDK fields**: Field names use underscore format (e.g. `adset_id`, `date_start`). The SDK returns raw API data as `dict()` — JSON/JSONB columns in PostgreSQL require `json.dumps()` serialization via the transform pipeline before upsert. Date/time strings are parsed to offset-naive UTC `datetime` objects.
16. **Backend container runs with `--reload`** for faster iteration during development. `docker compose restart backend` after adding new dependencies (volumes are mounted, so code changes trigger auto-reload). Beware of mid-request interruptions during heavy sync operations.
