"""
Configuration from environment. All settings have defaults where safe.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Catalog source: S3 URI (s3://bucket/key) or HTTPS URL
    tools_catalog_s3_uri: Optional[str] = None
    tools_catalog_url: Optional[str] = None

    # Cache
    tools_cache_ttl_seconds: int = 300
    tools_cache_maxsize: int = 1  # single catalog object

    # Tool execution
    tool_run_timeout_seconds: int = 120

    # Logging
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"

    def get_catalog_source(self) -> Optional[str]:
        """Preferred catalog source: S3 URI first, then URL."""
        return self.tools_catalog_s3_uri or self.tools_catalog_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
