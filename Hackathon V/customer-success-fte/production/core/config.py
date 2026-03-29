# Customer Success FTE - Configuration Management
# Environment-based settings with pydantic-settings

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # =============================================================================
    # APPLICATION
    # =============================================================================

    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    app_name: str = Field(default="Customer Success FTE", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # =============================================================================
    # DATABASE
    # =============================================================================

    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="customer_success", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="postgres", description="Database password")

    db_min_connections: int = Field(default=5, description="Minimum pool connections")
    db_max_connections: int = Field(default=20, description="Maximum pool connections")
    db_command_timeout: int = Field(default=60, description="Query timeout in seconds")
    db_max_inactive_lifetime: int = Field(default=300, description="Max inactive connection lifetime (seconds)")

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # =============================================================================
    # KAFKA
    # =============================================================================

    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)"
    )
    kafka_topic_prefix: str = Field(default="customer_success", description="Kafka topic prefix")

    @property
    def kafka_topics(self) -> dict:
        """Kafka topic names."""
        return {
            "emails": f"{self.kafka_topic_prefix}.emails",
            "whatsapp": f"{self.kafka_topic_prefix}.whatsapp",
            "web_forms": f"{self.kafka_topic_prefix}.web_forms",
            "escalations": f"{self.kafka_topic_prefix}.escalations",
            "metrics": f"{self.kafka_topic_prefix}.metrics",
        }

    # =============================================================================
    # OPENAI
    # =============================================================================

    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="Default OpenAI model")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for vector search"
    )
    openai_embedding_dimensions: int = Field(
        default=1536,
        description="Embedding dimensions"
    )

    # =============================================================================
    # CHANNEL CONFIGURATION
    # =============================================================================

    # Gmail
    gmail_enabled: bool = Field(default=True, description="Enable Gmail channel")
    gmail_poll_interval: int = Field(default=30, description="Gmail poll interval (seconds)")

    # WhatsApp (Twilio)
    whatsapp_enabled: bool = Field(default=True, description="Enable WhatsApp channel")
    twilio_account_sid: Optional[str] = Field(default=None, description="Twilio account SID")
    twilio_auth_token: Optional[str] = Field(default=None, description="Twilio auth token")
    twilio_whatsapp_number: Optional[str] = Field(default=None, description="Twilio WhatsApp number")

    # Web Form
    web_form_enabled: bool = Field(default=True, description="Enable web form channel")

    # =============================================================================
    # AGENT CONFIGURATION
    # =============================================================================

    agent_max_iterations: int = Field(default=10, description="Max agent loop iterations")
    agent_tool_timeout: float = Field(default=30.0, description="Tool call timeout (seconds)")
    agent_response_max_tokens: int = Field(default=2000, description="Max response tokens")

    # =============================================================================
    # RATE LIMITING
    # =============================================================================

    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Max requests per minute per customer")

    # =============================================================================
    # METRICS & MONITORING
    # =============================================================================

    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_export_interval: int = Field(default=60, description="Metrics export interval (seconds)")

    # =============================================================================
    # SECURITY
    # =============================================================================

    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    cors_origins: list = Field(
        default=["*"],
        description="CORS allowed origins"
    )

    # =============================================================================
    # VALIDATORS
    # =============================================================================

    def validate(self) -> None:
        """Validate critical settings."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        if self.environment == "production" and self.db_password == "postgres":
            raise ValueError("Default database password not allowed in production")


# =============================================================================
# GLOBAL SETTINGS INSTANCE
# =============================================================================

settings = Settings()

# Validate on import (only if OPENAI_API_KEY is set in environment)
if os.getenv("OPENAI_API_KEY"):
    try:
        settings.validate()
    except ValueError as e:
        import warnings
        warnings.warn(f"Settings validation warning: {e}")
