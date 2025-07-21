from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import redis
from app.config import settings


# Redis connection for rate limiting storage
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    default_limits=["1000/day", "100/hour"]
)


def get_user_id_from_request(request: Request):
    """Extract user ID from JWT token for user-based rate limiting."""
    try:
        from app.auth.dependencies import get_current_user_optional
        user = get_current_user_optional(request)
        return user.id if user else get_remote_address(request)
    except Exception:
        return get_remote_address(request)


# User-specific limiter
user_limiter = Limiter(
    key_func=get_user_id_from_request,
    storage_uri=settings.redis_url,
    default_limits=["500/day", "50/hour"]
)


# Custom rate limit exceeded handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded responses."""
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )
    return response


# Rate limiting decorators for different endpoints
class RateLimits:
    """Common rate limiting configurations."""
    
    # Authentication endpoints
    AUTH_LOGIN = "5/minute"
    AUTH_REGISTER = "3/minute"
    
    # API endpoints
    API_READ = "100/minute"
    API_WRITE = "20/minute"
    API_HEAVY = "5/minute"
    
    # Public endpoints
    PUBLIC = "1000/hour"
    
    # Per-user limits
    USER_API = "1000/hour"
    USER_JOBS = "50/hour"
    USER_DATASETS = "100/hour"