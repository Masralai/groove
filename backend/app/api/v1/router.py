from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_readonly_db
from app.core.fd_logger import FdLogger
from app.repositories.mongo_repository import mongo_repository
from app.repositories.postgres_repository import postgres_repository
from app.services.llm_service import llm_service
from app.services.sync_service import SyncAlreadyRunningError, data_sync_service
from app.services.validation.sql_validator import sql_validator

logger = FdLogger("app.api.v1.router")


def _quota_response(retry_after: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={
            "error": "quota_exceeded",
            "message": message,
            "retry_after": retry_after,
        },
    )


def _check_quota(result: dict) -> JSONResponse | None:
    if result.get("error_type") == "quota_exceeded":
        return _quota_response(
            retry_after=result.get("retry_after", 60),
            message=result["error"],
        )
    return None

api_router = APIRouter()


async def _text_fallback(user_query: str, sql_result: dict | None = None) -> dict:
    """Return a text-only answer when SQL generation/execution fails."""
    llm_response = (sql_result or {}).get("llm_response", "")
    if llm_response:
        return {"answer": llm_response, "sql": None, "data": []}
    summary_result = await llm_service.summarize_results(user_query, "", [])
    return {
        "answer": summary_result.get("summary", "Could not process this query."),
        "sql": None,
        "data": []
    }


# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}

# Schema introspection endpoint
@api_router.get("/schema")
async def get_schema():
    """Get DDL introspection for all database tables."""
    ddl = llm_service._get_schema_ddl()
    return {"schema": ddl}

# Data synchronization endpoints
@api_router.post("/fetch")
async def trigger_data_sync(
    full: bool = Query(False, description="Trigger full re-sync instead of incremental"),
) -> dict[str, Any]:
    """Trigger manual data synchronization."""
    try:
        result = await data_sync_service.sync_all(full_sync=full)
        return {
            "status": "success",
            "data": result,
            "full_sync": full
        }
    except SyncAlreadyRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.get("/fetch/status")
async def get_sync_status() -> dict:
    """Get last sync status and statistics."""
    status = await mongo_repository.get_sync_status()
    return status

# Read API endpoints - Phase 3
@api_router.get("/campaigns")
async def get_campaigns(
    status: str | None = Query(None, description="Filter by campaign status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """Get campaigns with optional filtering and pagination."""
    try:
        campaigns = await postgres_repository.get_campaigns(
            db=db,
            status=status,
            limit=limit,
            offset=offset
        )
        return campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")

@api_router.get("/ads")
async def get_ads(
    campaign_id: str | None = Query(None, description="Filter by campaign ID"),
    status: str | None = Query(None, description="Filter by ad status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """Get ads with optional filtering and pagination."""
    try:
        ads = await postgres_repository.get_ads(
            db=db,
            campaign_id=campaign_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return ads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ads: {str(e)}")

@api_router.get("/insights")
async def get_insights(
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    campaign_id: str | None = Query(None, description="Filter by campaign ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """Get insights with optional filtering and pagination."""
    try:
        insights = await postgres_repository.get_insights(
            db=db,
            date_from=date_from,
            date_to=date_to,
            campaign_id=campaign_id,
            limit=limit,
            offset=offset
        )
        return insights
    except Exception as e:
        logger.error(f"Failed to fetch insights: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Failed to load insight data. Please try again later."
            }
        )

# Chat endpoint - Phase 4
@api_router.post("/chat")
async def chat_with_data(
    query: dict[str, str],
    db: AsyncSession = Depends(get_readonly_db)
):
    """
    Handle natural language queries about ads data.

    Expected input: {"query": "Your question here"}
    Returns: {"answer": str, "sql": str, "data": List[Dict]}
    """
    user_query = query.get("query", "").strip()

    if not user_query:
        return JSONResponse(
            status_code=400,
            content={
                "error": "empty_query",
                "message": "Please enter a question before submitting."
            }
        )

    try:
        # Step 0: Gather data context for LLM
        try:
            date_range = await db.execute(text(
                "SELECT MIN(date), MAX(date) FROM insights"
            ))
            date_row = date_range.fetchone()
            campaigns = await db.execute(text(
                "SELECT name FROM campaigns ORDER BY name"
            ))
            campaign_names = [row[0] for row in campaigns.fetchall()]
            insight_count = await db.execute(text(
                "SELECT COUNT(*) FROM insights"
            ))
            count_row = insight_count.fetchone()
            data_context_parts = []
            if date_row and date_row[0]:
                data_context_parts.append(
                    f"Date range in insights: {date_row[0]} to {date_row[1]}"
                )
            if campaign_names:
                data_context_parts.append(
                    f"Campaigns: {', '.join(campaign_names)}"
                )
            if count_row:
                data_context_parts.append(f"Total insight rows: {count_row[0]}")
            data_context = "\n".join(data_context_parts)
            if data_context:
                logger.info(f"Data context: {data_context}")
        except Exception:
            data_context = ""

        # Step 1: Generate SQL from natural language
        logger.info(f"Generating SQL for query: {user_query}")
        sql_result = await llm_service.generate_sql(user_query, data_context=data_context)

        if not sql_result["success"]:
            quota_resp = _check_quota(sql_result)
            if quota_resp:
                return quota_resp
            logger.info(f"SQL generation failed, using text-only fallback")
            return await _text_fallback(user_query, sql_result)

        generated_sql = sql_result["sql"]
        logger.info(f"Generated SQL: {generated_sql}")

        # Step 2: Validate the generated SQL
        is_valid, validation_error = sql_validator.validate_sql(generated_sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {validation_error}")
            # Try to regenerate with error context
            logger.info("Attempting to regenerate SQL with error context")
            retry_prompt = (
                f"{user_query}\n\nPrevious attempt failed validation: "
                f"{validation_error}. Please correct the SQL."
            )
            retry_result = await llm_service.generate_sql(retry_prompt, use_cache=False)

            if not retry_result["success"]:
                logger.error(f"SQL regeneration failed: {retry_result['error']}")
                quota_resp = _check_quota(retry_result)
                if quota_resp:
                    return quota_resp
                logger.info("Retry SQL generation failed, using text-only fallback")
                return await _text_fallback(user_query)

            generated_sql = retry_result["sql"]
            logger.info(f"Regenerated SQL: {generated_sql}")

            # Validate again
            is_valid, validation_error = sql_validator.validate_sql(generated_sql)
            if not is_valid:
                logger.error(f"SQL validation failed on retry: {validation_error}")
                logger.info("Retry SQL validation failed, using text-only fallback")
                return await _text_fallback(user_query)

        # Step 3: Execute the SQL query
        logger.info(f"Executing SQL: {generated_sql}")
        try:
            await db.execute(text("SET statement_timeout = '30s'"))
            result = await db.execute(text(generated_sql))

            columns = result.keys()
            rows = result.fetchall()
            query_results = [dict(zip(columns, row)) for row in rows]

            logger.info(f"Query executed successfully, returned {len(query_results)} rows")

        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            sanitized_error = sql_validator.sanitize_error_message(str(e))

            logger.info("Attempting to auto-repair SQL with error context")
            repair_prompt = (
                "The previous SQL query failed with error:"
                f" {sanitized_error}\n\nOriginal question:"
                f" {user_query}\n\nPlease generate a corrected SQL query."
            )
            repair_result = await llm_service.generate_sql(repair_prompt, use_cache=False)

            if repair_result["success"]:
                is_valid, validation_error = sql_validator.validate_sql(repair_result["sql"])
                if is_valid:
                    try:
                        await db.execute(text("SET statement_timeout = '30s'"))
                        result = await db.execute(text(repair_result["sql"]))
                        columns = result.keys()
                        rows = result.fetchall()
                        query_results = [dict(zip(columns, row)) for row in rows]
                        generated_sql = repair_result["sql"]
                        logger.info(
                            "Repaired SQL executed successfully, returned"
                            f" {len(query_results)} rows"
                        )
                    except Exception as retry_e:
                        logger.error(f"Repaired SQL also failed: {str(retry_e)}")
                        logger.info("Repair failed, using text-only fallback")
                        return await _text_fallback(user_query)
                else:
                    logger.error(f"Repaired SQL failed validation: {validation_error}")
                    logger.info("Repair validation failed, using text-only fallback")
                    return await _text_fallback(user_query)
            else:
                logger.error(f"Failed to generate repair SQL: {repair_result['error']}")
                quota_resp = _check_quota(repair_result)
                if quota_resp:
                    return quota_resp
                logger.info("Repair SQL generation failed, using text-only fallback")
                return await _text_fallback(user_query)

        # Step 4: Summarize the results
        logger.info("Generating summary of results")
        summary_result = await llm_service.summarize_results(
            user_query, generated_sql, query_results
        )

        if not summary_result["success"]:
            logger.warning(f"Summary generation failed: {summary_result['error']}")
            if not query_results:
                summary = (
                    "No data found for your query. Try a different date range or campaign."
                )
            else:
                summary = (
                    f"Found {len(query_results)} results. Please see the data below"
                    " for details."
                )
        else:
            summary = summary_result["summary"]

        return {
            "answer": summary,
            "sql": generated_sql,
            "data": query_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in chat endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": (
                    "An unexpected error occurred while processing your question."
                    " Please try again."
                )
            }
        )
