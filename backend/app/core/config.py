from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import Optional, Any
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
    
    class Config:
        case_sensitive = True
        env_file = ".env"

def load_yaml_config(path: str) -> dict[str, Any]:
    """Load YAML configuration file."""
    config_path = Path(path)
    if not config_path.is_absolute():
        # Make path relative to project root
        config_path = Path(__file__).parent.parent.parent / path
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

settings = Settings()