"""
Integration test configuration and fixtures
"""
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Test environment variables
TEST_JWT_SECRET = "test-secret-key-for-integration-tests"
TEST_COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "")
TEST_COSMOS_KEY = os.getenv("COSMOS_KEY", "")

# Test token (normally would be obtained from auth service)
TEST_ADMIN_TOKEN = os.getenv("TEST_ADMIN_TOKEN", "")


@pytest.fixture
def test_client() -> Generator:
    """
    Create a test client for the FastAPI application
    """
    from app.main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_test_client() -> Generator:
    """
    Create an async test client for the FastAPI application
    """
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> dict:
    """
    Get authorization headers with admin token
    """
    token = TEST_ADMIN_TOKEN or "mock-jwt-token-for-testing"
    return {
        "Authorization": f"Bearer {token}"
    }


def pytest_configure(config):
    """
    Configure pytest with custom markers
    """
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
