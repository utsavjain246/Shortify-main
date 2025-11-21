# 🔗 Shortify - Modern URL Shortener

> **⚠️ NEW ARCHITECTURE**: This project has been completely rebuilt with microservices! No longer uses Flask. See [QUICKSTART.md](QUICKSTART.md) for setup.

A production-ready URL shortener built with microservices architecture, featuring real-time analytics, QR code generation, and a beautiful minimalistic UI.

[![Test Status](https://img.shields.io/github/workflow/status/yourusername/Shortify/Run%20Tests?label=tests)](https://github.com/yourusername/Shortify/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

### Core Features
- 🚀 **Fast URL Shortening** - Generate short links in milliseconds
- 🎨 **Custom Aliases** - Create branded, memorable short links
- 📊 **Real-time Analytics** - Track clicks, referrers, and engagement
- 📱 **QR Code Generation** - Instant QR codes for all short URLs
- 🌓 **Dark Mode** - Beautiful UI with light/dark theme support
- 🔐 **User Authentication** - Secure JWT-based authentication
- ⚡ **Redis Caching** - Lightning-fast URL lookups
- 📈 **Comprehensive Dashboard** - Manage and analyze all your links

### Technical Features
- 🏗️ **Microservices Architecture** - Scalable and maintainable
- 🐳 **Docker Compose** - Easy deployment and development
- 🔄 **CI/CD Pipeline** - Automated testing and deployment
- 🔒 **Security First** - SQL injection prevention, XSS protection
- 📝 **Auto-generated API Docs** - FastAPI interactive documentation
- 🧪 **Test Coverage** - Comprehensive test suite
- 🎯 **Production Ready** - Resource limits, health checks, monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                              │
│              React + Vite + Tailwind CSS                     │
│                    (Port 3000/80)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    API Gateway                               │
│        FastAPI - Request Routing & CORS                     │
│                    (Port 8000)                               │
└────┬─────────────┬──────────────┬────────────────┬─────────┘
     │             │              │                │
     ▼             ▼              ▼                ▼
┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌──────────────┐
│  Auth   │  │   URL   │  │  Analytics  │  │  PostgreSQL  │
│ Service │  │ Service │  │   Service   │  │   Database   │
│  :8003  │  │  :8001  │  │    :8002    │  │    :5432     │
└────┬────┘  └────┬────┘  └──────┬──────┘  └──────┬───────┘
     │            │               │                │
     └────────────┴───────────────┴────────────────┘
                          │
                    ┌─────▼─────┐
                    │   Redis   │
                    │   Cache   │
                    │   :6379   │
                    └───────────┘
```

## 📦 Services

### 1. **API Gateway** (Port 8000)
- Single entry point for all requests
- Request routing to microservices
- JWT authentication middleware
- CORS handling
- Rate limiting

### 2. **Auth Service** (Port 8003)
- User registration and login
- JWT token generation and validation
- Password hashing (bcrypt)
- User management

### 3. **URL Service** (Port 8001)
- URL shortening with custom aliases
- URL retrieval and validation
- QR code generation
- Redis caching
- URL expiration

### 4. **Analytics Service** (Port 8002)
- Click event tracking
- Real-time analytics
- Visitor statistics
- Referrer tracking
- Time-based reports

### 5. **Frontend** (Port 3000/80)
- React with Vite
- Tailwind CSS
- Responsive design
- Dark mode support
- Real-time updates

## 🚀 Quick Start

> **First time here?** Check [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions!

### Prerequisites
- Docker Desktop (20.10+)
- Docker Compose (2.0+)
- Git

**That's it!** No Python, Node, PostgreSQL, or Redis installation needed.

### One-Command Setup

```bash
# Clone, setup, and start
git clone https://github.com/yourusername/Shortify.git
cd Shortify
./setup.sh && make up
```

### Manual Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Shortify.git
cd Shortify
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration (optional for dev)
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### ⚠️ Important Notes

- **No Flask commands**: This app uses FastAPI, not Flask
- **All services run in Docker**: No manual database setup needed
- **Database auto-initializes**: `init-db.sql` runs automatically
- **First build takes time**: Docker needs to build all images

## 🛠️ Development

### Project Structure
```
Shortify/
├── services/
│   ├── api-gateway/        # API Gateway service
│   ├── auth-service/       # Authentication service
│   ├── url-service/        # URL shortening service
│   ├── analytics-service/  # Analytics service
│   └── init-db.sql        # Database initialization
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   └── context/       # React context
│   └── public/
├── .github/workflows/     # CI/CD pipelines
├── docker-compose.yml     # Development compose
├── docker-compose.prod.yml # Production compose
├── Makefile              # Development commands
└── README.md
```

### Available Commands

```bash
# Setup environment
make setup

# Start services
make up

# View logs
make logs

# Stop services
make down

# Run tests
make test

# Clean up
make clean

# Restart specific service
make restart-auth-service

# View service logs
make logs-url-service
```

### Running Tests

```bash
# Run all tests
make test

# Run tests for specific service
cd services/auth-service
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html
```

## 🔐 Environment Variables

### Required Variables

```env
# Database
POSTGRES_USER=shortify_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=shortify_db
DATABASE_URL=postgresql://user:pass@postgres:5432/shortify_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your_super_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
VITE_API_URL=http://localhost:8000

# Production
BASE_URL=https://yourdomain.com
```

## 📊 API Documentation

Once the services are running, access the interactive API documentation:

- **API Gateway**: http://localhost:8000/docs
- **Auth Service**: http://localhost:8003/docs
- **URL Service**: http://localhost:8001/docs
- **Analytics Service**: http://localhost:8002/docs

### Example API Calls

#### Shorten a URL
```bash
curl -X POST http://localhost:8000/api/urls/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/very-long-url",
    "custom_alias": "my-link"
  }'
```

#### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

#### Get Analytics
```bash
curl http://localhost:8000/api/analytics/my-link
```

## 🚢 Deployment

### Docker Deployment

#### Development
```bash
docker-compose up -d
```

#### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

1. Build services
```bash
cd services/auth-service && docker build -t shortify-auth .
cd ../url-service && docker build -t shortify-url .
cd ../analytics-service && docker build -t shortify-analytics .
cd ../api-gateway && docker build -t shortify-gateway .
cd ../../frontend && docker build -t shortify-frontend .
```

2. Run with environment variables
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed cloud deployment guides for:
- AWS (ECS, EC2)
- Google Cloud (GKE)
- Azure (AKS)
- DigitalOcean
- Heroku

## 🧪 Testing

### Backend Tests
```bash
# Run all service tests
make test

# Test specific service
cd services/auth-service
pytest tests/ -v --cov
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Tests
```bash
# Start services
docker-compose up -d

# Run integration tests
pytest integration_tests/ -v
```

## 📈 Monitoring & Performance

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health

# Individual services
curl http://localhost:8003/  # Auth
curl http://localhost:8001/  # URL
curl http://localhost:8002/  # Analytics
```

### Metrics
- Request latency
- Cache hit ratio
- Database query performance
- Error rates
- Service availability

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api-gateway

# View last 100 lines
docker-compose logs --tail=100 url-service
```

## 🔒 Security

- **SQL Injection Prevention**: Parameterized queries with psycopg2
- **XSS Protection**: Input sanitization and validation
- **CORS Configuration**: Controlled cross-origin requests
- **Password Hashing**: bcrypt with salt
- **JWT Authentication**: Secure token-based auth
- **HTTPS**: SSL/TLS encryption (production)
- **Rate Limiting**: Request throttling
- **Security Headers**: X-Frame-Options, CSP, etc.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React
- Write tests for new features
- Update documentation
- Keep commits atomic and well-described

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - [GitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- React team for the frontend library
- Tailwind CSS for the styling framework
- PostgreSQL and Redis teams

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Shortify/issues)
- **Email**: support@yourdomain.com
- **Documentation**: [docs/](docs/)

## 🗺️ Roadmap

- [ ] Link expiration dates
- [ ] Bulk URL shortening
- [ ] Link password protection
- [ ] Advanced analytics (geolocation, devices)
- [ ] Custom domains
- [ ] API rate limiting per user
- [ ] Webhook notifications
- [ ] Browser extension
- [ ] Mobile apps (iOS/Android)

---

**Built with ❤️ using modern microservices architecture**
