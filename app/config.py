"""Configuration via environment variables."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    upstream_base_url: str = "https://api.deepseek.com/v1"
    upstream_api_key: str = ""
    client_api_keys: str = ""  # comma-separated
    prompts_file: str = "prompts.yaml"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def client_keys(self) -> set[str]:
        return {k.strip() for k in self.client_api_keys.split(",") if k.strip()}


settings = Settings()


@lru_cache(maxsize=1)
def load_prompts() -> dict:
    path = Path(settings.prompts_file)
    if not path.exists():
        return {"system_prompt": ""}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"system_prompt": ""}
