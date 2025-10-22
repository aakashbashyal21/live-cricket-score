import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional  # Added Optional here

from models import CricketMatch, MatchesResponse, HealthCheck
from utils import MatchService

# Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Initialize FastAPI app
app = FastAPI(
    title="Cricket Match Parser API",
    description="API to parse cricket match data from Reddit's r/cricket Match Threads",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
match_service = MatchService()

@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint with health check"""
    return HealthCheck(status="healthy", timestamp=datetime.now())

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(status="healthy", timestamp=datetime.now())

@app.get("/matches/today", response_model=MatchesResponse)
async def get_today_matches(
    limit: int = Query(default=10, ge=1, le=100, description="Number of today's matches to fetch")
):
    """Get only today's cricket match threads"""
    try:
        matches = await match_service.get_today_matches(limit=limit)
        
        return MatchesResponse(
            count=len(matches),
            matches=matches,
            fetched_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Exception handlers
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )