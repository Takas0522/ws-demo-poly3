"""
Application Insights テレメトリモジュール（集約例外パターン）

各エンドポイントで個別にエラー送信を行うのではなく、
FastAPI の集約例外ハンドラで一括して Application Insights に送信します。

APPLICATIONINSIGHTS_CONNECTION_STRING が設定されている場合のみ
Application Insights にテレメトリを送信します。
ローカル開発時は例外を握りつぶさず、ログ出力・エラーレスポンスとして返します。
"""

import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_is_configured = False


def setup_telemetry(app: FastAPI, connection_string: str | None = None, cloud_role_name: str = "unknown") -> None:
    """
    Application Insights テレメトリの初期化と集約例外ハンドラの登録。

    Args:
        app: FastAPI アプリケーションインスタンス
        connection_string: Application Insights 接続文字列。
            未設定の場合、App Insights への送信はスキップされるが、
            集約例外ハンドラは登録される。
        cloud_role_name: Application Insights の cloud_RoleName に設定する値。
    """
    global _is_configured

    # Application Insights の初期化
    if connection_string:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor

            configure_azure_monitor(
                connection_string=connection_string,
                resource=Resource.create({"service.name": cloud_role_name}),
            )
            _is_configured = True
            logger.info("Application Insights テレメトリを初期化しました")
        except ImportError:
            logger.warning(
                "azure-monitor-opentelemetry が未インストールです。"
                "Application Insights は無効です"
            )
        except Exception as e:
            logger.warning(f"Application Insights の初期化に失敗しました: {e}")
    else:
        logger.info(
            "APPLICATIONINSIGHTS_CONNECTION_STRING が未設定のため、"
            "Application Insights は無効です"
        )

    # --- 集約例外ハンドラの登録 ---

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        未ハンドル例外の集約処理。

        - Application Insights にエラーを送信
        - ログにエラーを出力（ローカル開発でも確認可能）
        - HTTPレスポンスとしてエラーを返す（例外を握りつぶさない）
        """
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        _track_exception(exc)

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        HTTPException の集約処理。

        - サーバーエラー (5xx) のみ Application Insights に送信
        - 4xx はクライアントエラーのため送信しない
        - 全てのHTTPExceptionをレスポンスとして返す
        """
        if exc.status_code >= 500:
            logger.error(
                f"HTTP {exc.status_code} on {request.method} {request.url.path}: "
                f"{exc.detail}",
                exc_info=True,
            )
            _track_exception(exc)

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


def _track_exception(exc: Exception) -> None:
    """例外を Application Insights に送信する。未構築時は何もしない。"""
    if not _is_configured:
        return

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_status(trace.StatusCode.ERROR, str(exc))
            span.record_exception(exc)
        else:
            # アクティブなスパンがない場合は新しいスパンで記録
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("unhandled_exception") as new_span:
                new_span.set_status(trace.StatusCode.ERROR, str(exc))
                new_span.record_exception(exc)
    except Exception:
        # Application Insights への送信失敗はアプリケーションに影響させない
        pass
