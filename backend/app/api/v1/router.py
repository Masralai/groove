from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.sync_service import data_sync_service
from app.core.database import get_db
from app.repositories.postgres_repository import postgres_repository
from app.repositories.mongo_repository import mongo_repository
from app.services.llm_agent_service import llm_agent_service
from app.services.validation.sql_validator import sql_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Any, Dict, List, Optional
from app.models.postgres import Campaign, AdSet, Ad, Insight
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}

# Schema introspection endpoint
@api_router.get("/schema")
async def get_schema():
    """Get DDL introspection for all database tables."""
    ddl = llm_agent_service._get_schema_ddl()
    return {"schema": ddl}

# Data synchronization endpoints
@api_router.post("/fetch")
async def trigger_data_sync(
    full: bool = Query(False, description="Trigger full re-sync instead of incremental"),
) -> Dict[str, Any]:
    """Trigger manual data synchronization."""
    try:
        result = await data_sync_service.sync_all(full_sync=full)
        return {
            "status": "success",
            "data": result,
            "full_sync": full
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.get("/fetch/status")
async def get_sync_status() -> Dict:
    """Get last sync status and statistics."""
    status = await mongo_repository.get_sync_status()
    return status

# Read API endpoints - Phase 3
@api_router.get("/campaigns")
async def get_campaigns(
    status: Optional[str] = Query(None, description="Filter by campaign status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> List[Dict]:
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
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    status: Optional[str] = Query(None, description="Filter by ad status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> List[Dict]:
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
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db)
) -> List[Dict]:
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch insights: {str(e)}")

# Chat endpoint - Phase 4
@api_router.post("/chat")
async def chat_with_data(
    query: Dict[str, str],
    db: AsyncSession = Depends(get_db)
):
    """
    Handle natural language queries about ads data.
    
    Expected input: {"query": "Your question here"}
    Returns: {"answer": str, "sql": str, "data": List[Dict]}
    """
    user_query = query.get("query", "").strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Step 1: Generate SQL from natural language
        logger.info(f"Generating SQL for query: {user_query}")
        sql_result = await llm_agent_service.generate_sql(user_query)
        
        if not sql_result["success"]:
            logger.error(f"SQL generation failed: {sql_result['error']}")
            raise HTTPException(
                status_code=400, 
                detail=f"I couldn't generate a valid query. {sql_result['error']}"
            )
        
        generated_sql = sql_result["sql"]
        logger.info(f"Generated SQL: {generated_sql}")
        
        # Step 2: Validate the generated SQL
        is_valid, validation_error = sql_validator.validate_sql(generated_sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {validation_error}")
            # Try to regenerate with error context
            logger.info("Attempting to regenerate SQL with error context")
            retry_result = await llm_agent_service.generate_sql(
                f"{user_query}\n\nPrevious attempt failed validation: {validation_error}. Please correct the SQL."
            )
            
            if not retry_result["success"]:
                logger.error(f"SQL regeneration failed: {retry_result['error']}")
                raise HTTPException(
                    status_code=400,
                    detail="I couldn't generate a valid query after multiple attempts. Try rephrasing your question."
                )
            
            generated_sql = retry_result["sql"]
            logger.info(f"Regenerated SQL: {generated_sql}")
            
            # Validate again
            is_valid, validation_error = sql_validator.validate_sql(generated_sql)
            if not is_valid:
                logger.error(f"SQL validation failed on retry: {validation_error}")
                raise HTTPException(
                    status_code=400,
                    detail="I couldn't generate a valid query that passes security checks. Try rephrasing your question."
                )
        
        # Step 3: Execute the SQL query
        logger.info(f"Executing SQL: {generated_sql}")
        try:
            # Add statement timeout for safety
            await db.execute(text("SET statement_timeout = '30s'"))
            result = await db.execute(text(generated_sql))
            
            # Convert results to list of dictionaries
            columns = result.keys()
            rows = result.fetchall()
            query_results = [dict(zip(columns, row)) for row in rows]
            
            logger.info(f"Query executed successfully, returned {len(query_results)} rows")
            
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            sanitized_error = sql_validator.sanitize_error_message(str(e))
            
            # Try to get LLM to fix the SQL
            logger.info("Attempting to auto-repair SQL with error context")
            repair_result = await llm_agent_service.generate_sql(
                f"The previous SQL query failed with error: {sanitized_error}\n\nOriginal question: {user_query}\n\nPlease generate a corrected SQL query."
            )
            
            if repair_result["success"]:
                # Validate the repaired SQL
                is_valid, validation_error = sql_validator.validate_sql(repair_result["sql"])
                if is_valid:
                    try:
                        await db.execute(text("SET statement_timeout = '30s'"))
                        result = await db.execute(text(repair_result["sql"]))
                        columns = result.keys()
                        rows = result.fetchall()
                        query_results = [dict(zip(columns, row)) for row in rows]
                        generated_sql = repair_result["sql"]  # Use the repaired SQL
                        logger.info(f"Repaired SQL executed successfully, returned {len(query_results)} rows")
                    except Exception as retry_e:
                        logger.error(f"Repaired SQL also failed: {str(retry_e)}")
                        raise HTTPException(
                            status_code=400,
                            detail="I couldn't execute a valid query. The data might not exist for your question or there may be a technical issue."
                        )
                else:
                    logger.error(f"Repaired SQL failed validation: {validation_error}")
                    raise HTTPException(
                        status_code=400,
                        detail="I couldn't generate a valid query after attempting to fix the error. Try rephrasing your question."
                    )
            else:
                logger.error(f"Failed to generate repair SQL: {repair_result['error']}")
                raise HTTPException(
                    status_code=400,
                    detail="I couldn't generate a valid query. Try rephrasing your question."
                )
        
        # Step 4: Summarize the results
        logger.info("Generating summary of results")
        summary_result = await llm_agent_service.summarize_results(
            user_query, generated_sql, query_results
        )
        
        if not summary_result["success"]:
            logger.warning(f"Summary generation failed: {summary_result['error']}")
            # Provide a basic summary if LLM fails
            if not query_results:
                summary = "No data found for your query. Try a different date range or campaign."
            else:
                summary = f"Found {len(query_results)} results. Please see the data below for details."
        else:
            summary = summary_result["summary"]
        
        # Step 5: Return the response
        return {
            "answer": summary,
            "sql": generated_sql,
            "data": query_results
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your question. Please try again."
        )