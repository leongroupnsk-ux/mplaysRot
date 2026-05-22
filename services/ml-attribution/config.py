from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/Users/nikitaosepkov/Desktop/клон mplays/.env", extra="ignore")

    app_env: str = "development"
    service_name: str = "ml-attribution"
    
    # Database
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "attribly"
    postgres_user: str = "attribly"
    postgres_password: str

    # ClickHouse
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_db: str = "attribly"
    clickhouse_user: str = "attribly"
    clickhouse_password: str

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 2

    # ML Model
    model_confidence_threshold: float = 0.7
    lookback_hours: int = 24
    retrain_interval_hours: int = 24

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
