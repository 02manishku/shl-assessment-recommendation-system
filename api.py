"""
SHL Assessment Recommendation API
FastAPI backend for the recommendation system.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import os
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json

from recommender import AssessmentRecommender

load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # Add file handler if needed
        # logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="API for recommending SHL assessments based on job descriptions",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for cross-origin requests
# In production, replace ["*"] with specific allowed origins, e.g., ["https://yourdomain.com"]
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if allowed_origins == ["*"]:
    logger.warning("⚠️  CORS is allowing all origins. For production, set ALLOWED_ORIGINS in .env")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommender (lazy loading)
recommender: Optional[AssessmentRecommender] = None


def get_recommender() -> AssessmentRecommender:
    """Get or initialize the recommender instance."""
    global recommender
    if recommender is None:
        try:
            recommender = AssessmentRecommender()
            recommender.load_index()
            logger.info("Recommender initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing recommender: {e}")
            raise
    return recommender


# Request/Response models
class RecommendationRequest(BaseModel):
    """Request model for recommendation endpoint."""
    query: str
    top_k: Optional[int] = 10  # Number of recommendations to return (default: 10)


class RecommendationItem(BaseModel):
    """Model for a single recommendation."""
    name: str
    url: str
    type: Optional[str] = None
    similarity: float
    description: Optional[str] = None
    duration: Optional[str] = None
    difficulty: Optional[str] = None
    skills: Optional[str] = None
    prerequisites: Optional[str] = None
    use_cases: Optional[str] = None
    industry: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for recommendation endpoint."""
    query: str
    recommendations: List[RecommendationItem]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "SHL Assessment Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "recommend": "/recommend"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns {"status": "ok"} if the API is running.
    """
    try:
        # Try to get recommender to verify it's working
        get_recommender()
        return HealthResponse(status="ok")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    # Log request
    start_time = time.time()
    logger.info(f"[{request_id}] {request.method} {request.url.path} - Client: {get_remote_address(request)}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    elapsed_time = time.time() - start_time
    logger.info(f"[{request_id}] Completed in {elapsed_time:.3f}s - Status: {response.status_code}")
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
@limiter.limit(os.getenv("RATE_LIMIT", "60/minute"))
async def recommend(request: Request, recommendation_request: RecommendationRequest):
    """
    Get assessment recommendations based on a query or job description.
    
    Args:
        request: FastAPI request object (for rate limiting)
        recommendation_request: Request containing the query text
        
    Returns:
        List of recommended assessments with similarity scores
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    try:
        # Validate query
        if not recommendation_request.query or not recommendation_request.query.strip():
            logger.warning(f"[{request_id}] Empty query received")
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        # Validate query length (max 5000 characters to prevent abuse)
        query_length = len(recommendation_request.query.strip())
        max_query_length = 5000
        if query_length > max_query_length:
            logger.warning(f"[{request_id}] Query too long: {query_length} characters")
            raise HTTPException(
                status_code=400,
                detail=f"Query too long. Maximum length is {max_query_length} characters. Your query is {query_length} characters."
            )
        
        # Get recommender
        recommender = get_recommender()
        
        # Get recommendations with reranking enabled for better relevance
        start_time = time.time()
        
        query_preview = recommendation_request.query[:100] + '...' if len(recommendation_request.query) > 100 else recommendation_request.query
        logger.info(f"[{request_id}] Processing recommendation request - Query: {query_preview}")
        
        # Use top_k from request, clamped between 1 and 20
        requested_top_k = max(1, min(20, recommendation_request.top_k))
        recommendations = recommender.recommend(
            recommendation_request.query, 
            top_k=requested_top_k, 
            use_reranking=True, 
            balance_types=True
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] Generated {len(recommendations)} recommendations in {elapsed_time:.2f} seconds")
        
        # Helper function to clean nan values
        def clean_value(value):
            """Convert pandas nan/None to None, otherwise return string."""
            if value is None:
                return None
            if isinstance(value, float) and (value != value or value == float('nan')):  # Check for NaN
                return None
            if isinstance(value, str) and (value.lower() == 'nan' or value.strip() == ''):
                return None
            return str(value) if value else None
        
        # Format response - PRESERVE ORDER from recommender (already reranked by Gemini)
        # Do NOT sort or reorder - the recommender returns results in the correct priority order
        recommendation_items = []
        logger.info(f"[{request_id}] Formatting {len(recommendations)} recommendations (preserving rerank order)")
        
        for idx, rec in enumerate(recommendations, 1):
            name = rec.get('Assessment Name', rec.get('name', 'Unknown'))
            url = rec.get('URL', rec.get('url', ''))
            test_type = rec.get('Test Type', rec.get('type', ''))
            similarity = rec.get('similarity', 0.0)
            rerank_pos = rec.get('rerank_position', 0)
            
            # Log first 3 to verify order
            if idx <= 3:
                logger.info(f"[{request_id}]   Position {idx}: {name} (rerank_pos: {rerank_pos}, sim: {similarity:.4f})")
            
            recommendation_items.append(
                RecommendationItem(
                    name=name,
                    url=url,
                    type=clean_value(test_type),
                    similarity=similarity,
                    description=clean_value(rec.get('Description', rec.get('description'))),
                    duration=clean_value(rec.get('Duration', rec.get('duration'))),
                    difficulty=clean_value(rec.get('Difficulty', rec.get('difficulty'))),
                    skills=clean_value(rec.get('Skills', rec.get('skills'))),
                    prerequisites=clean_value(rec.get('Prerequisites', rec.get('prerequisites'))),
                    use_cases=clean_value(rec.get('Use Cases', rec.get('use_cases'))),
                    industry=clean_value(rec.get('Industry', rec.get('industry')))
                )
            )
        
        # Log structured response
        response_data = {
            "request_id": request_id,
            "query_length": query_length,
            "recommendations_count": len(recommendation_items),
            "processing_time": elapsed_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"[{request_id}] Response: {json.dumps(response_data)}")
        
        # Return in the exact order received (preserves Gemini reranking)
        return RecommendationResponse(
            query=recommendation_request.query,
            recommendations=recommendation_items
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error processing recommendation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize recommender on startup."""
    logger.info("Starting up API server...")
    logger.info("Checking dependencies...")
    
    # Verify required files exist
    required_files = [
        os.getenv('FAISS_INDEX_FILE', 'data/shl_index.faiss'),
        os.getenv('METADATA_FILE', 'data/shl_index.pkl')
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        logger.warning(f"⚠️  Missing required files: {missing_files}")
        logger.warning("   Run 'python embedder.py' to generate the index files")
    else:
        logger.info("✅ All required files found")
    
    # Verify Gemini API key
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        logger.error("❌ GEMINI_API_KEY not found in environment variables")
    else:
        logger.info("✅ Gemini API key found")
    
    # Lazy loading - will initialize on first request
    logger.info("API server ready (recommender will load on first request)")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

