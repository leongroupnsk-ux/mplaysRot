from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/Users/nikitaosepkov/Desktop/клон mplays/.env", extra="ignore")

    app_env: str = "development"
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "attribly"
    postgres_user: str = "attribly"
    postgres_password: str

    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_db: str = "attribly"
    clickhouse_user: str = "attribly"
    clickhouse_password: str

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_clicks: str = "attribly.clicks"
    kafka_topic_orders: str = "attribly.orders"
    kafka_topic_events: str = "attribly.events"

    celery_broker_url: str
    celery_result_backend: str

    sentry_dsn: str = ""

    telegram_webhook_secret: str = ""
    messenger_max_webhook_secret: str = ""

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
