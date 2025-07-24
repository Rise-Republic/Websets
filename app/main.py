from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi.errors import RateLimitExceeded

from app.monitoring.metrics import MetricsMiddleware, get_metrics_collector

from app.config import settings
from app.telemetry import configure_tracing
from app.logging_utils import configure_logging
from app.database import create_tables
from app.api.v1 import v1_router
from app.api.versioning import versioning_router
from app.middleware import (
    limiter,
    user_limiter,
    rate_limit_handler,
    AuditMiddleware,
    RBACMiddleware,
    SecurityMiddleware,
)

# Configure logging with redaction
configure_logging(settings.log_level, json=True)

# Create FastAPI app
app = FastAPI(
    title="WebSet Miner",
    description="Autonomous LLM-powered system for discovering, extracting, and structuring public web data at scale",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
configure_tracing(app)

# Add rate limiting
app.state.limiter = limiter
app.state.user_limiter = user_limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(HTTPSRedirectMiddleware)

# Add CORS middleware
cors_origins = settings.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Only trusted origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Include OPTIONS for preflight
    allow_headers=["Authorization", "Content-Type"],  # Only needed headers
)

# Security headers
app.add_middleware(SecurityMiddleware)

# Security middleware
app.add_middleware(RBACMiddleware)
app.add_middleware(AuditMiddleware)

# Metrics middleware must be added before routers so all routes are instrumented
metrics = get_metrics_collector()
app.add_middleware(MetricsMiddleware, metrics_collector=metrics)

# Include routers
app.include_router(v1_router)

# API versioning routes
app.include_router(versioning_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    origin = request.headers.get("origin")
    allowed = settings.allowed_origins
    cors_origin = origin if origin in allowed or "*" in allowed else allowed[0]
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
        },
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting WebSet Miner application")

    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")

    # Additional startup tasks can be added here
    logger.info("WebSet Miner startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down WebSet Miner application")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WebSet Miner API",
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
        reload=settings.environment == "development",
    )
