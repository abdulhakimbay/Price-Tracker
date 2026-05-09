from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Price Tracker"
    
    @property
    def DATABASE_URL(self):
        return "postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self):
        return "redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()