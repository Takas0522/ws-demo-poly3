# Auth Service (認証認可サービス)

Auth Service for ws-demo-poly3 project.

## Overview

This service provides authentication and authorization functionality using FastAPI and Azure Cosmos DB. It handles user authentication via JWT tokens, role-based access control, and validates user access to the management application.

## Features

- JWT-based authentication and authorization
- User login and token generation
- Token verification and refresh
- Role-based access control (全体管理者, 管理者, 閲覧者)
- Privileged tenant access validation
- Login attempt tracking and account lockout
- FastAPI web framework
- Azure Cosmos DB integration
- Health check endpoint
- Environment-based configuration

## Documentation

### Service Documentation
- [Service Specification](./docs/services/auth/spec.md) - Complete service specification including authentication flows, API endpoints, and security requirements
- [Data Model](./docs/services/auth/data-model.md) - Cosmos DB schema for users, roles, and login attempts

### Architecture Documentation
- [API Guidelines](./docs/architecture/api-guidelines.md) - REST API design standards
- [Authentication Flow](./docs/architecture/authentication-flow.md) - JWT-based authentication and authorization flows
- [Database Design](./docs/architecture/database-design.md) - Cosmos DB container design and partition strategy

## Setup

### Prerequisites

- Python 3.11+
- Azure Cosmos DB account (optional for local development)
- Docker Desktop (v20.10以上) - Cosmos DB Emulatorを使用する場合

### Installation

```bash
# Install dependencies using pip
pip install -r requirements.txt

# Or using poetry
poetry install
```

### Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your Cosmos DB credentials:
- `COSMOSDB_ENDPOINT`: Your Cosmos DB endpoint URL
- `COSMOSDB_KEY`: Your Cosmos DB access key
- `COSMOSDB_DATABASE`: Database name
- `COSMOSDB_CONTAINER`: Container name

## Running the Service

### Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Or using poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

The service will be available at:
- API: http://localhost:8001
- API Documentation: http://localhost:8001/docs
- Alternative API Documentation: http://localhost:8001/redoc

## API Endpoints

### Health Check

```bash
GET /health
```

Returns service health status including Cosmos DB connection status.

Response:
```json
{
  "status": "healthy",
  "service": "Auth Service",
  "version": "0.1.0",
  "cosmos_db": "connected"
}
```

### Authentication

```bash
# Login
POST /api/auth/login
Content-Type: application/json

{
  "loginId": "admin@example.com",
  "password": "password"
}

# Verify Token
POST /api/auth/verify
Authorization: Bearer <jwt_token>

# Refresh Token
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "<refresh_token>"
}
```

### Root

```bash
GET /
```

Returns basic service information.

## Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| 全体管理者 | System-wide administrator | Full access to all services and operations |
| 管理者 | Administrator | Can manage regular tenants and users |
| 閲覧者 | Read-only user | Can only view information |

## Access Control

**IMPORTANT**: Only users belonging to **privileged tenants** can log in to the management application.

## Database Schema

### Containers

- `users` - User information and credentials (Partition key: `/id`)
- `login-attempts` - Login attempt tracking for security (Partition key: `/loginId`)
- `role-configs` - Role definitions per service (Partition key: `/serviceId`)

See [Data Model documentation](./docs/services/auth/data-model.md) for detailed schema.

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

## Project Structure

```
services/auth/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration settings
│   │   └── cosmos.py        # Cosmos DB client
│   └── models/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

### Code Style

This project uses:
- `black` for code formatting
- `ruff` for linting

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/
```

### Seeding Data

```bash
# Run data seeding script
python scripts/seed_data.py

# Setup all containers and seed data
python scripts/setup_all.py
```

## Related Services

- **User Management Service** (ws-demo-poly2) - Manages tenants and tenant users
- **Service Setting Service** (ws-demo-poly4) - Manages service assignments to tenants
- **Frontend** (ws-demo-poly1) - Web UI for the management application

## License

This project is part of the ws-demo-poly workspace.

## References

- FastAPI: https://fastapi.tiangolo.com/
- Azure Cosmos DB: https://docs.microsoft.com/azure/cosmos-db/
- Pydantic: https://docs.pydantic.dev/
