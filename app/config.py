from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service settings
    service_name: str = "service-setting-service"
    port: int = 8003

    # Cosmos DB settings
    cosmos_db_endpoint: str
    cosmos_db_key: str
    cosmos_db_database: str = "service_management"
    cosmos_db_container: str = "services"
    cosmos_db_connection_verify: bool = True

    # JWT settings
    jwt_secret: str = "your-development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Application Insights settings
    applicationinsights_connection_string: str = ""

    # Log settings
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
