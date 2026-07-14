from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Cycom ERP Backend"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = "sqlite:///./cycom_erp.db"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    DEV_BOOTSTRAP_SCHEMA: bool = False
    UPLOAD_DIR: str = "uploads"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    def assert_production_safe(self) -> None:
        if self.JWT_SECRET_KEY in ("change-me", "cycom-super-secret-key-for-development-only"):
            raise RuntimeError(
                "JWT_SECRET_KEY is a default placeholder; set a real secret in the environment."
            )


settings = Settings()
