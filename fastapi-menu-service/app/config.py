"""
Configuration management with security best practices
"""
import os
import secrets
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable loading"""

    # ==========================================
    # APPLICATION SETTINGS
    # ==========================================
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    api_key: Optional[str] = Field(default=None, env="API_KEY")

    # ==========================================
    # SUPABASE CONFIGURATION
    # ==========================================
    supabase_url: Optional[str] = Field(default="https://jlfqzcaospvspmzbvbxd.supabase.co", env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")

    # ==========================================
    # REDIS CONFIGURATION
    # ==========================================
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # ==========================================
    # API KEYS (External Services)
    # ==========================================
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    apify_api_token: Optional[str] = Field(default=None, env="APIFY_API_TOKEN")
    render_api_token: Optional[str] = Field(default=None, env="RENDER_API_TOKEN")

    # ==========================================
    # PAYMENT PROCESSING
    # ==========================================
    stripe_publishable_key: Optional[str] = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    stripe_secret_key: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")

    # ==========================================
    # SECURITY SETTINGS
    # ==========================================
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    fernet_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="FERNET_KEY")

    # ==========================================
    # MONITORING & LOGGING
    # ==========================================
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    cors_origins: list = Field(default=["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS")
    trusted_hosts: list = Field(default=["localhost", "127.0.0.1"], env="TRUSTED_HOSTS")

    @field_validator('cors_origins', 'trusted_hosts')
    @classmethod
    def parse_list(cls, v):
        """Parse list from environment variable"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback: split by comma
                return [item.strip() for item in v.split(',') if item.strip()]
        return v

    # ==========================================
    # DATABASE
    # ==========================================
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    class Config:
        """Pydantic configuration"""
        env_file = ".env.secrets"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"

    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_url:
            return self.redis_url
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def validate_security_settings(self):
        """Validate security-related settings"""
        if self.is_production:
            if not self.jwt_secret_key or len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")

            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")

            if not self.supabase_service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required in production")

        # Validate required API keys only in production
        if self.is_production:
            required_keys = [self.supabase_url, self.supabase_key, self.openrouter_api_key]
            if not all(required_keys):
                raise ValueError("Missing required environment variables. Check .env.secrets file.")


# Global settings instance
settings = Settings()

# Validate settings on import
settings.validate_security_settings()
