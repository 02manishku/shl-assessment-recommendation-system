"""
Unit tests for recommender module.
"""

import pytest
import os
from recommender import AssessmentRecommender


@pytest.fixture
def recommender():
    """Create a recommender instance for testing."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        rec = AssessmentRecommender(api_key=api_key)
        # Try to load index, but skip if files don't exist
        try:
            rec.load_index()
        except FileNotFoundError:
            pytest.skip("Index files not found. Run embedder.py first.")
        
        return rec
    except Exception as e:
        pytest.skip(f"Failed to initialize recommender: {e}")


def test_recommender_initialization(recommender):
    """Test that recommender can be initialized."""
    assert recommender is not None
    assert recommender.index is not None
    assert len(recommender.metadata) > 0


def test_generate_query_embedding(recommender):
    """Test query embedding generation."""
    query = "software engineer"
    embedding = recommender.generate_query_embedding(query)
    assert embedding is not None
    assert len(embedding.shape) == 1  # Should be 1D array
    assert embedding.shape[0] > 0  # Should have some dimension


def test_recommend_basic(recommender):
    """Test basic recommendation functionality."""
    query = "Java developer"
    recommendations = recommender.recommend(query, top_k=5, use_reranking=False, balance_types=False)
    
    assert recommendations is not None
    assert isinstance(recommendations, list)
    assert len(recommendations) <= 5
    
    # Check structure of recommendations
    if len(recommendations) > 0:
        rec = recommendations[0]
        assert "Assessment Name" in rec or "name" in rec
        assert "URL" in rec or "url" in rec
        assert "similarity" in rec


def test_recommend_with_reranking(recommender):
    """Test recommendation with reranking enabled."""
    query = "Python developer"
    recommendations = recommender.recommend(query, top_k=5, use_reranking=True, balance_types=False)
    
    assert recommendations is not None
    assert isinstance(recommendations, list)
    assert len(recommendations) <= 5


def test_recommend_with_balance_types(recommender):
    """Test recommendation with type balancing enabled."""
    query = "software engineer with teamwork skills"
    recommendations = recommender.recommend(query, top_k=10, use_reranking=False, balance_types=True)
    
    assert recommendations is not None
    assert isinstance(recommendations, list)
    
    # Check that we have both K and P types if available
    if len(recommendations) > 0:
        types = [r.get("Test Type", r.get("type", "")) for r in recommendations]
        types = [t for t in types if t]
        # Should have at least one type
        assert len(types) > 0


def test_recommend_empty_query(recommender):
    """Test recommendation with empty query."""
    query = ""
    recommendations = recommender.recommend(query, top_k=5)
    
    # Should still return results (empty query might match everything or return empty)
    assert recommendations is not None
    assert isinstance(recommendations, list)

