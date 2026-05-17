import logging
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import Optional, Any, Dict
import yaml
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Groove"
    
    # Meta API Settings
    META_ACCESS_TOKEN: str
    META_AD_ACCOUNT_ID: str
    
    # Gemini/LLM Settings
    GEMINI_API_KEY: str
    
    # Database Settings
    POSTGRES_DSN: PostgresDsn
    MONGODB_URI: str
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Configuration
    CONFIG_FILE_PATH: str = "config/sources.yaml"
    meta_ads: Dict[str, Any] = {}
    
    class Config:
        case_sensitive = True
        env_file = ".env"

def load_yaml_config(path: str) -> dict[str, Any]:
    """Load YAML configuration file."""
    config_path = Path(path)
    if not config_path.is_absolute():
        # Make path relative to project root (4 levels up from core/config.py)
        config_path = Path(__file__).parent.parent.parent.parent / path
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

settings = Settings()
try:
    _config_data = load_yaml_config(settings.CONFIG_FILE_PATH)
    settings.meta_ads = _config_data.get("meta_ads", {})
except FileNotFoundError:
    logger = logging.getLogger(__name__)
    logger.warning("Config file not found at %s, using defaults. Set up %s for full functionality.",
                   settings.CONFIG_FILE_PATH, settings.CONFIG_FILE_PATH)