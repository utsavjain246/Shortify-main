#!/bin/bash
# Setup script for Shortify - Microservices Architecture

set -e  # Exit on error

echo "🚀 Setting up Shortify..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Visit: https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your configuration."
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

echo "🐳 Building Docker images..."
docker-compose build

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application, run:"
echo "  docker-compose up -d"
echo ""
echo "Or use the Makefile:"
echo "  make up"
echo ""
echo "Access the application at:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Gateway: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
