# 🚀 Deployment Guide

This guide covers deploying Shortify to various platforms.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Environment Configuration](#environment-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Monitoring](#monitoring)

---

## Local Development

### Prerequisites
- Docker Desktop 20.10+
- Docker Compose 2.0+
- Git

### Steps

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/Shortify.git
cd Shortify
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start Services**
```bash
docker-compose up -d
```

4. **Access Application**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Production Deployment

1. **Set Environment Variables**
```bash
export POSTGRES_PASSWORD="your_secure_password"
export JWT_SECRET_KEY="your_secret_key_min_32_chars"
export BASE_URL="https://yourdomain.com"
```

2. **Deploy with Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Verify Deployment**
```bash
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health
```

### Using Pre-built Images

```bash
# Pull images from GitHub Container Registry
docker pull ghcr.io/yourusername/shortify-auth-service:latest
docker pull ghcr.io/yourusername/shortify-url-service:latest
docker pull ghcr.io/yourusername/shortify-analytics-service:latest
docker pull ghcr.io/yourusername/shortify-api-gateway:latest
docker pull ghcr.io/yourusername/shortify-frontend:latest

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

---

## Cloud Platforms

### AWS Deployment

#### Option 1: EC2 Instance

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t3.medium or larger
   - Security Group: Allow ports 80, 443, 22

2. **Install Docker**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

3. **Deploy Application**
```bash
git clone https://github.com/yourusername/Shortify.git
cd Shortify
cp .env.example .env
# Edit .env
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 2: ECS (Elastic Container Service)

1. **Create Task Definitions** for each service
2. **Create ECS Cluster**
3. **Create Services** with Load Balancer
4. **Configure RDS** for PostgreSQL
5. **Configure ElastiCache** for Redis

### Google Cloud Platform

#### Google Kubernetes Engine (GKE)

1. **Create Kubernetes Cluster**
```bash
gcloud container clusters create shortify-cluster \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --region=us-central1
```

2. **Deploy with Kubernetes**
```bash
kubectl apply -f k8s/
```

### DigitalOcean

#### Droplet Deployment

1. **Create Droplet**
   - Ubuntu 22.04
   - 2GB RAM minimum
   - Enable monitoring

2. **Install Dependencies**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
```

3. **Deploy Application**
```bash
git clone https://github.com/yourusername/Shortify.git
cd Shortify
docker-compose -f docker-compose.prod.yml up -d
```

#### App Platform

1. **Create App** from GitHub repository
2. **Configure Services**:
   - auth-service (Dockerfile: services/auth-service/Dockerfile)
   - url-service (Dockerfile: services/url-service/Dockerfile)
   - analytics-service (Dockerfile: services/analytics-service/Dockerfile)
   - api-gateway (Dockerfile: services/api-gateway/Dockerfile)
   - frontend (Dockerfile: frontend/Dockerfile)
3. **Add PostgreSQL Database**
4. **Add Redis Database**
5. **Set Environment Variables**

### Heroku

**Note**: Heroku requires special configuration for multiple services.

1. **Create Apps** (one per service)
```bash
heroku create shortify-auth
heroku create shortify-url
heroku create shortify-analytics
heroku create shortify-gateway
heroku create shortify-frontend
```

2. **Add PostgreSQL and Redis**
```bash
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
```

3. **Deploy Each Service**
```bash
git subtree push --prefix services/auth-service heroku-auth main
```

---

## Environment Configuration

### Required Environment Variables

```env
# Database
POSTGRES_USER=shortify_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=shortify_db
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# JWT Authentication
JWT_SECRET_KEY=<random-32-char-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
BASE_URL=https://your-domain.com
ENVIRONMENT=production

# Frontend
VITE_API_URL=https://api.your-domain.com
```

### Generating Secure Keys

```bash
# Generate JWT Secret
openssl rand -hex 32

# Generate PostgreSQL Password
openssl rand -base64 24
```

---

## SSL/TLS Setup

### Using Let's Encrypt (Certbot)

1. **Install Certbot**
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Obtain Certificate**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

3. **Auto-renewal**
```bash
sudo certbot renew --dry-run
```

### Nginx Configuration

Create `/etc/nginx/sites-available/shortify`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Redirect short URLs
    location ~ ^/[a-zA-Z0-9_-]+$ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring

### Health Checks

```bash
# Check all services
curl https://yourdomain.com/health

# Check individual services
docker-compose ps
```

### Logging

```bash
# View logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f api-gateway

# Save logs to file
docker-compose logs > logs.txt
```

### Metrics

Consider integrating:
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **Sentry** for error tracking
- **LogRocket** for frontend monitoring

---

## Backup & Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U shortify_user shortify_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U shortify_user shortify_db < backup.sql
```

### Automated Backups

Add to crontab:
```bash
0 2 * * * /path/to/backup-script.sh
```

---

## Scaling

### Horizontal Scaling

Run multiple instances of services:

```yaml
# docker-compose.prod.yml
api-gateway:
  deploy:
    replicas: 3
```

### Load Balancing

Use nginx or cloud load balancers to distribute traffic across instances.

---

## Troubleshooting

### Services won't start
```bash
docker-compose logs <service-name>
docker-compose restart <service-name>
```

### Database connection issues
- Check DATABASE_URL format
- Verify PostgreSQL is running
- Check network connectivity

### High memory usage
- Review resource limits in docker-compose.prod.yml
- Consider upgrading server
- Enable Redis persistence with limits

---

## Security Checklist

- [ ] Use strong, unique passwords
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Set up firewall rules
- [ ] Enable database encryption
- [ ] Use environment variables for secrets
- [ ] Regular security updates
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts
- [ ] Regular backups
- [ ] Enable Docker security scanning
