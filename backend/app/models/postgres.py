from sqlalchemy import Column, Text, Numeric, Integer, DateTime, Date, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import uuid
from datetime import datetime, timezone

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Text, primary_key=True)
    name = Column(Text)
    status = Column(Text)
    objective = Column(Text)
    daily_budget = Column(Numeric)
    lifetime_budget = Column(Numeric)
    created_time = Column(DateTime)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AdSet(Base):
    __tablename__ = "ad_sets"
    
    id = Column(Text, primary_key=True)
    campaign_id = Column(Text, nullable=False)  # Foreign key to campaigns.id
    name = Column(Text)
    status = Column(Text)
    daily_budget = Column(Numeric)
    lifetime_budget = Column(Numeric)
    targeting = Column(JSONB)
    bid_strategy = Column(Text)
    created_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Ad(Base):
    __tablename__ = "ads"
    
    id = Column(Text, primary_key=True)
    ad_set_id = Column(Text, nullable=False)  # Foreign key to ad_sets.id
    name = Column(Text)
    status = Column(Text)
    creative = Column(JSONB)
    created_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_id = Column(Text, nullable=False)  # Foreign key to ads.id
    date = Column(Date, nullable=False)
    impressions = Column(Integer)
    clicks = Column(Integer)
    spend = Column(Numeric)
    reach = Column(Integer)
    frequency = Column(Numeric)
    ctr = Column(Numeric)
    cpc = Column(Numeric)
    cpm = Column(Numeric)
    conversions = Column(Integer)
    conversion_value = Column(Numeric)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint('ad_id', 'date', name='uq_insights_ad_id_date'),
    )