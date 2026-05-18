# Security

## Read-Only PostgreSQL User for LLM Service

In production, the LLM service should use a separate PostgreSQL user with SELECT-only privileges to prevent any possible SQL mutation, even if the SQL validator is bypassed.

### Setup

Run this SQL against your PostgreSQL instance:

```sql
CREATE ROLE llm_agent WITH LOGIN PASSWORD '<strong-password>';
GRANT CONNECT ON DATABASE groove TO llm_agent;
GRANT USAGE ON SCHEMA public TO llm_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO llm_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO llm_agent;
```

### Configuration

Add the following to your `.env` file:

```env
POSTGRES_READONLY_DSN=postgresql+asyncpg://llm_agent:<password>@postgres:5432/groove
```

The data sync service continues to use the admin `POSTGRES_DSN` with full DML privileges.

## CORS

CORS origins are configured via the `CORS_ORIGINS` environment variable (comma-separated list). Default allows local development origins.

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Secret Key

Override `SECRET_KEY` in production. The dev default is `"dev-secret-key-change-in-production"` and will trigger a warning on startup.

## SQL Injection Mitigations

See the Security section in `README.md` for the full defense-in-depth strategy (regex validation, read-only transactions, input sanitization, multi-statement rejection).
