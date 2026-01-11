"""
Main FastAPI application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.services import cosmos_db
from app.api import auth_router, root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Initializing CosmosDB connection...")
    await cosmos_db.initialize()
    if cosmos_db._initialized:
        print("✅ CosmosDB initialized successfully")
    else:
        print("❌ Warning: CosmosDB connection failed")
        print("   Please ensure CosmosDB Emulator is running")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="SaaS Authentication Service",
    description="JWT-based authentication service with tenant-aware multi-device session management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(root_router)
app.include_router(auth_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.auth_service_port,
        reload=settings.node_env == "development",
    )
