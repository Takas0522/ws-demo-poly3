# Auth Service

Auth Service for ws-demo-poly3 project.

## Overview

This service provides authentication and authorization functionality using FastAPI and Azure Cosmos DB.

## Features

- FastAPI web framework
- Azure Cosmos DB integration
- Health check endpoint
- Environment-based configuration

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

### Root

```bash
GET /
```

Returns basic service information.

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

## References

- FastAPI: https://fastapi.tiangolo.com/
- Azure Cosmos DB: https://docs.microsoft.com/azure/cosmos-db/
- Pydantic: https://docs.pydantic.dev/
