from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_
from app.models.postgres import Campaign, AdSet, Ad, Insight
import logging

logger = logging.getLogger(__name__)

class PostgresRepository:
    """Repository for PostgreSQL operations."""
    
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

    # Read operations for Phase 3
    async def get_campaigns(
        self, 
        db: AsyncSession, 
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
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
                "daily_budget": float(campaign.daily_budget) if campaign.daily_budget else None,
                "lifetime_budget": float(campaign.lifetime_budget) if campaign.lifetime_budget else None,
                "created_time": campaign.created_time.isoformat() if campaign.created_time else None,
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
        campaign_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get ads with optional filtering and pagination."""
        query = select(Ad)
        
        if campaign_id:
            # Join with ad_sets to filter by campaign_id
            query = query.join(AdSet, Ad.ad_set_id == AdSet.id).where(AdSet.campaign_id == campaign_id)
            
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
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        campaign_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get insights with optional filtering and pagination."""
        query = select(Insight)
        
        # Apply date filters
        if date_from:
            query = query.where(Insight.date >= date_from)
        if date_to:
            query = query.where(Insight.date <= date_to)
            
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
                "conversion_value": float(insight.conversion_value) if insight.conversion_value else None,
                "created_at": insight.created_at.isoformat() if insight.created_at else None,
                "updated_at": insight.updated_at.isoformat() if insight.updated_at else None
            }
            for insight in insights
        ]

# Global instance
postgres_repository = PostgresRepository()