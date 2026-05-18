# Product Requirements Document: Meta Ads Data Pipeline + NL Chatbot

## Overview

Build a production-ready service that integrates with the Meta Marketing API, fetches ads data into a persistent datastore, and provides a natural language chatbot interface for querying the data.

## Part 1: Meta Marketing API Data Pipeline

### Objectives

- Fetch campaigns, ad sets, ads, and daily insights from the Meta Marketing API
- Store raw API responses in MongoDB (staging/data lake)
- Transform and upsert normalized data into PostgreSQL (analytics)
- Support both manual (API) and scheduled (daily cron) syncs
- Handle pagination, rate limits, and partial failures gracefully

### Entities

| Entity | Source | Fields |
|--------|--------|--------|
| Campaigns | `/{ad-account-id}/campaigns` | id, name, status, objective, daily_budget, lifetime_budget, created_time, start_time, stop_time |
| Ad Sets | `/{ad-account-id}/adsets` | id, campaign_id, name, status, daily_budget, lifetime_budget, targeting, bid_strategy, created_time |
| Ads | `/{ad-account-id}/ads` | id, ad_set_id, name, status, creative, created_time |
| Insights | `/{ad-account-id}/insights` | date, impressions, clicks, spend, reach, frequency, ctr, cpc, cpm, conversions, conversion_value |

### Data Flow

```
Meta API → DataSyncService → MongoDB (raw JSON) → Transform → PostgreSQL
                        ↑                              ↓
              POST /api/fetch                    Read APIs & Chat
              APScheduler (daily)
```

### Pipeline Characteristics

- **Idempotent upserts**: `INSERT ... ON CONFLICT DO UPDATE`
- **Resumable pagination**: Cursor-based, resumes from last successful page
- **Rate limit handling**: Exponential backoff with jitter on 429
- **Concurrent sync prevention**: PostgreSQL advisory lock
- **Error resilience**: MongoDB write always completes first; failed transforms recover on next sync from raw data

## Part 2: Natural Language Chatbot

### Objectives

- Allow users to query ads data in plain English
- Integrate Gemini LLM for text-to-SQL generation
- Return human-readable summaries with generated SQL visible
- Handle ambiguous, empty, or out-of-scope queries gracefully

### Flow

```
User Query → LLM Service → Gemini (SQL gen) → SQL Validator → PostgreSQL → Gemini (summarize) → Response
```

### LLM Service Design

#### System Prompt (3 components)

1. **Role definition**: "You are a Meta Ads data analyst with PostgreSQL access..."
2. **Schema injection**: Full DDL of all tables + 4 example queries with translations
3. **Constraints**:
   - Generate SELECT only (regex block on DDL/DML keywords)
   - Use column names from schema only
   - Summarize results in 1-2 sentences with currency formatting
   - If data doesn't exist, say so honestly
   - If query is ambiguous, ask for clarification

#### Error Handling

| Scenario | Response |
|----------|----------|
| Empty results | "No data found for your query. Try a different date range or campaign." |
| Invalid SQL | Retry once with error context. If still fails: "I couldn't generate a valid query. Try rephrasing." |
| Out-of-scope entity | "I can only answer questions about campaigns, ad sets, ads, and insights." |
| DB connection error | "The database is currently unavailable. Please try again." |

#### SQL Validation Pipeline

1. Strip comments and whitespace
2. Reject if contains DDL/DML keywords (DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, EXECUTE)
3. Must start with SELECT (or WITH for CTEs)
4. Reject multi-statement queries (semicolons in body)
5. Execute in read-only transaction
6. On failure: return error to Gemini for auto-repair (1 retry)

## System Architecture

```
┌────────────┐    ┌────────────────────────────┐    ┌──────────────┐
│  Next.js   │    │         FastAPI             │    │  PostgreSQL  │
│  :3000     │───▶│         :8000               │───▶│  :5432       │
│            │    │                             │    │              │
│  Dashboard │    │  Fetch Router  Chat Router  │    │  analytics   │
│  Chat Page │    │  DataSyncSvc   LLM Service    │    │              │
└────────────┘    │  MetaAPISvc    SQL Validator │    └──────────────┘
                  │  Config (YAML)               │
                  │  APScheduler                 │    ┌──────────────┐
                  │                              │───▶│  MongoDB     │
                  └────────────────────────────┘    │  :27017      │
                                                    │  raw staging │
                                                    └──────────────┘
```

## Data Model

### PostgreSQL

```sql
campaigns (id TEXT PK, name, status, objective, daily_budget, lifetime_budget, created_time, start_time, stop_time, created_at, updated_at)
ad_sets   (id TEXT PK, campaign_id FK, name, status, daily_budget, lifetime_budget, targeting JSONB, bid_strategy, created_time, created_at, updated_at)
ads       (id TEXT PK, ad_set_id FK, name, status, creative JSONB, created_time, created_at, updated_at)
insights  (id SERIAL PK, ad_id FK, date DATE, impressions INT, clicks INT, spend NUMERIC, reach INT, frequency NUMERIC, ctr NUMERIC, cpc NUMERIC, cpm NUMERIC, conversions INT, conversion_value NUMERIC, UNIQUE(ad_id, date), created_at, updated_at)
```

### MongoDB

```
campaigns_raw : One document per API response object
ad_sets_raw   : One document per API response object
ads_raw       : One document per API response object
insights_raw  : One document per API response object
```

## API Endpoints

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

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Databases | PostgreSQL 16 (analytics), MongoDB 7 (staging) |
| LLM | Gemini (Google AI) via `google-genai-sdk` |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Testing | pytest, pytest-asyncio, testcontainers, httpx_mock |
| Infrastructure | Docker Compose, APScheduler |
| Config | YAML (`config/sources.yaml`) |

## Testing Strategy (TDD)

Vertical-slice tracer bullets: one test → one implementation → repeat.

### Test Plan

| Order | Test | Scope |
|-------|------|-------|
| 1 | YAML config loads correctly | Unit |
| 2 | Meta API fetches campaigns (mocked HTTP) | Unit |
| 3 | Raw data saves to MongoDB | Integration |
| 4 | Transform normalizes raw campaign to typed record | Unit |
| 5 | Upsert to PostgreSQL is idempotent | Integration |
| 6 | GET /api/campaigns returns data | Integration |
| 7 | POST /api/fetch orchestrates end-to-end | Integration |
| 8 | LLM generates valid SQL from query | Unit (mocked LLM) |
| 9 | SQL validator rejects DDL statements | Unit |
| 10 | POST /api/chat returns answer | Integration |
| 11 | Scheduler fires daily sync | Unit |
| 12 | Chat handles empty data gracefully | Integration |

## Infrastructure

### Docker Compose

| Service | Image | Port |
|---------|-------|------|
| postgres | postgres:16-alpine | 5432 |
| mongodb | mongo:7 | 27017 |
| backend | Python 3.12 (Dockerfile) | 8000 |
| frontend | Node 20 (Dockerfile) | 3000 |

### Scheduling

- **APScheduler** in FastAPI process, daily at midnight
- **Database-level advisory lock** to prevent concurrent executions (critical with multi-worker scaling)
- Manual trigger via `POST /api/fetch`

### Configuration

```yaml
# config/sources.yaml
meta_ads:
  api_version: v22.0
  fields:
    campaigns: [id, name, status, objective, daily_budget, lifetime_budget, created_time, start_time, stop_time]
    ad_sets: [id, name, campaign_id, status, daily_budget, lifetime_budget, targeting, bid_strategy, created_time]
    ads: [id, name, ad_set_id, status, creative, created_time]
    insights: [impressions, clicks, spend, reach, frequency, ctr, cpc, cpm, conversions, conversion_value]
  insights_time_range_days: 30
```

## Documentation Requirements

### README.md will include

- Setup and run instructions
- Assumptions, design choices, and limitations
- Prompt engineering explanation
- Security considerations (SQL injection mitigations)
- Scaling strategy

### Prompt Engineering Section

```
System prompt struture: role definition → schema DDL → example queries → constraints.
Design rationale: The LLM sees exact column names ensuring valid SQL generation.
Few-shot examples demonstrate expected query format and output style.
```

### Security Section

```
Risks:
- Malicious user prompts generating dangerous SQL
- Prompt injection overriding system instructions

Mitigations:
- Pre-execution regex validation blocks all DDL/DML
- Read-only transaction wrapping
- PostgreSQL user with SELECT-only grants (production)
- Multi-statement rejection
- Error messages don't leak raw DB errors
```

### Scaling Section

```
Current approach: Schema-only injection (DDL), aggregate queries, pre-computed materials.

Millions-of-rows strategy:
- Keyword-based table selection (only inject relevant DDL)
- LLM generates aggregate queries first, then drill-down
- Pre-computed daily/weekly materialized views
- Query timeout middleware (30s)
- Future: vector-store-based table selection for wider schemas
```

## Frontend (DESIGN.md)

A dedicated `DESIGN.md` will document the component tree, layout grid, color palette, typography, and interaction states. Implemented using the `frontend-design` skill.

### Pages

1. **Dashboard (`/`)** — Campaigns table (name, status, objective, budget) + KPI summary cards (total spend, impressions, clicks)
2. **Chat (`/chat`)** — Full message interface with collapsible SQL blocks

## Assumptions & Limitations

### Assumptions

- Meta API token has `ads_read` permission
- Single ad account (no multi-account support)
- Daily insights granularity is sufficient
- MongoDB for staging/audit, PostgreSQL for analytics
- No authentication on the REST API (local dev)

### Limitations

- No real-time sync (daily cron + manual only)
- No multi-account aggregation
- No historical backfill beyond what Meta API provides
- No pagination streaming for very large syncs (memory-bound per request)
- No rate-limit budget management across multiple sync schedules
