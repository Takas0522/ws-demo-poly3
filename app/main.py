from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.api.v1 import health, services
from app.repositories.service_repository import service_repository
from app.utils.telemetry import setup_telemetry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="利用サービス設定サービス",
    description="サービス設定・割り当て管理API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Application Insights テレメトリ & 集約例外ハンドラの初期化
setup_telemetry(app, settings.applicationinsights_connection_string or None, cloud_role_name="service-setting-service")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(services.router, tags=["Services"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.service_name} on port {settings.port}")
    logger.info(f"Cosmos DB Endpoint: {settings.cosmos_db_endpoint}")
    logger.info(f"Database: {settings.cosmos_db_database}")
    # Initialize repository
    await service_repository.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.service_name}")
    # Close repository
    await service_repository.close()
