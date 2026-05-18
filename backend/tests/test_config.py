import pytest
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, ConfigDict
from typing import Optional
import yaml
import os
from pathlib import Path
from unittest.mock import patch

# Mock settings for testing
class TestSettings(BaseSettings):
    PROJECT_NAME: str = "Groove"
    API_V1_STR: str = "/api/v1"
    META_ACCESS_TOKEN: str = "test_token"
    META_AD_ACCOUNT_ID: str = "act_123456"
    GEMINI_API_KEY: str = "test_gemini_key"
    POSTGRES_DSN: PostgresDsn = "postgresql+asyncpg://user:pass@localhost/db"
    MONGODB_URI: str = "mongodb://localhost:27017/db"
    
    model_config = ConfigDict(env_file=".env.test")

def test_settings_load():
    """Test that settings load correctly from environment."""
    settings = TestSettings()
    assert settings.PROJECT_NAME == "Groove"
    assert settings.API_V1_STR == "/api/v1"

def test_yaml_config_loads():
    """Test that YAML configuration loads correctly."""
    config_path = Path(__file__).parent.parent.parent / "config" / "sources.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    assert "meta_ads" in config
    assert config["meta_ads"]["api_version"] == "v22.0"
    assert "campaigns" in config["meta_ads"]["fields"]
    assert config["meta_ads"]["insights_time_range_days"] == 30