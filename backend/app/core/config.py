import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ConfigDict, PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Groove"

    # Meta API Settings
    META_ACCESS_TOKEN: str
    META_AD_ACCOUNT_ID: str

    # LLM Provider: "openrouter" (default) or "lmstudio"
    LLM_PROVIDER: str = "openrouter"

    # OpenRouter (when LLM_PROVIDER=openrouter)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # LM Studio (when LLM_PROVIDER=lmstudio)
    LMSTUDIO_BASE_URL: str = "http://host.docker.internal:1234/v1"
    LMSTUDIO_MODEL: str = ""

    # Database Settings
    POSTGRES_DSN: PostgresDsn
    POSTGRES_READONLY_DSN: PostgresDsn | None = None  # type: ignore[assignment]

    @field_validator("POSTGRES_READONLY_DSN", mode="before")
    @classmethod
    def blank_string_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    MONGODB_URI: str

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://frontend:3000"

    # Configuration
    CONFIG_FILE_PATH: str = "config/sources.yaml"
    LOG_LEVEL: str = "INFO"
    meta_ads: dict[str, Any] = {}

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env")
    )

def load_yaml_config(path: str) -> dict[str, Any]:
    """Load YAML configuration file."""
    candidates = []
    if Path(path).is_absolute():
        candidates.append(Path(path))
    else:
        candidates.append(Path(__file__).parent.parent.parent.parent / path)
        candidates.append(Path(__file__).parent.parent.parent / "config" / Path(path).name)
        candidates.append(Path("/app") / path)

    for config_path in candidates:
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)

    raise FileNotFoundError(f"Config file not found. Tried: {candidates}")

settings = Settings()
try:
    _config_data = load_yaml_config(settings.CONFIG_FILE_PATH)
    settings.meta_ads = _config_data.get("meta_ads", {})
except FileNotFoundError:
    logger = logging.getLogger(__name__)
    logger.warning("Config file not found at %s, using defaults. Set up %s for full functionality.",
                   settings.CONFIG_FILE_PATH, settings.CONFIG_FILE_PATH)
