# Groove: Meta Ads Data Pipeline + NL Chatbot

Production-ready service integrating with the Meta Marketing API to fetch ads data into PostgreSQL + MongoDB, with a natural language chatbot powered by Gemini.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [API Endpoints](#api-endpoints)
- [Technology Stack](#technology-stack)
- [Setup and Installation](#setup-and-installation)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Status](#project-status)
- [Future Work](#future-work)
- [Gotchas & Notes](#gotchas--notes)

## Overview

Build a production-ready service that integrates with the Meta Marketing API, fetches ads data into a persistent datastore, and provides a natural language chatbot interface for querying the data.

The system consists of two main parts:
1. **Meta Marketing API Data Pipeline**: Fetches campaigns, ad sets, ads, and daily insights from Meta Marketing API, stores raw responses in MongoDB, and transforms/upserts normalized data into PostgreSQL
2. **Natural Language Chatbot**: Allows users to query ads data in plain English using Gemini LLM for text-to-SQL generation

## Architecture

```
┌────────────┐    ┌─────────────────────────────┐    ┌──────────────┐
│  Next.js   │    │         FastAPI             │    │  PostgreSQL  │
│  :3000     │───▶│         :8000               │───▶│  :5432       │
│            │    │                             │    │              │
│  Dashboard │    │  Fetch Router  Chat Router  │    │  analytics   │
│  Chat Page │    │  DataSyncSvc   LLM Service    │    │  (4 tables)  │
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
- **LLM Service**: Gemini integration, text-to-SQL, result summarization
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
| LLM | Gemini 2.5 Flash via `google-genai` |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 |
| Testing | pytest, pytest-asyncio, testcontainers, httpx_mock / responses |
| Infrastructure | Docker Compose (4 services) |
| Config | YAML (`config/sources.yaml`) |

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (for local development)
- Meta Marketing API access token
- Gemini API key from Google AI Studio

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
   GEMINI_API_KEY=<your-gemini-api-key>
   POSTGRES_DSN=postgresql+asyncpg://groove:groove@postgres:5432/groove
   MONGODB_URI=mongodb://mongodb:27017/groove
   ```

4. Build and start the services:
   ```bash
   docker compose up --build
   ```

## Environment Configuration

The following environment variables are required:

| Variable | Description | Example |
|----------|-------------|---------|
| `META_ACCESS_TOKEN` | Meta Marketing API access token | `EAAB...` |
| `META_AD_ACCOUNT_ID` | Meta Ad Account ID | `act_123456789` |
| `GEMINI_API_KEY` | Gemini API key from Google AI Studio | `AIza...` |
| `POSTGRES_DSN` | PostgreSQL connection string | `postgresql+asyncpg://groove:groove@postgres:5432/groove` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://mongodb:27017/groove` |

Optional variables with defaults in code:
- `SECRET_KEY`: For session security (default: "dev-secret-key-change-in-production")
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 8 days)

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
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
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

## Gotchas & Notes

1. **Meta API creds**: Needed for `POST /api/fetch` to work. Without them, the chat can still answer based on seeded/empty DB data.
2. **Gemini API key**: Free from Google AI Studio. Without it, the chat endpoint returns errors.
3. **APScheduler + multi-worker**: The PG advisory lock prevents double-fires. For production, use a dedicated scheduler container.
4. **MongoDB vs JSONB kept separate** — not merged per PRD decision. If asked why, refer to DECISIONS.md #1.
5. **GraphQL rejected** — REST/SDK chosen. See DECISIONS.md #15 for rationale.
6. **Frontend DESIGN.md**: See `DESIGN.md` at project root for the design system reference (Grafbase-inspired engineering aesthetic). The Tailwind v4 `@theme` block in `frontend/styles/globals.css` implements these tokens.
7. **LLM uses 2-call pattern**: SQL gen → execute → summarize. Acceptable latency (3-4s total) for single-user tool.
8. **Production PostgreSQL user**: For security, use a dedicated read-only user for the LLM service (see DECISIONS.md #11).
9. **Frontend docker-compose**: The `frontend` service in `docker-compose.yml` builds with `API_URL=http://backend:8000` and exposes port 3000. All four services (postgres, mongodb, backend, frontend) start together with `docker compose up --build`.
10. **Full-stack verification**: The frontend at `localhost:3000` proxies `/api/*` to the backend via Next.js rewrites. `curl localhost:3000/api/health` works without hitting the backend directly.
