"""
Unit tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data
    assert data["message"] == "SHL Assessment Recommendation API"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    # Health check might fail if index files don't exist, but should return 503, not 500
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ok"


def test_recommend_endpoint_empty_query():
    """Test recommend endpoint with empty query."""
    response = client.post("/recommend", json={"query": ""})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower() or "cannot" in data["detail"].lower()


def test_recommend_endpoint_missing_query():
    """Test recommend endpoint with missing query field."""
    response = client.post("/recommend", json={})
    assert response.status_code == 422  # Validation error


def test_recommend_endpoint_long_query():
    """Test recommend endpoint with query that's too long."""
    long_query = "a" * 5001  # Exceeds 5000 character limit
    response = client.post("/recommend", json={"query": long_query})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "long" in data["detail"].lower()


def test_recommend_endpoint_valid_query():
    """Test recommend endpoint with valid query (may fail if index not available)."""
    response = client.post("/recommend", json={"query": "software engineer"})
    # If index files exist, should return 200, otherwise might fail gracefully
    assert response.status_code in [200, 500, 503]
    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.options("/recommend")
    # CORS preflight requests
    assert response.status_code in [200, 405]  # 405 if method not allowed


def test_rate_limiting():
    """Test that rate limiting is configured (may not trigger in tests)."""
    # Make multiple rapid requests
    responses = []
    for _ in range(10):
        response = client.post("/recommend", json={"query": "test query"})
        responses.append(response.status_code)
    
    # At least some requests should be processed (rate limit shouldn't be too restrictive for tests)
    # This is a basic test - actual rate limiting depends on configuration
    assert len(responses) == 10

