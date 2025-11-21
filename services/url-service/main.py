"""
URL Service - Handles URL shortening, retrieval, and QR code generation
"""

import random
import string
import io
import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    select,
    update,
    BigInteger,
)
from sqlalchemy.exc import IntegrityError
import qrcode
import redis.asyncio as redis
import os

import asyncio
from sqlalchemy import text

app = FastAPI(title="URL Service", version="1.0.0")


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
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Database Setup
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Thread pool for CPU-bound tasks (QR code generation)
thread_pool = ThreadPoolExecutor()


# SQLAlchemy Models
class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)
    custom_alias = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, index=True)
    # We only need the model definition for joins if needed,
    # but analytics service handles the actual analytics data.
    # Keeping it minimal here to avoid circular deps if we were to share models.


# Pydantic Models
class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    user_id: Optional[int] = None


class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    full_short_url: str
    qr_code: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class URLStats(BaseModel):
    id: int
    original_url: str
    short_code: str
    full_short_url: str
    total_clicks: int
    created_at: datetime
    is_active: bool


# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


def generate_short_code(length: int = 6) -> str:
    """Generate random short code"""
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def _generate_qr_code_sync(url: str) -> Optional[str]:
    """Synchronous QR code generation"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"QR code generation failed: {e}")
        return None


async def generate_qr_code(url: str) -> Optional[str]:
    """Asynchronous wrapper for QR code generation"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _generate_qr_code_sync, url)


async def get_url_from_cache(short_code: str) -> Optional[str]:
    """Get URL from Redis cache"""
    try:
        return await redis_client.get(f"url:{short_code}")
    except Exception as e:
        print(f"Redis get failed: {e}")
        return None


async def set_url_in_cache(short_code: str, original_url: str, ttl: int = 3600):
    """Set URL in Redis cache with TTL (default 1 hour)"""
    try:
        await redis_client.setex(f"url:{short_code}", ttl, original_url)
    except Exception as e:
        print(f"Redis set failed: {e}")


async def delete_url_from_cache(short_code: str):
    """Delete URL from Redis cache"""
    try:
        await redis_client.delete(f"url:{short_code}")
    except Exception as e:
        print(f"Redis delete failed: {e}")


# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"service": "url-service", "status": "healthy"}


@app.post("/shorten", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(url_data: URLCreate, db: AsyncSession = Depends(get_db)):
    """Create a shortened URL"""
    short_code = None

    # Check if custom alias is provided
    if url_data.custom_alias:
        short_code = url_data.custom_alias
        # Validate custom alias
        if not short_code.replace("_", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom alias must contain only letters, numbers, hyphens, and underscores",
            )
        if len(short_code) < 3 or len(short_code) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom alias must be between 3 and 20 characters",
            )

        # Try to insert with custom alias
        new_url = URL(
            original_url=str(url_data.original_url),
            short_code=short_code,
            user_id=url_data.user_id,
            custom_alias=True,
        )
        db.add(new_url)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This custom alias is already taken",
            )
    else:
        # Generate unique short code
        max_attempts = 10
        for _ in range(max_attempts):
            short_code = generate_short_code()
            new_url = URL(
                original_url=str(url_data.original_url),
                short_code=short_code,
                user_id=url_data.user_id,
                custom_alias=False,
            )
            db.add(new_url)
            try:
                await db.commit()
                break
            except IntegrityError:
                await db.rollback()
                continue
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate unique short code",
            )

    await db.refresh(new_url)

    # Generate full URL and QR code
    full_short_url = f"{BASE_URL}/{short_code}"
    qr_code = await generate_qr_code(full_short_url)

    # Cache the URL
    await set_url_in_cache(short_code, new_url.original_url)

    return URLResponse(
        id=new_url.id,
        original_url=new_url.original_url,
        short_code=new_url.short_code,
        full_short_url=full_short_url,
        qr_code=qr_code,
        created_at=new_url.created_at,
        expires_at=new_url.expires_at,
        is_active=new_url.is_active,
    )


@app.get("/{short_code}")
async def get_original_url(short_code: str, db: AsyncSession = Depends(get_db)):
    """Get original URL by short code"""
    # Try cache first
    cached_url = await get_url_from_cache(short_code)
    if cached_url:
        return {"original_url": cached_url, "source": "cache"}

    # Get from database
    query = select(URL).where(URL.short_code == short_code)
    result = await db.execute(query)
    url_data = result.scalar_one_or_none()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
        )

    if not url_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This short URL has been deactivated",
        )

    if url_data.expires_at and url_data.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="This short URL has expired"
        )

    # Cache the URL
    await set_url_in_cache(short_code, url_data.original_url)

    return {"original_url": url_data.original_url, "source": "database"}


@app.get("/urls/user/{user_id}", response_model=List[URLStats])
async def get_user_urls(
    user_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """Get all URLs created by a user"""
    # Note: This query is a bit complex because it involves a join with analytics.
    # For simplicity in this refactor, we will do a raw SQL query via SQLAlchemy text
    # or we can define the Analytics model properly.
    # Let's use raw SQL for the join to ensure we match the original logic but async.
    from sqlalchemy import text

    query = text(
        """
        SELECT
            u.id,
            u.original_url,
            u.short_code,
            u.created_at,
            u.is_active,
            COALESCE(COUNT(a.id), 0) as total_clicks
        FROM urls u
        LEFT JOIN analytics a ON u.id = a.url_id
        WHERE u.user_id = :user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
        LIMIT :limit OFFSET :skip
    """
    )

    result = await db.execute(query, {"user_id": user_id, "limit": limit, "skip": skip})
    urls = result.fetchall()

    return [
        URLStats(
            id=row.id,
            original_url=row.original_url,
            short_code=row.short_code,
            full_short_url=f"{BASE_URL}/{row.short_code}",
            total_clicks=row.total_clicks,
            created_at=row.created_at,
            is_active=row.is_active,
        )
        for row in urls
    ]


@app.delete("/{short_code}")
async def delete_url(
    short_code: str, user_id: Optional[int] = None, db: AsyncSession = Depends(get_db)
):
    """Delete/deactivate a URL"""
    # Check ownership if user_id provided
    query = select(URL).where(URL.short_code == short_code)
    if user_id:
        query = query.where(URL.user_id == user_id)

    result = await db.execute(query)
    url_data = result.scalar_one_or_none()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found or you don't have permission",
        )

    # Deactivate URL instead of deleting
    url_data.is_active = False
    await db.commit()

    # Remove from cache
    await delete_url_from_cache(short_code)

    return {"message": "URL deactivated successfully"}


@app.get("/stats/{short_code}")
async def get_url_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    """Get statistics for a specific URL"""
    from sqlalchemy import text

    query = text(
        """
        SELECT
            u.id,
            u.original_url,
            u.short_code,
            u.created_at,
            u.is_active,
            COALESCE(COUNT(a.id), 0) as total_clicks
        FROM urls u
        LEFT JOIN analytics a ON u.id = a.url_id
        WHERE u.short_code = :short_code
        GROUP BY u.id
    """
    )

    result = await db.execute(query, {"short_code": short_code})
    url_data = result.fetchone()

    if not url_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found"
        )

    return URLStats(
        id=url_data.id,
        original_url=url_data.original_url,
        short_code=url_data.short_code,
        full_short_url=f"{BASE_URL}/{url_data.short_code}",
        total_clicks=url_data.total_clicks,
        created_at=url_data.created_at,
        is_active=url_data.is_active,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
