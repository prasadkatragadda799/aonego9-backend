from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/aonego9"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Comma-separated list of allowed frontend origins in production, e.g.
    # "https://aonego9-user.vercel.app,https://aonego9-vendor.vercel.app".
    # Defaults to "*" for local development.
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Managed Postgres providers (Render, Heroku, ...) hand out URLs as
        # postgres:// or postgresql://, which SQLAlchemy's async engine
        # can't use directly — it needs the asyncpg driver named explicitly.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def _guard_production_config(self) -> "Settings":
        # Fail loudly at startup instead of leaking the local-dev defaults
        # into production, where they'd otherwise surface as a cryptic
        # "connect call failed" to localhost:5432 or an insecure JWT secret.
        # This almost always means the service's env vars weren't actually
        # set (e.g. it was created by pointing Render at the repo directly
        # instead of via Blueprint, so render.yaml's `fromDatabase` wiring
        # never applied) — set DATABASE_URL manually in the dashboard from
        # the Postgres instance's "Internal Connection String", or recreate
        # the service via Render's Blueprint flow.
        if self.is_production:
            if "localhost" in self.DATABASE_URL or "user:password" in self.DATABASE_URL:
                raise RuntimeError(
                    "DATABASE_URL is still the local-dev default in a production "
                    "environment. Set it to your managed Postgres connection string."
                )
            if self.SECRET_KEY == "change-me":
                raise RuntimeError("SECRET_KEY is still the default value in a production environment.")
        return self


settings = Settings()
