from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "Auth Service"
    app_version: str = "0.1.0"
    debug: bool = False

    # Cosmos DB
    cosmos_endpoint: str = ""
    cosmos_key: str = ""
    cosmos_database_name: str = "auth_db"
    cosmos_container_name: str = "users"


settings = Settings()
