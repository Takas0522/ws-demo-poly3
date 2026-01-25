from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "Auth Service"
    app_version: str = "0.1.0"
    debug: bool = False

    # Cosmos DB
    cosmosdb_endpoint: str = ""
    cosmosdb_key: str = ""
    cosmosdb_database: str = "auth_db"
    cosmosdb_container: str = "users"
    
    # JWT Configuration
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 60  # 1 hour
    jwt_refresh_token_expire_days: int = 7  # 7 days
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "management-app"
    jwt_private_key_path: str = "keys/private_key.pem"
    jwt_public_key_path: str = "keys/public_key.pem"
    
    # Security
    password_bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    account_lock_duration_minutes: int = 30
    privileged_tenant_id: str = "tenant-001"


settings = Settings()
