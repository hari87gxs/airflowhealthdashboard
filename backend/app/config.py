"""
Application Configuration
Loads settings from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Airflow Configuration
    airflow_base_url: str = Field(
        ..., 
        description="Airflow webserver URL (e.g., http://localhost:8080)"
    )
    airflow_username: Optional[str] = Field(
        None, 
        description="Airflow username for basic auth"
    )
    airflow_password: Optional[str] = Field(
        None, 
        description="Airflow password for basic auth"
    )
    airflow_api_token: Optional[str] = Field(
        None, 
        description="Airflow API token (alternative to username/password)"
    )
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(
        120, 
        description="Cache TTL in seconds (default: 2 minutes)"
    )
    refresh_interval_seconds: int = Field(
        300, 
        description="Background refresh interval in seconds (default: 5 minutes)"
    )
    
    # Redis Configuration (optional - falls back to in-memory cache)
    redis_url: Optional[str] = Field(
        None, 
        description="Redis URL for distributed caching (optional)"
    )
    
    # Backend Configuration
    backend_host: str = Field("0.0.0.0", description="Backend host")
    backend_port: int = Field(8000, description="Backend port")
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # API Configuration
    api_prefix: str = Field("/api/v1", description="API prefix")
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    
    @validator("airflow_base_url")
    def validate_airflow_url(cls, v):
        """Ensure Airflow URL doesn't end with slash."""
        return v.rstrip("/")
    
    @validator("airflow_api_token", "airflow_username", "airflow_password")
    def validate_auth(cls, v, values):
        """Ensure either API token or username/password is provided."""
        if "airflow_api_token" in values:
            has_token = values.get("airflow_api_token") is not None
            has_basic = values.get("airflow_username") and values.get("airflow_password")
            
            if not has_token and not has_basic:
                raise ValueError(
                    "Either AIRFLOW_API_TOKEN or both AIRFLOW_USERNAME and "
                    "AIRFLOW_PASSWORD must be provided"
                )
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
