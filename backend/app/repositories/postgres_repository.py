from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.postgres import Campaign, AdSet, Ad, Insight
import logging

logger = logging.getLogger(__name__)

class PostgresRepository:
    """Repository for PostgreSQL upsert operations."""
    
    async def upsert_campaigns(self, db: AsyncSession, campaigns: List[Dict[str, Any]]) -> int:
        """Upsert campaigns into PostgreSQL."""
        if not campaigns:
            return 0
            
        upserted = 0
        for campaign in campaigns:
            stmt = text("""
                INSERT INTO campaigns (
                    id, name, status, objective, daily_budget, lifetime_budget, 
                    created_time, start_time, stop_time, updated_at
                ) VALUES (
                    :id, :name, :status, :objective, :daily_budget, :lifetime_budget,
                    :created_time, :start_time, :stop_time, :updated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    objective = EXCLUDED.objective,
                    daily_budget = EXCLUDED.daily_budget,
                    lifetime_budget = EXCLUDED.lifetime_budget,
                    created_time = EXCLUDED.created_time,
                    start_time = EXCLUDED.start_time,
                    stop_time = EXCLUDED.stop_time,
                    updated_at = EXCLUDED.updated_at
            """)
            
            await db.execute(stmt, {
                'id': campaign['id'],
                'name': campaign['name'],
                'status': campaign['status'],
                'objective': campaign['objective'],
                'daily_budget': campaign['daily_budget'],
                'lifetime_budget': campaign['lifetime_budget'],
                'created_time': campaign['created_time'],
                'start_time': campaign['start_time'],
                'stop_time': campaign['stop_time'],
                'updated_at': campaign['updated_at']
            })
            upserted += 1
            
        await db.commit()
        logger.info(f"Upserted {upserted} campaigns into PostgreSQL")
        return upserted
    
    async def upsert_ad_sets(self, db: AsyncSession, ad_sets: List[Dict[str, Any]]) -> int:
        """Upsert ad sets into PostgreSQL."""
        if not ad_sets:
            return 0
            
        upserted = 0
        for ad_set in ad_sets:
            stmt = text("""
                INSERT INTO ad_sets (
                    id, campaign_id, name, status, daily_budget, lifetime_budget,
                    targeting, bid_strategy, created_time, updated_at
                ) VALUES (
                    :id, :campaign_id, :name, :status, :daily_budget, :lifetime_budget,
                    :targeting, :bid_strategy, :created_time, :updated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    campaign_id = EXCLUDED.campaign_id,
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    daily_budget = EXCLUDED.daily_budget,
                    lifetime_budget = EXCLUDED.lifetime_budget,
                    targeting = EXCLUDED.targeting,
                    bid_strategy = EXCLUDED.bid_strategy,
                    created_time = EXCLUDED.created_time,
                    updated_at = EXCLUDED.updated_at
            """)
            
            await db.execute(stmt, {
                'id': ad_set['id'],
                'campaign_id': ad_set['campaign_id'],
                'name': ad_set['name'],
                'status': ad_set['status'],
                'daily_budget': ad_set['daily_budget'],
                'lifetime_budget': ad_set['lifetime_budget'],
                'targeting': ad_set['targeting'],
                'bid_strategy': ad_set['bid_strategy'],
                'created_time': ad_set['created_time'],
                'updated_at': ad_set['updated_at']
            })
            upserted += 1
            
        await db.commit()
        logger.info(f"Upserted {upserted} ad sets into PostgreSQL")
        return upserted
    
    async def upsert_ads(self, db: AsyncSession, ads: List[Dict[str, Any]]) -> int:
        """Upsert ads into PostgreSQL."""
        if not ads:
            return 0
            
        upserted = 0
        for ad in ads:
            stmt = text("""
                INSERT INTO ads (
                    id, ad_set_id, name, status, creative, created_time, updated_at
                ) VALUES (
                    :id, :ad_set_id, :name, :status, :creative, :created_time, :updated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    ad_set_id = EXCLUDED.ad_set_id,
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    creative = EXCLUDED.creative,
                    created_time = EXCLUDED.created_time,
                    updated_at = EXCLUDED.updated_at
            """)
            
            await db.execute(stmt, {
                'id': ad['id'],
                'ad_set_id': ad['ad_set_id'],
                'name': ad['name'],
                'status': ad['status'],
                'creative': ad['creative'],
                'created_time': ad['created_time'],
                'updated_at': ad['updated_at']
            })
            upserted += 1
            
        await db.commit()
        logger.info(f"Upserted {upserted} ads into PostgreSQL")
        return upserted
    
    async def upsert_insights(self, db: AsyncSession, insights: List[Dict[str, Any]]) -> int:
        """Upsert insights into PostgreSQL."""
        if not insights:
            return 0
            
        upserted = 0
        for insight in insights:
            # Skip if ad_id or date is missing
            if not insight.get('ad_id') or not insight.get('date'):
                continue
                
            stmt = text("""
                INSERT INTO insights (
                    ad_id, date, impressions, clicks, spend, reach, frequency,
                    ctr, cpc, cpm, conversions, conversion_value, updated_at
                ) VALUES (
                    :ad_id, :date, :impressions, :clicks, :spend, :reach, :frequency,
                    :ctr, :cpc, :cpm, :conversions, :conversion_value, :updated_at
                )
                ON CONFLICT (ad_id, date) DO UPDATE SET
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    spend = EXCLUDED.spend,
                    reach = EXCLUDED.reach,
                    frequency = EXCLUDED.frequency,
                    ctr = EXCLUDED.ctr,
                    cpc = EXCLUDED.cpc,
                    cpm = EXCLUDED.cpm,
                    conversions = EXCLUDED.conversions,
                    conversion_value = EXCLUDED.conversion_value,
                    updated_at = EXCLUDED.updated_at
            """)
            
            await db.execute(stmt, {
                'ad_id': insight['ad_id'],
                'date': insight['date'],
                'impressions': insight['impressions'],
                'clicks': insight['clicks'],
                'spend': insight['spend'],
                'reach': insight['reach'],
                'frequency': insight['frequency'],
                'ctr': insight['ctr'],
                'cpc': insight['cpc'],
                'cpm': insight['cpm'],
                'conversions': insight['conversions'],
                'conversion_value': insight['conversion_value'],
                'updated_at': insight['updated_at']
            })
            upserted += 1
            
        await db.commit()
        logger.info(f"Upserted {upserted} insights into PostgreSQL")
        return upserted