"""
Configuration settings for the authentication service.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file="../../../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Server settings
    auth_service_port: int = 3001
    node_env: str = "development"
    
    # JWT settings
    jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 3600  # 1 hour in seconds
    jwt_refresh_expires_in: int = 604800  # 7 days in seconds
    jwt_issuer: str = "saas-auth-service"
    jwt_audience: str = "saas-app"
    
    # CosmosDB settings
    cosmosdb_endpoint: str = "https://localhost:8081"
    cosmosdb_key: str = ""
    cosmosdb_database: str = "saas-management"
    
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
