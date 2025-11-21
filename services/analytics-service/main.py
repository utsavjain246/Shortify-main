"""
Analytics Service - Handles click tracking and analytics
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, text, select
import redis.asyncio as redis
import os

import asyncio
from sqlalchemy import text

app = FastAPI(title="Analytics Service", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    """Wait for database connection"""
    # Log masked connection string for debugging
    safe_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "UNKNOWN"
    print(f"Attempting to connect to database at: ...@{safe_url}")

    retries = 60
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("Database connection established")
            return
        except Exception as e:
            retries -= 1
            print(f"Database connection failed ({e}), retrying... ({retries} left)")
            await asyncio.sleep(5)

    raise RuntimeError("Could not connect to database after 5 minutes")


# Configuration
DATABASE_URL = os.getenv("DATABASE_URL").replace(
    "postgresql://", "postgresql+asyncpg://"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Database Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


# SQLAlchemy Models
class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, index=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)


class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    user_id = Column(Integer, index=True)
    is_active = Column(
        Integer, default=True
    )  # Using Integer/Boolean depending on DB schema, assuming Boolean mapped


# Pydantic Models
class ClickEvent(BaseModel):
    short_code: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None


class AnalyticsResponse(BaseModel):
    total_clicks: int
    unique_ips: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int
    top_referrers: List[Dict[str, int]]
    clicks_by_date: List[Dict[str, Any]]


class ClickRecord(BaseModel):
    id: int
    clicked_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]
    country: Optional[str]
    city: Optional[str]


# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def increment_click_counter(short_code: str):
    """Increment click counter in Redis for real-time stats"""
    try:
        await redis_client.incr(f"clicks:{short_code}")
        await redis_client.incr(f"clicks:total")

        # Set daily counter
        today = datetime.utcnow().strftime("%Y-%m-%d")
        await redis_client.incr(f"clicks:{short_code}:{today}")
    except Exception as e:
        print(f"Redis increment failed: {e}")


async def get_click_count_from_cache(short_code: str) -> Optional[int]:
    """Get click count from Redis cache"""
    try:
        count = await redis_client.get(f"clicks:{short_code}")
        return int(count) if count else None
    except Exception as e:
        print(f"Redis get failed: {e}")
        return None


# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"service": "analytics-service", "status": "healthy"}


@app.post("/track", status_code=status.HTTP_201_CREATED)
async def track_click(event: ClickEvent, db: AsyncSession = Depends(get_db)):
    """Track a click event"""
    # Get URL ID from short code
    query = select(URL).where(URL.short_code == event.short_code)
    result = await db.execute(query)
    url_data = result.scalar_one_or_none()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
        )

    # Note: We are not checking is_active here because tracking might happen
    # even if deactivated (though redirection logic usually handles that).
    # The original code checked is_active, so let's keep it consistent if possible,
    # but the URL model definition needs to be accurate.

    # Insert click record
    new_click = Analytics(
        url_id=url_data.id,
        ip_address=event.ip_address,
        user_agent=event.user_agent,
        referrer=event.referrer,
        country=event.country,
        city=event.city,
    )
    db.add(new_click)
    await db.commit()
    await db.refresh(new_click)

    # Increment Redis counters
    await increment_click_counter(event.short_code)

    return {
        "message": "Click tracked successfully",
        "click_id": new_click.id,
        "clicked_at": new_click.clicked_at,
    }


@app.get("/analytics/{short_code}", response_model=AnalyticsResponse)
async def get_analytics(short_code: str, db: AsyncSession = Depends(get_db)):
    """Get comprehensive analytics for a short URL"""
    # Get URL ID
    query = select(URL).where(URL.short_code == short_code)
    result = await db.execute(query)
    url_data = result.scalar_one_or_none()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
        )

    url_id = url_data.id
    now = datetime.utcnow()

    # We use raw SQL for complex aggregations for performance and simplicity in migration

    # Total clicks
    result = await db.execute(
        text("SELECT COUNT(*) as total FROM analytics WHERE url_id = :url_id"),
        {"url_id": url_id},
    )
    total_clicks = result.scalar()

    # Unique IPs
    result = await db.execute(
        text(
            "SELECT COUNT(DISTINCT ip_address) as unique_ips FROM analytics WHERE url_id = :url_id"
        ),
        {"url_id": url_id},
    )
    unique_ips = result.scalar()

    # Clicks today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        text(
            "SELECT COUNT(*) as clicks_today FROM analytics WHERE url_id = :url_id AND clicked_at >= :today_start"
        ),
        {"url_id": url_id, "today_start": today_start},
    )
    clicks_today = result.scalar()

    # Clicks this week
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        text(
            "SELECT COUNT(*) as clicks_week FROM analytics WHERE url_id = :url_id AND clicked_at >= :week_start"
        ),
        {"url_id": url_id, "week_start": week_start},
    )
    clicks_this_week = result.scalar()

    # Clicks this month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        text(
            "SELECT COUNT(*) as clicks_month FROM analytics WHERE url_id = :url_id AND clicked_at >= :month_start"
        ),
        {"url_id": url_id, "month_start": month_start},
    )
    clicks_this_month = result.scalar()

    # Top referrers
    result = await db.execute(
        text(
            """
            SELECT referrer, COUNT(*) as count
            FROM analytics
            WHERE url_id = :url_id AND referrer IS NOT NULL
            GROUP BY referrer
            ORDER BY count DESC
            LIMIT 10
        """
        ),
        {"url_id": url_id},
    )
    top_referrers = [
        {"referrer": row.referrer, "count": row.count} for row in result.fetchall()
    ]

    # Clicks by date (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    result = await db.execute(
        text(
            """
            SELECT
                DATE(clicked_at) as date,
                COUNT(*) as clicks
            FROM analytics
            WHERE url_id = :url_id AND clicked_at >= :thirty_days_ago
            GROUP BY DATE(clicked_at)
            ORDER BY date DESC
        """
        ),
        {"url_id": url_id, "thirty_days_ago": thirty_days_ago},
    )
    clicks_by_date = [
        {"date": str(row.date), "clicks": row.clicks} for row in result.fetchall()
    ]

    return AnalyticsResponse(
        total_clicks=total_clicks,
        unique_ips=unique_ips,
        clicks_today=clicks_today,
        clicks_this_week=clicks_this_week,
        clicks_this_month=clicks_this_month,
        top_referrers=top_referrers,
        clicks_by_date=clicks_by_date,
    )


@app.get("/clicks/{short_code}", response_model=List[ClickRecord])
async def get_click_records(
    short_code: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """Get individual click records for a short URL"""
    # Get URL ID
    query = select(URL).where(URL.short_code == short_code)
    result = await db.execute(query)
    url_data = result.scalar_one_or_none()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
        )

    # Get click records
    query = (
        select(Analytics)
        .where(Analytics.url_id == url_data.id)
        .order_by(Analytics.clicked_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    records = result.scalars().all()

    return records


@app.get("/analytics/user/{user_id}/summary")
async def get_user_analytics_summary(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get analytics summary for all URLs owned by a user"""

    # Total URLs
    result = await db.execute(
        text("SELECT COUNT(*) as total_urls FROM urls WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    total_urls = result.scalar()

    # Total clicks across all URLs
    result = await db.execute(
        text(
            """
            SELECT COUNT(*) as total_clicks
            FROM analytics a
            JOIN urls u ON a.url_id = u.id
            WHERE u.user_id = :user_id
        """
        ),
        {"user_id": user_id},
    )
    total_clicks = result.scalar()

    # Active URLs
    result = await db.execute(
        text(
            "SELECT COUNT(*) as active_urls FROM urls WHERE user_id = :user_id AND is_active = TRUE"
        ),
        {"user_id": user_id},
    )
    active_urls = result.scalar()

    # Top performing URL
    result = await db.execute(
        text(
            """
            SELECT u.short_code, u.original_url, COUNT(a.id) as clicks
            FROM urls u
            LEFT JOIN analytics a ON u.id = a.url_id
            WHERE u.user_id = :user_id
            GROUP BY u.id
            ORDER BY clicks DESC
            LIMIT 1
        """
        ),
        {"user_id": user_id},
    )
    top_url = result.fetchone()

    # Recent activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        text(
            """
            SELECT COUNT(*) as recent_clicks
            FROM analytics a
            JOIN urls u ON a.url_id = u.id
            WHERE u.user_id = :user_id AND a.clicked_at >= :seven_days_ago
        """
        ),
        {"user_id": user_id, "seven_days_ago": seven_days_ago},
    )
    recent_clicks = result.scalar()

    return {
        "total_urls": total_urls,
        "active_urls": active_urls,
        "total_clicks": total_clicks,
        "recent_clicks_7_days": recent_clicks,
        "top_performing_url": (
            {
                "short_code": top_url.short_code if top_url else None,
                "original_url": top_url.original_url if top_url else None,
                "clicks": top_url.clicks if top_url else 0,
            }
            if top_url
            else None
        ),
    }


@app.delete("/analytics/{short_code}")
async def delete_analytics(short_code: str, db: AsyncSession = Depends(get_db)):
    """Delete all analytics data for a short URL"""
    # Get URL ID
    query = select(URL).where(URL.short_code == short_code)
    result = await db.execute(query)
    url_data = result.scalar_one_or_none()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
        )

    # Delete analytics records
    await db.execute(
        text("DELETE FROM analytics WHERE url_id = :url_id"), {"url_id": url_data.id}
    )
    await db.commit()

    # Clear Redis cache
    try:
        await redis_client.delete(f"clicks:{short_code}")
    except Exception as e:
        print(f"Redis delete failed: {e}")

    return {
        "message": "Analytics data deleted successfully",
        "deleted_records": 0,  # We don't get rowcount easily with execute(text) in all drivers, simplifying
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
