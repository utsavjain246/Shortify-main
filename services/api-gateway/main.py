"""
API Gateway - Main entry point for all client requests
Routes requests to appropriate microservices
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from jose import JWTError, jwt
import httpx
import os

app = FastAPI(
    title="Shortify API Gateway",
    version="1.0.0",
    description="URL Shortener Microservices API",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8003")
URL_SERVICE_URL = os.getenv("URL_SERVICE_URL", "http://url-service:8001")
ANALYTICS_SERVICE_URL = os.getenv(
    "ANALYTICS_SERVICE_URL", "http://analytics-service:8002"
)

# Auth Config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

security = HTTPBearer(auto_error=False)


# Models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None


# Helper functions
async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Verify JWT token locally"""
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")

        if user_id is None:
            return None

        return {"user_id": user_id, "username": username}
    except JWTError:
        return None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


# Routes
@app.get("/")
async def root():
    """API Gateway health check"""
    return {
        "service": "api-gateway",
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "auth": AUTH_SERVICE_URL,
            "url": URL_SERVICE_URL,
            "analytics": ANALYTICS_SERVICE_URL,
        },
    }


@app.get("/health")
async def health_check():
    """Check health of all services"""
    health_status = {"gateway": "healthy", "services": {}}

    async with httpx.AsyncClient() as client:
        # Check auth service
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/", timeout=5.0)
            health_status["services"]["auth"] = (
                "healthy" if response.status_code == 200 else "unhealthy"
            )
        except Exception:
            health_status["services"]["auth"] = "unhealthy"

        # Check URL service
        try:
            response = await client.get(f"{URL_SERVICE_URL}/", timeout=5.0)
            health_status["services"]["url"] = (
                "healthy" if response.status_code == 200 else "unhealthy"
            )
        except Exception:
            health_status["services"]["url"] = "unhealthy"

        # Check analytics service
        try:
            response = await client.get(f"{ANALYTICS_SERVICE_URL}/", timeout=5.0)
            health_status["services"]["analytics"] = (
                "healthy" if response.status_code == 200 else "unhealthy"
            )
        except Exception:
            health_status["services"]["analytics"] = "unhealthy"

    return health_status


# Auth routes
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """Register new user"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/register", json=user.dict()
            )
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                raise HTTPException(
                    status_code=400, detail=response.json().get("detail")
                )
            elif response.status_code == 422:
                raise HTTPException(
                    status_code=422, detail=response.json().get("detail")
                )
            else:
                print(f"Auth service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Registration failed: {response.text}",
                )
        except httpx.RequestError as e:
            print(f"Auth service connection error: {e}")
            raise HTTPException(status_code=503, detail="Auth service unavailable")


@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login user"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/login", json=user.dict())
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            else:
                raise HTTPException(status_code=500, detail="Login failed")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")


@app.get("/api/auth/me")
async def get_current_user(user_data: dict = Depends(verify_token)):
    """Get current user info"""
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_data


# URL routes
@app.post("/api/urls/shorten", status_code=status.HTTP_201_CREATED)
async def shorten_url(
    url_data: URLCreate,
    request: Request,
    user_data: Optional[dict] = Depends(verify_token),
):
    """Create shortened URL"""
    async with httpx.AsyncClient() as client:
        try:
            payload = url_data.model_dump(mode="json")
            if user_data:
                payload["user_id"] = user_data.get("user_id")

            response = await client.post(f"{URL_SERVICE_URL}/shorten", json=payload)

            if response.status_code == 201:
                return response.json()
            elif response.status_code == 409:
                raise HTTPException(
                    status_code=409, detail=response.json().get("detail")
                )
            elif response.status_code == 400:
                raise HTTPException(
                    status_code=400, detail=response.json().get("detail")
                )
            else:
                raise HTTPException(status_code=500, detail="URL shortening failed")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="URL service unavailable")


@app.get("/api/urls/user/{user_id}")
async def get_user_urls(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    user_data: dict = Depends(verify_token),
):
    """Get user's URLs (authenticated)"""
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Ensure user can only access their own URLs
    if user_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{URL_SERVICE_URL}/urls/user/{user_id}",
                params={"skip": skip, "limit": limit},
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch URLs")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="URL service unavailable")


@app.delete("/api/urls/{short_code}")
async def delete_url(short_code: str, user_data: dict = Depends(verify_token)):
    """Delete/deactivate URL (authenticated)"""
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{URL_SERVICE_URL}/{short_code}",
                params={"user_id": user_data.get("user_id")},
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail="URL not found or access denied"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to delete URL")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="URL service unavailable")


# Analytics routes
@app.get("/api/analytics/{short_code}")
async def get_analytics(short_code: str):
    """Get analytics for a short URL"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ANALYTICS_SERVICE_URL}/analytics/{short_code}"
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Short URL not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch analytics")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Analytics service unavailable")


@app.get("/api/analytics/user/{user_id}/summary")
async def get_user_analytics_summary(
    user_id: int, user_data: dict = Depends(verify_token)
):
    """Get analytics summary for user (authenticated)"""
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Ensure user can only access their own analytics
    if user_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ANALYTICS_SERVICE_URL}/analytics/user/{user_id}/summary"
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=500, detail="Failed to fetch analytics summary"
                )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Analytics service unavailable")


# URL redirection - Main feature
@app.get("/{short_code}")
async def redirect_to_url(short_code: str, request: Request):
    """Redirect to original URL and track analytics"""
    # Prevent API routes from being treated as short codes
    if short_code.startswith("api") or short_code in ["health", "docs", "openapi.json"]:
        raise HTTPException(status_code=404, detail="Not found")

    async with httpx.AsyncClient() as client:
        try:
            # Get original URL
            url_response = await client.get(f"{URL_SERVICE_URL}/{short_code}")

            if url_response.status_code == 404:
                raise HTTPException(status_code=404, detail="Short URL not found")
            elif url_response.status_code == 410:
                raise HTTPException(
                    status_code=410,
                    detail="This short URL has expired or been deactivated",
                )
            elif url_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to retrieve URL")

            url_data = url_response.json()
            original_url = url_data.get("original_url")

            # Track click asynchronously (fire and forget)
            try:
                await client.post(
                    f"{ANALYTICS_SERVICE_URL}/track",
                    json={
                        "short_code": short_code,
                        "ip_address": get_client_ip(request),
                        "user_agent": request.headers.get("user-agent"),
                        "referrer": request.headers.get("referer"),
                    },
                    timeout=2.0,
                )
            except Exception as e:
                # Don't fail redirect if analytics tracking fails
                print(f"Analytics tracking failed: {e}")

            # Redirect to original URL
            return RedirectResponse(url=original_url, status_code=307)

        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Service unavailable")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
