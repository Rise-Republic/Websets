from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import create_tables
from app.api import auth_router, jobs_router, datasets_router, health_router
from app.api.v1 import v1_router
from app.api.versioning import versioning_router
from app.middleware import limiter, rate_limit_handler

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("Starting WebSet Miner application")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    logger.info("WebSet Miner startup completed")
    yield
    logger.info("Shutting down WebSet Miner application")


# Create FastAPI app
app = FastAPI(
    title="WebSet Miner",
    description="Autonomous LLM-powered system for discovering, extracting, and structuring public web data at scale",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add CORS middleware
cors_origins = settings.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Only trusted origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Include OPTIONS for preflight
    allow_headers=["Authorization", "Content-Type"],  # Only needed headers
)

# Include routers
# Legacy routes (backward compatibility)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(datasets_router)

# V1 API routes
app.include_router(v1_router)

# API versioning routes
app.include_router(versioning_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )





@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WebSet Miner API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )