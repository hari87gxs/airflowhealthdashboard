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
    
    # LLM Configuration for Failure Analysis
    llm_provider: str = Field(
        "azure_openai", 
        description="LLM provider: openai, anthropic, azure_openai"
    )
    llm_api_key: Optional[str] = Field(
        None, 
        description="LLM API key for failure analysis"
    )
    llm_model: str = Field(
        "gpt-4o", 
        description="LLM model to use (e.g., gpt-4o, gpt-4, gpt-3.5-turbo, claude-3-5-sonnet-20241022)"
    )
    llm_enabled: bool = Field(
        True, 
        description="Enable/disable LLM-powered failure analysis"
    )
    
    # Azure OpenAI specific configuration
    azure_openai_endpoint: Optional[str] = Field(
        None,
        description="Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/)"
    )
    azure_openai_api_version: str = Field(
        "2024-08-01-preview",
        description="Azure OpenAI API version"
    )
    azure_openai_deployment_name: Optional[str] = Field(
        None,
        description="Azure OpenAI deployment name for your model"
    )
    
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
