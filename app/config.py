"""アプリケーション設定"""
import os
from typing import List
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


class Settings:
    """アプリケーション設定クラス"""

    # アプリケーション設定
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "auth-service")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_VERSION: str = os.getenv("API_VERSION", "v1")

    # Cosmos DB設定
    COSMOS_DB_CONNECTION_STRING: str = os.getenv("COSMOS_DB_CONNECTION_STRING", "")
    COSMOS_DB_DATABASE_NAME: str = os.getenv("COSMOS_DB_DATABASE_NAME", "management-app")
    COSMOS_DB_CONTAINER_NAME: str = os.getenv("COSMOS_DB_CONTAINER_NAME", "auth")

    # JWT設定
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")  # Required, no default
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # 特権テナントID設定
    PRIVILEGED_TENANT_IDS: List[str] = (
        os.getenv("PRIVILEGED_TENANT_IDS", "tenant_privileged").split(",")
        if os.getenv("PRIVILEGED_TENANT_IDS")
        else ["tenant_privileged"]
    )

    # Application Insights
    APPINSIGHTS_INSTRUMENTATIONKEY: str = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY", "")

    # CORS設定
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")

    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.ENVIRONMENT == "development"

    def validate(self) -> None:
        """必須設定の検証"""
        errors = []

        if not self.COSMOS_DB_CONNECTION_STRING:
            errors.append("COSMOS_DB_CONNECTION_STRING is required")

        if not self.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY is required")
        elif len(self.JWT_SECRET_KEY) < 64:
            errors.append("JWT_SECRET_KEY must be at least 64 characters")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


# シングルトンインスタンス
settings = Settings()
