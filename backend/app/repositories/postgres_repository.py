import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres import Ad, AdSet, Campaign, Insight

logger = logging.getLogger(__name__)


def _batch_upsert_sql(
    table: str,
    records: list[dict[str, Any]],
    conflict_columns: list[str],
    skip_in_update: set[str] | None = None,
) -> tuple:
    """Build a single INSERT ... ON CONFLICT DO UPDATE statement for all records.

    Returns (sql_string, params_dict) for use with db.execute().
    """
    if not records:
        return "", {}

    skip = set(skip_in_update or [])
    columns = list(records[0].keys())

    value_rows = []
    params = {}
    for i, record in enumerate(records):
        row = []
        for col in columns:
            param = f"{col}_{i}"
            row.append(f":{param}")
            params[param] = record[col]
        value_rows.append(f"({' ,'.join(row)})")

    col_list = ", ".join(columns)
    values_list = ", ".join(value_rows)
    conflict_list = ", ".join(conflict_columns)

    update_cols = [c for c in columns if c not in conflict_columns and c not in skip]
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

    sql = (
        f"INSERT INTO {table} ({col_list})\n"
        f"VALUES {values_list}\n"
        f"ON CONFLICT ({conflict_list}) DO UPDATE SET\n  {set_clause}"
    )
    return sql, params


class PostgresRepository:
    """Repository for PostgreSQL operations."""

    async def upsert_campaigns(self, db: AsyncSession, campaigns: list[dict[str, Any]]) -> int:
        """Upsert campaigns into PostgreSQL."""
        if not campaigns:
            return 0

        sql, params = _batch_upsert_sql(
            "campaigns", campaigns,
            conflict_columns=["id"],
            skip_in_update={"created_at"},
        )
        await db.execute(text(sql), params)
        await db.commit()
        logger.info(f"Upserted {len(campaigns)} campaigns into PostgreSQL")
        return len(campaigns)

    async def upsert_ad_sets(self, db: AsyncSession, ad_sets: list[dict[str, Any]]) -> int:
        """Upsert ad sets into PostgreSQL."""
        if not ad_sets:
            return 0

        sql, params = _batch_upsert_sql(
            "ad_sets", ad_sets,
            conflict_columns=["id"],
            skip_in_update={"created_at"},
        )
        await db.execute(text(sql), params)
        await db.commit()
        logger.info(f"Upserted {len(ad_sets)} ad sets into PostgreSQL")
        return len(ad_sets)

    async def upsert_ads(self, db: AsyncSession, ads: list[dict[str, Any]]) -> int:
        """Upsert ads into PostgreSQL."""
        if not ads:
            return 0

        sql, params = _batch_upsert_sql(
            "ads", ads,
            conflict_columns=["id"],
            skip_in_update={"created_at"},
        )
        await db.execute(text(sql), params)
        await db.commit()
        logger.info(f"Upserted {len(ads)} ads into PostgreSQL")
        return len(ads)

    async def upsert_insights(self, db: AsyncSession, insights: list[dict[str, Any]]) -> int:
        """Upsert insights into PostgreSQL."""
        if not insights:
            return 0

        # Filter out records missing required fields
        valid = [i for i in insights if i.get('ad_id') and i.get('date')]
        if not valid:
            return 0

        sql, params = _batch_upsert_sql(
            "insights", valid,
            conflict_columns=["ad_id", "date"],
            skip_in_update={"created_at"},
        )
        await db.execute(text(sql), params)
        await db.commit()
        logger.info(f"Upserted {len(valid)} insights into PostgreSQL")
        return len(valid)

    # Read operations for Phase 3
    async def get_campaigns(
        self,
        db: AsyncSession,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get campaigns with optional filtering and pagination."""
        query = select(Campaign)

        if status:
            query = query.where(Campaign.status == status)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        campaigns = result.scalars().all()

        # Convert to list of dictionaries
        return [
            {
                "id": campaign.id,
                "name": campaign.name,
                "status": campaign.status,
                "objective": campaign.objective,
                "daily_budget": (
                    float(campaign.daily_budget) if campaign.daily_budget else None
                ),
                "lifetime_budget": (
                    float(campaign.lifetime_budget) if campaign.lifetime_budget else None
                ),
                "created_time": (
                    campaign.created_time.isoformat() if campaign.created_time else None
                ),
                "start_time": campaign.start_time.isoformat() if campaign.start_time else None,
                "stop_time": campaign.stop_time.isoformat() if campaign.stop_time else None,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
                "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None
            }
            for campaign in campaigns
        ]

    async def get_ads(
        self,
        db: AsyncSession,
        campaign_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get ads with optional filtering and pagination."""
        query = select(Ad)

        if campaign_id:
            # Join with ad_sets to filter by campaign_id
            query = query.join(AdSet, Ad.ad_set_id == AdSet.id).where(
                AdSet.campaign_id == campaign_id
            )

        if status:
            query = query.where(Ad.status == status)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        ads = result.scalars().all()

        # Convert to list of dictionaries
        return [
            {
                "id": ad.id,
                "ad_set_id": ad.ad_set_id,
                "name": ad.name,
                "status": ad.status,
                "creative": ad.creative,
                "created_time": ad.created_time.isoformat() if ad.created_time else None,
                "created_at": ad.created_at.isoformat() if ad.created_at else None,
                "updated_at": ad.updated_at.isoformat() if ad.updated_at else None
            }
            for ad in ads
        ]

    async def get_insights(
        self,
        db: AsyncSession,
        date_from: str | None = None,
        date_to: str | None = None,
        campaign_id: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get insights with optional filtering and pagination."""
        query = select(Insight)

        # Apply date filters
        if date_from:
            try:
                date_from_val = datetime.strptime(date_from, "%Y-%m-%d").date()
            except ValueError:
                logger.warning("Invalid date_from format: %s, ignoring filter", date_from)
                date_from_val = None
            if date_from_val:
                query = query.where(Insight.date >= date_from_val)
        if date_to:
            try:
                date_to_val = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                logger.warning("Invalid date_to format: %s, ignoring filter", date_to)
                date_to_val = None
            if date_to_val:
                query = query.where(Insight.date <= date_to_val)

        # Apply campaign filter by joining through ads and ad_sets
        if campaign_id:
            query = query.join(Ad, Insight.ad_id == Ad.id)\
                        .join(AdSet, Ad.ad_set_id == AdSet.id)\
                        .where(AdSet.campaign_id == campaign_id)

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        insights = result.scalars().all()

        # Convert to list of dictionaries
        return [
            {
                "id": insight.id,
                "ad_id": insight.ad_id,
                "date": insight.date.isoformat() if insight.date else None,
                "impressions": insight.impressions,
                "clicks": insight.clicks,
                "spend": float(insight.spend) if insight.spend else None,
                "reach": insight.reach,
                "frequency": float(insight.frequency) if insight.frequency else None,
                "ctr": float(insight.ctr) if insight.ctr else None,
                "cpc": float(insight.cpc) if insight.cpc else None,
                "cpm": float(insight.cpm) if insight.cpm else None,
                "conversions": insight.conversions,
                "conversion_value": (
                    float(insight.conversion_value) if insight.conversion_value else None
                ),
                "created_at": insight.created_at.isoformat() if insight.created_at else None,
                "updated_at": insight.updated_at.isoformat() if insight.updated_at else None
            }
            for insight in insights
        ]

# Global instance
postgres_repository = PostgresRepository()
