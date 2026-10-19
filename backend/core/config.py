from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Callrizer"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()