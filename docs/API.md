# 📚 API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Auth Endpoints

### Register User
```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00Z",
  "is_active": true
}
```

### Login
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "johndoe"
}
```

### Get Current User
```http
GET /api/auth/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "user_id": 1,
  "username": "johndoe",
  "email": "john@example.com"
}
```

---

## URL Endpoints

### Shorten URL
```http
POST /api/urls/shorten
```

**Request Body:**
```json
{
  "original_url": "https://example.com/very-long-url",
  "custom_alias": "my-link"  // optional
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "original_url": "https://example.com/very-long-url",
  "short_code": "my-link",
  "full_short_url": "http://localhost:8000/my-link",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": null,
  "is_active": true
}
```

### Get User URLs
```http
GET /api/urls/user/{user_id}?skip=0&limit=100
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "original_url": "https://example.com/page",
    "short_code": "abc123",
    "full_short_url": "http://localhost:8000/abc123",
    "total_clicks": 42,
    "created_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
]
```

### Delete URL
```http
DELETE /api/urls/{short_code}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "message": "URL deactivated successfully"
}
```

### Redirect to Original URL
```http
GET /{short_code}
```

**Response:** `307 Temporary Redirect`
- Redirects to original URL
- Tracks analytics in background

---

## Analytics Endpoints

### Get URL Analytics
```http
GET /api/analytics/{short_code}
```

**Response:** `200 OK`
```json
{
  "total_clicks": 150,
  "unique_ips": 87,
  "clicks_today": 12,
  "clicks_this_week": 45,
  "clicks_this_month": 120,
  "top_referrers": [
    {
      "referrer": "https://twitter.com",
      "count": 35
    },
    {
      "referrer": "https://facebook.com",
      "count": 28
    }
  ],
  "clicks_by_date": [
    {
      "date": "2024-01-01",
      "clicks": 12
    },
    {
      "date": "2024-01-02",
      "clicks": 18
    }
  ]
}
```

### Get User Analytics Summary
```http
GET /api/analytics/user/{user_id}/summary
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "total_urls": 25,
  "active_urls": 23,
  "total_clicks": 1547,
  "recent_clicks_7_days": 234,
  "top_performing_url": {
    "short_code": "best-link",
    "original_url": "https://example.com/popular",
    "clicks": 456
  }
}
```

---

## Health Check

### Gateway Health
```http
GET /health
```

**Response:** `200 OK`
```json
{
  "gateway": "healthy",
  "services": {
    "auth": "healthy",
    "url": "healthy",
    "analytics": "healthy"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Custom alias already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Short URL not found"
}
```

### 409 Conflict
```json
{
  "detail": "This custom alias is already taken"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. In production, consider implementing:
- 100 requests per minute for anonymous users
- 1000 requests per minute for authenticated users
- Burst allowance of 20 requests

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Test endpoints directly from the browser
- See request/response schemas
- View authentication requirements
- Download OpenAPI specification
