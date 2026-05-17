from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    OSRM_BASE_URL: str = "http://127.0.0.1:5000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()