"""
FastAPI application with security headers and best practices
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import collections
from typing import Callable

from app.config import settings
from app.routers import ocr, auth, payments, user_preferences, table_extraction, new_health_router, dishes, user_management, pricing, menu_enrichment, enhanced_ocr_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Menu OCR API")
    yield
    logger.info("🛑 Shutting down Menu OCR API")

# Create FastAPI application
app = FastAPI(
    title="Menu OCR API",
    description="AI-powered menu optical character recognition and health analysis",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan
)

# Security Middleware
if settings.is_production:
    # HTTPS Redirect in production
    app.add_middleware(HTTPSRedirectMiddleware)

# Trusted Host Middleware
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts  # Use configurable trusted hosts
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400  # 24 hours
)

# Custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Add security headers to all responses"""
    start_time = time.time()

    response = await call_next(request)

    # Calculate request processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.supabase.co https://*.supabase.co; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp

    # HSTS (HTTP Strict Transport Security) - only in production with HTTPS
    if settings.is_production and request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

# Rate Limiting (Optimized in-memory implementation)
import collections

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = collections.defaultdict(list)
        self.last_cleanup = 0
    
    def is_rate_limited(self, client_ip: str) -> tuple[bool, int, int]:
        """Check if client is rate limited. Returns (is_limited, remaining_requests, reset_time)"""
        current_time = int(time.time())
        
        # Clean old entries every 30 seconds (not on every request)
        if current_time - self.last_cleanup >= 30:
            cutoff_time = current_time - self.window_seconds
            self.requests = collections.defaultdict(
                list, 
                {ip: [t for t in timestamps if t > cutoff_time] 
                 for ip, timestamps in self.requests.items() 
                 if [t for t in timestamps if t > cutoff_time]}
            )
            self.last_cleanup = current_time
        
        # Check current request count
        current_requests = self.requests[client_ip]
        remaining = max(0, self.max_requests - len(current_requests))
        
        # If at limit, return reset time
        if len(current_requests) >= self.max_requests:
            reset_time = min(current_requests) + self.window_seconds
            return True, remaining, reset_time
        
        # Add current request
        current_requests.append(current_time)
        return False, remaining, current_time + self.window_seconds

# Global rate limiter instance
rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Optimized rate limiting middleware with proper headers"""
    if settings.is_production:
        client_ip = request.client.host if request.client else "unknown"
        
        is_limited, remaining, reset_time = rate_limiter.is_rate_limited(client_ip)
        
        if is_limited:
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded. Try again later.",
                    "reset_time": reset_time,
                    "retry_after": reset_time - int(time.time())
                }
            )
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = "100"
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["Retry-After"] = str(reset_time - int(time.time()))
            return response

    response = await call_next(request)
    
    # Add rate limit headers to all responses
    if settings.is_production:
        client_ip = request.client.host if request.client else "unknown"
        _, remaining, reset_time = rate_limiter.is_rate_limited(client_ip)
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0",
        "timestamp": time.time()
    }

# API Key authentication (if enabled)
if settings.api_key:
    @app.middleware("http")
    async def api_key_auth(request: Request, call_next: Callable) -> Response:
        if request.url.path.startswith("/docs") or request.url.path == "/health":
            return await call_next(request)

        auth_header = request.headers.get("Authorization") or request.headers.get("X-API-Key")
        if not auth_header or auth_header != f"Bearer {settings.api_key}":
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing API key"}
            )

        response = await call_next(request)
        return response

# Include routers (routers already have their prefixes defined, so don't add duplicate prefixes)
app.include_router(auth.router)
app.include_router(ocr.router)
app.include_router(table_extraction.router)
app.include_router(payments.router)
app.include_router(user_preferences.router)
app.include_router(new_health_router.router)
app.include_router(dishes.router)
app.include_router(user_management.router)
app.include_router(pricing.router)
app.include_router(menu_enrichment.router)
app.include_router(enhanced_ocr_router.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Menu OCR API",
        "version": "1.0.0",
        "docs": "/docs" if settings.is_development else None
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        workers=4 if settings.is_production else 1
    )