"""
Rate limiting middleware - limits requests per user per hour
"""
import logging
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.utils.storage import storage

logger = logging.getLogger(__name__)
settings = get_settings()

# Paths that are exempt from rate limiting
EXEMPT_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/auth/register", "/auth/login"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        if path in EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Get identifier from JWT or IP
        identifier = self._get_identifier(request)

        result = storage.get_rate_limit(
            identifier=identifier,
            window=settings.rate_limit_window,
            max_requests=settings.rate_limit_requests
        )

        reset_dt = datetime.utcfromtimestamp(result["reset_at"])

        if not result["allowed"]:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Maximum {settings.rate_limit_requests} requests per hour.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "reset_at": reset_dt.isoformat()
                },
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": reset_dt.isoformat(),
                    "Retry-After": str(settings.rate_limit_window)
                }
            )

        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
        response.headers["X-RateLimit-Reset"] = reset_dt.isoformat()

        return response

    def _get_identifier(self, request: Request) -> str:
        """Extract user identifier from Authorization header or fall back to IP"""
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            username = storage.get_token_user(token)
            if username:
                return f"user:{username}"

        # Fall back to IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}"