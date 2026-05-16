# Handover: Meta Ads Data Pipeline + NL Chatbot

## Project Overview

Production-ready service integrating with the Meta Marketing API to fetch ads data (campaigns, ad sets, ads, insights) into PostgreSQL + MongoDB, with a natural language chatbot powered by Gemini.

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

**Phase 4: LLM Agent + Chat** - COMPLETED
- LLM Agent service with Gemini integration for text-to-SQL generation and result summarization
- SQL Validator service with multi-layered protection (regex block, single-statement enforcement, read-only transactions)
- Chat endpoint (/api/chat) for natural language queries with error handling and retry logic
- System prompt engineering with schema injection and few-shot examples
- Comprehensive unit and integration tests for LLM agent, SQL validator, and chat endpoint

**Phase 5: Frontend** - COMPLETED
- Next.js 16 project with TypeScript, Tailwind CSS v4, App Router
- Design system tokens from DESIGN.md implemented via Tailwind v4 `@theme` block
- Reusable component library (KPICard, EmptyState, LoadingState)
- Landing page (`/`) — Hero with CTAs, feature cards, footer
- Dashboard page (`/dashboard`) — KPI summary cards (4 metrics) + campaigns table with status badges, pagination, sync button
- Chat page (`/chat`) — Full NL interface with message history, collapsible SQL blocks, loading/error states, recent queries sidebar
- Sticky header navigation with logo and nav links
- API proxy via next.config.ts rewrites (configurable `NEXT_PUBLIC_API_URL`)
- Accessibility: aria-labels, focus-visible rings, reduced-motion support, proper heading hierarchy
- Micro-interactions: hover-lift on cards, 200ms transitions, loading skeletons, bounce animation for AI "thinking"
- `.env.local` with backend URL for development

## Architecture

```
┌────────────┐    ┌──────────────────────────────┐    ┌──────────────┐
│  Next.js   │    │         FastAPI              │    │  PostgreSQL  │
│  :3000     │───▶│         :8000                │───▶│  :5432       │
│            │    │                              │    │              │
│  Dashboard │    │  Fetch Router  Chat Router   │    │  analytics   │
│  Chat Page │    │  DataSyncSvc   LLM Agent     │    │  (4 tables)  │
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
| `frontend-design` | Phase 5 — Design system extension or new page creation |
| `framer-motion-animator` | Phase 5 post-completion — Chat message entrance animations, page transitions |
| `high-end-visual-design` | Phase 5 post-completion — Premium animation/refinement pass |
| `ui-ux-pro-max` | Phase 5 post-completion — Accessibility audit, component refinement |
| `docker-expert` | Phase 5 pending — Dockerfile for frontend service |
| `create-readme` | Phase 6 — Generate/update README.md |
| `supabase-postgres-best-practices` | Any phase — Query optimization, indexing |

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

### Phase 4: LLM Agent + Chat - COMPLETED

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

### Phase 5: Frontend - COMPLETED

**Skills used:** `ui-ux-pro-max` for component architecture and accessibility; `high-end-visual-design` for premium styling (design system adapted from Grafbase reference)

| Step | Status | What |
|------|--------|------|
| 1 | COMPLETED | DESIGN.md adapted for Meta Ads dashboard (`/`) and chat (`/chat`) pages |
| 2 | COMPLETED | Next.js 16 app with Tailwind v4, TypeScript, App Router implemented |
| 3 | **PENDING** | Dockerfile for frontend — needs to be added to docker-compose.yml |
| 4 | **PENDING** | API integration with live backend — chat page calls `/api/chat` via proxy but needs real backend running. Dashboard uses mock/static data currently |

#### Frontend Structure

```
frontend/
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
│       │   └── page.tsx             # KPI cards + campaigns table (server component)
│       ├── globals.css               # Root Tailwind import
│       ├── layout.tsx                # Root layout with Inter font + Header
│       └── page.tsx                  # Landing page
├── src/components/
│   ├── KPICard.tsx                   # Reusable metric card component
│   ├── EmptyState.tsx                # Empty data state with action
│   └── LoadingState.tsx              # Card + table skeleton loaders
├── next.config.ts                    # API proxy rewrites → FastAPI :8000
├── .env.local                        # NEXT_PUBLIC_API_URL=http://localhost:8000
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
| `/dashboard` | Server component | 4 KPI cards (TPC, Impressions, Clicks, CTR), campaigns table with status filter & pagination |
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

#### What Still Needs Work (for next agent)

1. **Dockerfile for frontend** — Add Dockerfile and docker-compose service for the Next.js app
2. **Live API integration** — Dashboard currently shows static mock data; needs to fetch from GET `/api/campaigns` and GET `/api/insights`
3. **Chat API connection** — Chat page proxies POST `/api/chat` via Next.js rewrites; verify it works with running backend
4. **Mobile optimization** — Test and fine-tune responsive breakpoints for 375px and landscape
5. **Dark mode** — Not yet implemented; DESIGN.md is light-only but could be extended
6. **Error boundaries** — Add React error boundaries for client-side rendering failures
7. **Animations** — Chat message entrance animations, page transitions (consider framer-motion)

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
# Start backend
docker compose up --build

# Check health
curl http://localhost:8000/health

# In a separate terminal, start frontend
cd frontend && npm run dev

# Frontend will be at http://localhost:3000

# Trigger sync (requires valid Meta API credentials)
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

# Run tests (inside container)
docker compose exec backend pytest
```

## Gotchas & Notes

1. **Meta API creds**: Needed for `POST /api/fetch` to work. Without them, the chat can still answer based on seeded/empty DB data.
2. **Gemini API key**: Free from Google AI Studio. Without it, the chat endpoint returns errors.
3. **APScheduler + multi-worker**: The PG advisory lock prevents double-fires. For production, use a dedicated scheduler container.
4. **MongoDB vs JSONB kept separate** — not merged per PRD decision. If asked why, refer to DECISIONS.md #1.
5. **GraphQL rejected** — REST/SDK chosen. See DECISIONS.md #15 for rationale.
6. **Frontend done**: Next.js 16 with Tailwind v4. API proxy via rewrites. Static mock data on dashboard pending live integration. Chat page calls `/api/chat` which gets proxied to FastAPI.
7. **LLM uses 2-call pattern**: SQL gen → execute → summarize. Acceptable latency (3-4s total) for single-user tool.
8. **Frontend design system**: DESIGN.md is the source of truth. Tailwind v4 `@theme` block in `styles/globals.css` implements it. Run `npm run dev` in `frontend/` for dev server.
9. **No Dockerfile for frontend yet**: Frontend needs to be added to docker-compose.yml when ready. Currently runs via `cd frontend && npm run dev`.
10. **Client component patterns**: Chat page uses `"use client"` for interactive state. Dashboard and Landing pages are server components. When converting dashboard to live data, consider using a client wrapper or async server component with fetch.
