from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_clicks: str = "attribly.clicks"
    kafka_topic_orders: str = "attribly.orders"
    kafka_topic_events: str = "attribly.events"
    kafka_group_id: str = "etl-consumer"

    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_db: str = "attribly"
    clickhouse_user: str = "attribly"
    clickhouse_password: str = ""

    # Сколько сообщений буферизировать перед batch-вставкой в CH
    batch_size: int = 500
    # Максимальное время ожидания до принудительного flush (секунды)
    flush_interval: float = 5.0


settings = Settings()
