from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/Users/nikitaosepkov/Desktop/клон mplays/.env", extra="ignore")

    app_env: str = "development"
    service_name: str = "ads-integrations"
    
    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "attribly"
    postgres_user: str = "attribly"
    postgres_password: str

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 1

    # OAuth
    secret_key: str
    encryption_key: str

    # External APIs
    yandex_direct_api_version: str = "v5"
    vk_ads_api_version: str = "5.131"
    telegram_ads_endpoint: str = "https://ads.telegram.org"
    vk_blogger_endpoint: str = "https://apis.vk.com/method"

    # Service URLs
    api_gateway_url: str = "http://api-gateway:8000"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
