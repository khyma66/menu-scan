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
from typing import Callable

from app.config import settings
from app.routers import ocr, auth, payments, user_preferences, table_extraction, new_health_router

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
        allowed_hosts=["your-domain.com", "*.your-domain.com"]  # Update with your domain
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"] if settings.is_development else ["https://your-domain.com"],
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

# Rate Limiting (Simple in-memory implementation)
request_counts = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Simple rate limiting middleware"""
    if settings.is_production:
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time())

        # Clean old entries (older than 60 seconds)
        cutoff_time = current_time - 60
        request_counts_copy = request_counts.copy()
        for ip, timestamps in request_counts_copy.items():
            request_counts[ip] = [t for t in timestamps if t > cutoff_time]

        # Check rate limit (100 requests per minute)
        if client_ip in request_counts:
            if len(request_counts[client_ip]) >= 100:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded. Try again later."}
                )
            request_counts[client_ip].append(current_time)
        else:
            request_counts[client_ip] = [current_time]

    response = await call_next(request)
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

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR Processing"])
app.include_router(table_extraction.router, prefix="/table", tags=["Table Extraction"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(user_preferences.router, prefix="/preferences", tags=["User Preferences"])
app.include_router(new_health_router.router, prefix="/health", tags=["Health Analysis"])

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
