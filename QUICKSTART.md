# 🚀 Quick Start Guide

## ⚠️ Important: This is a Microservices Application

This application **NO LONGER uses Flask**. It has been completely rebuilt with:
- **Backend**: FastAPI microservices
- **Frontend**: React + Vite
- **Deployment**: Docker containers

## Prerequisites

- **Docker Desktop** (20.10+)
- **Docker Compose** (2.0+)
- **Git**

That's it! No need to install Python, Node, PostgreSQL, or Redis separately.

## Setup Methods

### Method 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd Shortify

# Run the setup script
./setup.sh

# Start the application
make up
# Or: docker-compose up -d
```

### Method 2: Manual Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Shortify

# Create environment file
cp .env.example .env

# Edit .env with your configuration (optional for development)
# nano .env

# Build and start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f
```

## Accessing the Application

Once running, access:

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Common Commands

```bash
# Start services
make up
# or: docker-compose up -d

# Stop services
make down
# or: docker-compose down

# View logs
make logs
# or: docker-compose logs -f

# Restart a service
make restart-api-gateway
# or: docker-compose restart api-gateway

# Rebuild services (after code changes)
docker-compose build
docker-compose up -d
```

## Database Initialization

The database is **automatically initialized** when you start the services for the first time using the `init-db.sql` script.

No need to run `flask init-db` or any manual database commands!

## Troubleshooting

### "flask init-db" error
This error means you're trying to run old Flask commands. This application no longer uses Flask.

**Solution**: Use Docker commands instead:
```bash
docker-compose up -d
```

### Port already in use
If you get port conflicts:

```bash
# Stop all services
docker-compose down

# Check what's using the port
lsof -i :8000
lsof -i :3000
lsof -i :5432

# Kill the process or change ports in docker-compose.yml
```

### Services not starting
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Permission denied on setup.sh
```bash
chmod +x setup.sh
./setup.sh
```

## Development Workflow

1. **Make code changes** in `services/` or `frontend/`

2. **Rebuild the specific service**:
```bash
# For backend services
docker-compose build auth-service
docker-compose up -d auth-service

# For frontend
docker-compose build frontend
docker-compose up -d frontend
```

3. **View logs** to debug:
```bash
docker-compose logs -f auth-service
```

## Production Deployment

For production deployment, see:
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Full deployment guide
- Use `docker-compose.prod.yml` instead of `docker-compose.yml`

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Need Help?

- Check the main [README.md](README.md)
- Review [API Documentation](docs/API.md)
- Check [Deployment Guide](docs/DEPLOYMENT.md)
- View API docs at http://localhost:8000/docs (when running)

## Architecture Overview

```
Frontend (React) → API Gateway (FastAPI) → Microservices
                                          ├── Auth Service
                                          ├── URL Service
                                          └── Analytics Service

All services connect to:
- PostgreSQL (Database)
- Redis (Cache)
```

---

**Remember**: This is a Docker-based microservices application. All services run in containers. No manual Python/Node setup required!
