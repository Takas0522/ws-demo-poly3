"""認証認可サービス - メインアプリケーション"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from azure.cosmos.aio import CosmosClient

from app.config import settings
from app.api import auth, users, roles

# ロガー設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def init_cosmos_db(app: FastAPI) -> None:
    """
    Cosmos DB初期化
    
    Args:
        app: FastAPIアプリケーションインスタンス
    
    Raises:
        Exception: Cosmos DB初期化に失敗した場合
    """
    try:
        # 設定検証
        settings.validate()

        # Cosmos DBクライアント作成
        cosmos_client = CosmosClient.from_connection_string(
            settings.COSMOS_DB_CONNECTION_STRING
        )

        # データベース取得
        database = cosmos_client.get_database_client(settings.COSMOS_DB_DATABASE_NAME)

        # コンテナ取得
        cosmos_container = database.get_container_client(
            settings.COSMOS_DB_CONTAINER_NAME
        )

        # app.stateに保存
        app.state.cosmos_client = cosmos_client
        app.state.cosmos_container = cosmos_container

        logger.info("Cosmos DB initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB: {e}")
        raise


async def cleanup_cosmos_db(app: FastAPI) -> None:
    """
    Cosmos DBクリーンアップ
    
    Args:
        app: FastAPIアプリケーションインスタンス
    """
    if hasattr(app.state, "cosmos_client"):
        await app.state.cosmos_client.close()
        logger.info("Cosmos DB connection closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションライフサイクル管理
    
    Args:
        app: FastAPIアプリケーションインスタンス
    
    Yields:
        None: アプリケーション実行中
    """
    # 起動時
    logger.info("Starting authentication service...")
    await init_cosmos_db(app)
    yield
    # 終了時
    logger.info("Shutting down authentication service...")
    await cleanup_cosmos_db(app)


# FastAPIアプリ作成
app = FastAPI(
    title="Authentication Service",
    description="マルチテナント管理アプリケーション - 認証認可サービス",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(
    auth.router,
    prefix=f"/api/{settings.API_VERSION}/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix=f"/api/{settings.API_VERSION}/users",
    tags=["Users"],
)

app.include_router(
    roles.router,
    prefix=f"/api/{settings.API_VERSION}",
    tags=["Roles"],
)


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
