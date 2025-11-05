"""Main FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import ocr, auth
from app.models import HealthResponse, ErrorResponse
from datetime import datetime
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    print("🚀 Starting Menu OCR API...")
    yield
    # Shutdown
    print("🛑 Shutting down Menu OCR API...")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ocr.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
from app.routers import dishes
app.include_router(dishes.router, prefix=settings.api_prefix)
from app.routers import user_info
app.include_router(user_info.router, prefix=settings.api_prefix)
from app.routers import new_health_router
app.include_router(new_health_router.router, prefix=settings.api_prefix)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from app.services.redis_cache import RedisCache
    from app.services.supabase_client import SupabaseClient
    
    # Check services
    services = {}
    
    # Redis is optional - check but don't fail if unavailable
    try:
        redis = RedisCache()
        await redis.ping()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"optional (unavailable: {str(e)})"
    
    # Supabase is required
    try:
        supabase = SupabaseClient()
        # Simple connection test
        services["supabase"] = "healthy"
    except Exception as e:
        services["supabase"] = f"unhealthy: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.api_version,
        services=services,
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Menu OCR API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return ErrorResponse(
        error=str(exc),
        details={"type": type(exc).__name__}
    )

