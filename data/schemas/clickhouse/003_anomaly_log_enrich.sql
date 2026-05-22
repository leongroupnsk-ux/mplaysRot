-- Migration 003: enrich anomaly_log with user_id, ad_platform, and a notified index
--
-- Why:
--   anomaly_log was created in 001 with only campaign-level fields.
--   Additions here make the table self-contained for analytics queries
--   ("all anomalies for user X on platform Y") and enable efficient
--   polling of unprocessed rows by the Celery alert task.
--
-- Run via:
--   clickhouse-client --multiquery < 003_anomaly_log_enrich.sql

-- user_id is Nullable because rows written before this migration have no value.
ALTER TABLE anomaly_log
    ADD COLUMN IF NOT EXISTS user_id    Nullable(UUID),
    ADD COLUMN IF NOT EXISTS ad_platform LowCardinality(String) DEFAULT '';

-- set(2) index covers the two values 0/1 and makes WHERE notified = 0 skip
-- entire granules that are fully notified — critical once the table grows large.
ALTER TABLE anomaly_log
    ADD INDEX IF NOT EXISTS idx_notified (notified) TYPE set(2) GRANULARITY 1;

-- Materialise the index for existing data.
ALTER TABLE anomaly_log MATERIALIZE INDEX idx_notified;
