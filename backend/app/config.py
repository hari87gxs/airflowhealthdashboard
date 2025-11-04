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
        ..., description="Airflow webserver URL (e.g., http://localhost:8080)"
    )
    airflow_username: Optional[str] = Field(
        None, description="Airflow username for basic auth"
    )
    airflow_password: Optional[str] = Field(
        None, description="Airflow password for basic auth"
    )
    airflow_api_token: Optional[str] = Field(
        None, description="Airflow API token (alternative to username/password)"
    )

    # AWS MWAA Configuration
    aws_region: Optional[str] = Field(
        None, description="AWS region for MWAA (e.g., us-east-1)"
    )
    mwaa_environment_name: Optional[str] = Field(
        None, description="MWAA environment name"
    )

    # Cache Configuration
    cache_ttl_seconds: int = Field(
        120, description="Cache TTL in seconds (default: 2 minutes)"
    )
    refresh_interval_seconds: int = Field(
        300, description="Background refresh interval in seconds (default: 5 minutes)"
    )

    # Redis Configuration (optional - falls back to in-memory cache)
    redis_url: Optional[str] = Field(
        None, description="Redis URL for distributed caching (optional)"
    )

    # Backend Configuration
    backend_host: str = Field("0.0.0.0", description="Backend host")
    backend_port: int = Field(8000, description="Backend port")

    # CORS Configuration
    cors_origins: list[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # API Configuration
    api_prefix: str = Field("/api/v1", description="API prefix")

    # Logging
    log_level: str = Field("INFO", description="Logging level")

    # LLM Configuration for Failure Analysis
    llm_provider: str = Field(
        "azure_openai", description="LLM provider: openai, anthropic, azure_openai"
    )
    llm_api_key: Optional[str] = Field(
        None, description="LLM API key for failure analysis"
    )
    llm_model: str = Field(
        "gpt-4o",
        description="LLM model to use (e.g., gpt-4o, gpt-4, gpt-3.5-turbo, claude-3-5-sonnet-20241022)",
    )
    llm_enabled: bool = Field(
        True, description="Enable/disable LLM-powered failure analysis"
    )

    # Azure OpenAI specific configuration
    azure_openai_endpoint: Optional[str] = Field(
        None,
        description="Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/)",
    )
    azure_openai_api_version: str = Field(
        "2024-08-01-preview", description="Azure OpenAI API version"
    )
    azure_openai_deployment_name: Optional[str] = Field(
        None, description="Azure OpenAI deployment name for your model"
    )

    # Slack Configuration
    slack_webhook_url: Optional[str] = Field(
        None, description="Slack webhook URL for notifications"
    )
    slack_enabled: bool = Field(True, description="Enable/disable Slack notifications")

    # Scheduled Reporting Configuration
    scheduled_reports_enabled: bool = Field(
        True, description="Enable/disable scheduled reports"
    )
    morning_report_hour: int = Field(
        10, description="Hour for morning report (0-23, default: 10 for 10 AM)"
    )
    morning_report_minute: int = Field(
        0, description="Minute for morning report (0-59, default: 0)"
    )
    evening_report_hour: int = Field(
        19, description="Hour for evening report (0-23, default: 19 for 7 PM)"
    )
    evening_report_minute: int = Field(
        0, description="Minute for evening report (0-59, default: 0)"
    )
    dashboard_url: str = Field(
        "https://dashboard.yourcompany.com",
        description="Public URL to the dashboard for Slack links",
    )

    @validator("airflow_base_url")
    def validate_airflow_url(cls, v):
        """Ensure Airflow URL doesn't end with slash."""
        return v.rstrip("/")

    @validator("morning_report_hour", "evening_report_hour")
    def validate_hour(cls, v):
        """Validate hour is between 0-23."""
        if not 0 <= v <= 23:
            raise ValueError("Hour must be between 0 and 23")
        return v

    @validator("morning_report_minute", "evening_report_minute")
    def validate_minute(cls, v):
        """Validate minute is between 0-59."""
        if not 0 <= v <= 59:
            raise ValueError("Minute must be between 0 and 59")
        return v

    @validator("airflow_api_token", "airflow_username", "airflow_password")
    def validate_auth(cls, v, values):
        """Ensure either API token, username/password, or MWAA config is provided."""
        if "airflow_api_token" in values:
            has_token = values.get("airflow_api_token") is not None
            has_basic = values.get("airflow_username") and values.get(
                "airflow_password"
            )
            has_mwaa = values.get("aws_region") and values.get("mwaa_environment_name")

            if not has_token and not has_basic and not has_mwaa:
                raise ValueError(
                    "Either AIRFLOW_API_TOKEN, both AIRFLOW_USERNAME and "
                    "AIRFLOW_PASSWORD, or both AWS_REGION and MWAA_ENVIRONMENT_NAME must be provided"
                )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
