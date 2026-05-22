from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/Users/nikitaosepkov/Desktop/клон mplays/.env", extra="ignore")

    app_env: str = "development"
    service_name: str = "ai-assistant"
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_api_endpoint: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.3
    openai_timeout_seconds: int = 15

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
    redis_db: int = 3

    # Rate limiting (requests per month)
    business_tier_limit: int = 50
    enterprise_tier_limit: int = 99999

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
