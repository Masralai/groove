# Groove: Meta Ads Data Pipeline + NL Chatbot

Production-ready service integrating with the Meta Marketing API to fetch ads data into PostgreSQL + MongoDB, with a natural language chatbot powered by OpenRouter (remote) or LM Studio (local).

## Quickstart

```bash
# 1. Clone, configure, and start everything
cp .env.example .env
# Edit .env — paste your Meta access token, ad account ID, and OpenRouter API key
docker compose up --build
```

Once running, open **[http://localhost:3000](http://localhost:3000)** in your browser:

| Page | What you can do |
|------|----------------|
| **Dashboard** (`/dashboard`) | View KPI cards (spend, impressions, clicks, CTR), filter campaigns by status, change the date range, trigger a data sync |
| **Chat** (`/chat`) | Ask questions in plain English — "How many campaigns?" or "Total spend?" |

Or query from the terminal:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"How many campaigns do we have?"}'
```

Returns:

```json
{"answer": "There are 3 campaigns in total.", "sql": "SELECT COUNT(*) FROM campaigns", "data": [{"campaign_count": 3}]}
```

- **answer** — plain-English explanation
- **sql** — the generated PostgreSQL query (or `null` if text-only)
- **data** — query result rows

> **Note**: With OpenRouter (default), typical response time is **2–15s** per query (free tier may spike to 30–50s). With LM Studio locally, queries take **1–2 minutes**. The web UI is at [http://localhost:3000/chat](http://localhost:3000/chat).

## Overview

Build a production-ready service that integrates with the Meta Marketing API, fetches ads data into a persistent datastore, and provides a natural language chatbot interface for querying the data.

The system consists of two main parts:

1. **Meta Marketing API Data Pipeline**: Fetches campaigns, ad sets, ads, and daily insights from Meta Marketing API, stores raw responses in MongoDB, and transforms/upserts normalized data into PostgreSQL
2. **Natural Language Chatbot**: Allows users to query ads data in plain English using OpenRouter (remote) or LM Studio (local) for text-to-SQL generation

## Architecture

```
┌────────────┐    ┌─────────────────────────────┐    ┌──────────────┐
│  Next.js   │    │         FastAPI             │    │  PostgreSQL  │
│  :3000     │───▶│         :8000               │───▶│  :5432       │
│            │    │                             │    │              │
│  Dashboard │    │  Fetch Router  Chat Router  │    │  analytics   │
│  Chat Page │    │  DataSyncSvc   LLM Service  │    │  (4 tables)  │
└────────────┘    │  MetaAPISvc    SQL Validator│    └──────────────┘
                  │  Config (YAML)              │
                  │  APScheduler                │    ┌──────────────┐
                  │                             │───▶│  MongoDB     │
                  └─────────────────────────────┘    │  :27017      │
                                                     │  raw staging │
                                                     └──────────────┘
```

### Services

- **MetaAPI Service**: REST calls to Graph API via `facebook_business` SDK, pagination, rate-limit backoff
- **Data Sync Service**: Orchestrates fetch → MongoDB → transform → PostgreSQL upsert
- **Transform Pipeline**: Raw JSON → typed records with field mapping
- **LLM Service**: OpenRouter/LM Studio integration, text-to-SQL, result summarization
- **SQL Validator**: Multi-layer validation (regex block on DDL, single-statement enforcement, read-only txn)

## Data Model

### PostgreSQL (Analytics)

```sql
campaigns (id TEXT PK, name, status, objective, daily_budget, lifetime_budget, created_time, start_time, stop_time, created_at, updated_at)
ad_sets   (id TEXT PK, campaign_id FK, name, status, daily_budget, lifetime_budget, targeting JSONB, bid_strategy, created_time, created_at, updated_at)
ads       (id TEXT PK, ad_set_id FK, name, status, creative JSONB, created_time, created_at, updated_at)
insights  (id TEXT PK, ad_id FK, date DATE, impressions INT, clicks INT, spend NUMERIC, reach INT, frequency NUMERIC, ctr NUMERIC, cpc NUMERIC, cpm NUMERIC, conversions INT, conversion_value NUMERIC, UNIQUE(ad_id, date), created_at, updated_at)
```

### MongoDB (Raw Staging)

- `campaigns_raw`: One document per API response object
- `ad_sets_raw`: One document per API response object
- `ads_raw`: One document per API response object
- `insights_raw`: One document per API response object

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
| GET | `/api/health` | Health check |

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Databases | PostgreSQL 16 (analytics), MongoDB 7 (staging) |
| Meta API | `facebook_business` SDK (REST) |
| LLM | OpenRouter or LM Studio (configurable via `LLM_PROVIDER`) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
| Testing | pytest, pytest-asyncio, testcontainers, respx |
| Infrastructure | Docker Compose (4 services) |
| Config | YAML (`config/sources.yaml`) |

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Meta Marketing API access token (generate one at [developers.facebook.com/tools/access_token](https://developers.facebook.com/tools/access_token/); short-lived tokens expire hourly — use a long-lived token or refresh as needed)
- OpenRouter API key (for remote LLM) **or** LM Studio running locally with a compatible model (e.g. `gemma-4-E4B-it-GGUF` on port 1234)

### Installation Steps

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd groove
   ```

2. Create environment file from template:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` to add your credentials:

    ```env
    META_ACCESS_TOKEN=<your-meta-access-token>
    META_AD_ACCOUNT_ID=act_<your-account-id>
    LLM_PROVIDER=openrouter
    OPENROUTER_API_KEY=sk-or-v1-<your-openrouter-api-key>
    POSTGRES_DSN=postgresql+asyncpg://groove:groove@localhost:5432/groove
    MONGODB_URI=mongodb://localhost:27017/groove
    ```

4. (Optional) The frontend auto-detects the backend URL. To override, set `NEXT_PUBLIC_API_URL` in `frontend/.env`:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. Build and start the services:

   ```bash
   docker compose up --build
   ```

## Environment Configuration

The following environment variables are required:

| Variable | Description | Example |
|----------|-------------|---------|
| `META_ACCESS_TOKEN` | Meta Marketing API access token | `EAAB...` |
| `META_AD_ACCOUNT_ID` | Meta Ad Account ID | `act_123456789` |
| `LLM_PROVIDER` | LLM provider: `openrouter` (remote) or `lmstudio` (local) | `openrouter` |
| `OPENROUTER_API_KEY` | OpenRouter API key (required when `LLM_PROVIDER=openrouter`) | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | OpenRouter model | `nvidia/nemotron-3-super-120b-a12b:free` |
| `LMSTUDIO_BASE_URL` | LM Studio server URL (required when `LLM_PROVIDER=lmstudio`) | `http://localhost:1234/v1` |
| `LMSTUDIO_MODEL` | LM Studio model name | `gemma-4-e4b` |
| `POSTGRES_DSN` | PostgreSQL connection string | `postgresql+asyncpg://groove:groove@localhost:5432/groove` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/groove` |

Optional variables with defaults in code:

- `SECRET_KEY`: For session security (default: "dev-secret-key-change-in-production")
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 8 days)
- `POSTGRES_READONLY_DSN`: Read-only PostgreSQL user for LLM service (default: uses same as `POSTGRES_DSN`)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: `http://localhost:3000,http://localhost:8000,http://frontend:3000`)

## Running the Application

### Using Docker Compose (Recommended)

```bash
# Start all services
docker compose up --build

# Check health
curl http://localhost:8000/api/health

# Trigger manual sync
curl -X POST http://localhost:8000/api/fetch

# Check campaigns
curl http://localhost:8000/api/campaigns

# Use chatbot
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Which campaign spent the most last week?"}'
```

### Local Development

> **Prerequisite**: Postgres (port 5432) and MongoDB (port 27017) must be running before starting the backend. The easiest way is via Docker:
>
> ```bash
> docker compose up -d postgres mongodb
> ```
>
> This starts both databases as daemons. They stay up until you run `docker compose down`.

```bash
# Backend (requires Postgres + MongoDB to already be running)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Override DB hostnames for local dev (Docker names don't resolve on host)
POSTGRES_DSN="postgresql+asyncpg://groove:groove@localhost:5432/groove" \
MONGODB_URI="mongodb://localhost:27017/groove" \
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal, after backend is ready)
cd frontend
npm install
npm run dev
```

Client-side pages fetch the backend directly at `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`). Next.js rewrites for `/api/*` are still configured and work for server-side requests — useful for verifying the chain:

```bash
curl http://localhost:3000/api/health
```

## Testing

Run the test suite:

```bash
# Using Docker (recommended for consistency)
docker compose exec backend pytest

# Local backend testing
cd backend
pytest
```

Test suite includes:

- Unit tests for configuration loading
- Unit tests for Meta API service (with mocked HTTP)
- Integration tests for MongoDB persistence
- Integration tests for PostgreSQL upsert operations
- Integration tests for API endpoints
- Unit tests for LLM SQL generation
- Unit tests for SQL validation
- Integration tests for full chat flow

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|------|
| Backend won't start | Missing env vars or database not ready | Run `docker compose logs backend` and check for missing credentials |
| Dashboard shows "No campaigns found" | Data hasn't been synced yet | Run `curl -X POST http://localhost:8000/api/fetch` or click "Sync Data" in the dashboard |
| Chat returns `null` for SQL | LLM couldn't generate a valid query | Check the query makes sense with available data (date ranges, campaign names). Try rephrasing. |
| Chat returns 500 / empty answers | LLM provider misconfigured | Verify `LLM_PROVIDER` in `.env` matches your setup and the API key is valid. Run `curl http://localhost:8000/api/health`. |
| Frontend shows errors on load | `NEXT_PUBLIC_API_URL` points to wrong backend | Ensure `frontend/.env` has `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| Meta sync fails (401) | Access token expired | Refresh your token at [developers.facebook.com/tools/access_token](https://developers.facebook.com/tools/access_token/) |
| Slow chat responses | Free OpenRouter throttling or slow hardware | Switch to a paid OpenRouter model (`OPENROUTER_MODEL`) or use LM Studio with a smaller model |


## Prompt Engineering

The LLM uses a structured 3-part system prompt for reliable SQL generation:

1. **Role definition**: "You are a Meta Ads data analyst with PostgreSQL access..."
2. **Schema injection**: Full DDL of all 4 tables (`campaigns`, `ad_sets`, `ads`, `insights`) plus 4 example queries with natural language translations
3. **Constraints**:
   - Generate SELECT only (regex block on DDL/DML keywords)
   - Use column names from schema only
   - Summarize results in 1-2 sentences with currency formatting
   - If data doesn't exist, say so honestly
   - If query is ambiguous, ask for clarification

**Design rationale**: The LLM sees exact column names ensuring valid SQL generation. Few-shot examples demonstrate expected query format and output style. Schema-only injection keeps context small and focused.

## Security

| Risk | Mitigation |
|------|-----------|
| Malicious prompts generating dangerous SQL | Pre-execution regex validation blocks all DDL/DML (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `EXECUTE`) |
| SQL injection bypassing validator | Read-only transaction wrapping; PostgreSQL enforces no-write at engine level |
| Prompt injection overriding instructions | Input sanitization strips instruction injection patterns ("ignore", "forget instructions") |
| Credential exposure | `.env` in `.gitignore`; production uses environment variables, not checked-in configs |
| Multi-statement attacks | Reject queries with semicolons in the body (after string-literal stripping) |

**Production recommendation**: Create a dedicated PostgreSQL user with SELECT-only grants on the 4 analytics tables and wire it as `POSTGRES_READONLY_DSN` for the LLM service. See `SECURITY.md` for setup details.

## Scaling

**Current approach**: Schema-only injection (DDL), aggregate queries, pre-computed materials. Full DDL for 4 tables fits well within modern LLM context windows.

**Millions-of-rows strategy**:

- Keyword-based table selection (only inject relevant DDL based on query terms)
- LLM generates aggregate queries first, then drill-down
- Pre-computed daily/weekly materialized views
- Query timeout middleware (30s)
- Future: vector-store-based table selection for wider schemas

For connection scaling, the backend uses a pool of 20 connections (max overflow 10) with a 10-second pool timeout. The PostgreSQL advisory lock prevents concurrent sync in multi-worker deployments.

