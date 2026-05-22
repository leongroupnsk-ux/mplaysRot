from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """LinkEngine API Configuration"""

    # Service
    SERVICE_NAME: str = "linkengine-api"
    SERVICE_PORT: int = 8007
    SERVICE_HOST: str = "0.0.0.0"
    DEBUG: bool = False

    # Database (PostgreSQL)
    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_USER: str = os.getenv("DB_USER", "attribly")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "attribly")
    DB_NAME: str = os.getenv("DB_NAME", "attribly")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = 3  # Dedicated DB for LinkEngine

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ClickHouse
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "clickhouse")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", 8123))
    CLICKHOUSE_DB: str = "default"

    # API Configuration
    SYSTEM_DOMAIN: str = os.getenv("SYSTEM_DOMAIN", "attribly.ru")
    DOMAIN_COST_YEARLY_RUB: int = 12_000  # Cost of domain registration/year

    # Link Settings
    SHORT_CODE_LENGTH: int = 6
    CACHE_TTL_SECONDS: int = 3600  # 1 hour for landing pages

    # Marketplace APIs
    WB_API_URL: str = "https://suppliers-api.wildberries.ru"
    OZON_API_URL: str = "https://api-seller.ozon.ru"

    # Rate Limiting
    RATE_LIMIT_LINKS_PER_MINUTE: int = 100
    RATE_LIMIT_LINKS_PER_MINUTE_FREE: int = 20

    # Verification
    SKU_VERIFICATION_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
