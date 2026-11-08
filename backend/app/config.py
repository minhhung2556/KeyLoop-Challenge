from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEBUG: bool = True
    DATABASE_PATH: str = "leads.db"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    log_level: str = "INFO"
    log_format: str = "console"
    LOG_FILE: str | None = None
    log_request_body: bool = True
    log_response_body: bool = False
    log_max_body_length: int = 4000
    BLOCKING_IO_THREAD_TOKENS: int = 40

    @property
    def database_path(self) -> Path:
        path = Path(self.DATABASE_PATH)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[1] / path
        return path


settings = Settings()
