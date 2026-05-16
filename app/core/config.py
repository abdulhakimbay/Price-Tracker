"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the API, logging, authentication, database, and Celery."""

    PROJECT_NAME: str = "Price Tracker"
    SECRET_KEY: str
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/price_tracker.txt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_TASK_QUEUE: str = "price-tracker"
    CELERY_PRICE_CHECK_INTERVAL_SECONDS: int = 300
    CELERY_TIMEZONE: str = "UTC"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "Price Tracker"
    SMTP_USE_STARTTLS: bool = True
    TELEGRAM_BOT_TOKEN: str

    @property
    def DATABASE_URL(self) -> str:
        """Build the async SQLAlchemy database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        """Build the Redis connection URL used by Celery."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Expose the broker URL used by Celery workers."""
        return self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Expose the result backend URL used by Celery workers."""
        return self.REDIS_URL

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
