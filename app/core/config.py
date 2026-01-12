"""
Configuration settings for the authentication service.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file first (override=True to ensure fresh values)
load_dotenv("/workspaces/ws-demo-poly-integration/.env", override=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )

    # Server settings
    auth_service_port: int = 3001
    node_env: str = "development"

    # JWT settings
    jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "RS256"
    jwt_expires_in: int = 3600  # 1 hour in seconds
    jwt_refresh_expires_in: int = 604800  # 7 days in seconds
    jwt_issuer: str = "saas-auth-service"
    jwt_audience: str = "saas-app"
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"

    # CosmosDB settings
    cosmosdb_endpoint: str = "https://localhost:8081"
    cosmosdb_key: str = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
    cosmosdb_database: str = "saas-management-dev"

    # Redis settings (for permission caching)
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    def __init__(self, **kwargs):
        """Initialize settings and ensure CosmosDB key is correctly loaded."""
        super().__init__(**kwargs)
        # Override with environment variable if available
        if 'COSMOSDB_KEY' in os.environ:
            self.cosmosdb_key = os.environ['COSMOSDB_KEY']

    # CORS settings
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate limiting
    rate_limit_window_ms: int = 900000  # 15 minutes
    rate_limit_max_requests: int = 100
    feature_rate_limiting: str = "enabled"

    # Security settings
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special_chars: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
