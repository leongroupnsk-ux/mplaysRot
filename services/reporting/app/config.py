from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str
    jwt_algorithm: str = "HS256"

    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_db: str = "attribly"
    clickhouse_user: str = "attribly"
    clickhouse_password: str

    minio_endpoint: str = "minio:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "attribly-reports"
    minio_secure: bool = False

    report_presigned_ttl: int = 3600  # seconds


settings = Settings()
