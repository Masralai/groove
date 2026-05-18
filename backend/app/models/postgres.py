import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class Ad(Base):
    __tablename__ = "ads"

    id = Column(Text, primary_key=True)
    ad_set_id = Column(Text, nullable=False)  # Foreign key to ad_sets.id
    name = Column(Text)
    status = Column(Text)
    creative = Column(JSONB)
    created_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('ad_id', 'date', name='uq_insights_ad_id_date'),
    )
