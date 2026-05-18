# Handover: Meta Ads Data Pipeline + NL Chatbot

## Project Overview

Production-ready service integrating with the Meta Marketing API to fetch ads data (campaigns, ad sets, ads, insights) into PostgreSQL + MongoDB, with a natural language chatbot powered by OpenRouter or LM Studio.

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
| Backend tests: 106 → 109 passing | 11 pre-existing failures fixed + 3 new advisory lock tests |
| Frontend test infra + dashboard-utils tests | `vitest` + `@testing-library/react` installed + 15 dashboard-utils unit tests |
| Advisory lock + 409 conflict | `pg_try_advisory_lock(42)` in `sync_all()`, `SyncAlreadyRunningError` exception, router returns 409 on concurrent sync |
| Batch upsert (all 4 entities) | `_batch_upsert_sql()` helper generates single multi-row `INSERT ... VALUES (...), (...), ... ON CONFLICT DO UPDATE` |
| CORS middleware | Added to `main.py` with `CORS_ORIGINS` env var, added to `.env.example` |
| SECRET_KEY startup warning | `logger.warning` if default dev key detected on startup |
| `pyproject.toml` + ruff | Build system, deps, dev deps, ruff config, mypy config, pytest config. `ruff check --fix` fixed 508 issues. |
| Dockerfile hardening (both) | Non-root users (`appuser`/`nodeuser` UID 1001) + `HEALTHCHECK` with `curl` on both backend and frontend |
| Backend `.dockerignore` | Created — excludes venv, pycache, pytest_cache, .env, etc. |
| Dashboard helpers extracted | `formatCurrency`, `computeKPIs`, `formatCompact`, `trendChange`, `statusBadgeClass` → `src/lib/dashboard-utils.ts` with 15 unit tests |
| Design tokens consolidated | `design-tokens.css` deleted, dark vars merged into `globals.css` `@theme` block, `[data-theme="dark"]` toggle selector fixed |
| EmptyState dedup | Shared `EmptyState` component extended with `variant="chat"`, inline duplicate removed from `chat/page.tsx` |
| `API_V1_STR` cleanup | Removed unused `/api/v1` prefix from config |

| README sections + SECURITY.md | Added Prompt Engineering, Security, Scaling sections to README.md. Created `SECURITY.md` with read-only DB user setup, CORS config, secret key advice. |
| CI/CD workflow | `.github/workflows/test.yml` — backend pytest + ruff lint, frontend vitest + build on push/PR to main |
| `.pre-commit-config.yaml` | Created with ruff (lint+format) + trailing-whitespace, end-of-file-fixer, check-yaml, check-json |
| Dual LLM provider (OpenRouter + LM Studio) | Added `LLM_PROVIDER`, `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL` to config; `_call_llm()` picks URL/model/headers/error-handling dynamically; quota checks skipped for LM Studio |
| LM Studio Docker networking fix | Changed from `network_mode: host` + bridge → `network_mode: host` on both backend + frontend; DSNs use `localhost`; LM Studio reached at `localhost:1234` |
| FdLogger for visible Docker logs | Replaced `logging.getLogger()` with `FdLogger` (direct `os.write(1, ...)`) in `main.py`, `router.py`, `llm_service.py` — makes logs visible in `docker compose logs` |
| Read-only DB user for LLM | Added `POSTGRES_READONLY_DSN` with blank-to-None validator; added `get_readonly_db()` dependency |
| Frontend component tests | 7 test files, 41 tests — covers chat, error states, non-JSON responses |
| Removed Recent Queries sidebar | Removed from chat UI: hardcoded `recentQueries` array, desktop sidebar, mobile FAB/sheet. Removed 2 corresponding tests |
| Fixed `response.json()` order | Reordered to check `response.ok` first, safe try-catch on error — prevents raw JSON parse errors shown to user |
| httpx timeout 60s → 180s | gemma-4-e4b takes ~51s to reason; 60s caused client disconnect mid-response |
| Skip SQL cache for retry/repair | Added `use_cache=False` parameter — validation retry and SQL execution repair always call LLM fresh |
| Fixed trailing `;` stripping bug | Regex markdown extraction path was missing `.rstrip(';')` — every markdown-wrapped SQL was falsely rejected as "multi-statement" |
| Fixed Docker networking | `network_mode: host` on backend + frontend; DSNs use `localhost`; LM Studio at `localhost:1234` |
| System prompt improved | Replaced forced-SQL constraint #9 with EXTRACT(DOW FROM date) guidance + constraint #10: prefer explanation over bad SQL. Added Example 5 showing `EXTRACT(DOW FROM date) = 2` |
| `summarize_results()` improved | Now calls LLM to explain empty results instead of generic "No data found" |
| Text-only chat fallback | All 5 400-error paths in router replaced with `_text_fallback()` returning `{answer, sql: null, data: []}` |
| `sql_validator.is_comment` fixed | `isinstance(token, sqlparse.sql.Comment)` — removed false "Multi-statement query" rejections |
| Data context injection | Queries PG for date range, campaigns, row count before LLM call — LLM knows actual data distribution |
| `server-wrapper.js` + `_chat_lock` reverted | Didn't fix ECONNRESET; reverted to `CMD ["node", "server.js"]` and removed `asyncio.Lock()` |
| README Quickstart section | Terminal curl examples with all 3 assignment queries + response format |
| Latency docs corrected | Gotcha #7 updated from "3-4s" to "~1-2 min (LM Studio)" |

### LLM Tests Fixed

| File | Approach |
|------|----------|
| `tests/test_llm/test_llm_service.py` | Patches `llm_service.client.models.generate_content` directly (module-level singleton, can't mock constructor) |
| `tests/test_llm/test_chat_integration.py` | Uses `app.dependency_overrides[get_db]` instead of `patch('app.core.database.get_db')` (FastAPI caches function refs at import time) |

## Current State

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
- LLM Service with OpenRouter/LM Studio integration for text-to-SQL generation and result summarization
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
| LLM Service | OpenRouter/LM Studio API integration, text-to-SQL, result summarization |
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
- **Concurrency**: PG advisory lock (`pg_try_advisory_lock(42)` — session-level, holds across multiple transactions within sync)
- **Sync failure**: Exponential backoff + cursor resume
- **Transaction integrity**: MongoDB-first writes, PG best-effort upsert
- **Migrations**: Alembic (production standard)
- **Meta API**: REST via `facebook_business` SDK (GraphQL deferred to separate branch)
- **LLM**: OpenRouter (remote, default) or LM Studio (local, configurable via `LLM_PROVIDER`)
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
| `create-readme` | README.md section creation or revision |
| `supabase-postgres-best-practices` | Query optimization, indexing, advisory lock, batch upsert |
| `docker-expert` | Dockerfile hardening (HEALTHCHECK, non-root user, .dockerignore, production compose) |
| `tdd` | Test-first approach for advisory lock, batch upsert, frontend component tests |
| `improve-codebase-architecture` | Dead code removal, component dedup, dashboard helper extraction |
| `python-packaging` | `pyproject.toml` setup |
| `humanizer` | Polish generated README text to sound less AI-written |
| `github-actions-docs` | CI/CD setup — GitHub Actions workflows for test-on-push |
| `design-taste-frontend` | CSS architecture fixes (design-tokens.css, dark mode) |
| `git-commit` | Conventional commit messages with auto type/scope detection |

### Frontend

#### Structure

```
frontend/
├── .dockerignore                     # Excludes node_modules, .next, .env.local from builds
├── Dockerfile                        # Multi-stage standalone build (ARG API_URL)
├── styles/
│   └── globals.css                  # Tailwind v4 @theme + custom component classes + dark mode vars
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

### Integration & Runtime Bugs Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Backend 500 on startup | `alembic_command.upgrade()` called synchronously inside async startup | Wrapped in `loop.run_in_executor()` thread pool |
| `/api/fetch` 500 | FastAPI validates response body against `-> Dict[str, int]` | Changed to `-> Dict[str, Any]` |
| Ad set sync fails | `targeting` field is a non-serializable `Targeting` SDK object | Added `_serialize()` + `_prepare_record()` in transform pipeline |
| Ad sync fails | Meta API field is `adset_id` (no underscore), model expects `ad_set_id` | Updated field names in `META_DEFAULT_FIELDS` + pipeline maps both |
| Campaign date error | `created_time` etc. are ISO strings from API, PG expects `datetime` | Added `_parse_datetime()` in pipeline, converts to offset-naive UTC |
| Insights API error | `conversion_value` is not a valid field in v22.0 | Removed from default fields |
| Insights API error | `time_range` param passed as string instead of dict | Pass dict directly |
| LLM provider migration | Gemini removed; OpenRouter + LM Studio added | Changed to dual-provider config via `LLM_PROVIDER`, `OPENROUTER_API_KEY`, `LMSTUDIO_BASE_URL` |
| Config file not found | Docker volume mount path mismatch — code looked for `/config/sources.yaml` but volume mounts to `/app/config` | Added `.get()` fallbacks in `meta_api_service.py` |
| Config path resolution | `load_yaml_config` went up 3 directory levels instead of 4 | Now goes up 4 dir levels to find project-root `config/sources.yaml` |
| `settings.meta_ads` empty | Not populated from YAML config on module load | Populated on import with graceful `FileNotFoundError` fallback |
| Missing `UniqueConstraint` | `insights` model lacked `UNIQUE(ad_id, date)` — `ON CONFLICT` upsert would crash | Added `UniqueConstraint(ad_id, date)` |
| LLM prompt DDL mismatch | System prompt used `SERIAL` PK and without `NOT NULL` on `date` | Updated DDL to match actual model: `TEXT PK`, `date NOT NULL` |
| PG partitioning conflict | `PARTITION BY RANGE (date)` on insights — PG requires partition cols in all unique constraints | Removed partitioning (unnecessary at this scale) |
| MongoDB healthcheck | Docker Compose used `mongo` CLI which doesn't exist in MongoDB 7 | Fixed to `mongosh` |
| Missing `__init__.py` | 9 bare Python packages lacked `__init__.py` | Added to all packages |
| Empty directory | `services/llm/` contained no files | Removed |

### Current Status

- All 8 API endpoints work end-to-end ✓
- Real Meta data sync works (3 campaigns, 4 ad sets, 4 ads) ✓
- Chat works: all 3 assignment queries return correct `{answer, sql, data}` ✓
- Data context injection: LLM sees date ranges, campaign names, row counts before generating SQL ✓
- Off-schema queries (e.g. "Tuesday" when no Tuesday data exists) handled via text-only fallback ✓
- Frontend: landing, dashboard, chat, 404 page all load ✓
- Dark mode, mobile nav, error boundaries deployed ✓
- Frontend proxy (`:3000/api/*`) has ECONNRESET — use direct backend for terminal ✓
- **109 backend tests passing**, 0 failing ✓
- **16 frontend tests passing** (1 infra + 15 dashboard-utils) ✓
- **Deprecation warnings**: 5 remaining (all `on_event` lifespan — intentionally skipped, project concludes in 1 week)
- **Insights return 0** — `ad_id` field fixed in transform pipeline; remaining issue may be that Meta account has no insight data, or query level/date range needs adjustment

### What Still Needs Work

Remaining items after this session's completions (CORS, SECRET_KEY, CI/CD, HEALTHCHECK, non-root users, `.dockerignore`, advisory lock, batch upsert, `pyproject.toml`, `API_V1_STR`, ruff, EmptyState dedup, design-tokens deletion, dark mode fix, pre-commit, README sections, SECURITY.md, dashboard helpers):

| Priority | Issue | Detail | Suggested Skill |
|----------|-------|--------|-----------------|
| **High** | **Frontend proxy ECONNRESET** | `network_mode: host` causes Next.js proxy to fail with `socket hang up` for queries >30s. Direct backend `:8000` works 100%. Needs nginx reverse proxy or alternative routing. | `docker-expert` |
| **High** | **No production deployment configs** | No K8s manifests, Helm charts, Terraform, or `docker-compose.prod.yml` | `docker-expert` |
| **High** | **Frontend components untested** | `Header.tsx`, `ThemeToggle.tsx`, `dashboard/page.tsx`, `chat/page.tsx`, `KPICard.tsx`, `EmptyState.tsx`, `LoadingState.tsx`, error boundaries, layouts — all lack tests | `tdd` |
| **Medium** | **Read-only DB user not plumbed** | SECURITY.md documents the `llm_agent` role setup, but LLM service still uses admin DSN. Chat runs in read-only txn as defense-in-depth | `supabase-postgres-best-practices` |
| **Medium** | **`testcontainers` unused** | Library in deps, but all tests use mocks — no real DB integration tests | `tdd` |
| **Low** | **Git audit for `.env`** | Verify `git log --all --diff-filter=A -- .env` that live tokens were never committed | manual |
| **Low** | **Single Alembic migration** | Fine for current schema, needs manual migration for any future change | manual |

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Databases | PostgreSQL 16 (analytics), MongoDB 7 (staging) |
| Meta API | `facebook_business` SDK (REST) |
| LLM | OpenRouter or LM Studio (configurable via `LLM_PROVIDER`) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
| Testing | pytest, pytest-asyncio, testcontainers, httpx_mock / responses |
| Infrastructure | Docker Compose (4 services) |
| Config | YAML (`config/sources.yaml`) |

## Environment Variables (.env.example)

```env
META_ACCESS_TOKEN=<meta-api-access-token>
META_AD_ACCOUNT_ID=act_<account-id>
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-<openrouter-api-key>
POSTGRES_DSN=postgresql+asyncpg://groove:groove@localhost:5432/groove
MONGODB_URI=mongodb://localhost:27017/groove
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
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

# Chat (requires LLM provider configured via .env and data to return meaningful results)
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
2. **LLM provider**: Set `LLM_PROVIDER=openrouter` (requires `OPENROUTER_API_KEY`) or `LLM_PROVIDER=lmstudio` (requires LM Studio running on `localhost:1234`). Default is `openrouter`.
3. **APScheduler + multi-worker**: The PG advisory lock prevents double-fires. For production, use a dedicated scheduler container.
4. **MongoDB vs JSONB kept separate** — not merged per PRD decision. If asked why, refer to DECISIONS.md #1.
5. **GraphQL rejected** — REST/SDK chosen. See DECISIONS.md #15 for rationale.
6. **Full stack runs via docker compose**: `docker compose up --build` starts all 4 services (postgres, mongodb, backend, frontend). Frontend at :3000 proxying API to backend at :8000.
7. **LLM uses 2-call pattern**: SQL gen → execute → summarize. With LM Studio locally, queries take ~1-2 min (model reasoning). With OpenRouter (cloud), latency drops to 2-15s.
8. **Frontend design system**: DESIGN.md is the source of truth. Tailwind v4 `@theme` block in `styles/globals.css` implements it.
9. **Frontend Docker build**: Requires `API_URL` build arg (set in docker-compose.yml). The frontend `next.config.ts` reads this at build time for the rewrites destination. During `npm run dev` it reads from `.env.local`.
10. **Client component patterns**: Chat page uses `"use client"` for interactive state. Dashboard is also `"use client"` (needs state for filters/pagination/sync). Landing page remains a server component.
11. **Dashboard KPIs**: Computed client-side from `/api/insights` data (full fetch with dynamic 30d-ago date). For large datasets, add a dedicated aggregate endpoint or server-side aggregation.
12. **Insights model**: Uses `Text PK` (UUID string), not `SERIAL`. The `UniqueConstraint(ad_id, date)` enables the `ON CONFLICT` upsert. Partitioning was removed (conflicts with PG's requirement that partition columns appear in all unique constraints).
13. **`settings.meta_ads`**: Now populated automatically from `config/sources.yaml` on import. Gracefully falls back to empty dict if YAML file is missing (useful for CI/testing).
14. **LLM provider**: Set `LLM_PROVIDER=openrouter` (remote, default) or `LLM_PROVIDER=lmstudio` (local). For OpenRouter, set `OPENROUTER_API_KEY` and optionally `OPENROUTER_MODEL`. For LM Studio, set `LMSTUDIO_BASE_URL` (default: `http://localhost:1234/v1`) and `LMSTUDIO_MODEL`.
15. **facebook-business SDK fields**: Field names use underscore format (e.g. `adset_id`, `date_start`). The SDK returns raw API data as `dict()` — JSON/JSONB columns in PostgreSQL require `json.dumps()` serialization via the transform pipeline before upsert. Date/time strings are parsed to offset-naive UTC `datetime` objects.
16. **Backend container runs with `--reload`** for faster iteration during development. `docker compose restart backend` after adding new dependencies (volumes are mounted, so code changes trigger auto-reload). Beware of mid-request interruptions during heavy sync operations.
