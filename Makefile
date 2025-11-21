.PHONY: help setup build up down logs clean test

# Default target
help:
	@echo "Shortify - URL Shortener Microservices"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup    - Setup environment and install dependencies"
	@echo "  make build    - Build all Docker containers"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View logs from all services"
	@echo "  make clean    - Clean up containers, volumes, and cache"
	@echo "  make test     - Run tests for all services"
	@echo "  make dev      - Start services in development mode"

# Setup environment
setup:
	@echo "Setting up Shortify environment..."
	@cp .env.example .env 2>/dev/null || echo ".env already exists"
	@echo "Please update .env with your configuration"
	@echo "Setup complete!"

# Build all containers
build:
	@echo "Building all containers..."
	docker-compose build

# Start all services
up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started! Access:"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Gateway: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"

# Start services with logs
dev:
	@echo "Starting services in development mode..."
	docker-compose up

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up everything
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f
	@echo "Cleanup complete!"

# Run tests
test:
	@echo "Running tests..."
	@cd services/auth-service && python -m pytest
	@cd services/url-service && python -m pytest
	@cd services/analytics-service && python -m pytest
	@echo "All tests completed!"

# Restart specific service
restart-%:
	docker-compose restart $*

# View logs for specific service
logs-%:
	docker-compose logs -f $*

# Database migrations
migrate:
	@echo "Running database migrations..."
	docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f /docker-entrypoint-initdb.d/init-db.sql
